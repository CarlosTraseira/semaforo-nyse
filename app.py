import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

try:
    # 1. Carga de llaves desde Secrets
    gemini_key = st.secrets["GEMINI_API_KEY"]
    fmp_key = st.secrets["FMP_API_KEY"]

    # 2. Configuración de IA
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo NYSE (Modo FMP 250)")
    ticker = st.text_input("Ticker de la empresa:", "BP").upper().strip()

    if st.button("Analizar"):
        with st.spinner(f'Consultando datos para {ticker}...'):
            # Consulta 1: Ratios TTM (ROE y Margen)
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={fmp_key}"
            res_ratios = requests.get(url_ratios).json()

            # Consulta 2: Quote (P/E Ratio)
            url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
            res_quote = requests.get(url_quote).json()

            # VERIFICACIÓN: ¿FMP devolvió datos?
            if not res_ratios or not res_quote:
                st.warning(f"No se encontraron datos completos para {ticker}. Intenta con otro (ej: AAPL, MSFT).")
            else:
                # Extraemos con seguridad los datos de la primera posición de la lista [0]
                q = res_quote[0]
                r = res_ratios[0]

                pe = q.get('pe', 0)
                roe = (r.get('returnOnEquityTTM', 0) or 0) * 100
                margin = (r.get('netProfitMarginTTM', 0) or 0) * 100

                # Mostrar Tabla
                st.subheader(f"Auditoría Real: {ticker}")
                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # Veredicto IA
                prompt = f"Analiza {ticker}: PE {pe:.2f}, ROE {roe:.2f}%, Margen {margin:.2f}%. Da un veredicto de semáforo (Verde, Amarillo o Rojo) y justifica en 2 líneas."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)

except Exception as e:
    st.error(f"Error de conexión o configuración: {e}")
    st.info("Asegúrate de que tus Secrets se llamen GEMINI_API_KEY y FMP_API_KEY.")
