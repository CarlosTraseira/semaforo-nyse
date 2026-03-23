import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import requests  # <--- ESTO ES LO QUE FALTABA Y CAUSABA EL ERROR

# Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- LÓGICA DE API KEY ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "general" in st.secrets and "GEMINI_API_KEY" in st.secrets["general"]:
    api_key = st.secrets["general"]["GEMINI_API_KEY"]

if not api_key:
    api_key = st.sidebar.text_input("Introduce Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    st.markdown("Auditoría financiera en tiempo real con datos de Yahoo Finance.")

    user_input = st.text_input("Ticker de la empresa (ej: BP, GOLD, AAPL):", "BP")

    if st.button("Analizar"):
        with st.spinner('Consultando terminal financiera...'):
            try:
                # 1. Limpieza de Ticker
                ticker_symbol = user_input.split('(')[-1].split(')')[0].strip().upper()
                
                # 2. Consulta a Yahoo Finance
                stock = yf.Ticker(ticker_symbol)
                info = stock.info

                # 3. Extracción de Datos
                pe = info.get('trailingPE', 0)
                roe = info.get('returnOnEquity', 0) * 100
                margin = info.get('profitMargins', 0) * 100
                debt = info.get('debtToEquity', 0)
                fcf = info.get('freeCashflow', 0)

                # 4. Mostrar Tabla de Datos Reales
                st.subheader(f"Datos Extraídos para {ticker_symbol}")
                df_data = {
                    "Indicador": ["Trailing P/E", "ROE", "Profit Margin", "Debt/Equity", "Free Cash Flow"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{debt:.2f}%", f"${fcf:,.0f}"],
                    "Meta": ["< 30x", "> 15%", "> 10%", "< 100%", "Positivo"]
                }
                st.table(pd.DataFrame(df_data))

                # 5. Análisis con Gemini
                prompt = f"""Actúa como Analista Financiero. Analiza estos datos REALES de {ticker_symbol}:
                - P/E: {pe}
                - ROE: {roe}%
                - Margen: {margin}%
                - Deuda/Equity: {debt}%
                Dame un veredicto 'Semáforo' (Verde, Amarillo o Rojo) y justifica en 3 puntos breves."""
                
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error detectado: {e}")
else:
    st.warning("⚠️ Configura tu GEMINI_API_KEY en los Secrets de Streamlit o en la barra lateral.")
