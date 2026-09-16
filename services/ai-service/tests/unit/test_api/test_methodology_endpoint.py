"""Unit tests for the methodology endpoints (A4.1, A4.2).

Covers:
    - GET /api/v1/methodology: current version, explicit version,
      unknown version 404, defensive 500
    - GET /api/v1/methodology/versions: shape, ordering, current
    - GET /api/v1/methodology/changelog: shape, ordering
    - Content type, response time, OpenAPI registration for all
      three endpoints

The endpoints have no query parameters beyond the optional
``?version=``, and no dependencies on the database, Redis, or
storage. The only monkeypatches are on the three data-access
functions (``build_methodology``, ``list_methodology_versions``,
``get_methodology_changelog``) for the failure-path tests.
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
# BASE ENDPOINT — HAPPY PATH
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
        body = client.get("/api/v1/methodology").json()
        assert set(body.keys()) == {
            "version",
            "updated_at",
            "models",
            "correlations",
            "regimes",
            "data_sources",
            "limitations",
        }

    def test_version_is_current(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology").json()
        assert body["version"] == "1.1.0"

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
# BASE ENDPOINT — ?version= PARAM
# ============================================================
class TestGetMethodologyWithVersion:
    """The optional ?version= query parameter."""

    def test_explicit_1_0_0(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology?version=1.0.0")
        assert r.status_code == 200
        assert r.json()["version"] == "1.0.0"

    def test_explicit_1_1_0(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology?version=1.1.0")
        assert r.status_code == 200
        assert r.json()["version"] == "1.1.0"

    def test_no_version_is_current(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology").json()
        assert body["version"] == "1.1.0"

    def test_unknown_version_returns_404(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology?version=9.9.9")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert detail["error"] == "unknown_version"
        assert "9.9.9" in detail["message"]

    def test_v1_0_0_has_the_same_sections(
        self, client: TestClient
    ) -> None:
        """A4.2 did not change the content, only added versioning."""
        v1 = client.get("/api/v1/methodology?version=1.0.0").json()
        v2 = client.get("/api/v1/methodology?version=1.1.0").json()
        assert [m["name"] for m in v1["models"]] == [
            m["name"] for m in v2["models"]
        ]
        assert v1["correlations"] == v2["correlations"]
        assert v1["regimes"] == v2["regimes"]


# ============================================================
# VERSION LIST ENDPOINT
# ============================================================
class TestGetVersions:
    """GET /api/v1/methodology/versions."""

    def test_status_200(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology/versions")
        assert r.status_code == 200

    def test_shape(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology/versions").json()
        assert set(body.keys()) == {"current_version", "versions"}

    def test_current_version(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology/versions").json()
        assert body["current_version"] == "1.1.0"

    def test_versions_list_ascending(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology/versions").json()
        assert body["versions"] == ["1.0.0", "1.1.0"]

    def test_content_type_json(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology/versions")
        assert r.headers["content-type"].startswith("application/json")


# ============================================================
# CHANGELOG ENDPOINT
# ============================================================
class TestGetChangelog:
    """GET /api/v1/methodology/changelog."""

    def test_status_200(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology/changelog")
        assert r.status_code == 200

    def test_shape(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology/changelog").json()
        assert set(body.keys()) == {"entries"}
        assert isinstance(body["entries"], list)

    def test_newest_first(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology/changelog").json()
        versions = [e["version"] for e in body["entries"]]
        assert versions == ["1.1.0", "1.0.0"]

    def test_entry_shape(self, client: TestClient) -> None:
        body = client.get("/api/v1/methodology/changelog").json()
        for entry in body["entries"]:
            assert set(entry.keys()) == {
                "version",
                "released_at",
                "summary",
                "changes",
            }
            assert entry["summary"].strip()
            assert isinstance(entry["changes"], list)

    def test_content_type_json(self, client: TestClient) -> None:
        r = client.get("/api/v1/methodology/changelog")
        assert r.headers["content-type"].startswith("application/json")


# ============================================================
# RESPONSE TIME
# ============================================================
class TestMethodologyLatency:
    """The responses are served well within the A4.1 target."""

    def test_base_under_500ms(self, client: TestClient) -> None:
        client.get("/api/v1/methodology")  # warm-up
        start = time.monotonic()
        r = client.get("/api/v1/methodology")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert r.status_code == 200
        assert elapsed_ms < 500.0, (
            f"methodology endpoint took {elapsed_ms:.1f} ms"
        )

    def test_versions_under_500ms(self, client: TestClient) -> None:
        client.get("/api/v1/methodology/versions")  # warm-up
        start = time.monotonic()
        r = client.get("/api/v1/methodology/versions")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert r.status_code == 200
        assert elapsed_ms < 500.0

    def test_changelog_under_500ms(self, client: TestClient) -> None:
        client.get("/api/v1/methodology/changelog")  # warm-up
        start = time.monotonic()
        r = client.get("/api/v1/methodology/changelog")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert r.status_code == 200
        assert elapsed_ms < 500.0


# ============================================================
# DEFENSIVE 500
# ============================================================
class TestMethodologyFailure:
    """A build failure is surfaced as a structured 500."""

    def test_build_failure_returns_500(
        self, client: TestClient
    ) -> None:
        with patch(
            "app.api.v1.methodology.build_methodology",
            side_effect=RuntimeError("boom"),
        ):
            r = client.get("/api/v1/methodology")

        assert r.status_code == 500
        detail = r.json()["detail"]
        assert detail["error"] == "methodology_unavailable"
        assert "methodology" in detail["message"].lower()
        assert detail["detail"] == "boom"

    def test_conversion_failure_returns_500(
        self, client: TestClient
    ) -> None:
        """A failure in the to_dict / model_validate step returns a
        structured 500. The two exception paths (build vs. convert)
        are separate handlers; this test exercises the second one."""
        with patch(
            "app.api.v1.methodology.MethodologyResponse.model_validate",
            side_effect=RuntimeError("validation boom"),
        ):
            r = client.get("/api/v1/methodology")

        assert r.status_code == 500
        detail = r.json()["detail"]
        assert detail["error"] == "methodology_unavailable"
        assert detail["detail"] == "validation boom"


class TestVersionsEndpointFailure:
    """A failure building the version list is a structured 500."""

    def test_version_list_failure_returns_500(
        self, client: TestClient
    ) -> None:
        with patch(
            "app.api.v1.methodology.list_methodology_versions",
            side_effect=RuntimeError("list boom"),
        ):
            r = client.get("/api/v1/methodology/versions")

        assert r.status_code == 500
        detail = r.json()["detail"]
        assert detail["error"] == "version_list_unavailable"
        assert detail["detail"] == "list boom"


class TestChangelogEndpointFailure:
    """A failure building the changelog is a structured 500."""

    def test_changelog_failure_returns_500(
        self, client: TestClient
    ) -> None:
        with patch(
            "app.api.v1.methodology.get_methodology_changelog",
            side_effect=RuntimeError("changelog boom"),
        ):
            r = client.get("/api/v1/methodology/changelog")

        assert r.status_code == 500
        detail = r.json()["detail"]
        assert detail["error"] == "changelog_unavailable"
        assert detail["detail"] == "changelog boom"


# ============================================================
# OPENAPI
# ============================================================
class TestOpenAPI:
    """The endpoints are advertised in the OpenAPI schema."""

    def test_paths_include_all_three(self, client: TestClient) -> None:
        spec = client.get("/openapi.json").json()
        assert "/api/v1/methodology" in spec["paths"]
        assert "/api/v1/methodology/versions" in spec["paths"]
        assert "/api/v1/methodology/changelog" in spec["paths"]

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

    def test_response_schemas_registered(
        self, client: TestClient
    ) -> None:
        spec = client.get("/openapi.json").json()
        schemas = spec.get("components", {}).get("schemas", {})
        for name in (
            "MethodologyResponse",
            "ModelSpecResponse",
            "CorrelationSpecResponse",
            "RegimeSpecResponse",
            "DataSourceSpecResponse",
            "LimitationSpecResponse",
            "MethodologyVersionListResponse",
            "MethodologyChangelogResponse",
            "ChangelogEntryResponse",
        ):
            assert name in schemas, f"{name} missing from OpenAPI"

    def test_version_query_param_documented(
        self, client: TestClient
    ) -> None:
        spec = client.get("/openapi.json").json()
        op = spec["paths"]["/api/v1/methodology"]["get"]
        params = op.get("parameters", [])
        names = [p["name"] for p in params]
        assert "version" in names