import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CONEXIÓN CON SECRETS ---
try:
    # Leemos las llaves que ya tienes bien puestas en Secrets
    gemini_key = st.secrets["GEMINI_API_KEY"]
    av_key = st.secrets["AV_API_KEY"]

    # Configuración de Google AI
    genai.configure(api_key=gemini_key)
    
    # CAMBIO CLAVE: Usamos el nombre corto del modelo para evitar el error 404
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    ticker = st.text_input("Introduce el Ticker (ej: BP, AAPL):", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Obteniendo datos de Alpha Vantage...'):
            # Consulta a Alpha Vantage con tu llave
            url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
            r = requests.get(url)
            data = r.json()

            if "Symbol" not in data:
                st.error("Límite de API alcanzado o Ticker incorrecto.")
            else:
                # Extraemos datos reales (adiós al 2239x de Yahoo)
                pe_raw = data.get('TrailingPE', '0')
                roe_raw = data.get('ReturnOnEquityTTM', '0')
                margin_raw = data.get('ProfitMargin', '0')

                # Convertimos a números (manejando casos donde venga 'None')
                pe = float(pe_raw) if pe_raw != 'None' else 0.0
                roe = float(roe_raw) * 100 if roe_raw != 'None' else 0.0
                margin = float(margin_raw) * 100 if margin_raw != 'None' else 0.0

                st.subheader(f"Auditoría Real: {ticker}")
                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                })
                st.table(df)

                # Generar el veredicto con Gemini
                prompt = f"Analiza financieramente a {ticker} con: P/E {pe}, ROE {roe}% y Margen {margin}%. Da un veredicto de Semáforo (Verde, Amarillo o Rojo) y justifica brevemente."
                
                # Intento de generación con manejo de errores específico para el modelo
                try:
                    response = model.generate_content(prompt)
                    st.subheader("🧠 Veredicto de la IA")
                    st.write(response.text)
                except Exception as ai_err:
                    st.error(f"Error al generar análisis con IA: {ai_err}")

except Exception as e:
    st.error(f"Error de configuración: {e}")
    st.info("Revisa que tus Secrets se llamen GEMINI_API_KEY y AV_API_KEY.")
