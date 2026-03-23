import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA SEGURA ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"].strip()
    fmp_key = st.secrets["FMP_API_KEY"].strip()
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Revisa tus Secrets en Streamlit.")
    st.stop()

st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Ticker de la empresa:", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner('Obteniendo métricas finales...'):
        # 1. Endpoints Gratuitos: Quote (Precio/PE) y Profile (Márgenes/Descripción)
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}"
        
        res_quote = requests.get(url_quote).json()
        res_profile = requests.get(url_profile).json()

        if not res_quote or not res_profile:
            st.error("No se encontraron datos. Intenta con otro Ticker.")
        else:
            q = res_quote[0]
            p = res_profile[0]

            # Extraemos lo mejor de cada uno
            pe = q.get('pe', 0) or 0
            price = q.get('price', 0)
            mkt_cap = q.get('marketCap', 0) / 1e9 # En billones
            
            # El Profile nos da el Beta (Riesgo) y a veces márgenes implícitos
            beta = p.get('beta', 0)
            industry = p.get('industry', 'N/A')

            st.subheader(f"Análisis de {p.get('companyName', ticker)}")
            
            # Tabla de visualización mejorada
            df = pd.DataFrame({
                "Métrica": ["Precio", "P/E Ratio", "Beta (Riesgo)", "Market Cap"],
                "Valor": [f"${price}", f"{pe:.2f}x", f"{beta:.2f}", f"{mkt_cap:.2f}B"],
                "Nota": ["Actual", "Bajo 20 es ideal", "Bajo 1.0 es estable", "Tamaño"]
            })
            st.table(df)

            # --- IA CONTEXTUAL ---
            prompt = f"Empresa: {p.get('companyName')}. Sector: {industry}. PE: {pe}. Beta: {beta}. Da un veredicto de inversión tipo semáforo."
            
            try:
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)
            except:
                st.warning("La IA está saturada, pero los datos están listos.")
