# Fund Comparator - Streamlit App

## 📋 Descripción

Aplicación Streamlit para comparar fondos de inversión y carteras de fondos de forma visual e interactiva.

## 🏗️ Estructura del Proyecto

```
streamlit_app/
├── streamlit_app.py              # Archivo principal de la aplicación
├── config.py                      # Constantes y configuración
├── styles.py                      # Estilos CSS personalizados
│
├── components/                    # Componentes de UI reutilizables
│   ├── __init__.py
│   ├── funds_components.py        # Componentes para fondos
│   └── portfolio_components.py    # Componentes para carteras
│
├── tabs/                          # Lógica de las pestañas
│   ├── __init__.py
│   ├── tab_funds.py               # Pestaña de comparación de fondos
│   └── tab_portfolios.py          # Pestaña de comparación de carteras
│
└── utils/                         # Utilidades auxiliares
    ├── __init__.py
    └── database_utils.py          # Funciones de consulta a BD
```

## 📦 Módulos

### `streamlit_app.py`
Archivo principal que:
- Configura la página de Streamlit
- Aplica estilos personalizados
- Renderiza el título y las pestañas principales

### `config.py`
Define constantes globales:
- `MAX_FUNDS`: Número máximo de fondos por comparación
- `MAX_PORTFOLIOS`: Número máximo de carteras
- `PORTFOLIO_COLORS`: Colores para las carteras
- Rutas del proyecto y base de datos

### `styles.py`
Contiene todos los estilos CSS personalizados de la aplicación.

### `components/`
Componentes de interfaz de usuario reutilizables:

#### `funds_components.py`
- `render_funds_inputs()`: Renderiza inputs para ISINs de fondos
- `render_funds_date_selector()`: Selector de fechas para fondos

#### `portfolio_components.py`
- `render_portfolios_inputs()`: Renderiza inputs para carteras
- `render_portfolios_date_selector()`: Selector de fechas para carteras

### `tabs/`
Lógica de negocio de las pestañas:

#### `tab_funds.py`
Gestiona la pestaña de comparación de fondos:
- Control de estado de sesión
- Lógica de comparación y caché
- Renderizado de gráficos

#### `tab_portfolios.py`
Gestiona la pestaña de comparación de carteras:
- Validación de carteras
- Generación de gráficos comparativos

### `utils/`
Funciones auxiliares:

#### `database_utils.py`
- `get_max_common_start_date()`: Obtiene la fecha común más tardía
- `get_min_start_date()`: Obtiene la fecha más antigua

## 🚀 Uso

```bash
streamlit run streamlit_app.py
```

## ✨ Características Principales

### Comparación de Fondos
- Hasta 10 fondos simultáneos
- Validación automática de ISINs
- Tres modos de fecha:
  - Histórico completo
  - Fecha de inicio común
  - Fecha personalizada
- Caché inteligente de gráficos
- Descarga de gráficos en HTML

### Comparación de Carteras
- Hasta 5 carteras simultáneas
- Validación de pesos (deben sumar 100%)
- Nombres personalizables
- Colores distintivos
- Indicadores visuales de estado

## 🎨 Mejoras Implementadas

1. **Separación de responsabilidades**: Cada módulo tiene una función clara
2. **Reutilización de código**: Componentes compartidos entre pestañas
3. **Mejor mantenibilidad**: Código organizado y documentado
4. **Escalabilidad**: Fácil añadir nuevas funcionalidades
5. **Type hints**: Anotaciones de tipo para mejor IDE support
6. **Documentación**: Docstrings en todas las funciones

## 📝 Notas de Refactorización

### Cambios principales:
- ✅ Archivo principal (`streamlit_app.py`) simplificado a ~50 líneas
- ✅ Estilos CSS extraídos a módulo separado
- ✅ Constantes centralizadas en `config.py`
- ✅ Componentes UI organizados por funcionalidad
- ✅ Lógica de pestañas separada y modular
- ✅ Funciones de base de datos en módulo dedicado
- ✅ Eliminación de código duplicado
- ✅ Mejora en nombres de variables y funciones
- ✅ Funciones privadas prefijadas con `_`

## 🔧 Dependencias Externas

- `streamlit`
- `plotly` (via `plot_funds.plot_funds`)
- Módulos propios del proyecto:
  - `compare_funds.compare_funds`
  - `plot_funds.plot_funds`
