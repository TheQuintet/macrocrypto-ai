# import logging
# from pathlib import Path
# from typing import Dict, Any, Tuple
# import pandas as pd

# from app.utils.feature_loader import FeatureLoader
# from app.ai.models.lightgbm_model import LightGBMModel
# from app.ai.models.xgboost_model import XGBoostModel
# from app.ai.models.prophet_model import ProphetModel
# from app.ai.comparison import ModelComparisonEngine

# logger = logging.getLogger(__name__)

# # --- Adapter: Map feature names to model expectations and clean timezones ---
# def adapt_columns(df: pd.DataFrame) -> pd.DataFrame:
#     """Maps actual dataset column names to model expectations and strips timezones from 'ds'."""
#     df = df.copy()
#     rename_map = {
#         'observation_date': 'ds',
#         'target_next_price': 'y'
        
#     }
#     # Only rename columns that actually exist in the dataframe
#     actual_rename = {k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns}
#     df = df.rename(columns=actual_rename)
    
#     # Prophet requires 'ds' to be timezone-naive; safely strip timezone if present
#     if 'ds' in df.columns:
#         df['ds'] = pd.to_datetime(df['ds']).apply(
#             lambda x: x.tz_localize(None) if pd.notnull(x) and getattr(x, 'tzinfo', None) is not None else x
#         )
        
#     return df
# # --- Step 1: Load Features ---
# def load_features() -> Tuple[pd.DataFrame, pd.DataFrame]:
#     """Loads and adapts training and validation feature partitions."""
#     logger.info("Step 1: Loading feature partitions...")
#     loader = FeatureLoader()
#     train_df = loader.load_partition("train")
#     val_df = loader.load_partition("val")
    
#     # Map columns to match model expectations
#     train_df = adapt_columns(train_df)
#     val_df = adapt_columns(val_df)
    
#     logger.info(f"Loaded and adapted train shape: {train_df.shape}, val shape: {val_df.shape}")
#     return train_df, val_df

# # --- Step 2: Instantiate Models ---
# def instantiate_models() -> Dict[str, Any]:
#     """Initializes the 6 candidate model variants (fresh vs. warm/incremental)."""
#     logger.info("Step 2: Instantiating candidate models...")
#     models = {
#         "prophet_fresh": ProphetModel(strategy="fresh"),
#         "prophet_warm": ProphetModel(strategy="warm"),
#         "xgboost_fresh": XGBoostModel(strategy="fresh"),
#         "xgboost_incremental": XGBoostModel(strategy="incremental"),
#         "lightgbm_fresh": LightGBMModel(strategy="fresh"),
#         "lightgbm_incremental": LightGBMModel(strategy="incremental"),
#     }
#     logger.info(f"Initialized models: {list(models.keys())}")
#     return models

# # --- Step 3: Train Models ---
# def train_models(models: Dict[str, Any], train_df: pd.DataFrame) -> Dict[str, Any]:
#     """Trains each candidate model on the full training dataframe."""
#     logger.info("Step 3: Training models...")
#     trained_models = {}
#     for name, model in models.items():
#         logger.info(f"Training model: {name}...")
#         model.train(train_df)
#         trained_models[name] = model
#     return trained_models


# # --- Step 4: Test and Evaluate Models ---
# def evaluate_models(models: Dict[str, Any], val_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
#     """Evaluates candidate models against the validation dataset."""
#     logger.info("Step 4: Testing and evaluating models...")
    
#     # Separate features and target from validation dataframe
#     target_col = 'y' if 'y' in val_df.columns else 'target_next_price'
#     drop_cols = [target_col, 'ds'] if 'ds' in val_df.columns else [target_col]
#     X_val = val_df.drop(columns=drop_cols, errors='ignore')
#     y_val = val_df[target_col]
    
#     evaluation_results = {}
#     for name, model in models.items():
#         logger.info(f"Evaluating model: {name}...")
#         metrics = model.get_metrics() if hasattr(model, "get_metrics") else {}
#         evaluation_results[name] = metrics
#     return evaluation_results


# # --- Step 5: Compare and Select the Winner ---
# def compare_and_select_winner(models: Dict[str, Any], val_df: pd.DataFrame) -> Tuple[str, Any]:
#     """Compares candidate models using ModelComparisonEngine and returns the winning champion model."""
#     logger.info("Step 5: Comparing models to select the winner...")
    
#     comparator = ModelComparisonEngine(models=models)
#     comparison_result = comparator.compare(val_df)
    
#     winning_name = comparison_result.best_model
#     if not winning_name or winning_name not in models:
#         # Fallback to the first model if best_model is unassigned
#         winning_name = list(models.keys())[0]
        
#     winning_model = models[winning_name]
#     logger.info(f"🏆 Winning Model Selected: {winning_name}")
#     return winning_name, winning_model


# # --- Step 6: Save Winning Model ---
# def save_winning_model(winning_name: str, winning_model: Any, output_dir: str = "app/ai/artifacts") -> str:
#     """Serializes and saves the winning model artifact to disk."""
#     logger.info(f"Step 6: Saving winning model ({winning_name})...")
#     path = Path(output_dir)
#     path.mkdir(parents=True, exist_ok=True)
    
#     file_path = path / "champion_model.pkl"
#     winning_model.save(str(file_path))
#     logger.info(f"Successfully saved champion model to {file_path}")
#     return str(file_path)


# def execute_model_training_workflow() -> str:
#     """Executes the complete 6-step model training and deployment pipeline."""
#     train_df, val_df = load_features()
#     models = instantiate_models()
#     trained_models = train_models(models, train_df)
#     _ = evaluate_models(trained_models, val_df)
#     winning_name, winning_model = compare_and_select_winner(trained_models, val_df)
#     saved_path = save_winning_model(winning_name, winning_model)
    
#     return saved_path

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     print("=== Running Complete Model Training Pipeline ===")
#     final_artifact_path = execute_model_training_workflow()
#     print(f"Pipeline completed successfully! Champion saved to: {final_artifact_path}")


import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
from tabulate import tabulate

from app.utils.feature_loader import FeatureLoader
from app.ai.models.lightgbm_model import LightGBMModel
from app.ai.models.xgboost_model import XGBoostModel
from app.ai.models.prophet_model import ProphetModel
from app.ai.comparison import ModelComparisonEngine

logger = logging.getLogger(__name__)

# --- Adapter: Map feature names to model expectations and clean timezones ---
def adapt_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Maps actual dataset column names to model expectations and strips timezones from 'ds'."""
    df = df.copy()
    rename_map = {
        'observation_date': 'ds',
        'target_next_price': 'y'
    }
    # Only rename columns that actually exist in the dataframe
    actual_rename = {k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns}
    df = df.rename(columns=actual_rename)
    
    # Prophet requires 'ds' to be timezone-naive; safely strip timezone if present
    if 'ds' in df.columns:
        df['ds'] = pd.to_datetime(df['ds']).apply(
            lambda x: x.tz_localize(None) if pd.notnull(x) and getattr(x, 'tzinfo', None) is not None else x
        )
        
    return df

# --- Step 1: Load Features ---
def load_features() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads and adapts training and validation feature partitions."""
    logger.info("Step 1: Loading feature partitions...")
    loader = FeatureLoader()
    train_df = loader.load_partition("train")
    val_df = loader.load_partition("val")
    
    # Map columns to match model expectations
    train_df = adapt_columns(train_df)
    val_df = adapt_columns(val_df)
    
    logger.info(f"Loaded and adapted train shape: {train_df.shape}, val shape: {val_df.shape}")
    return train_df, val_df

# --- Step 2: Instantiate Models ---
def instantiate_models() -> Dict[str, Any]:
    """Initializes the 6 candidate model variants (fresh vs. warm/incremental)."""
    logger.info("Step 2: Instantiating candidate models...")
    models = {
        "prophet_fresh": ProphetModel(strategy="fresh"),
        "prophet_warm": ProphetModel(strategy="warm"),
        "xgboost_fresh": XGBoostModel(strategy="fresh"),
        "xgboost_incremental": XGBoostModel(strategy="incremental"),
        "lightgbm_fresh": LightGBMModel(strategy="fresh"),
        "lightgbm_incremental": LightGBMModel(strategy="incremental"),
    }
    logger.info(f"Initialized models: {list(models.keys())}")
    return models

# --- Step 3: Train Models ---
def train_models(models: Dict[str, Any], train_df: pd.DataFrame) -> Dict[str, Any]:
    """Trains each candidate model on the full training dataframe."""
    logger.info("Step 3: Training models...")
    trained_models = {}
    for name, model in models.items():
        logger.info(f"Training model variant: {name}...")
        model.train(train_df)
        trained_models[name] = model
    return trained_models

# --- Step 4 & 5: Evaluate, Tabulate, and Compare Models ---
def evaluate_and_compare_models(models: Dict[str, Any], val_df: pd.DataFrame) -> Tuple[str, Any]:
    """Evaluates candidate models, displays formatted metric tables, and selects the winning champion."""
    logger.info("Step 4: Testing and evaluating models...")
    
    evaluation_records = []
    for name, model in models.items():
        try:
            metrics = getattr(model, "last_metrics", {})
            if not metrics and hasattr(model, "get_metrics"):
                metrics = model.get_metrics()
                
            mae = metrics.get("mae", float("nan"))
            rmse = metrics.get("rmse", float("nan"))
            mape_raw = metrics.get("mape", float("nan"))
            mape_str = f"{mape_raw * 100:.2f}%" if pd.notnull(mape_raw) else "N/A"
            
            evaluation_records.append({
                "Model Variant": name,
                "MAE": f"{mae:.4f}" if pd.notnull(mae) else "N/A",
                "RMSE": f"{rmse:.4f}" if pd.notnull(rmse) else "N/A",
                "MAPE (%)": mape_str
            })
        except Exception as e:
            logger.warning(f"Could not retrieve metrics for {name}: {e}")
            evaluation_records.append({
                "Model Variant": name,
                "MAE": "Error",
                "RMSE": "Error",
                "MAPE (%)": "Error"
            })

    # Print Tabular Report for Individual Evaluations
    print("\n" + "="*70)
    print("📊 INDIVIDUAL MODEL VALIDATION PERFORMANCE REPORT")
    print("="*70)
    eval_df = pd.DataFrame(evaluation_records)
    print(tabulate(eval_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    print("="*70 + "\n")

    # --- Step 5: Run Comparison Engine ---
    logger.info("Step 5: Running ModelComparisonEngine consensus and selection...")
    comparator = ModelComparisonEngine(models=models)
    comparison_result = comparator.compare(val_df)
    
    comparison_records = []
    for name, pred in comparison_result.predictions.items():
        status = "Failed" if pred.error else "Success"
        error_msg = str(pred.error) if pred.error else "-"
        comparison_records.append({
            "Model Variant": name,
            "Execution Status": status,
            "Error Details": error_msg
        })
        
    print("\n" + "="*70)
    print("🤝 COMPARISON ENGINE EXECUTION SUMMARY")
    print("="*70)
    print(f"• Agreement Score : {comparison_result.agreement_score:.3f}")
    print(f"• Models Run      : {', '.join(comparison_result.models_run)}")
    print(f"• Models Failed   : {', '.join(comparison_result.models_failed) if comparison_result.models_failed else 'None'}")
    print(f"• Total Elapsed   : {comparison_result.total_elapsed_seconds:.2f}s")
    print("-" * 70)
    comp_df = pd.DataFrame(comparison_records)
    print(tabulate(comp_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    print("="*70 + "\n")

    winning_name = comparison_result.best_model
    if not winning_name or winning_name not in models:
        winning_name = list(models.keys())[0]
        
    winning_model = models[winning_name]
    logger.info(f"🏆 Winning Champion Model Crowned: {winning_name}")
    return winning_name, winning_model

# --- Step 6: Save Winning Model ---
def save_winning_model(winning_name: str, winning_model: Any, output_dir: str = "app/ai/artifacts") -> str:
    """Serializes and saves the winning model artifact to disk."""
    logger.info(f"Step 6: Saving winning model ({winning_name})...")
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    file_path = path / "champion_model.pkl"
    winning_model.save(str(file_path))
    logger.info(f"Successfully saved champion model to {file_path}")
    return str(file_path)

def execute_model_training_workflow() -> str:
    """Executes the complete 6-step model training, tabulation, comparison, and deployment pipeline."""
    train_df, val_df = load_features()
    models = instantiate_models()
    trained_models = train_models(models, train_df)
    winning_name, winning_model = evaluate_and_compare_models(trained_models, val_df)
    saved_path = save_winning_model(winning_name, winning_model)
    
    return saved_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Running Complete Model Training & Evaluation Pipeline ===")
    final_artifact_path = execute_model_training_workflow()
    print(f"Pipeline completed successfully! Champion saved to: {final_artifact_path}")