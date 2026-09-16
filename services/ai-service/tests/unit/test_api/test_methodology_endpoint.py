"""Unit tests for GET /api/v1/methodology (A4.1).

Covers:
    - 200 with the full response shape
    - Content type and section presence
    - The version field
    - Response time well under the A4.1 target of 500 ms
    - Defensive 500 when build_methodology raises
    - OpenAPI schema is served with the endpoint listed

The endpoint has no query parameters and no dependencies on the
database, Redis, or storage, so the tests do not need any of the
session / storage fixtures the other endpoint tests use. The only
monkeypatch is on ``build_methodology`` for the failure-path test.
"""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ============================================================
# HAPPY PATH
# ============================================================
class TestGetMethodologyHappyPath:
    """200 with the full response shape."""

    def test_status_200(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology")
        assert r.status_code == 200

    def test_content_type_json(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology")
        assert r.headers["content-type"].startswith("application/json")

    def test_top_level_keys(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology")
        body = r.json()
        assert set(body.keys()) == {
            "version",
            "updated_at",
            "models",
            "correlations",
            "regimes",
            "data_sources",
            "limitations",
        }

    def test_version_present(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology").json()
        assert body["version"] == "1.0.0"

    def test_updated_at_present(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology").json()
        assert body["updated_at"] == "2026-09-16"

    def test_models_list(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology").json()
        assert len(body["models"]) == 6
        names = [m["name"] for m in body["models"]]
        assert "prophet_fresh" in names
        assert "xgboost_incremental" in names
        assert "lightgbm_fresh" in names
        for model in body["models"]:
            assert set(model.keys()) == {
                "name",
                "algorithm",
                "strategy",
                "description",
            }
            assert model["description"]

    def test_correlations_section(self, client: TestClient) -> None:
        corr = client.get("/api/v1/methodology").json()["correlations"]
        assert corr["method"] == "Pearson"
        assert corr["windows_days"] == [30, 90, 365]
        assert corr["strength_thresholds"] == {
            "strong_gt": 0.7,
            "medium_gte": 0.3,
        }
        assert corr["significance_threshold"] == 0.05
        assert corr["indicators"] == [
            "inflation",
            "rates",
            "gdp",
            "unemployment",
        ]

    def test_regimes_section(self, client: TestClient) -> None:
        regimes = client.get("/api/v1/methodology").json()["regimes"]
        assert regimes["labels"] == [
            "bull",
            "bear",
            "volatile",
            "neutral",
        ]
        assert regimes["priority"] == [
            "volatile",
            "bull",
            "bear",
            "neutral",
        ]
        assert regimes["bull_threshold_pct"] == 20.0
        assert regimes["bear_threshold_pct"] == 20.0
        assert regimes["volatility_threshold"] == 0.05

    def test_data_sources_section(self, client: TestClient) -> None:
        sources = client.get("/api/v1/methodology").json()[
            "data_sources"
        ]
        names = [s["name"] for s in sources]
        assert names == ["FRED", "CoinGecko", "MacroCrypto AI Service"]
        # FRED and CoinGecko carry a URL; the AI Service does not.
        by_name = {s["name"]: s for s in sources}
        assert by_name["FRED"]["url"].startswith("https://")
        assert by_name["CoinGecko"]["url"].startswith("https://")
        assert by_name["MacroCrypto AI Service"]["url"] == ""

    def test_limitations_section(self, client: TestClient) -> None:
        limitations = client.get("/api/v1/methodology").json()[
            "limitations"
        ]
        assert len(limitations) >= 3
        for lim in limitations:
            assert set(lim.keys()) == {"area", "description"}
            assert lim["area"].strip()
            assert lim["description"].strip()


# ============================================================
# RESPONSE TIME
# ============================================================
class TestMethodologyLatency:
    """The response is served well within the A4.1 target."""

    def test_under_500ms(self, client: TestClient) -> None:
        # Warm up so we are not measuring import cost.
        client.get("/api/v1/methodology")

        start = time.monotonic()
        r = client.get("/api/v1/methodology")
        elapsed_ms = (time.monotonic() - start) * 1000

        assert r.status_code == 200
        # The A4.1 acceptance criterion is < 500ms. In practice this
        # endpoint responds in single-digit milliseconds; the
        # assertion is deliberately generous to avoid flakiness on
        # loaded CI machines while still catching a regression that
        # adds real I/O.
        assert elapsed_ms < 500.0, (
            f"methodology endpoint took {elapsed_ms:.1f} ms"
        )


# ============================================================
# DEFENSIVE 500
# ============================================================
class TestMethodologyFailure:
    """A build failure is surfaced as a structured 500."""

    def test_build_failure_returns_500(self, client: TestClient) -> None:
        with patch(
            "app.api.v1.methodology.build_methodology",
            side_effect=RuntimeError("boom"),
        ):
            r = client.get("/api/v1/methodology")

        assert r.status_code == 500
        body = r.json()
        # FastAPI wraps a dict detail under "detail"; assert the
        # structured fields we set are present somewhere in there.
        detail = body.get("detail")
        assert detail is not None
        assert detail.get("error") == "methodology_unavailable"
        assert "methodology" in detail.get("message", "").lower()
        assert detail.get("detail") == "boom"


# ============================================================
# OPENAPI
# ============================================================
class TestOpenAPI:
    """The endpoint is advertised in the OpenAPI schema."""

    def test_openapi_paths_include_methodology(
        self, client: TestClient
    ) -> None:
        spec = client.get("/openapi.json").json()
        assert "/api/v1/methodology" in spec["paths"]

    def test_get_operation_documented(
        self, client: TestClient
    ) -> None:
        spec = client.get("/openapi.json").json()
        op = spec["paths"]["/api/v1/methodology"]["get"]
        assert op["summary"] == (
            "Get the AI Service methodology documentation"
        )
        assert "responses" in op
        assert "200" in op["responses"]

    def test_response_schema_is_registered(
        self, client: TestClient
    ) -> None:
        spec = client.get("/openapi.json").json()
        schemas = spec.get("components", {}).get("schemas", {})
        assert "MethodologyResponse" in schemas
        assert "ModelSpecResponse" in schemas
        assert "CorrelationSpecResponse" in schemas
        assert "RegimeSpecResponse" in schemas
        assert "DataSourceSpecResponse" in schemas
        assert "LimitationSpecResponse" in schemas