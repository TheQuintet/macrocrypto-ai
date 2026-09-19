"""
Generate the ML data coverage report directly from PostgreSQL.

The database is the source of truth for all row counts and dates.

The generated Markdown contains:
1. Coverage Data table
2. Granular Source Breakdown

No data is modified.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.database.session import SessionLocal


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_FILE = Path("coverage_data_report.md")


# ---------------------------------------------------------------------------
# Coverage configuration
# ---------------------------------------------------------------------------

FEATURES = [
    ("btc_prices", "btc_price", 1),
    ("btc_prices", "btc_volume", 2),
    ("btc_dominance", "btc_dominance", 3),
    ("macro_indicators", "gdp", 4),
    ("macro_indicators", "cpi", 4),
    ("macro_indicators", "unemployment", 4),
    ("macro_indicators", "federal_funds_rate", 4),
    ("macro_indicators", "m2_money_supply", 4),
    ("macro_indicators", "ten_year_treasury", 4),
    ("macro_indicators", "nasdaq_composite", 4),
    ("macro_indicators", "vix", 4),
    ("macro_indicators", "high_yield_spread", 4),
    ("macro_indicators", "dxy", 4),
    ("macro_indicators", "active_addresses", 4),
    ("macro_indicators", "gold_spot", 4),
    ("macro_indicators", "equity_corr", 4),
]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_number(value: int) -> str:
    return f"{value:,}"


def format_timestamp(value) -> str:
    if value is None:
        return ""

    return value.strftime("%Y-%m-%d %H:%M:%S+00")


def format_date_range(first_seen, last_seen) -> str:
    if first_seen is None or last_seen is None:
        return "no data"

    first = first_seen.strftime("%Y-%m-%d")
    last = last_seen.strftime("%Y-%m-%d")

    return f"{first} to {last}"


# ---------------------------------------------------------------------------
# Coverage queries
# ---------------------------------------------------------------------------

def get_btc_price_coverage(session, feature_name: str, sort_order: int):
    query = text(
        """
        SELECT
            :table_name AS table_name,
            :feature_name AS feature_name,
            COUNT(*) AS rows,
            MIN(time) AS first_seen,
            MAX(time) AS last_seen,
            COUNT(DISTINCT time::date) AS distinct_days,
            :sort_order AS sort_order
        FROM btc_prices
        WHERE
            CASE
                WHEN :feature_name = 'btc_price'
                    THEN price IS NOT NULL
                WHEN :feature_name = 'btc_volume'
                    THEN volume IS NOT NULL
                ELSE FALSE
            END
        """
    )

    return session.execute(
        query,
        {
            "table_name": "btc_prices",
            "feature_name": feature_name,
            "sort_order": sort_order,
        },
    ).mappings().one()


def get_btc_dominance_coverage(session, sort_order: int):
    query = text(
        """
        SELECT
            'btc_dominance' AS table_name,
            'btc_dominance' AS feature_name,
            COUNT(*) AS rows,
            MIN(time) AS first_seen,
            MAX(time) AS last_seen,
            COUNT(DISTINCT time::date) AS distinct_days,
            :sort_order AS sort_order
        FROM btc_dominance
        WHERE dominance IS NOT NULL
        """
    )

    return session.execute(
        query,
        {"sort_order": sort_order},
    ).mappings().one()


def get_macro_coverage(session, feature_name: str, sort_order: int):
    query = text(
        """
        SELECT
            'macro_indicators' AS table_name,
            :feature_name AS feature_name,
            COUNT(*) AS rows,
            MIN(time) AS first_seen,
            MAX(time) AS last_seen,
            COUNT(DISTINCT time::date) AS distinct_days,
            :sort_order AS sort_order
        FROM macro_indicators
        WHERE
            indicator_name = :feature_name
            AND value IS NOT NULL
        """
    )

    return session.execute(
        query,
        {
            "feature_name": feature_name,
            "sort_order": sort_order,
        },
    ).mappings().one()


def generate_coverage_rows(session):
    rows = []

    for table_name, feature_name, sort_order in FEATURES:

        if table_name == "btc_prices":
            row = get_btc_price_coverage(
                session,
                feature_name,
                sort_order,
            )

        elif table_name == "btc_dominance":
            row = get_btc_dominance_coverage(
                session,
                sort_order,
            )

        elif table_name == "macro_indicators":
            row = get_macro_coverage(
                session,
                feature_name,
                sort_order,
            )

        else:
            raise ValueError(
                f"Unsupported table: {table_name}"
            )

        rows.append(dict(row))

    return rows


# ---------------------------------------------------------------------------
# Source breakdown queries
# ---------------------------------------------------------------------------

def get_btc_price_sources(session):
    query = text(
        """
        SELECT
            source,
            COUNT(*) AS rows,
            MIN(time) AS first_seen,
            MAX(time) AS last_seen
        FROM btc_prices
        GROUP BY source
        ORDER BY MIN(time), source
        """
    )

    return session.execute(query).mappings().all()


def get_btc_dominance_sources(session):
    query = text(
        """
        SELECT
            source,
            COUNT(*) AS rows,
            MIN(time) AS first_seen,
            MAX(time) AS last_seen
        FROM btc_dominance
        GROUP BY source
        ORDER BY MIN(time), source
        """
    )

    return session.execute(query).mappings().all()


def get_macro_sources(session):
    query = text(
        """
        SELECT
            indicator_name AS feature,
            source,
            COUNT(*) AS rows,
            MIN(time) AS first_seen,
            MAX(time) AS last_seen
        FROM macro_indicators
        GROUP BY indicator_name, source
        ORDER BY
            indicator_name,
            MIN(time),
            source
        """
    )

    return session.execute(query).mappings().all()


def generate_source_rows(session):
    return {
        "btc_price": get_btc_price_sources(session),
        "btc_dominance": get_btc_dominance_sources(session),
        "macro_indicators": get_macro_sources(session),
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_coverage_table(rows):
    lines = [
        "| table_name | feature_name | rows | first_seen | last_seen | distinct_days | sort_order |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for row in rows:
        lines.append(
            "| "
            f"`{row['table_name']}` | "
            f"`{row['feature_name']}` | "
            f"{format_number(row['rows'])} | "
            f"{format_timestamp(row['first_seen'])} | "
            f"{format_timestamp(row['last_seen'])} | "
            f"{format_number(row['distinct_days'])} | "
            f"{row['sort_order']} |"
        )

    return "\n".join(lines)


def render_source_breakdown(source_rows):
    lines = [
        "",
        "### Granular Source Breakdown",
        "",
        "* **`btc_price` Sources:**",
    ]

    for row in source_rows["btc_price"]:
        lines.append(
            f"  * `{row['source']}`: "
            f"{format_number(row['rows'])} rows "
            f"({format_date_range(row['first_seen'], row['last_seen'])})"
        )

    lines.extend(
        [
            "",
            "* **`btc_dominance` Sources:**",
        ]
    )

    for row in source_rows["btc_dominance"]:
        lines.append(
            f"  * `{row['source']}`: "
            f"{format_number(row['rows'])} rows "
            f"({format_date_range(row['first_seen'], row['last_seen'])})"
        )

    lines.extend(
        [
            "",
            "* **`macro_indicators` Sources:**",
        ]
    )

    for row in source_rows["macro_indicators"]:
        lines.append(
            f"  * `{row['feature']}` (`{row['source']}`): "
            f"{format_number(row['rows'])} rows "
            f"({format_date_range(row['first_seen'], row['last_seen'])})"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Opening database session...")

    session = SessionLocal()

    try:
        print("Generating coverage data...")

        coverage_rows = generate_coverage_rows(session)

        print("Generating source breakdown...")

        source_rows = generate_source_rows(session)

        markdown = (
            render_coverage_table(coverage_rows)
            + "\n"
            + render_source_breakdown(source_rows)
            + "\n"
        )

        OUTPUT_FILE.write_text(
            markdown,
            encoding="utf-8",
        )

        print()
        print("Coverage report generated:")
        print(OUTPUT_FILE.resolve())
        print()
        print(markdown)

    finally:
        session.close()


if __name__ == "__main__":
    main()