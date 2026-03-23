import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA SEGURA DE SECRETOS ---
try:
    # .strip() elimina espacios y las comillas se manejan por el formato TOML de los Secrets
    gemini_key = st.secrets["GEMINI_API_KEY"].strip()
    fmp_key = st.secrets["FMP_API_KEY"].strip()
    
    # Configuración del modelo de IA
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error de configuración en Secrets: {e}")
    st.info("Asegúrate de que tus Secrets tengan el formato: LLAVE = 'valor'")
    st.stop()

# 2. Interfaz de usuario
st.title("🚦 Semáforo NYSE Pro")
st.markdown("### Análisis financiero con IA y datos en tiempo real")

ticker = st.text_input("Introduce el Ticker (ej: AAPL, MSFT, BP):", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos para {ticker}...'):
        # Endpoints gratuitos y estables de Financial Modeling Prep
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}"
        
        try:
            res_quote = requests.get(url_quote).json()
            res_profile = requests.get(url_profile).json()

            # Validación de respuesta de la API
            if not res_quote or len(res_quote) == 0:
                st.error("❌ No se encontraron datos para este ticker. Revisa si es correcto.")
            else:
                q = res_quote[0]
                p = res_profile[0] if res_profile else {}

                # Extracción de métricas clave
                nombre = q.get('name', ticker)
                precio = q.get('price', 0)
                pe_ratio = q.get('pe', 0) or 0
                market_cap = q.get('marketCap', 0) / 1e9  # Convertir a Billones
                beta = p.get('beta', 0) or 0
                sector = p.get('sector', 'N/A')

                # --- MOSTRAR TABLA DE DATOS ---
                st.subheader(f"Auditoría de {nombre}")
                
                # Lógica del Semáforo visual
                def color_pe(val):
                    if val <= 0: return "⚪ N/A"
                    if val < 15: return "🟢 Infravalorada"
