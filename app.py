import streamlit as st
import requests
import pandas as pd

# ==================================================
# CONFIG GENERAL
# ==================================================
st.set_page_config(
    page_title="🚦 Semáforo Fundamental – NYSE",
    page_icon="🚦",
    layout="centered"
)

# 👉 CAMBIÁ ESTO A False CUANDO QUIERAS USAR ALPHA REAL
USE_MOCK_DATA = True

# API KEY (solo se usa si USE_MOCK_DATA = False)
ALPHA_KEY = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")

# ==================================================
# HELPERS
# ==================================================
def num(x):
    try:
        return float(x)
    except:
        return None


def semaforo_texto(color):
    if color == "green":
        return "🟢 Bueno"
    if color == "yellow":
        return "🟡 Regular"
    if color == "red":
        return "🔴 Malo"
    return "⚪ N/D"


def evaluar_pe(pe):
    if pe is None:
