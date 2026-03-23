import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA SEGURA DE SECRETOS ---
try:
    # Limpieza de llaves para evitar errores de copiado
    gemini_key = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    fmp_key = st.secrets["FMP_API_KEY"].strip().replace('"', '').replace("'", "")
    
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en Secrets: {e}")
    st.stop()

st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Introduce el Ticker (ej: AAPL):", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos actualizados para {ticker}...'):
        # USAMOS EL ENDPOINT v3/quote QUE ES EL MÁS ESTABLE Y MODERNO
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        
        try:
            resp = requests.get(url)
            data = resp.json()
            
            # Verificación de errores de la API
            if isinstance(data, dict) and "Error Message" in data:
                st.error(f"FMP dice: {data['Error Message']}")
            elif not data:
                st.warning("No se encontraron datos. Intenta con un ticker conocido como AAPL.")
            else:
                # Datos extraídos del endpoint moderno
                info = data[0]
                nombre = info.get('name', ticker)
                precio = info.get('price', 0)
                pe = info.get('pe', 0) or 0
                cambio = info.get('changesPercentage', 0)

                st.subheader(f"Análisis de {nombre}")
                
                # Tabla de métricas
                df = pd.DataFrame({
                    "Métrica": ["Precio Actual", "P/E Ratio", "Variación Día (%)"],
                    "Valor": [f"${precio:,.2f}", f"{pe:.2f}x", f"{cambio:.2f}%"]
                })
                st.table(df)

                # --- IA VERDICT ---
                st.subheader("🧠 Veredicto de la IA")
                prompt = f"Analiza {nombre} ({ticker}): Precio ${precio}, PE {pe:.2f}. Di si es una buena opción de inversión hoy."
                
                try:
                    res_ia = model.generate_content(prompt)
                    st.success(res_ia.text)
                except:
                    st.warning("La IA no pudo procesar el veredicto, pero los datos están listos.")

        except Exception as e:
            st.error(f"Error de conexión: {e}")
