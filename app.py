import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Alpha", page_icon="🚦")

# --- CARGA SEGURA DE SECRETOS ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    alpha_key = st.secrets["ALPHA_VANTAGE_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en Secrets: {e}")
    st.stop()

# --- FUNCIÓN CON CACHÉ (Para no gastar créditos) ---
# Se guarda el resultado por 86400 segundos (24 horas)
@st.cache_data(ttl=86400)
def obtener_datos_alpha(ticker):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={alpha_key}"
    response = requests.get(url)
    return response.json()

st.title("🚦 Semáforo NYSE (Alpha Edition)")
st.markdown("### Datos: Alpha Vantage | Cerebro: Gemini IA")

ticker = st.text_input("Introduce el Ticker:", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Buscando en memoria o consultando Alpha Vantage...'):
        data = obtener_datos_alpha(ticker)

        if not data or "Symbol" not in data:
            st.error("❌ No se encontraron datos.")
            if "Note" in data:
                st.warning("Límite de API alcanzado (5 por min / 25 por día).")
        else:
            # Extracción de datos
            nombre = data.get('Name', ticker)
            pe = float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else 0
            roe = float(data.get('ReturnOnEquityTTM', 0)) * 100 if data.get('ReturnOnEquityTTM') != 'None' else 0
            div = data.get('DividendYield', '0')

            st.subheader(f"Auditoría: {nombre}")
            
            df = pd.DataFrame({
                "Métrica": ["P/E Ratio", "ROE (%)", "Dividend Yield"],
                "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{div}"],
                "Estado": ["🟢 Atractivo" if 0 < pe < 20 else "🔴 Caro", "🟢 Saludable" if roe > 15 else "🟡 Normal", "-"]
            })
            st.table(df)

            # --- VERDICTO IA ---
            st.subheader("🧠 Veredicto de la IA")
            prompt = f"Analiza {nombre} ({ticker}): PE {pe:.2f}, ROE {roe:.2f}%. Da un veredicto de inversión corto."
            
            try:
                # Intentamos obtener respuesta de la IA
                resultado_ia = model.generate_content(prompt)
                st.success(resultado_ia.text)
            except Exception as e:
                st.warning("La IA está saturada, pero los datos financieros son correctos.")
