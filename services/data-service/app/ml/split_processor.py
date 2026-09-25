from pathlib import Path
import pandas as pd

from app.ml.splitting_config import SplitConfig
from app.ml.target_generator import TargetGenerator
from app.ml.walk_forward import WalkForwardSplitter


class SplitProcessor:
    """Manages Stage 6 data governance, target generation, and walk-forward

    chronological splitting with strict leakage prevention buffers.
    """

    def __init__(self, split_config: SplitConfig = None):
        self.split_config = split_config or SplitConfig()
        self.target_generator = TargetGenerator(price_column="btc_price")
        self.splitter = WalkForwardSplitter(config=self.split_config)

    def process(self, raw_df: pd.DataFrame) -> dict:
        """Executes full Stage 6 pipeline and returns partitioned datasets

        and the live inference frontier.
        """
        df = raw_df.copy()
        initial_len = len(df)
        print(f"[Stage 6] Initial raw rows: {initial_len}")

        # 1. Purge warmup records
        df = df[df["warmup_complete"] == 1].copy()
        print(
            f"[Stage 6 Governance] Dropped {initial_len - len(df)} warmup rows"
            f" (warmup_complete == 0). Remaining: {len(df)}"
        )

        # 2. Drop records missing active_addresses
        pre_drop_len = len(df)
        df = df.dropna(subset=["active_addresses"]).copy()
        print(
            f"[Stage 6 Governance] Dropped {pre_drop_len - len(df)} rows with"
            f" missing active_addresses. Clean Baseline: {len(df)} rows"
        )

        # 3. Apply forward-fill strictly to NaN values in unemployment and generate imputation flag
        if "unemployment" in df.columns:
            mask = df["unemployment"].isna()
            n_null = mask.sum()
            if n_null > 0:
                df["unemployment_is_imputed"] = mask.astype(int)
                df["unemployment"] = df["unemployment"].ffill()
                print(f"[Stage 6 Governance] Forward-filled {n_null} unemployment NaN rows and added 'unemployment_is_imputed' flag.")
            else:
                print("[Stage 6 Governance] No NaN in unemployment; no ffill needed.")

        # 4. Generate target and split out live frontier
        supervised_df, live_frontier = self.target_generator.split_supervised_data(
            df
        )
        print(
            f"[Stage 6] Supervised rows after target separation:"
            f" {len(supervised_df)}"
        )

        # 5. Compute chronological walk-forward splits
        bounds = self.splitter.split_indices(len(supervised_df))

        train_start, train_end = bounds["train"]
        val_start, val_end = bounds["val"]
        test_start, test_end = bounds["test"]

        train_df = supervised_df.iloc[train_start:train_end].copy()
        val_df = supervised_df.iloc[val_start:val_end].copy()
        test_df = supervised_df.iloc[test_start:test_end].copy()

        total_split_rows = len(train_df) + len(val_df) + len(test_df)
        purged_embargo_rows = len(supervised_df) - total_split_rows

        print(
            f"[Stage 6 Splits] Train: {len(train_df)}, Val: {len(val_df)}, Test:"
            f" {len(test_df)}"
        )
        print(
            f"[Stage 6 Buffers] Purge/Embargo dropped boundary rows:"
            f" {purged_embargo_rows} (Total Supervised Split:"
            f" {total_split_rows})"
        )

        return {
            "train": train_df,
            "val": val_df,
            "test": test_df,
            "frontier": live_frontier,
            "clean_baseline_len": len(df),
            "purged_embargo_rows": purged_embargo_rows,
        }