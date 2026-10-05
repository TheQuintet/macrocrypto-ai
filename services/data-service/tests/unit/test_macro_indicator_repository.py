import pytest
from unittest.mock import MagicMock, patch

import app.database.macro_indicator_repository as macro_indicator_repository
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)


def create_repository():

    db = MagicMock()

    return MacroIndicatorRepository(
        db
    )



def test_create_indicator():

    repository = create_repository()

    repository.db.add = MagicMock()
    repository.db.commit = MagicMock()
    repository.db.refresh = MagicMock()


    result = repository.create_indicator(
        indicator_name="cpi",
        time="2026-01-01",
        value=300.0,
        previous_value=290.0,
        change_percent=3.44,
    )


    assert result.indicator_name == "cpi"

    assert result.value == 300.0

    assert result.previous_value == 290.0

    assert result.change_percent == 3.44

    assert result.source == "fred"


    repository.db.add.assert_called_once()

    repository.db.commit.assert_called_once()

    repository.db.refresh.assert_called_once()



def test_create_many_empty_list():

    repository = create_repository()


    result = repository.create_many(
        []
    )


    assert result == []

    repository.db.execute.assert_not_called()

    repository.db.commit.assert_not_called()



def test_create_many_success():

    repository = create_repository()

    repository.db.execute = MagicMock()

    repository.db.commit = MagicMock()


    indicators = [
        {
            "indicator_name": "cpi",
            "time": "2026-01-01",
            "value": 300,
            "previous_value": 290,
            "change_percent": 3.44,
            "source": "fred",
        }
    ]


    result = repository.create_many(
        indicators
    )


    assert result == indicators


    repository.db.execute.assert_called_once()

    repository.db.commit.assert_called_once()



def test_create_many_duplicate_handling():

    repository = create_repository()

    repository.db.execute = MagicMock()

    repository.db.commit = MagicMock()


    indicators = [
        {
            "indicator_name": "cpi",
            "time": "2026-01-01",
            "value": 300,
            "previous_value": None,
            "change_percent": None,
            "source": "fred",
        }
    ]


    result = repository.create_many(
        indicators
    )


    assert len(result) == 1

    assert result[0]["indicator_name"] == "cpi"

    repository.db.execute.assert_called_once()

    repository.db.commit.assert_called_once()


def test_create_many_splits_large_input_into_batches(monkeypatch):
    repository = create_repository()
    repository.db.execute = MagicMock()
    repository.db.commit = MagicMock()
    monkeypatch.setattr(
        macro_indicator_repository,
        "MAX_INSERT_BATCH_SIZE",
        2,
    )

    indicators = [
        {
            "indicator_name": "cpi",
            "time": f"2026-01-0{day}",
            "value": 300 + day,
            "previous_value": None,
            "change_percent": None,
            "source": "fred",
        }
        for day in range(1, 6)
    ]

    result = repository.create_many(indicators)

    assert result == indicators
    assert repository.db.execute.call_count == 3
    assert [
        len(call.args[0]._multi_values[0])
        for call in repository.db.execute.call_args_list
    ] == [2, 2, 1]
    repository.db.commit.assert_called_once()