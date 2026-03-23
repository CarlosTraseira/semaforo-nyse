import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CONEXIÓN CON SECRETS ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    av_key = st.secrets["AV_API_KEY"]

    genai.configure(api_key=gemini_key)
    
    # CAMBIO CRÍTICO: Usamos un nombre de modelo más compatible
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

    st.title("🚦 Semáforo de Calidad NYSE")
    ticker = st.text_input("Introduce el Ticker (ej: BP, AAPL):", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Consultando datos financieros...'):
            # Consulta a Alpha Vantage
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
            data = requests.get(url).json()

            if "Symbol" not in data:
                st.error("Límite de API alcanzado o Ticker incorrecto. Alpha Vantage permite 25 consultas/día.")
            else:
                # Extraemos y convertimos datos a números reales
                pe = float(data.get('TrailingPE', 0) if data.get('TrailingPE') != 'None' else 0)
                roe = float(data.get('ReturnOnEquityTTM', 0) if data.get('ReturnOnEquityTTM') != 'None' else 0) * 100
                margin = float(data.get('ProfitMargin', 0) if data.get('ProfitMargin') != 'None' else 0) * 100

                st.subheader(f"Auditoría Real: {ticker}")
                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # Veredicto de la IA
                prompt = f"Analiza la empresa {ticker} con estos datos: P/E de {pe}, ROE de {roe}% y Margen de {margin}%. Da un veredicto de Semáforo (Verde, Amarillo o Rojo) y justifica brevemente."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

except Exception as e:
    st.error(f"Error de sistema: {e}")
    st.info("Revisa que tus Secrets en Streamlit se llamen exactamente GEMINI_API_KEY y AV_API_KEY.")
