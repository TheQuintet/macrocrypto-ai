"""Stored-prediction comparison.

Compares the *stored* prediction batches of multiple models without
running any model in the request path. Reads what the scheduler has
already written to `btc_predictions` and computes:

    - Consensus: mean predicted price across models at each timestamp
    - Agreement score: a value in [0, 1] measuring how closely the
      models agree (1 = identical, 0 = spread ≥ mean)
    - Best model: the model with the lowest MAE in the recent window
      (delegated to PerformanceRepository)

This is deliberately separate from `app.ai.comparison`, which runs
in-memory model instances against a future DataFrame. That engine is
for the scheduler/backtest path; this module is for the read-only API
path. Both use the same agreement formula (coefficient of variation
based) so their numbers are consistent.

Design:
    - Pure functions and dataclasses — no DB, no pandas, no models
    - Takes List[PredictionRow] per model (already loaded by the caller)
    - Returns a StoredComparison with everything needed for the API
"""

import logging
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Agreement score bounds (mirrors app.ai.comparison)
AGREEMENT_SCORE_MIN = 0.0
AGREEMENT_SCORE_MAX = 1.0


# ============================================================
# RESULT TYPES
# ============================================================
@dataclass
class ConsensusPoint:
    """A single consensus (mean) prediction point.

    Attributes:
        time: The forecast timestamp.
        predicted_price: Mean predicted price across models (USD).
        lower_bound: Mean lower bound across models (USD), or None
            if no model provided bounds.
        upper_bound: Mean upper bound across models (USD), or None
            if no model provided bounds.
        contributing_models: Number of models that had a prediction
            at this timestamp.
    """

    time: Any
    predicted_price: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    contributing_models: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "time": self.time,
            "predicted_price": self.predicted_price,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "contributing_models": self.contributing_models,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ConsensusPoint(time={self.time}, "
            f"predicted_price={self.predicted_price:.2f}, "
            f"models={self.contributing_models})"
        )


@dataclass
class StoredComparison:
    """Result of comparing stored prediction batches.

    Attributes:
        models_compared: Names of models that contributed at least
            one consensus point.
        models_missing: Names of models that were requested but had
            no stored predictions, or whose timestamps did not
            overlap with any other model.
        consensus: Ordered list of ConsensusPoint, ascending by time.
        agreement_score: Score in [0, 1]. 1.0 when fewer than two
            models contribute (single model trivially agrees with
            itself).
        best_model: Name of the model with the lowest MAE in the
            recent window, as reported by the caller. May not be
            one of the models in `models_compared` — it reflects
            overall best, not "best among those compared".
        timestamps_compared: Number of distinct timestamps included
            in the consensus.
    """

    models_compared: List[str] = field(default_factory=list)
    models_missing: List[str] = field(default_factory=list)
    consensus: List[ConsensusPoint] = field(default_factory=list)
    agreement_score: float = 0.0
    best_model: Optional[str] = None
    timestamps_compared: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "models_compared": self.models_compared,
            "models_missing": self.models_missing,
            "consensus": [p.to_dict() for p in self.consensus],
            "agreement_score": self.agreement_score,
            "best_model": self.best_model,
            "timestamps_compared": self.timestamps_compared,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"StoredComparison("
            f"compared={len(self.models_compared)}, "
            f"missing={len(self.models_missing)}, "
            f"points={len(self.consensus)}, "
            f"agreement={self.agreement_score:.3f}, "
            f"best='{self.best_model}')"
        )


# ============================================================
# PUBLIC FUNCTION
# ============================================================
def compare_stored_predictions(
    batches: Dict[str, List[Any]],
    best_model: Optional[str] = None,
) -> StoredComparison:
    """Compare stored prediction batches from multiple models.

    Batches must be keyed by model name; each value is a list of
    PredictionRow (or anything exposing `.time`, `.predicted_price`,
    `.lower_bound`, `.upper_bound`). Timestamps are aligned by
    equality — only timestamps present in at least two models
    contribute to the consensus and agreement score.

    This function is pure: no I/O, no models, no pandas. It exists
    so the API layer can compose a comparison from data it has
    already loaded.

    Args:
        batches: Mapping of model_name → List[PredictionRow]. Models
            with empty lists are treated as missing.
        best_model: Optional name of the best model (by MAE),
            determined by the caller. Passed through unchanged.

    Returns:
        StoredComparison with models_compared, models_missing,
        consensus (ascending by time), agreement_score, best_model,
        and timestamps_compared.
    """
    requested = list(batches.keys())
    non_empty = {
        name: rows for name, rows in batches.items() if rows
    }
    empty = [name for name in requested if not batches[name]]

    if not non_empty:
        logger.info(
            f"compare_stored_predictions: no batches have data "
            f"(requested={requested})"
        )
        return StoredComparison(
            models_compared=[],
            models_missing=empty,
            consensus=[],
            agreement_score=0.0,
            best_model=best_model,
            timestamps_compared=0,
        )

    # ---- 1. Build timestamp → {model_name: row} index ----
    # Only keep models that appear in at least one other model's
    # timestamp set (a model with zero overlap is "missing" for
    # comparison purposes).
    by_time: Dict[Any, Dict[str, Any]] = {}
    for model_name, rows in non_empty.items():
        for row in rows:
            by_time.setdefault(row.time, {})[model_name] = row

    # ---- 2. Determine which models actually overlap ----
    overlapping: set = set()
    for model_map in by_time.values():
        if len(model_map) >= 2:
            overlapping.update(model_map.keys())

    models_compared = [name for name in non_empty if name in overlapping]
    models_isolated = [
        name for name in non_empty if name not in overlapping
    ]
    models_missing = empty + models_isolated

    if not models_compared:
        logger.info(
            f"compare_stored_predictions: no timestamp overlap "
            f"between any two models (non_empty={list(non_empty)})"
        )
        return StoredComparison(
            models_compared=[],
            models_missing=models_missing,
            consensus=[],
            agreement_score=0.0,
            best_model=best_model,
            timestamps_compared=0,
        )

    # ---- 3. Build consensus (only timestamps with >=2 contributors) ----
    consensus: List[ConsensusPoint] = []
    per_timestamp_yhats: List[List[float]] = []

    for ts in sorted(by_time.keys()):
        contributors = by_time[ts]
        # Only include points where at least two compared models
        # have a prediction — otherwise the "consensus" is just
        # one model's value.
        contributing = {
            name: row
            for name, row in contributors.items()
            if name in overlapping
        }
        if len(contributing) < 2:
            continue

        yhats = [row.predicted_price for row in contributing.values()]
        lowers = [
            row.lower_bound
            for row in contributing.values()
            if getattr(row, "lower_bound", None) is not None
        ]
        uppers = [
            row.upper_bound
            for row in contributing.values()
            if getattr(row, "upper_bound", None) is not None
        ]

        consensus.append(
            ConsensusPoint(
                time=ts,
                predicted_price=float(mean(yhats)),
                lower_bound=(
                    float(mean(lowers)) if lowers else None
                ),
                upper_bound=(
                    float(mean(uppers)) if uppers else None
                ),
                contributing_models=len(contributing),
            )
        )
        per_timestamp_yhats.append(yhats)

    if not consensus:
        logger.info(
            "compare_stored_predictions: no timestamps with >=2 "
            "contributing models"
        )
        return StoredComparison(
            models_compared=models_compared,
            models_missing=models_missing,
            consensus=[],
            agreement_score=0.0,
            best_model=best_model,
            timestamps_compared=0,
        )

    # ---- 4. Agreement score ----
    # Mirrors ModelComparisonEngine._calculate_agreement: mean over
    # timestamps of (std / mean), then 1 - that, clamped to [0, 1].
    agreement = _agreement_from_yhats(per_timestamp_yhats)

    logger.info(
        f"compare_stored_predictions: compared={models_compared}, "
        f"missing={models_missing}, points={len(consensus)}, "
        f"agreement={agreement:.3f}"
    )

    return StoredComparison(
        models_compared=models_compared,
        models_missing=models_missing,
        consensus=consensus,
        agreement_score=agreement,
        best_model=best_model,
        timestamps_compared=len(consensus),
    )


# ============================================================
# HELPERS
# ============================================================
def _agreement_from_yhats(
    per_timestamp_yhats: List[List[float]],
) -> float:
    """Compute the coefficient-of-variation agreement score.

    For each timestamp, compute std/mean of the model predictions.
    Average those CVs across timestamps, then return 1 - mean_cv,
    clamped to [0, 1].

    Matches `ModelComparisonEngine._calculate_agreement` so numbers
    stay consistent between the API path and the backtest path.

    Args:
        per_timestamp_yhats: For each timestamp, the list of model
            predictions at that timestamp. Each inner list must
            have at least two values.

    Returns:
        Agreement score in [0, 1]. Returns 1.0 if there are no
        timestamps or all means are zero.
    """
    if not per_timestamp_yhats:
        return 1.0

    cvs: List[float] = []
    for yhats in per_timestamp_yhats:
        if len(yhats) < 2:
            continue
        m = mean(yhats)
        if m == 0:
            continue
        s = stdev(yhats)
        cvs.append(s / m)

    if not cvs:
        return 1.0

    mean_cv = mean(cvs)
    agreement = 1.0 - mean_cv
    return float(
        max(AGREEMENT_SCORE_MIN, min(AGREEMENT_SCORE_MAX, agreement))
    )