import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración visual
st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

def get_status(val, metric):
    if metric == "PE": return "🟢 Barato" if val < 15 else "🟡 Normal" if val < 25 else "🔴 Caro"
    if metric == "ROE": return "🟢 Excelente" if val > 15 else "🟡 Aceptable" if val > 8 else "🔴 Bajo"
    if metric == "Margin": return "🟢 Alto" if val > 10 else "🟡 Medio" if val > 5 else "🔴 Ajustado"
    return ""

try:
    # 2. Carga de llaves (limpieza de espacios)
    gemini_key = st.secrets["GEMINI_API_KEY"].strip()
    fmp_key = st.secrets["FMP_API_KEY"].strip()

    # 3. Configuración de IA
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo NYSE Pro")
    st.caption("Datos: Financial Modeling Prep | Cerebro: Google Gemini")

    ticker = st.text_input("Ticker de la empresa:", "BP").upper().strip()

    if st.button("Analizar"):
        with st.spinner(f'Analizando {ticker}...'):
            # Consulta a FMP
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={fmp_key}"
            url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
            
            res_ratios = requests.get(url_ratios).json()
            res_quote = requests.get(url_quote).json()

            if not res_ratios or not res_quote:
                st.warning(f"No hay datos suficientes para {ticker}. Prueba con AAPL o MSFT.")
            else:
                q = res_quote[0]
                r = res_ratios[0]

                pe = q.get('pe') or 0
                roe = (r.get('returnOnEquityTTM') or 0) * 100
                margin = (r.get('netProfitMarginTTM') or 0) * 100
                name = q.get('name', ticker)

                # Tabla de Resultados
                st.subheader(f"Métricas de {name}")
                df = pd.DataFrame({
                    "Indicador": ["P/E Ratio", "ROE (%)", "Margen Neto (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"],
                    "Estado": [get_status(pe, "PE"), get_status(roe, "ROE"), get_status(margin, "Margin")]
                })
                st.table(df)

                # Intento de Análisis con IA
                st.subheader("🧠 Veredicto de la IA")
                try:
                    prompt = f"Analiza {name} ({ticker}): P/E {pe:.2f}, ROE {roe:.2f}%, Margen {margin:.2f}%. Da 3 puntos clave y veredicto final."
                    response = model.generate_content(prompt)
                    st.success(response.text)
                except Exception as ai_err:
                    st.error("La IA está teniendo problemas de conexión con tu API Key.")
                    st.info("Sugerencia: Genera una nueva API Key en Google AI Studio y pégala en Secrets.")

except Exception as e:
    st.error(f"Error crítico: {e}")
