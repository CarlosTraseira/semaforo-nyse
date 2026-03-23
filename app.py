import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA SEGURA DE LLAVES ---
gemini_key = st.secrets.get("GEMINI_API_KEY", "").strip()
fmp_key = st.secrets.get("FMP_API_KEY", "").strip()

if not gemini_key or not fmp_key:
    st.error("🚨 Faltan llaves en Secrets. Revisa GEMINI_API_KEY y FMP_API_KEY.")
    st.stop()

# Configuración IA
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Ticker de la empresa:", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos para {ticker}...'):
        # 1. Endpoints 100% Gratuitos de FMP
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        url_metrics = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?apikey={fmp_key}"
        
        res_quote = requests.get(url_quote).json()
        res_metrics = requests.get(url_metrics).json()

        if not res_quote:
            st.error("❌ No se encontró el Ticker o la API Key de FMP falló.")
        else:
            # Extraer datos con seguridad
            q = res_quote[0] if len(res_quote) > 0 else {}
            # Si no hay métricas TTM, intentamos ratios básicos
            m = res_metrics[0] if (res_metrics and len(res_metrics) > 0) else {}

            pe = q.get('pe', 0) or 0
            # ROE y Margen desde Key Metrics (Gratis)
            roe = (m.get('dividendYieldTTM', 0) or 0) * 100 # Usamos dividendos como prueba si ROE falla
            # Intentemos obtener el ROE real si existe el campo
            roe_real = (m.get('roeTTM', 0) or 0) * 100
            
            st.subheader(f"Datos de Mercado: {q.get('name', ticker)}")
            
            # Tabla de visualización
            df = pd.DataFrame({
                "Métrica": ["Precio Actual", "P/E Ratio", "ROE (TTM %)", "Div. Yield (%)"],
                "Valor": [f"${q.get('price', 0)}", f"{pe:.2f}x", f"{roe_real:.2f}%", f"{roe:.2f}%"]
            })
            st.table(df)

            # --- IA VERDICT ---
            try:
                prompt = f"Analiza {ticker} con PE de {pe:.2f} y ROE de {roe_real:.2f}%. Dame un veredicto de semáforo muy breve."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.success(response.text)
            except Exception as e:
                st.warning("La IA no pudo procesar el veredicto, pero los datos financieros están arriba.")
