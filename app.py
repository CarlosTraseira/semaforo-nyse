import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- LÍNEA DE VERIFICACIÓN ---
st.info("Versión del sistema: 2.0 (Alpha Vantage Mode)")

try:
    # Intento de lectura de Secrets
    gemini_key = st.secrets["GEMINI_API_KEY"]
    av_key = st.secrets["AV_API_KEY"]

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    ticker = st.text_input("Ticker:", "BP").upper().strip()

    if st.button("Analizar"):
        with st.spinner('Obteniendo datos REALES...'):
            # CONSULTA DIRECTA A ALPHA VANTAGE
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
            data = requests.get(url).json()

            if "Symbol" not in data:
                st.error("Error: No se reciben datos de Alpha Vantage. Revisa tu API Key en Secrets.")
            else:
                # Conversión segura
                pe = float(data.get('TrailingPE', 0) if data.get('TrailingPE') != 'None' else 0)
                roe = float(data.get('ReturnOnEquityTTM', 0) if data.get('ReturnOnEquityTTM') != 'None' else 0) * 100
                margin = float(data.get('ProfitMargin', 0) if data.get('ProfitMargin') != 'None' else 0) * 100

                st.subheader(f"Métricas Auditadas: {ticker}")
                st.table(pd.DataFrame({
                    "Métrica": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                }))

                # IA
                response = model.generate_content(f"Analiza {ticker}: PE {pe}, ROE {roe}%, Margen {margin}%.")
                st.write(response.text)
except Exception as e:
    st.error(f"Error crítico: {e}")
