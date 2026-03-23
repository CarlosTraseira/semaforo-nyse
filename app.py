import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA ULTRA SEGURA DE LLAVES ---
# .get() evita que la app truene si la llave no existe en Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip().replace('"', '').replace("'", "")
fmp_key = st.secrets.get("FMP_API_KEY", "").strip().replace('"', '').replace("'", "")

if not gemini_key or not fmp_key:
    st.error("🚨 Error: No se encuentran las llaves en Secrets.")
    st.stop()

# Configuración IA
try:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error configurando Gemini: {e}")

st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Ticker de la empresa:", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando Wall Street para {ticker}...'):
        # Endpoints gratuitos más estables
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}"
        
        try:
            res_quote = requests.get(url_quote).json()
            res_profile = requests.get(url_profile).json()

            # VALIDACIÓN CRÍTICA: Si FMP manda error en lugar de datos
            if isinstance(res_quote, dict) and "Error Message" in res_quote:
                st.error(f"FMP dice: {res_quote['Error Message']}")
                st.info("Revisa que tu FMP_API_KEY sea correcta y no tenga espacios.")
            elif not res_quote or len(res_quote) == 0:
                st.warning(f"No se encontraron datos para {ticker}. Intenta con AAPL.")
            else:
                # Si llegamos aquí, tenemos datos reales
                q = res_quote[0]
                p = res_profile[0] if res_profile else {}

                pe = q.get('pe', 0) or 0
                price = q.get('price', 0)
                beta = p.get('beta', 0) or 0
                name = q.get('name', ticker)

                st.subheader(f"Métricas de {name}")
                
                df = pd.DataFrame({
                    "Indicador": ["Precio Actual", "P/E Ratio", "Beta (Riesgo)"],
                    "Valor": [f"${price}", f"{pe:.2f}x", f"{beta:.2f}"]
                })
                st.table(df)

                # Veredicto IA
                prompt = f"Analiza brevemente {name} ({ticker}): PE de {pe:.2f} y Beta de {beta:.2f}. Da un veredicto de semáforo."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)

        except Exception as e:
            st.error(f"Error inesperado: {e}")
