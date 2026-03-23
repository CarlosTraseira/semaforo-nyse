import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- LÓGICA DE API KEY (BLINDADA) ---
api_key = None

# 1. Intenta leer de Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
# 2. Si falla, intenta leer de una sección general
elif "general" in st.secrets and "GEMINI_API_KEY" in st.secrets["general"]:
    api_key = st.secrets["general"]["GEMINI_API_KEY"]

# Si NO se encontró en secrets, mostrar el input en la barra lateral
if not api_key:
    api_key = st.sidebar.text_input("Introduce Gemini API Key:", type="password")

if api_key:
    # Configurar la IA
    genai.configure(api_key=api_key)
    # ... resto del código igual ...
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    st.markdown("Auditoría financiera en tiempo real con datos de Yahoo Finance.")

    user_input = st.text_input("Ticker de la empresa (ej: BP, GOLD, AAPL):", "BP")

    if st.button("Analizar"):
        with st.spinner('Consultando terminal financiera...'):
            try:
                # 1. Limpieza de Ticker
                ticker_symbol = user_input.split('(')[-1].split(')')[0].strip().upper()
                
                # --- TRUCO DE CAMUFLAJE PARA EVITAR BLOQUEOS ---
                # Creamos una sesión que simula ser un navegador real
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                stock = yf.Ticker(ticker_symbol, session=session)
                info = stock.info

                # 2. Extracción de Datos Crudos
                pe = info.get('trailingPE', 0)
                roe = info.get('returnOnEquity', 0) * 100
                margin = info.get('profitMargins', 0) * 100
                debt = info.get('debtToEquity', 0)
                fcf = info.get('freeCashflow', 0)

                # 3. Mostrar Tabla de Datos Reales
                st.subheader(f"Datos Extraídos para {ticker_symbol}")
                df_data = {
                    "Indicador": ["Trailing P/E", "ROE", "Profit Margin", "Debt to Equity", "Free Cash Flow"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{debt:.2f}%", f"${fcf:,.0f}"],
                    "Meta": ["< 30x", "> 15%", "> 10%", "< 100%", "Positivo"]
                }
                st.table(pd.DataFrame(df_data))

                # 4. Análisis con Gemini
                prompt = f"""Actúa como Analista Financiero. Analiza estos datos REALES de {ticker_symbol}:
                - P/E: {pe}
                - ROE: {roe}%
                - Margen: {margin}%
                - Deuda: {debt}%
                Dame un veredicto 'Semáforo' (Verde, Amarillo o Rojo) y justifica en 3 puntos breves."""
                
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error detectado: {e}")
                st.info("Si ves un error de 'Rate Limited', espera 30 segundos e intenta de nuevo.")
else:
    st.warning("⚠️ Introduce tu Gemini API Key en la barra lateral para activar la herramienta.")
