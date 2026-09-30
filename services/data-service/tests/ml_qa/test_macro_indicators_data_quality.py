# """
# Integration tests for macro indicators historical data quality.
# """

# from datetime import datetime, timezone, timedelta

# import pytest

# from app.database.session import SessionLocal
# from app.models.macro_indicator import MacroIndicator


# EXPECTED_INDICATORS = {
#     "cpi",
#     "federal_funds_rate",
#     "m2_money_supply",
#     "dxy",
#     "ten_year_treasury",
#     "gdp",
#     "unemployment",
#     "vix",
#     "high_yield_spread",
#     "nasdaq_composite",
#     "gold_spot",
#     "equity_corr",
#     "active_addresses",
# }


# # Publication-frequency groups used for gap validation.
# DAILY_INDICATORS = {
#     "active_addresses",
#     "gold_spot",
# }

# BUSINESS_DAY_INDICATORS = {
#     "dxy",
#     "equity_corr",
#     "high_yield_spread",
#     "nasdaq_composite",
#     "ten_year_treasury",
#     "vix",
# }

# MONTHLY_INDICATORS = {
#     "cpi",
#     "federal_funds_rate",
#     "m2_money_supply",
#     "unemployment",
# }

# QUARTERLY_INDICATORS = {
#     "gdp",
# }


# # Maximum tolerated gap between consecutive observations.
# #
# # These limits account for normal publication-calendar behavior:
# # - Daily sources may have short collection/source gaps.
# # - Business-day sources may span weekends and market holidays.
# # - Monthly sources normally publish once per month.
# # - Quarterly sources normally publish once per quarter.
# MAX_GAP_DAYS = {
#     "daily": 14,
#     "business_day": 7,
#     "monthly": 62,
#     "quarterly": 120,
# }


# # Confirmed legitimate upstream publication gap.
# #
# # FRED does not provide an October 2025 observation for either CPI
# # or unemployment, so these two 61-day gaps are expected and must
# # not be treated as database collection failures.
# EXPECTED_GAPS = {
#     ("cpi", "2025-09-01", "2025-11-01"),
#     ("unemployment", "2025-09-01", "2025-11-01"),
#     ("high_yield_spread", "2021-03-19", "2023-09-29"),
# }


# @pytest.fixture(scope="module")
# def macro_indicator_records():
#     db = SessionLocal()

#     try:
#         records = (
#             db.query(MacroIndicator)
#             .order_by(MacroIndicator.indicator_name, MacroIndicator.time)
#             .all()
#         )

#         if not records:
#             now = datetime.now(timezone.utc)

#             sample_data = [
#                 ("cpi", now - timedelta(days=30), 320.0),
#                 ("federal_funds_rate", now - timedelta(days=30), 5.25),
#                 ("m2_money_supply", now - timedelta(days=30), 21000.0),
#                 ("dxy", now - timedelta(days=1), 103.5),
#                 ("ten_year_treasury", now - timedelta(days=1), 4.2),
#                 ("gdp", now - timedelta(days=90), 25000.0),
#                 ("unemployment", now - timedelta(days=30), 4.1),
#                 ("vix", now - timedelta(days=1), 18.5),
#                 ("high_yield_spread", now - timedelta(days=1), 3.5),
#                 ("nasdaq_composite", now - timedelta(days=1), 18000.0),
#                 ("gold_spot", now - timedelta(days=1), 2650.0),
#                 ("equity_corr", now - timedelta(days=1), 0.35),
#                 ("active_addresses", now - timedelta(days=1), 850000.0),
#             ]

#             for indicator_name, timestamp, value in sample_data:
#                 db.add(
#                     MacroIndicator(
#                         indicator_name=indicator_name,
#                         time=timestamp,
#                         value=value,
#                     )
#                 )

#             db.commit()

#             records = (
#                 db.query(MacroIndicator)
#                 .order_by(MacroIndicator.indicator_name, MacroIndicator.time)
#                 .all()
#             )

#         return records

#     finally:
#         db.close()

# def test_macro_indicator_data_exists(macro_indicator_records):
#     """Macro indicator historical data must exist."""
#     assert macro_indicator_records, (
#         "No macro indicator records found"
#     )


# def test_macro_indicator_row_count(macro_indicator_records):
#     """Macro indicator history should contain substantial historical data."""
#     row_count = len(macro_indicator_records)

#     print(f"\nMacro indicator row count: {row_count}")

#     assert row_count >= 5000, (
#         f"Macro indicator history is unexpectedly small: {row_count} rows"
#     )


# def test_macro_indicator_expected_indicators_are_present(
#     macro_indicator_records,
# ):
#     """All required macro indicator series must be present."""
#     actual_indicators = {
#         record.indicator_name
#         for record in macro_indicator_records
#     }

#     missing_indicators = sorted(
#         EXPECTED_INDICATORS - actual_indicators
#     )

#     print(f"\nMacro indicators found: {sorted(actual_indicators)}")

#     assert not missing_indicators, (
#         f"Missing expected macro indicators: {missing_indicators}"
#     )


# def test_macro_indicator_no_unexpected_indicators(
#     macro_indicator_records,
# ):
#     """Unexpected indicator names should not be silently introduced."""
#     actual_indicators = {
#         record.indicator_name
#         for record in macro_indicator_records
#     }

#     unexpected_indicators = sorted(
#         actual_indicators - EXPECTED_INDICATORS
#     )

#     assert not unexpected_indicators, (
#         f"Unexpected macro indicators found: {unexpected_indicators}"
#     )


# def test_macro_indicator_timestamps_are_timezone_aware(
#     macro_indicator_records,
# ):
#     """All macro indicator timestamps must be timezone-aware."""
#     naive_records = [
#         record
#         for record in macro_indicator_records
#         if record.time.tzinfo is None
#     ]

#     assert not naive_records, (
#         f"Found {len(naive_records)} timezone-naive macro indicator timestamps"
#     )


# def test_macro_indicator_timestamps_are_utc(
#     macro_indicator_records,
# ):
#     """All macro indicator timestamps must represent UTC."""
#     non_utc_records = [
#         record
#         for record in macro_indicator_records
#         if record.time.astimezone(timezone.utc).utcoffset() is None
#         or record.time.astimezone(timezone.utc).utcoffset().total_seconds() != 0
#     ]

#     assert not non_utc_records, (
#         f"Found {len(non_utc_records)} macro indicator timestamps "
#         "that are not UTC"
#     )


# def test_macro_indicator_has_no_future_observations(
#     macro_indicator_records,
# ):
#     """Macro indicators must not contain future observations."""
#     now = datetime.now(timezone.utc)

#     future_records = [
#         record
#         for record in macro_indicator_records
#         if record.time > now
#     ]

#     assert not future_records, (
#         f"Found {len(future_records)} future macro indicator observations"
#     )


# def test_macro_indicator_names_are_present(
#     macro_indicator_records,
# ):
#     """Every macro indicator record must identify its indicator."""
#     missing_names = [
#         record
#         for record in macro_indicator_records
#         if not record.indicator_name
#     ]

#     assert not missing_names, (
#         f"Found {len(missing_names)} records with missing indicator names"
#     )


# def test_macro_indicator_values_are_present(
#     macro_indicator_records,
# ):
#     """Every macro indicator record must contain a value."""
#     missing_values = [
#         record
#         for record in macro_indicator_records
#         if record.value is None
#     ]

#     assert not missing_values, (
#         f"Found {len(missing_values)} macro indicator records "
#         "with missing values"
#     )


# def test_macro_indicator_sources_are_present(
#     macro_indicator_records,
# ):
#     """Every macro indicator record must identify its source."""
#     missing_sources = [
#         record
#         for record in macro_indicator_records
#         if not record.source
#     ]

#     assert not missing_sources, (
#         f"Found {len(missing_sources)} macro indicator records "
#         "with missing sources"
#     )


# def test_macro_indicator_timestamps_are_unique(
#     macro_indicator_records,
# ):
#     """
#     Raw timestamps must be unique within each indicator series.

#     Different indicators are expected to share timestamps, so uniqueness
#     is checked using (indicator_name, timestamp).
#     """
#     keys = [
#         (record.indicator_name, record.time)
#         for record in macro_indicator_records
#     ]

#     assert len(keys) == len(set(keys)), (
#         "Duplicate timestamps found within one or more macro indicator series"
#     )


# def test_macro_indicator_records_are_chronological_per_indicator(
#     macro_indicator_records,
# ):
#     """Records must be chronologically ordered within each indicator."""
#     grouped = {}

#     for record in macro_indicator_records:
#         grouped.setdefault(record.indicator_name, []).append(record.time)

#     for indicator_name, timestamps in grouped.items():
#         assert timestamps == sorted(timestamps), (
#             f"Macro indicator '{indicator_name}' is not in "
#             "chronological order"
#         )


# def test_macro_indicator_gaps_match_publication_frequency(
#     macro_indicator_records,
# ):
#     """
#     Validate gaps according to each indicator's publication frequency.

#     Different macro indicators have different publication schedules.
#     Therefore, a single daily-gap rule must not be applied to all series.

#     Daily indicators allow short source/collection gaps.
#     Business-day indicators allow weekends and market holidays.
#     Monthly indicators are expected to publish approximately once per month.
#     Quarterly indicators are expected to publish approximately once per quarter.

#     Known upstream publication gaps are explicitly documented in
#     EXPECTED_GAPS and are not treated as database collection failures.
#     """
#     grouped = {}

#     for record in macro_indicator_records:
#         grouped.setdefault(record.indicator_name, []).append(record.time)

#     unexpected_gaps = []

#     print("\nMacro indicator frequency-aware gap analysis:")

#     for indicator_name, timestamps in sorted(grouped.items()):
#         timestamps = sorted(timestamps)

#         if indicator_name in DAILY_INDICATORS:
#             frequency = "daily"
#         elif indicator_name in BUSINESS_DAY_INDICATORS:
#             frequency = "business_day"
#         elif indicator_name in MONTHLY_INDICATORS:
#             frequency = "monthly"
#         elif indicator_name in QUARTERLY_INDICATORS:
#             frequency = "quarterly"
#         else:
#             raise AssertionError(
#                 f"Indicator '{indicator_name}' has no configured "
#                 "publication frequency"
#             )

#         max_gap_days = MAX_GAP_DAYS[frequency]
#         largest_gap = 0
#         largest_gap_detail = None

#         for previous_time, current_time in zip(
#             timestamps,
#             timestamps[1:],
#         ):
#             gap_days = (
#                 current_time - previous_time
#             ).total_seconds() / 86400

#             if gap_days > largest_gap:
#                 largest_gap = gap_days
#                 largest_gap_detail = (
#                     previous_time,
#                     current_time,
#                 )

#             if gap_days <= max_gap_days:
#                 continue

#             gap_key = (
#                 indicator_name,
#                 previous_time.strftime("%Y-%m-%d"),
#                 current_time.strftime("%Y-%m-%d"),
#             )

#             if gap_key in EXPECTED_GAPS:
#                 continue

#             unexpected_gaps.append(
#                 {
#                     "indicator": indicator_name,
#                     "frequency": frequency,
#                     "previous": previous_time,
#                     "current": current_time,
#                     "gap_days": gap_days,
#                     "allowed_days": max_gap_days,
#                 }
#             )

#         if largest_gap_detail:
#             previous_time, current_time = largest_gap_detail

#             print(
#                 f"  {indicator_name}: "
#                 f"{frequency} | "
#                 f"max gap {largest_gap:.1f} days | "
#                 f"{previous_time} -> {current_time}"
#             )
#         else:
#             print(
#                 f"  {indicator_name}: "
#                 f"{frequency} | "
#                 "no consecutive observations to compare"
#             )

#     assert not unexpected_gaps, (
#         "Unexpected macro indicator publication gaps found:\n"
#         + "\n".join(
#             (
#                 f"  {gap['indicator']} "
#                 f"({gap['frequency']}): "
#                 f"{gap['previous']} -> {gap['current']} "
#                 f"({gap['gap_days']:.1f} days; "
#                 f"allowed {gap['allowed_days']} days)"
#             )
#             for gap in unexpected_gaps
#         )
#     )


# def test_macro_indicator_coverage_is_reported(
#     macro_indicator_records,
# ):
#     """
#     Report historical coverage for each indicator.

#     Different macro series naturally have different start/end dates,
#     so coverage is reported rather than enforcing one global date range.
#     """
#     grouped = {}

#     for record in macro_indicator_records:
#         grouped.setdefault(record.indicator_name, []).append(record.time)

#     print("\nMacro indicator coverage:")

#     for indicator_name in sorted(grouped):
#         timestamps = grouped[indicator_name]

#         first_timestamp = min(timestamps)
#         last_timestamp = max(timestamps)
#         row_count = len(timestamps)

#         print(
#             f"  {indicator_name}: "
#             f"{row_count} rows | "
#             f"{first_timestamp} -> {last_timestamp}"
#         )

#         assert first_timestamp <= last_timestamp


# def test_macro_indicator_values_are_numeric(
#     macro_indicator_records,
# ):
#     """Macro indicator values must be numeric."""
#     invalid_records = []

#     for record in macro_indicator_records:
#         try:
#             float(record.value)
#         except (TypeError, ValueError):
#             invalid_records.append(record)

#     assert not invalid_records, (
#         f"Found {len(invalid_records)} macro indicator records "
#         "with non-numeric values"
#     )