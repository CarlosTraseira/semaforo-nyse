 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index b4eb169d5899b9873c41b872ce9a34f9f10ece51..fe2d1ad9d8e514bd95e41b8648623f8f2d6beac6 100644
--- a/README.md
+++ b/README.md
@@ -1,28 +1,46 @@
-# 🚦 Semáforo Fundamental – Alpha Vantage
+# 🚦 Semáforo NYSE
 
-Aplicación simple en **Streamlit** para evaluar la calidad financiera de empresas
-usando **datos fundamentales reales** de Alpha Vantage (free tier).
+App en Streamlit para evaluar rápidamente 6 indicadores fundamentales de un ticker (enfocado en NYSE), usando solo servicios gratuitos.
 
-## ✅ Qué hace
-- Consulta ratios fundamentales reales
-- Evalúa calidad con semáforo (🟢🟡🔴)
-- Usa **1 sola llamada por ticker**
-- Ideal para cursos, demos y MVPs
-
-## 📊 Indicadores usados
+## Indicadores incluidos
 - Trailing P/E
-- ROE (TTM)
+- ROE
 - Profit Margin
-- Debt / Equity
+- Debt to Equity
+- Free Cash Flow
+- Dividend Yield (%)
+
+## Qué hace la app
+- Consulta datos reales desde Alpha Vantage (`OVERVIEW` + `CASH_FLOW`).
+- Muestra una tabla con columnas:
+  - **Indicador**
+  - **Valor**
+  - **Referencia** (estándares generales usados por analistas)
+  - **Estado**
+  - **Explicación**
+- Incluye sección de **verificación** con links directos al endpoint usado.
+- Agrega acceso a **SEC EDGAR** para validar en fuente primaria (10-K / 10-Q).
 
-## 🔑 Requisitos
+## Requisitos
 - Python 3.9+
 - API key gratuita de Alpha Vantage
 
-## 🔐 Configurar API Key
+## Instalación
+```bash
+pip install -r requirements.txt
+```
 
-Crear `.streamlit/secrets.toml`:
+## Configurar API key
+Puedes ingresarla en la barra lateral de la app o guardarla en `.streamlit/secrets.toml`:
 
 ```toml
 ALPHA_VANTAGE_API_KEY = "TU_API_KEY"
-``
+```
+
+## Ejecutar
+```bash
+streamlit run app.py
+```
+
+## Nota importante
+Los umbrales de referencia son orientativos y pueden variar por sector, tamaño de empresa y ciclo económico.
 
EOF
)
