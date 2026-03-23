import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# Mostrar versión para confirmar que el código se actualizó
st.sidebar.write("v2.1 - Alpha Vantage Mode")

try:
    # 1. Cargar llaves
    gemini_key = st.secrets["GEMINI_API_KEY"]
    av_key = st.secrets["AV_API_KEY"]

    # 2. Configurar IA (Nombre de modelo compatible)
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    ticker = st.text_input("Ticker de la empresa:", "BP").upper().strip()

    if st.button("Analizar"):
        with st.spinner('Auditando datos...'):
            # Consulta a Alpha Vantage
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
            data = requests.get(url).json()

            if "Symbol" not in data:
                st.error("Límite de API alcanzado (25/día) o error de llave. Intenta en unos minutos.")
            else:
                # Extraer datos y limpiar el error de Yahoo
                pe = float(data.get('TrailingPE', 0) if data.get('TrailingPE') != 'None' else 0)
                roe = float(data.get('ReturnOnEquityTTM', 0) if data.get('ReturnOnEquityTTM') != 'None' else 0) * 100
                margin = float(data.get('ProfitMargin', 0) if data.get('ProfitMargin') != 'None' else 0) * 100

                # Tabla
                st.subheader(f"Resultados para {ticker}")
                st.table(pd.DataFrame({
                    "Métrica": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                }))

                # Análisis
                prompt = f"Analiza la empresa {ticker}: P/E {pe}, ROE {roe}%, Margen {margin}%. Da veredicto semáforo."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

except Exception as e:
    st.error(f"Fallo de conexión: {e}")
