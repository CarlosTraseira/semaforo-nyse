import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

try:
    # 2. Carga segura de llaves (usando .strip() para evitar errores de espacios)
    gemini_key = st.secrets["GEMINI_API_KEY"].strip()
    fmp_key = st.secrets["FMP_API_KEY"].strip()

    # 3. Configuración de Google Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo NYSE Pro")
    st.markdown("Análisis financiero en tiempo real con FMP y Google IA.")

    ticker = st.text_input("Introduce el Ticker (ej: AAPL, BP, MSFT):", "BP").upper().strip()

    if st.button("Analizar"):
        with st.spinner(f'Auditando {ticker}...'):
            # --- CONSULTA A FINANCIAL MODELING PREP ---
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={fmp_key}"
            url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
            
            res_ratios = requests.get(url_ratios).json()
            res_quote = requests.get(url_quote).json()

            if not res_ratios or not res_quote:
                st.error(f"No se encontraron datos para {ticker}. Revisa si el ticker es correcto.")
            else:
                # Extraer datos de las listas
                q = res_quote[0]
                r = res_ratios[0]

                # Ratios principales
                pe = q.get('pe', 0) or 0
                roe = (r.get('returnOnEquityTTM', 0) or 0) * 100
                margin = (r.get('netProfitMarginTTM', 0) or 0) * 100
                nombre = q.get('name', ticker)

                # --- MOSTRAR TABLA DE DATOS ---
                st.subheader(f"Métricas de {nombre}")
                
                # Definir estados para la tabla
                def get_status(val, metric):
                    if metric == "PE": return "🟢 Barato" if val < 15 else "🟡 Normal" if val < 25 else "🔴 Caro"
                    if metric == "ROE": return "🟢 Excelente" if val > 15 else "🟡 Aceptable" if val > 8 else "🔴 Bajo"
                    if metric == "Margin": return "🟢 Alto" if val > 10 else "🟡 Medio" if val > 5 else "🔴 Ajustado"
                    return ""

                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen Neto (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"],
                    "Diagnóstico": [get_status(pe, "PE"), get_status(roe, "ROE"), get_status(margin, "Margin")]
                })
                st.table(df)

                # --- ANÁLISIS CON IA GEMINI ---
                st.subheader("🧠 Veredicto de la IA")
                prompt = f"""
                Actúa como un analista financiero experto de Wall Street. 
                Analiza la empresa {nombre} ({ticker}) con estos datos actuales:
                - Ratio P/E: {pe:.2f}
                - Rentabilidad ROE: {roe:.2f}%
                - Margen de Beneficio: {margin:.2f}%
                
                Dame un veredicto de 'Semáforo' (Verde, Amarillo o Rojo) y explica por qué en 3 puntos clave muy breves.
                """
                
                try:
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as ai_err:
                    st.error(f"Error en la IA: {ai_err}")
                    st.info("Revisa que tu GEMINI_API_KEY en Secrets no tenga errores.")

except Exception as e:
    st.error(f"Error de Configuración: {e}")
    st.info("Asegúrate de tener GEMINI_API_KEY y FMP_API_KEY en los Secrets de Streamlit.")
