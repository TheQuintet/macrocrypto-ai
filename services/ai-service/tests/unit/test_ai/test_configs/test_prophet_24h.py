"""Unit tests for the Prophet 24h configuration.

Test organization:
    - TestProphetConfigBase: Base dataclass behavior
    - TestProphet24hDefaults: 24h-specific defaults
    - TestProphet24hSerialization: JSON round-trip + save/load
    - TestProphet24hKwargs: build_prophet_24h_kwargs() helper
    - TestProphet24hValidation: validate() error paths
    - TestProphet24hIntegration: builds a real ProphetModel adapter
    - TestProphet24hConstants: module constants
"""

import json
import os
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from app.ai import (
    Prophet24hConfig,
    ProphetConfig,
    ProphetModel,
    build_prophet_24h_kwargs,
    PROPHET_24H_CONFIG,
)
from app.ai.configs.base import PROPHET_REGRESSORS
from app.ai.configs.prophet_24h import (
    FORECAST_FREQ,
    HORIZON_DAYS,
    HORIZON_HOURS,
    HORIZON_LABEL,
    build_adapter_config,
)


# ============================================================
# BASE CONFIG TESTS
# ============================================================
class TestProphetConfigBase:
    """Tests for the base ProphetConfig dataclass."""

    def test_default_construction(self) -> None:
        """Test that a base ProphetConfig can be constructed."""
        config = ProphetConfig()
        assert config.horizon_label == "24h"
        assert config.horizon_hours == 24
        assert config.seasonality_mode == "multiplicative"

    def test_regressors_are_independent_copies(self) -> None:
        """Test that each instance gets its own regressors list."""
        a = ProphetConfig()
        b = ProphetConfig()
        assert a.regressors is not b.regressors
        # But equal in content
        assert a.regressors == b.regressors

    def test_frozen_cannot_mutate(self) -> None:
        """Test that the dataclass is immutable."""
        config = ProphetConfig()
        with pytest.raises(FrozenInstanceError):
            config.changepoint_prior_scale = 0.99  # type: ignore[misc]

    def test_to_dict_returns_plain_dict(self) -> None:
        """Test that to_dict returns a plain dictionary."""
        config = ProphetConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["horizon_label"] == "24h"
        assert isinstance(d["regressors"], list)

    def test_to_json_roundtrip(self) -> None:
        """Test that to_json + from_dict preserves values."""
        config = ProphetConfig()
        json_str = config.to_json()
        parsed = json.loads(json_str)
        restored = ProphetConfig.from_dict(parsed)
        assert restored == config

    def test_from_dict_ignores_unknown_fields(self) -> None:
        """Test that from_dict drops unknown keys gracefully."""
        data = {
            "horizon_label": "custom",
            "regressors": ["a", "b"],
            "future_field": "ignored",
        }
        config = ProphetConfig.from_dict(data)
        assert config.horizon_label == "custom"
        assert config.regressors == ["a", "b"]

    def test_to_prophet_kwargs_keys(self) -> None:
        """Test that to_prophet_kwargs returns the Prophet hyperparams."""
        config = ProphetConfig()
        kwargs = config.to_prophet_kwargs()
        expected_keys = {
            "changepoint_prior_scale",
            "seasonality_prior_scale",
            "holidays_prior_scale",
            "seasonality_mode",
            "yearly_seasonality",
            "weekly_seasonality",
            "daily_seasonality",
            "interval_width",
        }
        assert set(kwargs.keys()) == expected_keys
        # Horizon metadata must NOT leak into Prophet kwargs
        assert "horizon_label" not in kwargs
        assert "regressors" not in kwargs

    def test_repr(self) -> None:
        """Test __repr__ format."""
        config = ProphetConfig()
        r = repr(config)
        assert "ProphetConfig" in r
        assert "horizon='24h'" in r
        assert "regressors=10" in r


# ============================================================
# 24H DEFAULTS TESTS
# ============================================================
class TestProphet24hDefaults:
    """Tests for the Prophet24hConfig defaults."""

    def test_horizon_label(self) -> None:
        """Test the horizon label."""
        config = Prophet24hConfig()
        assert config.horizon_label == "24h"

    def test_horizon_hours(self) -> None:
        """Test the horizon in hours."""
        config = Prophet24hConfig()
        assert config.horizon_hours == 24

    def test_horizon_days(self) -> None:
        """Test the horizon in days."""
        config = Prophet24hConfig()
        assert config.horizon_days == 1

    def test_freq_is_hourly(self) -> None:
        """Test that the forecast frequency is hourly."""
        config = Prophet24hConfig()
        assert config.freq == "H"

    def test_hourly_seasonality_enabled(self) -> None:
        """Test that hourly seasonality is enabled."""
        config = Prophet24hConfig()
        assert config.hourly_seasonality is True

    def test_daily_seasonality_enabled(self) -> None:
        """Test that daily seasonality is enabled."""
        config = Prophet24hConfig()
        assert config.daily_seasonality is True

    def test_weekly_seasonality_enabled(self) -> None:
        """Test that weekly seasonality is enabled."""
        config = Prophet24hConfig()
        assert config.weekly_seasonality is True

    def test_yearly_seasonality_disabled(self) -> None:
        """Test that yearly seasonality is disabled (irrelevant for 24h)."""
        config = Prophet24hConfig()
        assert config.yearly_seasonality is False

    def test_interval_width_is_95(self) -> None:
        """Test that the native interval width is 0.95."""
        config = Prophet24hConfig()
        assert config.interval_width == 0.95

    def test_all_ten_regressors_present(self) -> None:
        """Test that all 10 base regressors are configured."""
        config = Prophet24hConfig()
        assert len(config.regressors) == 10
        assert config.regressors == PROPHET_REGRESSORS

    def test_confidence_levels(self) -> None:
        """Test the supported confidence levels."""
        config = Prophet24hConfig()
        assert config.confidence_levels == [0.70, 0.85, 0.95]

    def test_is_prophet_config_subclass(self) -> None:
        """Test that Prophet24hConfig extends ProphetConfig."""
        config = Prophet24hConfig()
        assert isinstance(config, ProphetConfig)

    def test_is_frozen(self) -> None:
        """Test that the 24h config is immutable."""
        config = Prophet24hConfig()
        with pytest.raises(FrozenInstanceError):
            config.hourly_seasonality = False  # type: ignore[misc]

    def test_default_construction_and_singleton_are_equal(self) -> None:
        """Test that a fresh instance equals the module singleton."""
        assert Prophet24hConfig() == PROPHET_24H_CONFIG


# ============================================================
# SERIALIZATION TESTS
# ============================================================
class TestProphet24hSerialization:
    """Tests for 24h config serialization."""

    def test_to_dict_round_trip(self) -> None:
        """Test to_dict → from_dict preserves equality."""
        config = Prophet24hConfig()
        restored = Prophet24hConfig.from_dict(config.to_dict())
        assert restored == config

    def test_to_json_is_valid_json(self) -> None:
        """Test that to_json produces valid JSON."""
        config = Prophet24hConfig()
        parsed = json.loads(config.to_json())
        assert parsed["horizon_label"] == "24h"
        assert parsed["hourly_seasonality"] is True

    def test_save_and_load(self, tmp_path) -> None:
        """Test save + load round-trip via filesystem."""
        config = Prophet24hConfig()
        path = str(tmp_path / "prophet_24h.json")
        config.save(path)

        assert os.path.exists(path)
        restored = Prophet24hConfig.load(path)
        assert restored == config

    def test_load_missing_file_raises(self, tmp_path) -> None:
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Prophet24hConfig.load(str(tmp_path / "does_not_exist.json"))

    def test_saved_json_contains_key_fields(self, tmp_path) -> None:
        """Test that saved JSON contains the expected top-level keys."""
        config = Prophet24hConfig()
        path = str(tmp_path / "prophet_24h.json")
        config.save(path)

        with open(path, "r") as f:
            data = json.load(f)

        for key in (
            "horizon_label",
            "horizon_hours",
            "freq",
            "hourly_seasonality",
            "daily_seasonality",
            "weekly_seasonality",
            "regressors",
            "confidence_levels",
        ):
            assert key in data, f"Missing key: {key}"


# ============================================================
# KWARGS HELPER TESTS
# ============================================================
class TestProphet24hKwargs:
    """Tests for build_prophet_24h_kwargs()."""

    def test_returns_dict(self) -> None:
        """Test that build_prophet_24h_kwargs returns a dict."""
        kwargs = build_prophet_24h_kwargs()
        assert isinstance(kwargs, dict)

    def test_keys_match_prophet_hyperparams(self) -> None:
        """Test that returned keys are the Prophet hyperparameters."""
        kwargs = build_prophet_24h_kwargs()
        expected = {
            "changepoint_prior_scale",
            "seasonality_prior_scale",
            "holidays_prior_scale",
            "seasonality_mode",
            "yearly_seasonality",
            "weekly_seasonality",
            "daily_seasonality",
            "interval_width",
        }
        assert set(kwargs.keys()) == expected

    def test_excludes_horizon_metadata(self) -> None:
        """Test that horizon metadata is not in the kwargs."""
        kwargs = build_prophet_24h_kwargs()
        assert "horizon_label" not in kwargs
        assert "horizon_hours" not in kwargs
        assert "regressors" not in kwargs
        assert "confidence_levels" not in kwargs
        assert "freq" not in kwargs

    def test_values_match_config(self) -> None:
        """Test that kwargs values match the config values."""
        config = Prophet24hConfig()
        kwargs = build_prophet_24h_kwargs(config)
        assert kwargs["seasonality_mode"] == config.seasonality_mode
        assert kwargs["daily_seasonality"] == config.daily_seasonality
        assert kwargs["weekly_seasonality"] == config.weekly_seasonality
        assert (
            kwargs["changepoint_prior_scale"]
            == config.changepoint_prior_scale
        )

    def test_uses_singleton_by_default(self) -> None:
        """Test that the default argument is the module singleton."""
        kwargs = build_prophet_24h_kwargs()
        assert kwargs == PROPHET_24H_CONFIG.to_prophet_kwargs()

    def test_custom_config_override(self) -> None:
        """Test that a custom config changes the returned kwargs."""
        custom = Prophet24hConfig(changepoint_prior_scale=0.42)
        kwargs = build_prophet_24h_kwargs(custom)
        assert kwargs["changepoint_prior_scale"] == 0.42

    def test_build_adapter_config_is_alias(self) -> None:
        """Test that build_adapter_config returns the same result."""
        assert build_adapter_config() == build_prophet_24h_kwargs()


# ============================================================
# VALIDATION TESTS
# ============================================================
class TestProphet24hValidation:
    """Tests for validate()."""

    def test_valid_config_passes(self) -> None:
        """Test that the default config is valid."""
        Prophet24hConfig().validate()

    def test_invalid_horizon_hours(self) -> None:
        """Test that non-positive horizon_hours raises."""
        with pytest.raises(ValueError, match="horizon_hours must be positive"):
            Prophet24hConfig(horizon_hours=0).validate()

    def test_invalid_horizon_days(self) -> None:
        """Test that non-positive horizon_days raises."""
        with pytest.raises(ValueError, match="horizon_days must be positive"):
            Prophet24hConfig(horizon_days=0).validate()

    def test_invalid_interval_width_zero(self) -> None:
        """Test that interval_width=0 raises."""
        with pytest.raises(ValueError, match="interval_width"):
            Prophet24hConfig(interval_width=0.0).validate()

    def test_invalid_interval_width_one(self) -> None:
        """Test that interval_width=1.0 raises."""
        with pytest.raises(ValueError, match="interval_width"):
            Prophet24hConfig(interval_width=1.0).validate()

    def test_invalid_seasonality_mode(self) -> None:
        """Test that an invalid seasonality_mode raises."""
        with pytest.raises(ValueError, match="seasonality_mode"):
            Prophet24hConfig(seasonality_mode="bogus").validate()

    def test_empty_regressors(self) -> None:
        """Test that empty regressors list raises."""
        with pytest.raises(ValueError, match="regressors list"):
            Prophet24hConfig(regressors=[]).validate()

    def test_empty_confidence_levels(self) -> None:
        """Test that empty confidence_levels list raises."""
        with pytest.raises(ValueError, match="confidence_levels list"):
            Prophet24hConfig(confidence_levels=[]).validate()

    def test_invalid_confidence_level(self) -> None:
        """Test that a confidence level outside (0,1) raises."""
        with pytest.raises(ValueError, match="confidence level"):
            Prophet24hConfig(confidence_levels=[1.5]).validate()


# ============================================================
# INTEGRATION TESTS
# ============================================================
class TestProphet24hIntegration:
    """Integration test: config flows into a real ProphetModel adapter."""

    def test_config_kwargs_accepted_by_adapter(self) -> None:
        """Test that build_prophet_24h_kwargs() output works with ProphetModel."""
        kwargs = build_prophet_24h_kwargs()
        model = ProphetModel(strategy="fresh", config=kwargs)

        # The adapter merges kwargs on top of its own DEFAULT_CONFIG
        assert (
            model.config["seasonality_mode"]
            == PROPHET_24H_CONFIG.seasonality_mode
        )
        assert (
            model.config["daily_seasonality"]
            == PROPHET_24H_CONFIG.daily_seasonality
        )
        assert (
            model.config["weekly_seasonality"]
            == PROPHET_24H_CONFIG.weekly_seasonality
        )
        assert (
            model.config["changepoint_prior_scale"]
            == PROPHET_24H_CONFIG.changepoint_prior_scale
        )

    def test_config_can_train_a_prophet_model(self) -> None:
        """Test that a ProphetModel built from this config can train.

        Uses a small synthetic hourly dataset (enough rows for the
        MIN_TRAINING_ROWS=30 threshold).
        """
        # Build the config-driven adapter
        model = ProphetModel(
            strategy="fresh",
            config=build_prophet_24h_kwargs(),
        )

        # Synthetic hourly data
        n = 60
        dates = pd.date_range(
            "2024-01-01", periods=n, freq="h"
        )
        import numpy as np

        np.random.seed(42)
        y = 50_000 + np.linspace(0, 500, n) + np.random.normal(0, 50, n)

        data = pd.DataFrame(
            {
                "ds": dates,
                "y": y,
                "cpi": [3.2] * n,
                "interest_rate": [4.5] * n,
                "m2_growth": [2.8] * n,
                "dxy": [102.5] * n,
                "treasury_yield": [4.2] * n,
                "volume": [25_000_000_000] * n,
                "volatility": [0.15] * n,
                "dominance": [52.5] * n,
                "active_addresses": [850_000] * n,
                "price_lag_7d": [50_000] * n,
            }
        )

        metrics = model.train(data)
        assert model.is_model_trained() is True
        assert "mae" in metrics
        assert metrics["mae"] >= 0


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestProphet24hConstants:
    """Tests for module constants."""

    def test_horizon_label_constant(self) -> None:
        """Test HORIZON_LABEL."""
        assert HORIZON_LABEL == "24h"

    def test_horizon_hours_constant(self) -> None:
        """Test HORIZON_HOURS."""
        assert HORIZON_HOURS == 24

    def test_horizon_days_constant(self) -> None:
        """Test HORIZON_DAYS."""
        assert HORIZON_DAYS == 1

    def test_forecast_freq_constant(self) -> None:
        """Test FORECAST_FREQ is hourly."""
        assert FORECAST_FREQ == "H"

    def test_singleton_is_valid(self) -> None:
        """Test that the module singleton validates cleanly."""
        PROPHET_24H_CONFIG.validate()  # should not raise

    def test_singleton_is_prophet_24h_config(self) -> None:
        """Test that the singleton is a Prophet24hConfig."""
        assert isinstance(PROPHET_24H_CONFIG, Prophet24hConfig)