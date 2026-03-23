import streamlit as st
import requests
import pandas as pd

# ==================================================
# CONFIG GENERAL
# ==================================================
st.set_page_config(
    page_title="Semáforo Fundamental – NYSE",
    page_icon="🚦",
    layout="centered"
)

USE_MOCK_DATA = True
ALPHA_KEY = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")

# ==================================================
# HELPERS
# ==================================================
def num(x):
    try:
        return float(x)
    except:
        return None


def semaforo(color):
    return {
        "green": "🟢 Bueno",
        "yellow": "🟡 Regular",
        "red": "🔴 Malo",
        "grey": "⚪ N/D"
    }.get(color, "⚪ N/D")


def evaluar_pe(x):
    if x is None: return "grey"
    if x < 30: return "green"
    if x < 45: return "yellow"
    return "red"


def evaluar_roe(x):
    if x is None: return "grey"
    if x >= 0.15: return "green"
    if x >= 0.08: return "yellow"
    return "red"


def evaluar_margin(x):
    if x is None: return "grey"
    if x >= 0.10: return "green"
    if x >= 0.05: return "yellow"
    return "red"


def evaluar_debt(x):
    if x is None: return "grey"
    if x < 1: return "green"
    if x < 2: return "yellow"
    return "red"


def evaluar_fcf(x):
    if x is None: return "grey"
    return "green" if x > 0 else "red"


# ==================================================
# UI
# ==================================================
st.title("🚦 Semáforo Fundamental – NYSE")
st.caption("Indicadores fundamentales con verificación directa en la fuente")

ticker = st.text_input(
    "Ticker (ej: AAPL, MSFT, KO)",
    value="AAPL"
).upper().strip()

# ==================================================
# DATA
# ==================================================
if st.button("Analizar empresa"):
    with st.spinner("Procesando datos..."):

        if USE_MOCK_DATA:
            data = {
                "Name": "Apple Inc.",
                "Sector": "Technology",
                "Industry": "Consumer Electronics",
                "TrailingPE": "28.5",
                "ReturnOnEquityTTM": "0.55",
                "ProfitMargin": "0.25",
                "DebtToEquityRatio": "1.7",
                "FreeCashFlowTTM": "95000000000"
            }
        else:
            if not ALPHA_KEY:
                st.error("Falta configurar ALPHA_VANTAGE_API_KEY en secrets.")
                st.stop()

            url = (
                "https://www.alphavantage.co/query"
                f"?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_KEY}"
            )
            data = requests.get(url, timeout=15).json()

        pe = num(data.get("TrailingPE"))
        roe = num(data.get("ReturnOnEquityTTM"))
        margin = num(data.get("ProfitMargin"))
        debt = num(data.get("DebtToEquityRatio"))
        fcf = num(data.get("FreeCashFlowTTM"))

        df = pd.DataFrame({
            "Indicador": [
                "Trailing P/E",
                "ROE (TTM)",
                "Profit Margin",
                "Debt / Equity",
                "Free Cash Flow (TTM)"
            ],
            "Valor": [
                f"{pe:.2f}" if pe else "N/D",
                f"{roe*100:.2f}%" if roe else "N/D",
                f"{margin*100:.2f}%" if margin else "N/D",
                f"{debt:.2f}" if debt else "N/D",
                f"${fcf/1e9:.1f} B" if fcf else "N/D"
            ],
            "Evaluación": [
                semaforo(evaluar_pe(pe)),
                semaforo(evaluar_roe(roe)),
                semaforo(evaluar_margin(margin)),
                semaforo(evaluar_debt(debt)),
                semaforo(evaluar_fcf(fcf))
            ]
        })

        st.subheader(f"{data.get('Name')} ({ticker})")
        st.table(df)

        # ==================================================
        # VERIFICACIÓN
        # ==================================================
        st.markdown("### 🔎 Cómo verificar cada indicador")

        st.markdown(f"""
**Trailing P/E, ROE, Profit Margin, Debt/Equity**  
👉 Yahoo Finance – *Statistics*  
https://finance.yahoo.com/quote/{ticker}/key-statistics  
📌 Ver secciones *Valuation Measures* y *Financial Highlights*

**Free Cash Flow (TTM)**  
👉 Yahoo Finance – *Cash Flow*  
https://finance.yahoo.com/quote/{ticker}/cash-flow  
📌 Ver tabla *Cash Flow Statement* → fila *Free Cash Flow*

**Fuente primaria (datos crudos)**  
👉 Alpha Vantage – Company Overview  
https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}
""")

        if USE_MOCK_DATA:
            st.info("🧪 Modo desarrollo (datos simulados).")
