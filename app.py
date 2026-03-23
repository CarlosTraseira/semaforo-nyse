import streamlit as st
import requests
import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="🚦 Semáforo Fundamental – Alpha Vantage",
    page_icon="🚦",
    layout="centered"
)

ALPHA_KEY = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def num(x):
    try:
        return float(x)
    except:
        return None


def semaforo(valor, bueno, regular):
    """
    Devuelve color según umbrales
    """
    if valor is None:
        return "⚪ N/D"
    if valor >= bueno:
        return "🟢 Bueno"
    if valor >= regular:
        return "🟡 Regular"
    return "🔴 Malo"


# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("🚦 Semáforo Fundamental (Alpha Vantage)")
st.caption("Datos fundamentales reales – Free Tier")

ticker = st.text_input(
    "Ticker (NYSE / NASDAQ)",
    value="AAPL",
    help="Ejemplos: AAPL, MSFT, KO, JPM"
).upper().strip()

if not ALPHA_KEY:
    st.warning("⚠️ Falta configurar ALPHA_VANTAGE_API_KEY en secrets.")
    st.stop()

# --------------------------------------------------
# FETCH DATA
# --------------------------------------------------
if st.button("Analizar empresa"):
    with st.spinner("Consultando Alpha Vantage..."):

        url = (
            "https://www.alphavantage.co/query"
            f"?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_KEY}"
        )

        r = requests.get(url, timeout=15)
        data = r.json()

        if not data or "Symbol" not in data:
            st.error("Ticker inválido o límite diario alcanzado.")
            st.stop()

        # --------------------------------------------------
        # EXTRACT
        # --------------------------------------------------
        company = data.get("Name")
        sector = data.get("Sector")
        industry = data.get("Industry")

        pe = num(data.get("TrailingPE"))
        roe = num(data.get("ReturnOnEquityTTM"))
        margin = num(data.get("ProfitMargin"))
        debt = num(data.get("DebtToEquityRatio"))

        # --------------------------------------------------
        # TABLE
        # --------------------------------------------------
        df = pd.DataFrame({
            "Indicador": [
                "Trailing P/E",
                "ROE (TTM)",
                "Profit Margin",
                "Debt / Equity"
            ],
            "Valor": [
                f"{pe:.2f}" if pe else "N/D",
                f"{roe*100:.2f}%" if roe else "N/D",
                f"{margin*100:.2f}%" if margin else "N/D",
                f"{debt:.2f}" if debt else "N/D"
            ],
            "Evaluación": [
                semaforo(30 - pe if pe else None, 0, -10),
                semaforo(roe, 0.15, 0.08),
                semaforo(margin, 0.10, 0.05),
                semaforo(1 / debt if debt else None, 1, 0.5)
            ]
        })

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------
        st.subheader(f"{company} ({ticker})")
        st.caption(f"{sector} · {industry}")

        st.table(df)

        st.info(
            "Fuente: Alpha Vantage – function=OVERVIEW\n\n"
            "Nota: el free tier permite 25 consultas por día."
        )
