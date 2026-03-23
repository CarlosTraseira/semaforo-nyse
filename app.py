import streamlit as st
import requests
import pandas as pd

# ==================================================
# CONFIG GENERAL
# ==================================================
st.set_page_config(
    page_title="🚦 Semáforo Fundamental – NYSE",
    page_icon="🚦",
    layout="centered"
)

# 👉 CAMBIÁ ESTO A False CUANDO QUIERAS USAR ALPHA REAL
USE_MOCK_DATA = True

# API KEY (solo se usa si USE_MOCK_DATA = False)
ALPHA_KEY = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")

# ==================================================
# HELPERS
# ==================================================
def num(x):
    try:
        return float(x)
    except:
        return None


def semaforo_texto(color):
    if color == "green":
        return "🟢 Bueno"
    if color == "yellow":
        return "🟡 Regular"
    if color == "red":
        return "🔴 Malo"
    return "⚪ N/D"


def evaluar_pe(pe):
    if pe is None:
        return "grey"
    if pe < 30:
        return "green"
    if pe < 45:
        return "yellow"
    return "red"


def evaluar_roe(roe):
    if roe is None:
        return "grey"
    if roe >= 0.15:
        return "green"
    if roe >= 0.08:
        return "yellow"
    return "red"


def evaluar_margin(m):
    if m is None:
        return "grey"
    if m >= 0.10:
        return "green"
    if m >= 0.05:
        return "yellow"
    return "red"


def evaluar_debt(d):
    if d is None:
        return "grey"
    if d < 1:
        return "green"
    if d < 2:
        return "yellow"
    return "red"


# ==================================================
# UI
# ==================================================
st.title("🚦 Semáforo Fundamental – NYSE")
st.caption("Evaluación rápida de calidad financiera")

ticker = st.text_input(
    "Ticker (ej: AAPL, MSFT, KO)",
    value="AAPL"
).upper().strip()

# ==================================================
# DATA
# ==================================================
if st.button("Analizar empresa"):
    with st.spinner("Procesando datos..."):

        # ------------------------------
        # MODO MOCK (DESARROLLO)
        # ------------------------------
        if USE_MOCK_DATA:
            data = {
                "Name": "Apple Inc.",
                "Sector": "Technology",
                "Industry": "Consumer Electronics",
                "TrailingPE": "28.5",
                "ReturnOnEquityTTM": "0.55",
                "ProfitMargin": "0.25",
                "DebtToEquityRatio": "1.7"
            }

        # ------------------------------
        # MODO REAL (ALPHA VANTAGE)
        # ------------------------------
        else:
            if not ALPHA_KEY:
                st.error("Falta configurar ALPHA_VANTAGE_API_KEY en secrets.")
                st.stop()

            url = (
                "https://www.alphavantage.co/query"
                f"?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_KEY}"
            )

            r = requests.get(url, timeout=15)
            data = r.json()

            if not data or "Symbol" not in data:
                st.error("Ticker inválido o límite diario alcanzado.")
                st.stop()

        # ==================================================
        # EXTRACCIÓN
        # ==================================================
        company = data.get("Name")
        sector = data.get("Sector")
        industry = data.get("Industry")

        pe = num(data.get("TrailingPE"))
        roe = num(data.get("ReturnOnEquityTTM"))
        margin = num(data.get("ProfitMargin"))
        debt = num(data.get("DebtToEquityRatio"))

        # ==================================================
        # TABLA
        # ==================================================
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
                semaforo_texto(evaluar_pe(pe)),
                semaforo_texto(evaluar_roe(roe)),
                semaforo_texto(evaluar_margin(margin)),
                semaforo_texto(evaluar_debt(debt))
            ]
        })

        # ==================================================
        # OUTPUT
        # ==================================================
        st.subheader(f"{company} ({ticker})")
        st.caption(f"{sector} · {industry}")

        st.table(df)

        if USE_MOCK_DATA:
            st.info(
                "🧪 Modo desarrollo activo (datos simulados).\n\n"
                "Cambiar USE_MOCK_DATA = False para usar Alpha Vantage real."
            )
        else:
            st.info(
                "Fuente de datos: Alpha Vantage (function=OVERVIEW)\n\n"
                "Free tier: 25 requests por día."
            )
