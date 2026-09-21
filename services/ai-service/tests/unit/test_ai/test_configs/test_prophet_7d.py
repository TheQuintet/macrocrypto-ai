"""Unit tests for the Prophet 7d configuration.

Test organization:
    - TestProphet7dDefaults: 7d-specific defaults
    - TestProphet7dDifferencesFrom24h: explicit contrasts with 24h config
    - TestProphet7dSerialization: JSON round-trip + save/load
    - TestProphet7dKwargs: build_prophet_kwargs() helper
    - TestProphet7dValidation: validate() error paths
    - TestProphet7dIntegration: builds a real ProphetModel adapter
    - TestProphet7dConstants: module constants
"""

import json
import os
from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from app.ai import (
    Prophet7dConfig,
    Prophet24hConfig,
    ProphetConfig,
    ProphetModel,
    PROPHET_7D_CONFIG,
)
from app.ai.configs.base import PROPHET_REGRESSORS
from app.ai.configs.prophet_7d import (
    FORECAST_FREQ,
    HORIZON_DAYS,
    HORIZON_HOURS,
    HORIZON_LABEL,
    build_adapter_config,
    build_prophet_kwargs,
)


# ============================================================
# DEFAULTS TESTS
# ============================================================
class TestProphet7dDefaults:
    """Tests for the Prophet7dConfig defaults."""

    def test_horizon_label(self) -> None:
        """Test the horizon label."""
        config = Prophet7dConfig()
        assert config.horizon_label == "7d"

    def test_horizon_hours(self) -> None:
        """Test the horizon in hours (7 * 24 = 168)."""
        config = Prophet7dConfig()
        assert config.horizon_hours == 168

    def test_horizon_days(self) -> None:
        """Test the horizon in days."""
        config = Prophet7dConfig()
        assert config.horizon_days == 7

    def test_freq_is_daily(self) -> None:
        """Test that the forecast frequency is daily."""
        config = Prophet7dConfig()
        assert config.freq == "D"

    def test_hourly_seasonality_disabled(self) -> None:
        """Test that hourly seasonality is disabled."""
        config = Prophet7dConfig()
        assert config.hourly_seasonality is False

    def test_daily_seasonality_disabled(self) -> None:
        """Test that daily seasonality is disabled (data is daily)."""
        config = Prophet7dConfig()
        assert config.daily_seasonality is False

    def test_weekly_seasonality_enabled(self) -> None:
        """Test that weekly seasonality is enabled."""
        config = Prophet7dConfig()
        assert config.weekly_seasonality is True

    def test_yearly_seasonality_enabled(self) -> None:
        """Test that yearly seasonality is enabled for the 7d horizon."""
        config = Prophet7dConfig()
        assert config.yearly_seasonality is True

    def test_interval_width_is_95(self) -> None:
        """Test that the native interval width is 0.95."""
        config = Prophet7dConfig()
        assert config.interval_width == 0.95

    def test_changepoint_prior_scale_is_tuned(self) -> None:
        """Test the tuned changepoint_prior_scale for 7d."""
        config = Prophet7dConfig()
        assert config.changepoint_prior_scale == 0.10

    def test_seasonality_prior_scale_is_tuned(self) -> None:
        """Test the tuned seasonality_prior_scale for 7d."""
        config = Prophet7dConfig()
        assert config.seasonality_prior_scale == 5.0

    def test_holidays_prior_scale(self) -> None:
        """Test that holidays_prior_scale is the default 10.0."""
        config = Prophet7dConfig()
        assert config.holidays_prior_scale == 10.0

    def test_all_ten_regressors_present(self) -> None:
        """Test that all 10 base regressors are configured."""
        config = Prophet7dConfig()
        assert len(config.regressors) == 10
        assert config.regressors == PROPHET_REGRESSORS

    def test_confidence_levels(self) -> None:
        """Test the supported confidence levels."""
        config = Prophet7dConfig()
        assert config.confidence_levels == [0.70, 0.85, 0.95]

    def test_is_prophet_config_subclass(self) -> None:
        """Test that Prophet7dConfig extends ProphetConfig."""
        config = Prophet7dConfig()
        assert isinstance(config, ProphetConfig)

    def test_is_frozen(self) -> None:
        """Test that the 7d config is immutable."""
        config = Prophet7dConfig()
        with pytest.raises(FrozenInstanceError):
            config.yearly_seasonality = False  # type: ignore[misc]

    def test_default_construction_and_singleton_are_equal(self) -> None:
        """Test that a fresh instance equals the module singleton."""
        assert Prophet7dConfig() == PROPHET_7D_CONFIG


# ============================================================
# DIFFERENCES FROM 24H TESTS
# ============================================================
class TestProphet7dDifferencesFrom24h:
    """Explicit contrasts between the 7d and 24h configurations."""

    def test_freq_differs(self) -> None:
        """Test that 7d uses daily freq, 24h uses hourly."""
        assert Prophet7dConfig().freq == "D"
        assert Prophet24hConfig().freq == "H"

    def test_horizon_hours_differs(self) -> None:
        """Test that 7d has 7x the horizon hours of 24h."""
        assert Prophet7dConfig().horizon_hours == 168
        assert Prophet24hConfig().horizon_hours == 24

    def test_horizon_days_differs(self) -> None:
        """Test that the horizon in days differs."""
        assert Prophet7dConfig().horizon_days == 7
        assert Prophet24hConfig().horizon_days == 1

    def test_hourly_seasonality_opposite(self) -> None:
        """Test that hourly seasonality differs."""
        assert Prophet7dConfig().hourly_seasonality is False
        assert Prophet24hConfig().hourly_seasonality is True

    def test_yearly_seasonality_opposite(self) -> None:
        """Test that yearly seasonality differs."""
        assert Prophet7dConfig().yearly_seasonality is True
        assert Prophet24hConfig().yearly_seasonality is False

    def test_changepoint_prior_differs(self) -> None:
        """Test that 7d uses a higher changepoint_prior_scale."""
        assert Prophet7dConfig().changepoint_prior_scale == 0.10
        assert Prophet24hConfig().changepoint_prior_scale == 0.05

    def test_seasonality_prior_differs(self) -> None:
        """Test that 7d uses a lower seasonality_prior_scale."""
        assert Prophet7dConfig().seasonality_prior_scale == 5.0
        assert Prophet24hConfig().seasonality_prior_scale == 10.0

    def test_weekly_seasonality_same(self) -> None:
        """Test that both configs enable weekly seasonality."""
        assert Prophet7dConfig().weekly_seasonality is True
        assert Prophet24hConfig().weekly_seasonality is True

    def test_regressors_same(self) -> None:
        """Test that both configs use the same regressors."""
        assert Prophet7dConfig().regressors == Prophet24hConfig().regressors


# ============================================================
# SERIALIZATION TESTS
# ============================================================
class TestProphet7dSerialization:
    """Tests for 7d config serialization."""

    def test_to_dict_round_trip(self) -> None:
        """Test to_dict → from_dict preserves equality."""
        config = Prophet7dConfig()
        restored = Prophet7dConfig.from_dict(config.to_dict())
        assert restored == config

    def test_to_json_is_valid_json(self) -> None:
        """Test that to_json produces valid JSON."""
        config = Prophet7dConfig()
        parsed = json.loads(config.to_json())
        assert parsed["horizon_label"] == "7d"
        assert parsed["yearly_seasonality"] is True
        assert parsed["changepoint_prior_scale"] == 0.10

    def test_save_and_load(self, tmp_path) -> None:
        """Test save + load round-trip via filesystem."""
        config = Prophet7dConfig()
        path = str(tmp_path / "prophet_7d.json")
        config.save(path)

        assert os.path.exists(path)
        restored = Prophet7dConfig.load(path)
        assert restored == config

    def test_load_missing_file_raises(self, tmp_path) -> None:
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Prophet7dConfig.load(str(tmp_path / "does_not_exist.json"))

    def test_saved_json_contains_key_fields(self, tmp_path) -> None:
        """Test that saved JSON contains the expected top-level keys."""
        config = Prophet7dConfig()
        path = str(tmp_path / "prophet_7d.json")
        config.save(path)

        with open(path, "r") as f:
            data = json.load(f)

        for key in (
            "horizon_label",
            "horizon_hours",
            "horizon_days",
            "freq",
            "hourly_seasonality",
            "daily_seasonality",
            "weekly_seasonality",
            "yearly_seasonality",
            "regressors",
            "confidence_levels",
        ):
            assert key in data, f"Missing key: {key}"


# ============================================================
# KWARGS HELPER TESTS
# ============================================================
class TestProphet7dKwargs:
    """Tests for build_prophet_kwargs()."""

    def test_returns_dict(self) -> None:
        """Test that build_prophet_kwargs returns a dict."""
        kwargs = build_prophet_kwargs()
        assert isinstance(kwargs, dict)

    def test_keys_match_prophet_hyperparams(self) -> None:
        """Test that returned keys are the Prophet hyperparameters."""
        kwargs = build_prophet_kwargs()
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
        kwargs = build_prophet_kwargs()
        assert "horizon_label" not in kwargs
        assert "horizon_hours" not in kwargs
        assert "horizon_days" not in kwargs
        assert "regressors" not in kwargs
        assert "confidence_levels" not in kwargs
        assert "freq" not in kwargs

    def test_values_match_config(self) -> None:
        """Test that kwargs values match the config values."""
        config = Prophet7dConfig()
        kwargs = build_prophet_kwargs(config)
        assert kwargs["seasonality_mode"] == config.seasonality_mode
        assert kwargs["daily_seasonality"] == config.daily_seasonality
        assert kwargs["weekly_seasonality"] == config.weekly_seasonality
        assert kwargs["yearly_seasonality"] == config.yearly_seasonality
        assert (
            kwargs["changepoint_prior_scale"]
            == config.changepoint_prior_scale
        )

    def test_uses_singleton_by_default(self) -> None:
        """Test that the default argument is the module singleton."""
        kwargs = build_prophet_kwargs()
        assert kwargs == PROPHET_7D_CONFIG.to_prophet_kwargs()

    def test_custom_config_override(self) -> None:
        """Test that a custom config changes the returned kwargs."""
        custom = Prophet7dConfig(changepoint_prior_scale=0.42)
        kwargs = build_prophet_kwargs(custom)
        assert kwargs["changepoint_prior_scale"] == 0.42

    def test_build_adapter_config_is_alias(self) -> None:
        """Test that build_adapter_config returns the same result."""
        assert build_adapter_config() == build_prophet_kwargs()


# ============================================================
# VALIDATION TESTS
# ============================================================
class TestProphet7dValidation:
    """Tests for validate()."""

    def test_valid_config_passes(self) -> None:
        """Test that the default config is valid."""
        Prophet7dConfig().validate()

    def test_invalid_horizon_hours(self) -> None:
        """Test that non-positive horizon_hours raises."""
        with pytest.raises(ValueError, match="horizon_hours must be positive"):
            Prophet7dConfig(horizon_hours=0).validate()

    def test_invalid_horizon_days(self) -> None:
        """Test that non-positive horizon_days raises."""
        with pytest.raises(ValueError, match="horizon_days must be positive"):
            Prophet7dConfig(horizon_days=0).validate()

    def test_invalid_interval_width_zero(self) -> None:
        """Test that interval_width=0 raises."""
        with pytest.raises(ValueError, match="interval_width"):
            Prophet7dConfig(interval_width=0.0).validate()

    def test_invalid_interval_width_one(self) -> None:
        """Test that interval_width=1.0 raises."""
        with pytest.raises(ValueError, match="interval_width"):
            Prophet7dConfig(interval_width=1.0).validate()

    def test_invalid_seasonality_mode(self) -> None:
        """Test that an invalid seasonality_mode raises."""
        with pytest.raises(ValueError, match="seasonality_mode"):
            Prophet7dConfig(seasonality_mode="bogus").validate()

    def test_empty_regressors(self) -> None:
        """Test that empty regressors list raises."""
        with pytest.raises(ValueError, match="regressors list"):
            Prophet7dConfig(regressors=[]).validate()

    def test_empty_confidence_levels(self) -> None:
        """Test that empty confidence_levels list raises."""
        with pytest.raises(ValueError, match="confidence_levels list"):
            Prophet7dConfig(confidence_levels=[]).validate()

    def test_invalid_confidence_level(self) -> None:
        """Test that a confidence level outside (0,1) raises."""
        with pytest.raises(ValueError, match="confidence level"):
            Prophet7dConfig(confidence_levels=[1.5]).validate()


# ============================================================
# INTEGRATION TESTS
# ============================================================
class TestProphet7dIntegration:
    """Integration test: config flows into a real ProphetModel adapter."""

    def test_config_kwargs_accepted_by_adapter(self) -> None:
        """Test that build_prophet_kwargs() output works with ProphetModel."""
        kwargs = build_prophet_kwargs()
        model = ProphetModel(strategy="fresh", config=kwargs)

        # The adapter merges kwargs on top of its own DEFAULT_CONFIG
        assert (
            model.config["seasonality_mode"]
            == PROPHET_7D_CONFIG.seasonality_mode
        )
        assert (
            model.config["daily_seasonality"]
            == PROPHET_7D_CONFIG.daily_seasonality
        )
        assert (
            model.config["weekly_seasonality"]
            == PROPHET_7D_CONFIG.weekly_seasonality
        )
        assert (
            model.config["yearly_seasonality"]
            == PROPHET_7D_CONFIG.yearly_seasonality
        )
        assert (
            model.config["changepoint_prior_scale"]
            == PROPHET_7D_CONFIG.changepoint_prior_scale
        )

    def test_config_can_train_a_prophet_model(self) -> None:
        """Test that a ProphetModel built from this config can train.

        Uses a small synthetic daily dataset (enough rows for the
        MIN_TRAINING_ROWS=30 threshold).
        """
        # Build the config-driven adapter
        model = ProphetModel(
            strategy="fresh",
            config=build_prophet_kwargs(),
        )

        # Synthetic daily data
        n = 60
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
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
class TestProphet7dConstants:
    """Tests for module constants."""

    def test_horizon_label_constant(self) -> None:
        """Test HORIZON_LABEL."""
        assert HORIZON_LABEL == "7d"

    def test_horizon_hours_constant(self) -> None:
        """Test HORIZON_HOURS (7 * 24 = 168)."""
        assert HORIZON_HOURS == 168

    def test_horizon_days_constant(self) -> None:
        """Test HORIZON_DAYS."""
        assert HORIZON_DAYS == 7

    def test_forecast_freq_constant(self) -> None:
        """Test FORECAST_FREQ is daily."""
        assert FORECAST_FREQ == "D"

    def test_singleton_is_valid(self) -> None:
        """Test that the module singleton validates cleanly."""
        PROPHET_7D_CONFIG.validate()  # should not raise

    def test_singleton_is_prophet_7d_config(self) -> None:
        """Test that the singleton is a Prophet7dConfig."""
        assert isinstance(PROPHET_7D_CONFIG, Prophet7dConfig)