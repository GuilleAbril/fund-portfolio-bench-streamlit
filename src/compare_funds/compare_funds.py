"""
Módulo para cargar y procesar datos de fondos para comparación.
Gestiona la carga desde Parquet, alineamiento temporal y normalización.
"""

import sqlite3
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa
from pathlib import Path
from typing import List, Dict, Optional


# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Sube desde src/compare_funds/
DATA_DIR = PROJECT_ROOT / "src" / "download_data" / "data"
METADATA_DB = DATA_DIR / "metadata_funds.db"

# ─────────────────────────────────────────────
# FUNCIONES DE METADATA (SQLite)
# ─────────────────────────────────────────────

def get_funds_metadata(isins: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Obtiene metadata de fondos desde SQLite.
    
    Args:
        isins: Lista de ISINs a consultar
        
    Returns:
        Dict con {isin: {'start_date': '...', 'name': '...'}}
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
    """Comprueba si existe el archivo parquet del fondo"""
    return (DATA_DIR / f"{isin}.parquet").exists()


# ─────────────────────────────────────────────
# CARGA DE DATOS (Parquet)
# ─────────────────────────────────────────────

def load_normalized_data_fund(isin: str, start_date: Optional[str] = None) -> Optional[pa.Table]:
    """
    Carga datos RAW de un fondo (sin normalizar).
    
    Args:
        isin: ISIN del fondo
        start_date: Fecha desde la que filtrar (opcional)
        
    Returns:
        fund_data: pa.Table[date, total_return]
    """
    filepath = DATA_DIR / f"{isin}.parquet"
    if not filepath.exists():
        return None

    try:
        # Leer parquet
        fund_data = pq.read_table(filepath)

        # Filtrar por fecha si se proporciona
        if start_date:
            mask = pc.greater_equal(fund_data['date'], start_date)
            fund_data = fund_data.filter(mask)

        base_value = fund_data["total_return"][0]
        division = pc.divide(fund_data["total_return"], base_value)
        normalized_column = pc.multiply(division, pa.scalar(100.0))
        idx = fund_data.schema.get_field_index("total_return")
        fund_data = fund_data.set_column(idx, "total_return", normalized_column)

        if len(fund_data) == 0:
            return None

        return fund_data

    except Exception as e:
        print(f"Error cargando {isin}: {e}")
        return None


# ─────────────────────────────────────────────
# NORMALIZACIÓN Y ALINEAMIENTO
# ─────────────────────────────────────────────

def normalize_to_base_100(values: List[float]) -> List[float]:
    """Normaliza lista de valores a base 100 desde el primer elemento"""
    if not values or values[0] == 0:
        return values
    first = values[0]
    return [(v / first) * 100.0 for v in values]


# ─────────────────────────────────────────────
# COMPARACIÓN DE FONDOS
# ─────────────────────────────────────────────

def get_funds_for_comparison(
        isins: List[str],
        start_date: Optional[str] = None
) -> List[Dict]: #[str, str, pa.Table]
    """
    start_date: Optional[str] = None,
    use_common_date: bool = True
    Prepara fondos para comparación.

    Args:
        isins: Lista de ISINs
        start_date: Fecha desde la que cargar datos (None = histórico completo)
        
    Returns:
        List[Dict]
        {'isin': str, 'name': str, 'fund_data': pa.Table[date, total_return]}
    """
    # Cargar datos raw
    funds_info = []
    for isin in isins:
        # Obtener nombre del metadata
        metadata = get_funds_metadata([isin])
        name = metadata.get(isin, {}).get('name', isin)
        data = load_normalized_data_fund(isin, start_date)
        dates_parsed = pc.cast(data["date"], pa.date32())
        min_date = pc.min(dates_parsed)
        max_date = pc.max(dates_parsed)
        v_inicial = data["total_return"][0].as_py()
        v_final = data["total_return"][-1].as_py()
        n_years = pc.days_between(min_date, max_date).as_py() / 365.25
        cagr = (v_final / v_inicial) ** (1 / n_years) - 1
        if data:
            funds_info.append(
                {'isin': isin, 'name': name, 'fund_data': data, 'cagr': cagr}
            )

    if not funds_info:
        return []

    return funds_info

# ─────────────────────────────────────────────
# COMPARACIÓN DE CARTERAS
# ─────────────────────────────────────────────
def weight_portfolio_funds(funds_data_weights: list[dict]):
    """
    :param funds_data_weights:
    :return: pa.Table["date", "total_return"]
    """

    # funds_data_weights -> List of Dict con {isin: str, fund_data: pa.Table['dates', 'values'], weights: double}
    # 1. Create a Master Calendar: Combine all unique dates from all tables
    all_dates_combined = pa.concat_tables([f_w.get("fund_data").select(["date"]) for f_w in funds_data_weights])
    master_calendar = pa.Table.from_arrays(
        [pc.unique(all_dates_combined["date"])],
        names=["date"]
    ).sort_by([("date", "ascending")])

    weighted_arrays = []

    # 2. Process each fund
    for item in funds_data_weights:
        table = item['fund_data']
        weight = item['weight']

        # Align the fund data to the master calendar
        # Dates without values will result in 'null'
        aligned_table = master_calendar.join(table, keys="date", join_type="left outer")
        aligned_table = aligned_table.sort_by([("date", "ascending")])

        # Fill missing values by carrying forward the last known 'total_return'
        filled_values = pc.fill_null_forward(aligned_table["total_return"])

        # Multiply the filled array by the fund's specific weight
        weighted_array = pc.multiply(filled_values, weight)
        weighted_arrays.append(weighted_array)

    # 3. Aggregate results
    # Initialize the accumulator with the first weighted array
    total_weighted_return = weighted_arrays[0]

    # TODO mirar que hace aqui que los mete mal
    for i in range(1, len(weighted_arrays)):
        # We use fill_null(0) during addition to handle funds with different start dates
        # ensuring they don't turn the whole sum into 'null'
        total_weighted_return = pc.add(
            pc.fill_null(total_weighted_return, 0),
            pc.fill_null(weighted_arrays[i], 0)
        )

    # 4. Final Table Construction
    final_table = pa.Table.from_arrays(
        [master_calendar["date"], total_weighted_return],
        names=["date", "total_return"]
    )

    return final_table


# ─────────────────────────────────────────────
# COMPARACIÓN DE CARTERAS
# ─────────────────────────────────────────────
def get_portfolio_for_comparison(
        portfolio: Dict,
        # portfolio -> {'name': f'Cartera {p_idx + 1}','funds': funds, 'portfolio_start_date': portfolio_start_date,'color': PORTFOLIO_COLORS[p_idx]}
        # funds: list({'isin': isin, 'weight': weight})
        start_date_portfolios: Optional[str] = None
) -> Optional[Dict]:
    """
    Prepara una cartera para comparación.

    Args:
        portfolio: Dict con 'name', 'funds': [{'isin': '...', 'weight': 50.0}, ...]
        start_date_portfolios: Fecha desde la que cargar datos
    Returns:
        'name': portfolio['name'],
        'portfolio_total_return': pa.Table["date", "total_return"]
    """
    # Validar que pesos sumen 100%
    total_weight = sum(f['weight'] for f in portfolio['funds'])
    if abs(total_weight - 100.0) > 0.01:
        return None

    # fecha a partir de la cual generar los datos del portfolio
    if start_date_portfolios:
        start_date = start_date_portfolios
    else:
        start_date = portfolio['portfolio_start_date']

    # Cargar fondos de la cartera
    funds_info = []
    for fund in portfolio['funds']:
        data = load_normalized_data_fund(fund['isin'], start_date)
        if data:
            funds_info.append({
                'weight': fund['weight'] / 100.0,  # Convertir a decimal
                'fund_data': data
            })

    if not funds_info:
        return None

    portfolio_weighted_total_return = weight_portfolio_funds(funds_info)

    dates_parsed = pc.cast(portfolio_weighted_total_return["date"], pa.date32())
    min_date = pc.min(dates_parsed)
    max_date = pc.max(dates_parsed)
    v_inicial = portfolio_weighted_total_return["total_return"][0].as_py()
    v_final = portfolio_weighted_total_return["total_return"][-1].as_py()
    n_years = pc.days_between(min_date, max_date).as_py() / 365.25
    cagr = (v_final / v_inicial) ** (1 / n_years) - 1

    return {
        'name': portfolio['name'],
        'portfolio_total_return': portfolio_weighted_total_return,
        'cagr': cagr
    }


def get_portfolios_for_comparison(
        portfolios: List[Dict], # lista de dicts con isins, pesos y fecha de comienzo de cada portfolio (el min de su fondo más reciente)
        start_date_portfolios: Optional[str] = None
) -> List[Dict[str, pa.Table]]:
    """
    Prepara múltiples carteras para comparación.

    Args:
        portfolios: Lista de carteras
        start_date_portfolios: Fecha desde la que cargar datos

    Returns:
        List [
        'name': portfolio['name'],
        'portfolio_total_return': pa.Table["date", "total_return"]
        ]
    """
    result = []
    for portfolio in portfolios:
        # portfolio -> {'name': f'Cartera {p_idx + 1}','funds': funds, 'portfolio_start_date': portfolio_start_date,'color': PORTFOLIO_COLORS[p_idx]}
        # funds: list({'isin': isin, 'weight': weight})
        portfolio_info = get_portfolio_for_comparison(portfolio, start_date_portfolios) #{name: str, portfolio_total_return: Table[date, total_return]}
        if portfolio_info:
            result.append(portfolio_info)

    return result