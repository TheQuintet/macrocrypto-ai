from pathlib import Path
from typing import Optional

import pandas as pd
import pytest

from app.ai.run_model_pipeline import (
    evaluate_and_compare_models,
    train_models,
)


class PipelineFakeModel:
    def __init__(
        self,
        strategy: str,
        predictions: Optional[pd.DataFrame] = None,
        fail_on_incremental: bool = False,
    ) -> None:
        self.strategy = strategy
        self.predictions = predictions
        self.fail_on_incremental = fail_on_incremental
        self.last_training_mode: Optional[str] = None
        self.train_calls: list[tuple[bool, Optional[str], int]] = []

    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> None:
        self.train_calls.append(
            (warm_start, previous_model_path, len(data))
        )
        if warm_start and self.fail_on_incremental:
            self.last_training_mode = "fresh"
            return
        self.last_training_mode = (
            "warm" if self.strategy == "warm" and warm_start
            else "incremental" if self.strategy == "incremental" and warm_start
            else "fresh"
        )
        if warm_start:
            assert previous_model_path is not None
            assert Path(previous_model_path).exists()

    def save(self, path: str) -> None:
        Path(path).write_text("checkpoint", encoding="utf-8")

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        if self.predictions is None:
            raise AssertionError("No prediction fixture configured")
        return self.predictions.copy()


def test_train_models_uses_seed_then_strategy_training(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.ai.run_model_pipeline._model_extension",
        lambda _model: ".checkpoint",
    )
    training_data = pd.DataFrame(
        {
            "ds": pd.date_range("2020-01-01", periods=100, freq="D"),
            "y": range(100),
        }
    )
    models = {
        "fresh": PipelineFakeModel("fresh"),
        "warm": PipelineFakeModel("warm"),
        "incremental": PipelineFakeModel("incremental"),
    }

    train_models(models, training_data)

    assert len(models["fresh"].train_calls) == 1
    assert models["fresh"].train_calls[0][0] is False
    for strategy in ("warm", "incremental"):
        calls = models[strategy].train_calls
        assert len(calls) == 2
        assert calls[0] == (False, None, 80)
        assert calls[1][0] is True
        assert calls[1][2] == 100


def test_train_models_rejects_strategy_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.ai.run_model_pipeline._model_extension",
        lambda _model: ".checkpoint",
    )
    training_data = pd.DataFrame(
        {
            "ds": pd.date_range("2020-01-01", periods=100, freq="D"),
            "y": range(100),
        }
    )

    with pytest.raises(RuntimeError, match="requested incremental training"):
        train_models(
            {"incremental": PipelineFakeModel(
                "incremental", fail_on_incremental=True
            )},
            training_data,
        )


def test_evaluation_selects_by_validation_error_on_shared_dates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    validation = pd.DataFrame(
        {"ds": dates, "y": [10.0, 20.0, 30.0]}
    )
    models = {
        "lower_train_error": PipelineFakeModel(
            "fresh",
            pd.DataFrame(
                {"ds": dates[:2], "yhat": [10.0, 22.0]}
            ),
        ),
        "higher_train_error": PipelineFakeModel(
            "fresh",
            pd.DataFrame(
                {"ds": dates[1:], "yhat": [25.0, 30.0]}
            ),
        ),
    }

    winner_name, winner = evaluate_and_compare_models(models, validation)

    assert winner_name == "lower_train_error"
    assert winner is models["lower_train_error"]
    output = capsys.readouterr().out
    assert "Directional Accuracy (%)" in output
    assert "naive_persistence_baseline" in output
    assert "0.0000" in output


def test_evaluation_does_not_select_if_candidate_prediction_fails() -> None:
    validation = pd.DataFrame(
        {
            "ds": pd.date_range("2024-01-01", periods=2, freq="D"),
            "y": [10.0, 20.0],
        }
    )
    models = {
        "working": PipelineFakeModel(
            "fresh",
            pd.DataFrame(
                {
                    "ds": validation["ds"],
                    "yhat": [10.0, 20.0],
                }
            ),
        ),
        "failed": PipelineFakeModel("fresh"),
    }

    with pytest.raises(RuntimeError, match="one or more candidates failed"):
        evaluate_and_compare_models(models, validation)


def test_evaluation_does_not_select_model_worse_than_persistence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    validation = pd.DataFrame(
        {"ds": dates, "y": [10.0, 20.0, 30.0]}
    )
    models = {
        "poor_model": PipelineFakeModel(
            "fresh",
            pd.DataFrame(
                {"ds": dates[1:], "yhat": [40.0, 50.0]}
            ),
        )
    }

    result = evaluate_and_compare_models(models, validation)

    output = capsys.readouterr().out
    assert "naive_persistence_baseline" in output
    assert "No eligible model" in output
    assert "No model was selected or saved" in output
    assert result is None
