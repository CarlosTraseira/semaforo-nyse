import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración inicial
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA DE LLAVES ---
gemini_key = st.secrets["GEMINI_API_KEY"].strip()
fmp_key = st.secrets["FMP_API_KEY"].strip()

# Configuración IA
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Interfaz
st.title("🚦 Semáforo NYSE Pro")
ticker = st.text_input("Introduce el Ticker:", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Consultando datos...'):
        # Llamadas a la API
        url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
        url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={fmp_key}"
        
        res_quote = requests.get(url_quote).json()
        res_profile = requests.get(url_profile).json()

        if not res_quote:
            st.error("No se encontraron datos. Revisa el Ticker.")
        else:
            q = res_quote[0]
            p = res_profile[0] if res_profile else {}

            # Datos básicos
            precio = q.get('price', 0)
            pe = q.get('pe', 0) or 0
            beta = p.get('beta', 0) or 0

            # Mostrar Tabla
            st.subheader(f"Métricas de {q.get('name', ticker)}")
            
            # Semáforo simple para el PE
            estado_pe = "🔴 Sobrevalorada"
            if pe <= 0: estado_pe = "⚪ N/A"
            elif pe < 15: estado_pe = "🟢 Infravalorada"
            elif pe < 25: estado_pe = "🟡 Valor Justo"

            df = pd.DataFrame({
                "Métrica": ["Precio", "P/E Ratio", "Beta (Riesgo)"],
                "Valor": [f"${precio}", f"{pe:.2f}x", f"{beta:.2f}"],
                "Semáforo": ["-", estado_pe, "🟢 Estable" if beta < 1.2 else "🟡 Volátil"]
            })
            st.table(df)

            # --- VERDICTO IA ---
            st.subheader("🧠 Veredicto de la IA")
            prompt = f"Analiza {ticker} con PE de {pe} y Beta de {beta}. Dame un veredicto de inversión muy corto."
            
            try:
                response = model.generate_content(prompt)
                st.success(response.text)
            except Exception:
                st.warning("La IA no pudo responder, pero los datos financieros están listos.")
