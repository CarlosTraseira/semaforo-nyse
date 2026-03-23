import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- BLOQUE DE SEGURIDAD PARA LLAVES ---
gemini_key = None
fmp_key = None

if "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"].strip()
if "FMP_API_KEY" in st.secrets:
    fmp_key = st.secrets["FMP_API_KEY"].strip()

# Verificación visual para ti (luego lo borraremos)
if not gemini_key or not fmp_key:
    st.error("🚨 Faltan llaves en Secrets.")
    st.info("Asegúrate de que en el cuadro de Secrets diga exactamente: GEMINI_API_KEY = 'tu_llave'")
    st.stop()

# 2. Configuración IA
try:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configurando Gemini: {e}")

# 3. Interfaz
st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Ticker de la empresa:", "BP").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos financieros...'):
        try:
            # Consultas a FMP
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={fmp_key}"
            url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
            
            res_ratios = requests.get(url_ratios).json()
            res_quote = requests.get(url_quote).json()

            if not res_ratios or not res_quote:
                st.warning("No se recibieron datos de FMP. Revisa tu llave de FMP.")
            else:
                q = res_quote[0]
                r = res_ratios[0]

                pe = q.get('pe') or 0
                roe = (r.get('returnOnEquityTTM') or 0) * 100
                margin = (r.get('netProfitMarginTTM') or 0) * 100

                # Tabla
                st.subheader(f"Auditoría: {ticker}")
                df = pd.DataFrame({
                    "Métrica": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # IA
                prompt = f"Analiza {ticker}: PE {pe:.2f}, ROE {roe:.2f}%, Margen {margin:.2f}%. Veredicto semáforo corto."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)

        except Exception as e:
            st.error(f"Hubo un problema al procesar los datos: {e}")
