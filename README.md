# 🚦 Semáforo NYSE

App en Streamlit para evaluar rápidamente 6 indicadores fundamentales de un ticker (enfocado en NYSE), usando solo servicios gratuitos.

## Indicadores incluidos
- Trailing P/E
- ROE
- Profit Margin
- Debt to Equity
- Free Cash Flow
- Dividend Yield (%)

## Qué hace la app
- Consulta datos reales desde Alpha Vantage (`OVERVIEW` + `CASH_FLOW`).
- Muestra una tabla con columnas:
  - **Indicador**
  - **Valor**
  - **Referencia** (estándares generales usados por analistas)
  - **Estado**
  - **Explicación**
- Incluye sección de **verificación** con links directos al endpoint usado.
- Agrega acceso a **SEC EDGAR** para validar en fuente primaria (10-K / 10-Q).

## Requisitos
- Python 3.9+
- API key gratuita de Alpha Vantage

## Instalación
```bash
pip install -r requirements.txt
```

## Configurar API key
Puedes ingresarla en la barra lateral de la app o guardarla en `.streamlit/secrets.toml`:

```toml
ALPHA_VANTAGE_API_KEY = "TU_API_KEY"
```

## Ejecutar
```bash
streamlit run app.py
```

## Nota importante
Los umbrales de referencia son orientativos y pueden variar por sector, tamaño de empresa y ciclo económico.
