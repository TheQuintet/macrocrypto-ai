"""Cross-repository tests for CLI-mode table routing.

Every repository that reads or writes a table with a `_cli` mirror
must resolve the active table by consulting `settings.cli_mode`.
This file asserts that contract in one place, so a reviewer can
see at a glance that CLI-mode isolation is respected everywhere.

Scope:
    - `_resolve_*_table()` methods on each repository
    - Behavior when `settings.cli_mode` is False (production)
    - Behavior when `settings.cli_mode` is True  (sandboxed)

Out of scope:
    - The actual SQL those resolvers feed into (covered by each
      repository's own test file)
    - Whether the `_cli` mirror tables exist in the DB (that's a
      migration concern, tested elsewhere)

Adding coverage for a new repository:
    Copy the shape of any `Test<Repo>Routing` class below. Patch
    `settings` on the module that owns the resolver, then assert
    that both `settings.cli_mode = False` and `settings.cli_mode
    = True` produce the expected table object.

Rationale for one file rather than N test classes spread around:
    The routing rule is a *contract* — "CLI mode isolates writes
    from production." It is best verified in one place so that:
        1. A reviewer can audit it quickly.
        2. A regression here fails loudly rather than hiding inside
           a large per-repository test file.
        3. Adding a new repository makes the missing test obvious.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.repositories.champion_repository import (
    ChampionRepository,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.database.tables import (
    btc_predictions,
    btc_predictions_cli,
    champion_candidates,
    champion_candidates_cli,
    model_champions,
    model_champions_cli,
)


# ============================================================
# HELPERS
# ============================================================
def _make_session() -> MagicMock:
    """Build a no-op AsyncMock session.

    The routing helpers don't touch the session — they only
    consult `settings.cli_mode` and return a table object — so
    the session is never exercised. We pass one anyway to satisfy
    each repository's constructor.
    """
    return MagicMock(spec=["execute", "flush", "commit"])


def _patch_cli_mode(module: str, cli: bool):
    """Patch `settings.cli_mode` on the given module to `cli`.

    Args:
        module: The dotted path of the module that owns the
            resolver (e.g. `"app.database.repositories.champion_repository"`).
        cli: The boolean value to assign to `settings.cli_mode`.
    """
    return patch(f"{module}.settings.cli_mode", cli)


# ============================================================
# CHAMPION REPOSITORY
# ============================================================
class TestChampionRepositoryRouting:
    """Routing for `ChampionRepository`."""

    CHAMPION_MODULE = (
        "app.database.repositories.champion_repository"
    )

    def test_champion_table_is_production_when_not_cli(self) -> None:
        repo = ChampionRepository(_make_session())
        with _patch_cli_mode(self.CHAMPION_MODULE, False):
            assert repo._resolve_champion_table() is model_champions

    def test_champion_table_is_cli_when_cli(self) -> None:
        repo = ChampionRepository(_make_session())
        with _patch_cli_mode(self.CHAMPION_MODULE, True):
            assert repo._resolve_champion_table() is model_champions_cli

    def test_candidates_table_is_production_when_not_cli(self) -> None:
        repo = ChampionRepository(_make_session())
        with _patch_cli_mode(self.CHAMPION_MODULE, False):
            assert repo._resolve_candidates_table() is champion_candidates

    def test_candidates_table_is_cli_when_cli(self) -> None:
        repo = ChampionRepository(_make_session())
        with _patch_cli_mode(self.CHAMPION_MODULE, True):
            assert (
                repo._resolve_candidates_table()
                is champion_candidates_cli
            )

    def test_toggle_between_modes_in_same_process(self) -> None:
        """The resolver reads settings at call time, not construction time.

        This matters: a repository constructed in production mode
        must resolve to the CLI table if `cli_mode` is flipped on
        afterwards, and vice versa. The resolver is not memoized.
        """
        repo = ChampionRepository(_make_session())
        with _patch_cli_mode(self.CHAMPION_MODULE, False):
            assert repo._resolve_champion_table() is model_champions
        with _patch_cli_mode(self.CHAMPION_MODULE, True):
            assert repo._resolve_champion_table() is model_champions_cli
        with _patch_cli_mode(self.CHAMPION_MODULE, False):
            assert repo._resolve_champion_table() is model_champions


# ============================================================
# PREDICTION REPOSITORY
# ============================================================
class TestPredictionRepositoryRouting:
    """Routing for `PredictionRepository`."""

    PREDICTION_MODULE = (
        "app.database.repositories.prediction_repository"
    )

    def test_predictions_table_is_production_when_not_cli(self) -> None:
        repo = PredictionRepository(_make_session())
        with _patch_cli_mode(self.PREDICTION_MODULE, False):
            assert repo._resolve_predictions_table() is btc_predictions

    def test_predictions_table_is_cli_when_cli(self) -> None:
        repo = PredictionRepository(_make_session())
        with _patch_cli_mode(self.PREDICTION_MODULE, True):
            assert (
                repo._resolve_predictions_table() is btc_predictions_cli
            )

    def test_toggle_between_modes_in_same_process(self) -> None:
        """Same non-memoization guarantee as the champion repo."""
        repo = PredictionRepository(_make_session())
        with _patch_cli_mode(self.PREDICTION_MODULE, False):
            assert repo._resolve_predictions_table() is btc_predictions
        with _patch_cli_mode(self.PREDICTION_MODULE, True):
            assert (
                repo._resolve_predictions_table() is btc_predictions_cli
            )
        with _patch_cli_mode(self.PREDICTION_MODULE, False):
            assert repo._resolve_predictions_table() is btc_predictions


# ============================================================
# CROSS-REPOSITORY INVARIANTS
# ============================================================
class TestRoutingInvariants:
    """Invariants that must hold across every repository.

    These are structural checks — they don't construct any
    repository. They just verify that the naming convention for
    the CLI mirrors is followed, so a new repository can't
    accidentally introduce a differently-named mirror table.
    """

    def test_all_cli_tables_end_with_suffix(self) -> None:
        """Every `_cli` mirror table ends with `_cli` in its name."""
        cli_tables = [
            model_champions_cli,
            champion_candidates_cli,
            btc_predictions_cli,
        ]
        for t in cli_tables:
            assert t.name.endswith("_cli"), (
                f"CLI mirror {t.name!r} does not follow the "
                f"<name>_cli naming convention"
            )

    def test_production_and_cli_tables_share_columns(self) -> None:
        """Each production table and its `_cli` mirror share column names.

        The mirror is created by `CREATE TABLE ... (LIKE ... INCLUDING
        ALL)`, so the columns must match exactly. If they ever
        diverge, the repository code that runs against one mode
        would break silently in the other.
        """
        pairs = [
            (model_champions, model_champions_cli),
            (champion_candidates, champion_candidates_cli),
            (btc_predictions, btc_predictions_cli),
        ]
        for prod, cli in pairs:
            prod_cols = {c.name for c in prod.columns}
            cli_cols = {c.name for c in cli.columns}
            assert prod_cols == cli_cols, (
                f"Column mismatch between {prod.name} and {cli.name}: "
                f"prod-only={prod_cols - cli_cols}, "
                f"cli-only={cli_cols - prod_cols}"
            )

    def test_production_and_cli_tables_are_distinct_objects(self) -> None:
        """A CLI mirror must not be the same object as its production table.

        If someone accidentally aliased the CLI table to the
        production one (e.g. by a bad import), CLI mode would write
        to production silently. This test catches that.
        """
        pairs = [
            (model_champions, model_champions_cli),
            (champion_candidates, champion_candidates_cli),
            (btc_predictions, btc_predictions_cli),
        ]
        for prod, cli in pairs:
            assert prod is not cli, (
                f"{prod.name} and {cli.name} are the same object; "
                f"CLI isolation is broken"
            )