"""
Module for loading and processing fund data for comparison.
Handles loading from Parquet files, temporal alignment, and normalization.
"""

import sqlite3
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa
from pathlib import Path
from typing import List, Dict, Optional


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DB = DATA_DIR / "metadata_funds.db"

# ─────────────────────────────────────────────
# METADATA FUNCTIONS (SQLite)
# ─────────────────────────────────────────────

def get_funds_metadata(isins: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Retrieves fund metadata from the SQLite database.

    Args:
        isins: List of ISINs to query.

    Returns:
        Dictionary mapping each ISIN to its metadata:
        {isin: {'start_date': '...', 'name': '...'}}.
    """
    if not METADATA_DB.exists():
        return {}

    conn = sqlite3.connect(METADATA_DB)
    placeholders = ','.join('?' * len(isins))
    query = f'SELECT isin, start_date, name FROM funds WHERE isin IN ({placeholders})'
    cursor = conn.execute(query, isins)

    metadata = {
        row[0]: {'start_date': row[1], 'name': row[2]}
        for row in cursor.fetchall()
    }
    conn.close()

    return metadata


def fund_exists(isin: str) -> bool:
    """Checks whether the parquet file for the given fund exists."""
    return (DATA_DIR / f"{isin}.parquet").exists()


# ─────────────────────────────────────────────
# DATA LOADING (Parquet)
# ─────────────────────────────────────────────

def load_normalized_data_fund(isin: str, start_date: Optional[str] = None, end_date: Optional[str] = None)\
        -> Optional[pa.Table]:
    """
    Loads and normalizes fund data to base 100.

    Args:
        isin: Fund ISIN identifier.
        start_date: Optional start date filter (inclusive).
        end_date: End date filter (inclusive).

    Returns:
        PyArrow Table with columns [date, total_return] normalized to base 100,
        or None if the file is missing or data is empty.
    """
    filepath = DATA_DIR / f"{isin}.parquet"
    if not filepath.exists():
        return None

    try:
        fund_data = pq.read_table(filepath)

        # Apply start date filter if provided
        if start_date:
            mask_greater = pc.greater_equal(fund_data['date'], start_date)
            fund_data = fund_data.filter(mask_greater)

        mask_less = pc.less_equal(fund_data['date'], end_date)
        fund_data = fund_data.filter(mask_less)
        base_value = fund_data["total_return"][0]
        division = pc.divide(fund_data["total_return"], base_value)
        normalized_column = pc.multiply(division, pa.scalar(100.0))
        idx = fund_data.schema.get_field_index("total_return")
        fund_data = fund_data.set_column(idx, "total_return", normalized_column)

        if len(fund_data) == 0:
            return None

        return fund_data

    except Exception as e:
        print(f"Error loading {isin}: {e}")
        return None


# ─────────────────────────────────────────────
# NORMALIZATION AND ALIGNMENT
# ─────────────────────────────────────────────

def normalize_to_base_100(values: List[float]) -> List[float]:
    """Normalizes a list of values to base 100 from the first element."""
    if not values or values[0] == 0:
        return values
    first = values[0]
    return [(v / first) * 100.0 for v in values]


# ─────────────────────────────────────────────
# FUND COMPARISON
# ─────────────────────────────────────────────

def get_funds_for_comparison(
        isins: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
) -> List[Dict]:
    """
    Prepares fund data for comparison, including CAGR calculation.

    Args:
        isins: List of fund ISINs.
        start_date: Start date filter (None = full history per fund).
        end_date: End date filter.

    Returns:
        List of dicts with keys:
        {'isin': str, 'name': str, 'fund_data': pa.Table, 'cagr': float}.
    """
    funds_info = []
    for isin in isins:
        metadata = get_funds_metadata([isin])
        name = metadata.get(isin, {}).get('name', isin)

        data = load_normalized_data_fund(isin, start_date, end_date)
        dates_parsed = pc.cast(data["date"], pa.date32())
        min_date = pc.min(dates_parsed)
        max_date = pc.max(dates_parsed)
        v_inicial = data["total_return"][0].as_py()
        v_final = data["total_return"][-1].as_py()
        n_years = pc.days_between(min_date, max_date).as_py() / 365.25
        if n_years >= 1:
            cagr_performance = (v_final / v_inicial) ** (1 / n_years) - 1
        else:
            cagr_performance = (v_final / v_inicial) - 1

        if data:
            funds_info.append(
                {'isin': isin, 'name': name, 'fund_data': data, 'cagr': cagr_performance}
            )

    if not funds_info:
        return []

    return funds_info

# ─────────────────────────────────────────────
# PORTFOLIO WEIGHTING
# ─────────────────────────────────────────────
def weight_portfolio_funds(funds_data_weights: list[dict]):
    """
    Calculates the weighted total return of a portfolio by combining
    individual fund returns according to their assigned weights.

    Args:
        funds_data_weights: List of dicts, each containing:
            - 'fund_data': pa.Table with columns [date, total_return]
            - 'weight': float (decimal, e.g. 0.5 for 50%)

    Returns:
        pa.Table with columns [date, total_return] representing the
        weighted portfolio performance.
    """
    # 1. Build a master calendar from all unique dates across funds
    all_dates_combined = pa.concat_tables([f_w.get("fund_data").select(["date"]) for f_w in funds_data_weights])
    master_calendar = pa.Table.from_arrays(
        [pc.unique(all_dates_combined["date"])],
        names=["date"]
    ).sort_by([("date", "ascending")])

    weighted_arrays = []

    # 2. Align each fund to the master calendar and apply its weight
    for item in funds_data_weights:
        table = item['fund_data']
        weight = item['weight']

        aligned_table = master_calendar.join(table, keys="date", join_type="left outer")
        aligned_table = aligned_table.sort_by([("date", "ascending")])

        # Forward-fill missing values for dates where a fund has no data
        filled_values = pc.fill_null_forward(aligned_table["total_return"])

        weighted_array = pc.multiply(filled_values, weight)
        weighted_arrays.append(weighted_array)

    # 3. Sum all weighted arrays into a single total return series
    total_weighted_return = weighted_arrays[0]

    for i in range(1, len(weighted_arrays)):
        # Use fill_null(0) to handle funds with different start dates
        total_weighted_return = pc.add(
            pc.fill_null(total_weighted_return, 0),
            pc.fill_null(weighted_arrays[i], 0)
        )

    # 4. Build final table
    final_table = pa.Table.from_arrays(
        [master_calendar["date"], total_weighted_return],
        names=["date", "total_return"]
    )

    return final_table


# ─────────────────────────────────────────────
# PORTFOLIO COMPARISON
# ─────────────────────────────────────────────
def get_portfolio_for_comparison(
        portfolio: Dict,
        start_date_portfolios: Optional[str] = None, end_date: Optional[str] = None
) -> Optional[Dict]:
    """
    Prepares a single portfolio for comparison.

    Args:
        portfolio: Dict with keys 'name', 'funds' (list of {'isin', 'weight'}),
                   and 'portfolio_start_date'.
        start_date_portfolios: Override start date (None = use portfolio's own start date).
        end_date: End date filter.

    Returns:
        Dict with keys {'name', 'portfolio_total_return': pa.Table, 'cagr': float},
        or None if weights don't sum to 100% or no data is available.
    """
    # Validate that weights sum to 100%
    total_weight = sum(f['weight'] for f in portfolio['funds'])
    if abs(total_weight - 100.0) > 0.01:
        return None

    # Determine the effective start date
    if start_date_portfolios:
        start_date = start_date_portfolios
    else:
        start_date = portfolio['portfolio_start_date']

    # Load and normalize each fund in the portfolio
    funds_info = []
    for fund in portfolio['funds']:
        data = load_normalized_data_fund(fund['isin'], start_date, end_date)
        if data:
            funds_info.append({
                'weight': fund['weight'] / 100.0,
                'fund_data': data
            })

    if not funds_info:
        return None

    portfolio_weighted_total_return = weight_portfolio_funds(funds_info)

    # Calculate CAGR
    dates_parsed = pc.cast(portfolio_weighted_total_return["date"], pa.date32())
    min_date = pc.min(dates_parsed)
    max_date = pc.max(dates_parsed)
    v_inicial = portfolio_weighted_total_return["total_return"][0].as_py()
    v_final = portfolio_weighted_total_return["total_return"][-1].as_py()
    n_years = pc.days_between(min_date, max_date).as_py() / 365.25
    if n_years >= 1:
        cagr_performance = (v_final / v_inicial) ** (1 / n_years) - 1
    else:
        cagr_performance = (v_final / v_inicial) - 1

    return {
        'name': portfolio['name'],
        'portfolio_total_return': portfolio_weighted_total_return,
        'cagr': cagr_performance
    }


def get_portfolios_for_comparison(
        portfolios: List[Dict],
        start_date_portfolios: Optional[str] = None, end_date: Optional[str] = None
) -> List[Dict[str, pa.Table]]:
    """
    Prepares multiple portfolios for comparison.

    Args:
        portfolios: List of portfolio dicts (see get_portfolio_for_comparison).
        start_date_portfolios: Override start date for all portfolios (None = per-portfolio).
        end_date: End date filter.

    Returns:
        List of dicts with keys {'name', 'portfolio_total_return': pa.Table, 'cagr': float}.
    """
    result = []
    for portfolio in portfolios:
        portfolio_info = get_portfolio_for_comparison(portfolio, start_date_portfolios, end_date)
        if portfolio_info:
            result.append(portfolio_info)

    return result