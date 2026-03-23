import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA Y LIMPIEZA DE LLAVES ---
try:
    # Limpiamos posibles espacios o comillas extra que se cuelen en los Secrets
    gemini_key = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    fmp_key = st.secrets["FMP_API_KEY"].strip().replace('"', '').replace("'", "")
    
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en la configuración de llaves: {e}")
    st.stop()

st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Introduce el Ticker (ej: AAPL):", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos para {ticker}...'):
        # Endpoints gratuitos de FMP
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}"
        
        try:
            resp = requests.get(url_quote)
            res_quote = resp.json()
            
            # VERIFICACIÓN DE ERROR DE API (Clave para resolver tu KeyError)
            if isinstance(res_quote, dict) and "Error Message" in res_quote:
                st.error(f"⚠️ Error de la API FMP: {res_quote['Error Message']}")
                st.info("Revisa si tu API Key en Secrets es correcta o si expiró.")
            elif not res_quote:
                st.warning(f"No se encontraron datos para {ticker}. Verifica el símbolo.")
            else:
                # Si llegamos aquí, los datos son válidos
                q = res_quote[0]
                res_profile = requests.get(url_profile).json()
                p = res_profile[0] if res_profile else {}

                # Métricas
                pe = q.get('pe', 0) or 0
                precio = q.get('price', 0)
                beta = p.get('beta', 0) or 0

                st.subheader(f"Análisis de {q.get('name', ticker)}")
                
                # Tabla de datos
                df = pd.DataFrame({
                    "Indicador": ["Precio", "P/E Ratio", "Beta (Riesgo)"],
                    "Valor": [f"${precio}", f"{pe:.2f}x", f"{beta:.2f}"]
                })
                st.table(df)

                # --- IA VERDICT ---
                prompt = f"Analiza {ticker}: PE {pe:.2f}, Beta {beta:.2f}. Da un veredicto de inversión muy corto."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)

        except Exception as e:
            st.error(f"Hubo un problema al procesar los datos: {e}")
