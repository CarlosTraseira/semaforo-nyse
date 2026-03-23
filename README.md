# 🚦 Semáforo Fundamental – Alpha Vantage

Aplicación simple en **Streamlit** para evaluar la calidad financiera de empresas
usando **datos fundamentales reales** de Alpha Vantage (free tier).

## ✅ Qué hace
- Consulta ratios fundamentales reales
- Evalúa calidad con semáforo (🟢🟡🔴)
- Usa **1 sola llamada por ticker**
- Ideal para cursos, demos y MVPs

## 📊 Indicadores usados
- Trailing P/E
- ROE (TTM)
- Profit Margin
- Debt / Equity

## 🔑 Requisitos
- Python 3.9+
- API key gratuita de Alpha Vantage

## 🔐 Configurar API Key

Crear `.streamlit/secrets.toml`:

```toml
ALPHA_VANTAGE_API_KEY = "TU_API_KEY"
``
