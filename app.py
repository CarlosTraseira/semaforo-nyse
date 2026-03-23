import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA DE LLAVES DESDE SECRETS ---
# Estos nombres deben coincidir EXACTAMENTE con lo que pusiste en el cuadro de Secrets
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    av_key = st.secrets["AV_API_KEY"]
    
    # Configurar Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    st.title("🚦 Semáforo de Calidad NYSE")
    ticker = st.text_input("Ticker de la empresa:", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Obteniendo datos reales...'):
            # Consulta a Alpha Vantage
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
            data = requests.get(url).json()

            if "Symbol" not in data:
                st.error("Error: No se pudieron obtener datos. Verifica el ticker o el límite de la API.")
            else:
                # Extracción y conversión de datos
                pe = float(data.get('TrailingPE', 0))
                roe = float(data.get('ReturnOnEquityTTM', 0)) * 100
                margin = float(data.get('ProfitMargin', 0)) * 100
                
                # Mostrar Tabla
                st.subheader(f"Métricas Auditadas: {ticker}")
                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # Análisis con IA
                prompt = f"Analiza {ticker}: P/E {pe}, ROE {roe}%, Margen {margin}%. Da veredicto semáforo."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

except Exception as e:
    st.error(f"Error de configuración: {e}")
    st.info("Asegúrate de que las llaves en 'Secrets' se llamen GEMINI_API_KEY y AV_API_KEY.")
