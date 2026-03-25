import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA SEGURA DE SECRETOS ---
try:
    # Limpiamos las llaves de posibles espacios o comillas accidentales del formato TOML
    gemini_key = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    fmp_key = st.secrets["FMP_API_KEY"].strip().replace('"', '').replace("'", "")
    
    # Configuración de Google Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en los Secrets: {e}")
    st.stop()

# 2. Interfaz de usuario
st.title("🚦 Semáforo NYSE Pro")
st.markdown("### Análisis con datos de Alpha Vantage y Cerebro Gemini")

ticker = st.text_input("Introduce el Ticker (ej: AAPL, MSFT, TSLA):", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Obteniendo datos de mercado para {ticker}...'):
        # Usamos el endpoint GLOBAL_QUOTE de Alpha Vantage (vía FMP Proxy o directo)
        # Este es el que evita el error de 'Legacy Endpoint'
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        
        try:
            response = requests.get(url)
            data = response.json()

            # Verificación de errores de la API
            if isinstance(data, dict) and "Error Message" in data:
                st.error(f"Error de la API: {data['Error Message']}")
            elif not data:
                st.warning("No se encontraron datos. Intenta con un ticker válido.")
            else:
                # Extraemos los datos del primer resultado
                info = data[0]
                nombre = info.get('name', ticker)
                precio = info.get('price', 0)
                pe = info.get('pe', 0) or 0
                cambio = info.get('changesPercentage', 0)

                # --- MOSTRAR RESULTADOS ---
                st.subheader(f"Resultados para {nombre}")
                
                # Definición de colores para el semáforo
                color = "🟢" if pe < 20 and pe > 0 else "🟡" if pe < 30 else "🔴"
                
                df = pd.DataFrame({
                    "Métrica": ["Precio Actual", "P/E Ratio", "Variación (%)"],
                    "Valor": [f"${precio:,.2f}", f"{pe:.2f}x", f"{cambio:.2f}%"],
                    "Estado": ["-", f"{color} Analizando", "-"]
                })
                st.table(df)

                # --- ANÁLISIS DE IA ---
                st.subheader("🧠 Veredicto de la IA")
                prompt = f"Analiza la empresa {nombre} con un precio de {precio} y un PE Ratio de {pe}. ¿Es buen momento para comprar? Da un veredicto corto."
                
                try:
                    resultado_ia = model.generate_content(prompt)
                    st.success(resultado_ia.text)
                except Exception as ia_err:
                    st.warning("La IA no pudo procesar el análisis, pero los datos están arriba.")

        except Exception as e:
            st.error(f"Error de conexión o procesamiento: {e}")

# Pie de página informativo
st.divider()
st.caption("Nota: Esta app usa el motor de Streamlit Cloud y datos de FMP/Alpha Vantage.")
