
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import sqlite3

'''
schema of fund data, [isin].parquet -> date,total_return
schema of metadata_funds.db -> funds table (isin PRIMARY KEY, start_date, name, last_updated)
'''

# ─────────────────────────────────────────────
# FUNCIONES SQLITE METADATA
# ─────────────────────────────────────────────

def init_metadata_db(db_path='data/metadata_funds.db'):
    """Inicializa la base de datos SQLite con la tabla de fondos"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS funds (
                                                      isin TEXT PRIMARY KEY,
                                                      start_date TEXT NOT NULL,
                                                      name TEXT NOT NULL,
                                                      last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                 )
                 ''')
    conn.commit()
    conn.close()


def add_funds_to_metadata(isins: list, start_dates: list, names: list, db_path='data/metadata_funds.db'):
    """Añade o actualiza fondos en la metadata (upsert)"""
    conn = sqlite3.connect(db_path)
    data = list(zip(isins, start_dates, names))
    conn.executemany('''
                     INSERT INTO funds (isin, start_date, name)
                     VALUES (?, ?, ?)
                         ON CONFLICT(isin) DO UPDATE SET
                         name = excluded.name,
                                                  last_updated = CURRENT_TIMESTAMP
                     ''', data)
    conn.commit()
    conn.close()


def get_fund_last_date(isin_fund: str, data_path='data') -> str | None:
    """Obtiene la última fecha disponible de un fondo en su parquet"""
    filepath = Path(data_path) / f'{isin_fund}.parquet'
    if not filepath.exists():
        return None

    try:
        table = pq.read_table(filepath, columns=['date'])
        # Obtener la última fecha (asumiendo que están ordenadas)
        last_date = table['date'][-1].as_py()
        return last_date
    except:
        return None


# ─────────────────────────────────────────────
# FUNCIONES PARQUET COTIZACIONES
# ─────────────────────────────────────────────

def save_fund_data_to_parquet(fund_data: list[dict], isin: str, path='data'):
    """
    Guarda o actualiza datos de cotización en parquet.
    Si el archivo existe, solo añade registros nuevos (append inteligente).
    """
    filepath = Path(path) / f'{isin}.parquet'
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Preparar nueva tabla
    new_table = pa.Table.from_pylist(fund_data)
    new_table = new_table.select(['date', 'totalReturn'])
    new_table = new_table.rename_columns(['date', 'total_return'])

    # Si el archivo existe, hacer append inteligente
    if filepath.exists():
        existing_table = pq.read_table(filepath)

        # Obtener la última fecha existente
        last_existing_date = existing_table['date'][-1].as_py()

        # Filtrar solo registros nuevos (fecha > última fecha existente)
        mask = pc.greater(new_table['date'], last_existing_date)
        new_records = new_table.filter(mask)

        if len(new_records) > 0:
            # Concatenar solo si hay registros nuevos
            combined_table = pa.concat_tables([existing_table, new_records])
            print(f"  + Añadidos {len(new_records)} registros nuevos a {isin}")
        else:
            print(f"  ⊘ {isin} ya está actualizado (sin registros nuevos)")
            combined_table = existing_table
    else:
        combined_table = new_table
        print(f"  ✓ Creado archivo nuevo para {isin} con {len(new_table)} registros")

    # Guardar
    pq.write_table(
        combined_table,
        filepath,
        compression='zstd',
        compression_level=9
    )
