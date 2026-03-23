import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- LÓGICA DE API KEYS ---
gemini_key = st.secrets.get("GEMINI_API_KEY")
av_key = st.secrets.get("AV_API_KEY")

if gemini_key and av_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    user_input = st.text_input("Ticker de la empresa (ej: BP, AAPL):", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Consultando Alpha Vantage...'):
            try:
                # 1. Consulta a Alpha Vantage (OVERVIEW)
                url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={user_input}&apikey={av_key}'
                data = requests.get(url).json()

                if not data or "Symbol" not in data:
                    st.error("No se encontraron datos. Verifica el Ticker o el límite de tu API Key.")
                else:
                    # 2. Extracción de Ratios (Alpha Vantage devuelve strings, convertimos a float)
                    pe = float(data.get('TrailingPE', 0))
                    roe = float(data.get('ReturnOnEquityTTM', 0)) * 100
                    margin = float(data.get('ProfitMargin', 0)) * 100
                    debt = float(data.get('DebtToEquityRatio', 0))
                    
                    # 3. Mostrar Tabla
                    st.subheader(f"Datos Reales: {user_input}")
                    df_data = {
                        "Indicador": ["Trailing P/E", "ROE (%)", "Profit Margin (%)", "Debt to Equity"],
                        "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{debt:.2f}"],
                        "Meta": ["< 30x", "> 15%", "> 10%", "< 1.0"]
                    }
                    st.table(pd.DataFrame(df_data))

                    # 4. Análisis con Gemini
                    prompt = f"Analiza estos datos de {user_input}: P/E {pe}, ROE {roe}%, Margen {margin}%. Dame veredicto Semáforo y 3 puntos."
                    response = model.generate_content(prompt)
                    st.subheader("🧠 Veredicto de la IA")
                    st.write(response.text)

            except Exception as e:
                st.error(f"Error técnico: {e}")
else:
    st.warning("Faltan configurar las API Keys (Gemini o Alpha Vantage) en los Secrets.")
