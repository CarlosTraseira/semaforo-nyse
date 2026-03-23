import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CONEXIÓN CON SECRETS ---
try:
    # Aquí es donde la App lee lo que pusiste en el cuadro negro de Secrets
    gemini_key = st.secrets["GEMINI_API_KEY"]
    av_key = st.secrets["AV_API_KEY"]

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    ticker = st.text_input("Introduce el Ticker (ej: BP, AAPL):", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Consultando Alpha Vantage...'):
            # Usamos tu API de Alpha Vantage (adiós a los datos locos de Yahoo)
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
            r = requests.get(url)
            data = r.json()

            if "Symbol" not in data:
                st.error("Límite de API alcanzado o Ticker incorrecto.")
            else:
                # Extraemos los datos REALES
                pe = float(data.get('TrailingPE', 0))
                roe = float(data.get('ReturnOnEquityTTM', 0)) * 100
                margin = float(data.get('ProfitMargin', 0)) * 100

                # Tabla Profesional
                st.subheader(f"Auditoría Real: {ticker}")
                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # El veredicto de la IA
                prompt = f"Analiza {ticker}: PE {pe}, ROE {roe}%, Margen {margin}%. Dame veredicto semáforo y 3 puntos."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

except Exception as e:
    st.error(f"Falta configurar los Secrets: {e}")
