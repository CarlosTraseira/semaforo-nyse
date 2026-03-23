import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA DE SECRETOS ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"].strip()
    fmp_key = st.secrets["FMP_API_KEY"].strip()
    
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en Secrets: {e}")
    st.stop()

st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Ticker de la empresa:", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos gratuitos para {ticker}...'):
        # USAMOS RUTAS DISPONIBLES EN EL PLAN GRATUITO
        # 1. Quote: Para el P/E Ratio (Gratis)
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        # 2. Ratios: Usamos la versión de lista (Gratis) en lugar de TTM
        url_ratios = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?limit=1&apikey={fmp_key}"
        
        res_quote = requests.get(url_quote).json()
        res_ratios = requests.get(url_ratios).json()

        # VERIFICACIÓN DE RESPUESTA
        if not res_quote or not res_ratios:
            st.error("❌ Error de API: No se recibieron datos.")
            st.info("Esto pasa si la Key de FMP es incorrecta o si superaste el límite diario (250 peticiones).")
            # Mostramos la respuesta para diagnosticar
            st.write("Respuesta de FMP:", res_quote) 
        else:
            try:
                q = res_quote[0]
                r = res_ratios[0]

                # Extraemos datos con nombres de campos del plan gratuito
                pe = q.get('pe', 0)
                roe = (r.get('returnOnEquity', 0) or 0) * 100
                margin = (r.get('netProfitMargin', 0) or 0) * 100

                # --- TABLA ---
                st.subheader(f"Análisis de {ticker}")
                df = pd.DataFrame({
                    "Métrica": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # --- IA ---
                prompt = f"Analiza {ticker}: PE {pe:.2f}, ROE {roe:.2f}%, Margen {margin:.2f}%. Da un veredicto de inversión muy corto."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)

            except Exception as e:
                st.error(f"Error al procesar los datos: {e}")
