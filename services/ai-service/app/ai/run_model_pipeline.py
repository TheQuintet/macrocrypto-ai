"""Train, compare, and save forecasting model candidates.

Candidates are selected by validation error against held-out targets.
The test partition is deliberately not loaded by this workflow.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from tabulate import tabulate

from app.ai.base import ForecastModel
from app.ai.metrics import current_prices_for_target_dates, directional_accuracy
from app.ai.models.lightgbm_model import LightGBMModel
from app.ai.models.prophet_model import ProphetModel
from app.ai.models.xgboost_model import XGBoostModel
from app.utils.feature_loader import FeatureLoader

logger = logging.getLogger(__name__)

WARMUP_FRACTION = 0.8
MIN_WARMUP_ROWS = 60


def adapt_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map prepared feature names to the forecasting-model contract."""
    adapted = df.copy()
    rename_map = {
        "observation_date": "ds",
        "target_next_price": "y",
    }
    actual_rename = {
        source: target
        for source, target in rename_map.items()
        if source in adapted.columns and target not in adapted.columns
    }
    adapted = adapted.rename(columns=actual_rename)

    if "ds" in adapted.columns:
        dates = pd.to_datetime(adapted["ds"])
        if dates.dt.tz is not None:
            dates = dates.dt.tz_localize(None)
        adapted["ds"] = dates

    return adapted


def load_features() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and adapt training and validation feature partitions."""
    logger.info("Loading training and validation feature partitions")
    loader = FeatureLoader()
    train_df = adapt_columns(loader.load_partition("train"))
    val_df = adapt_columns(loader.load_partition("val"))
    _validate_partition(train_df, "train")
    _validate_partition(val_df, "validation")

    logger.info(
        "Loaded partitions: train=%s rows, validation=%s rows",
        len(train_df),
        len(val_df),
    )
    return train_df, val_df


def instantiate_models() -> Dict[str, ForecastModel]:
    """Create the six supported model and strategy candidates."""
    return {
        "prophet_fresh": ProphetModel(strategy="fresh"),
        "prophet_warm": ProphetModel(strategy="warm"),
        "xgboost_fresh": XGBoostModel(strategy="fresh"),
        "xgboost_incremental": XGBoostModel(strategy="incremental"),
        "lightgbm_fresh": LightGBMModel(strategy="fresh"),
        "lightgbm_incremental": LightGBMModel(strategy="incremental"),
    }


def train_models(
    models: Dict[str, ForecastModel],
    train_df: pd.DataFrame,
) -> Dict[str, ForecastModel]:
    """Train all candidates, exercising each configured strategy.

    Warm/incremental candidates first train a chronological seed model,
    save it to a temporary checkpoint, and then train on the full
    training history with the model's warm-start path enabled.
    """
    _validate_partition(train_df, "train")
    ordered_train = train_df.sort_values("ds").reset_index(drop=True)
    split_at = int(len(ordered_train) * WARMUP_FRACTION)
    if split_at < MIN_WARMUP_ROWS or split_at >= len(ordered_train):
        raise ValueError(
            f"Training partition needs at least {MIN_WARMUP_ROWS + 1} "
            "rows to compare warm/incremental candidates"
        )

    seed_data = ordered_train.iloc[:split_at].copy()
    expected_modes = {
        "fresh": "fresh",
        "warm": "warm",
        "incremental": "incremental",
    }

    with tempfile.TemporaryDirectory(prefix="model_candidates_") as temp_dir:
        for name, model in models.items():
            strategy = getattr(model, "strategy", None)
            if strategy not in expected_modes:
                raise ValueError(
                    f"Candidate '{name}' has unsupported strategy "
                    f"{strategy!r}"
                )

            logger.info("Training candidate %s (%s)", name, strategy)
            if strategy == "fresh":
                model.train(ordered_train.copy())
                actual_mode = getattr(model, "last_training_mode", "fresh")
            else:
                model.train(seed_data.copy())
                checkpoint = Path(temp_dir) / f"{name}{_model_extension(model)}"
                model.save(str(checkpoint))
                model.train(
                    ordered_train.copy(),
                    warm_start=True,
                    previous_model_path=str(checkpoint),
                )
                actual_mode = getattr(model, "last_training_mode", None)

            expected_mode = expected_modes[strategy]
            if actual_mode != expected_mode:
                raise RuntimeError(
                    f"Candidate '{name}' requested {expected_mode} training "
                    f"but model used {actual_mode!r}"
                )

    return models


def evaluate_and_compare_models(
    models: Dict[str, ForecastModel],
    val_df: pd.DataFrame,
) -> Tuple[str, ForecastModel] | None:
    """Score candidates and return the lowest-MAE candidate if eligible."""
    _validate_partition(val_df, "validation")
    if not models:
        raise ValueError("At least one model is required for evaluation")

    actual = val_df[["ds", "y"]].copy()
    actual["ds"] = pd.to_datetime(actual["ds"])
    actual = actual[np.isfinite(actual["y"]) & (actual["y"] != 0)]
    if actual["ds"].duplicated().any():
        raise ValueError("Validation partition contains duplicate dates")
    actual_by_date = actual.set_index("ds")["y"]

    predictions: Dict[str, pd.DataFrame] = {}
    failures: Dict[str, str] = {}
    for name, model in models.items():
        try:
            prediction = model.predict(val_df.copy())
            missing = {"ds", "yhat"} - set(prediction.columns)
            if missing:
                raise ValueError(
                    f"Prediction output is missing columns: {sorted(missing)}"
                )

            prediction = prediction[["ds", "yhat"]].copy()
            prediction["ds"] = pd.to_datetime(prediction["ds"])
            prediction = prediction[np.isfinite(prediction["yhat"])]
            if prediction["ds"].duplicated().any():
                raise ValueError("Prediction output contains duplicate dates")
            predictions[name] = prediction.set_index("ds")["yhat"].to_frame()
        except Exception as exc:
            logger.exception("Validation prediction failed for %s", name)
            failures[name] = f"{type(exc).__name__}: {exc}"

    common_dates = set(actual_by_date.index)
    for prediction in predictions.values():
        common_dates.intersection_update(prediction.index)

    if failures:
        failure_table = [
            {"Model Variant": name, "Status": "FAILED", "Details": error}
            for name, error in failures.items()
        ]
        print(tabulate(failure_table, headers="keys", tablefmt="github"))
        raise RuntimeError(
            "Cannot select a winner because one or more candidates failed "
            "validation prediction"
        )
    if not common_dates:
        raise RuntimeError(
            "Candidates have no common finite validation predictions"
        )

    ordered_dates = sorted(common_dates)
    actual_values = actual_by_date.loc[ordered_dates].to_numpy(dtype=float)
    if not np.isfinite(actual_values).all():
        raise ValueError("Validation targets contain non-finite values")
    current_prices = current_prices_for_target_dates(val_df, ordered_dates)

    records = []
    for name, prediction in predictions.items():
        predicted_values = prediction.loc[ordered_dates, "yhat"].to_numpy(
            dtype=float
        )
        errors = actual_values - predicted_values
        records.append(
            {
                "Model Variant": name,
                "Validation Rows": len(ordered_dates),
                "MAE": float(np.mean(np.abs(errors))),
                "RMSE": float(np.sqrt(np.mean(np.square(errors)))),
                "MAPE (%)": float(
                    np.mean(np.abs(errors / actual_values)) * 100
                ),
                "Directional Accuracy (%)": directional_accuracy(
                    actual_values, predicted_values, current_prices
                ),
            }
        )

    persistence_errors = actual_values - current_prices
    baseline = {
        "Model Variant": "naive_persistence_baseline",
        "Validation Rows": len(ordered_dates),
        "MAE": float(np.mean(np.abs(persistence_errors))),
        "RMSE": float(np.sqrt(np.mean(np.square(persistence_errors)))),
        "MAPE (%)": float(
            np.mean(np.abs(persistence_errors / actual_values)) * 100
        ),
        "Directional Accuracy (%)": directional_accuracy(
            actual_values, current_prices, current_prices
        ),
    }
    records.sort(
        key=lambda row: (
            row["MAE"],
            row["MAPE (%)"],
            row["Model Variant"],
        )
    )
    display_records = records + [baseline]
    print(
        f"\nValidation scores on {len(ordered_dates)} shared dates "
        f"({ordered_dates[0]} to {ordered_dates[-1]}):"
    )
    print(
        "Stored model MAPE is in percentage points (for example, 0.3213 "
        "means 0.3213%, not 32.13%)."
    )
    print(
        "Directional accuracy compares each predicted/actual next-day move "
        "against that date's BTC price; persistence predicts no move."
    )
    print(
        tabulate(
            display_records,
            headers="keys",
            tablefmt="github",
            floatfmt=".4f",
        )
    )

    winning_name = records[0]["Model Variant"]
    if records[0]["MAE"] >= baseline["MAE"]:
        message = (
            "No eligible model: no candidate beats naive persistence on "
            f"shared validation dates by MAE (best model="
            f"{records[0]['MAE']:.4f}, persistence={baseline['MAE']:.4f}). "
            "No model was selected or saved."
        )
        logger.info(message)
        print(message)
        return None

    logger.info("Selected validation winner: %s", winning_name)
    return winning_name, models[winning_name]


def save_winning_model(
    winning_name: str,
    winning_model: ForecastModel,
    output_dir: str = "models/evaluation_candidates",
) -> str:
    """Save the selected candidate using its native model format."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    artifact_path = output_path / f"{winning_name}{_model_extension(winning_model)}"
    winning_model.save(str(artifact_path))
    logger.info("Saved selected evaluation candidate to %s", artifact_path)
    return str(artifact_path)


def execute_model_training_workflow() -> str | None:
    """Train candidates and save a validation winner, if it beats persistence."""
    train_df, val_df = load_features()
    models = train_models(instantiate_models(), train_df)
    selection = evaluate_and_compare_models(models, val_df)
    if selection is None:
        return None

    winning_name, winning_model = selection
    return save_winning_model(winning_name, winning_model)


def _validate_partition(data: pd.DataFrame, name: str) -> None:
    if data is None or data.empty:
        raise ValueError(f"{name.capitalize()} partition is empty")

    required = {"ds", "y"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(
            f"{name.capitalize()} partition is missing required columns: "
            f"{sorted(missing)}"
        )
    if data["ds"].isna().any():
        raise ValueError(f"{name.capitalize()} partition has missing dates")
    if data["y"].isna().any():
        raise ValueError(f"{name.capitalize()} partition has missing targets")


def _model_extension(model: ForecastModel) -> str:
    if isinstance(model, (ProphetModel, XGBoostModel)):
        return ".json"
    if isinstance(model, LightGBMModel):
        return ".txt"
    raise TypeError(
        f"Unsupported model type for artifact serialization: "
        f"{type(model).__name__}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Training and evaluating six forecasting candidates ===")
    artifact_path = execute_model_training_workflow()
    if artifact_path is not None:
        print(f"Selected candidate saved to: {artifact_path}")
