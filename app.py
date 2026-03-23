import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CONFIGURACIÓN DE API KEY ---
# En Streamlit Cloud, esto se configura en 'Secrets' para seguridad
api_key = st.sidebar.text_input("Introduce tu Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    st.markdown("Extrae datos reales de Yahoo Finance y los analiza con IA.")

    user_input = st.text_input("Ticker de la empresa (ej: BP, GOLD, AAPL):", "BP")

    if st.button("Analizar"):
        with st.spinner('Consultando terminal financiera...'):
            try:
                # 1. Limpieza de Ticker
                ticker_symbol = user_input.split('(')[-1].split(')')[0].strip().upper()
                stock = yf.Ticker(ticker_symbol)
                info = stock.info

                # 2. Extracción de Datos Crudos (Precisión 100%)
                pe = info.get('trailingPE', 0)
                roe = info.get('returnOnEquity', 0) * 100
                margin = info.get('profitMargins', 0) * 100
                debt = info.get('debtToEquity', 0)
                fcf = info.get('freeCashflow', 0)

                # 3. Mostrar Tabla de Datos Reales
                df_data = {
                    "Indicador": ["Trailing P/E", "ROE", "Profit Margin", "Debt to Equity", "Free Cash Flow"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{debt:.2f}%", f"${fcf:,.0f}"],
                    "Meta": ["< 30x", "> 15%", "> 10%", "< 100%", "Positivo"]
                }
                st.table(pd.DataFrame(df_data))

                # 4. Análisis con Gemini (Solo razonamiento, no inventa datos)
                prompt = f"""Actúa como Analista Financiero. Analiza estos datos REALES de {ticker_symbol}:
                - P/E: {pe} (Meta < 30)
                - ROE: {roe}% (Meta > 15%)
                - Margen: {margin}% (Meta > 10%)
                Dame un veredicto 'Semáforo' (Verde, Amarillo o Rojo) y justifica en 3 puntos."""
                
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto del Analista IA")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error al conectar con la API: {e}")
else:
    st.warning("Por favor, introduce tu API Key de Gemini en la barra lateral para comenzar.")
