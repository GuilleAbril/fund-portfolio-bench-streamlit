from datetime import datetime, timedelta
from mstarpy import Funds

from utils_download import init_metadata_db, get_fund_last_date, save_fund_data_to_parquet, \
    add_funds_to_metadata

'''
schema of fund data, [isin].parquet -> date,total_return
schema of metadata_funds.db -> funds table (isin PRIMARY KEY, start_date, name, last_updated)
'''

# ─────────────────────────────────────────────
# SCRIPT PRINCIPAL
# ─────────────────────────────────────────────

# Inicializar base de datos SQLite
init_metadata_db()

# ISINs a descargar/actualizar
with open('data/isins_to_download.txt', 'r') as f:
    isins = [line.strip() for line in f if line.strip()]

# Calcular fechas
today = datetime.now()
days_since_friday = (today.weekday() - 4) % 7
if days_since_friday == 0:
    days_since_friday = 7
last_friday = (today - timedelta(days=days_since_friday)).replace(hour=0, minute=0, second=0, microsecond=0)

# Fecha por defecto para fondos nuevos
default_start_date = datetime.strptime("1990-01-01", "%Y-%m-%d")

# Listas para acumular metadata
isins_list = []
fund_start_date_list = []
fund_names = []

print(f"\n{'='*60}")
print(f"Descargando datos hasta: {last_friday.strftime('%Y-%m-%d')}")
print(f"Para los isins: {isins}")
print(f"{'='*60}\n")

for idx, isin in enumerate(isins, 1):
    print(f"[{idx}/{len(isins)}] Procesando {isin}...")

    try:
        # Obtener última fecha disponible del fondo (si existe)
        last_date = get_fund_last_date(isin)

        # Determinar fecha de inicio para la descarga
        if last_date:
            # Si ya existe, descargar solo desde la última fecha
            start_date = datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)
            print(f"  → Actualizando desde {start_date.strftime('%Y-%m-%d')}")

            # NUEVO: Verificar si ya está actualizado hasta last_friday
            if start_date > last_friday:
                print(f"  ⊘ {isin} ya está actualizado hasta {last_date} (posterior a {last_friday.strftime('%Y-%m-%d')})")
                continue

        else:
            # Fondo nuevo, descargar histórico completo
            start_date = default_start_date
            print(f"  → Descargando histórico completo desde {start_date.strftime('%Y-%m-%d')}")

        # Descargar datos
        f = Funds(term=isin)
        data = f.nav(start_date=start_date, end_date=last_friday)

        if not data or len(data) == 0:
            print(f"  ⊘ No hay datos nuevos para {isin}")
            continue

        print(f"  ✓ {f.name}")
        print(f"    Registros descargados: {len(data)}")

        # Guardar cotizaciones en parquet
        save_fund_data_to_parquet(data, isin)

        # Acumular metadata (solo para fondos nuevos o con datos actualizados)
        isins_list.append(isin)
        fund_start_date_list.append(data[0]['date'])  # Primera fecha del histórico
        fund_names.append(f.name)

    except ConnectionError as e:
        print(f"  ✗ Error de conexión: {e}")
        print(f"  ⚠ Deteniendo descarga...")
        break

    except Exception as e:
        print(f"  ✗ Error inesperado: {e}")
        continue

# Actualizar metadata en SQLite
if isins_list:
    print(f"\n{'='*60}")
    print(f"📊 Actualizando metadata en SQLite...")
    add_funds_to_metadata(isins_list, fund_start_date_list, fund_names)
    print(f"✓ Metadata actualizado ({len(isins_list)} fondos)")
    print(f"{'='*60}\n")
else:
    print("\n⚠ No se descargó ningún fondo nuevo")