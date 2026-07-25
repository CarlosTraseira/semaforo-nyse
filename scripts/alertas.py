# -*- coding: utf-8 -*-
"""
Alertas del Semáforo — vigilancia diaria del Semáforo de ENTRADA.

Toma las empresas que ya pasaron el Semáforo de Calidad (las de lista_top20.json)
y revisa su Semáforo de Entrada (consenso técnico TradingView, 1S y 1M) vía el
Worker. Cuando una CRUZA a verde (zona de compra), dispara una alerta — una sola
vez, en la transición, para no spamear.

El Semáforo de Riesgo NO se automatiza (depende de la operación puntual): la
alerta avisa "buena empresa + buen momento → calculá tu riesgo y decidí".

Estado entre corridas en alertas_estado.json (commiteado por el workflow).
Primera corrida = se "siembra" el estado sin enviar nada.

Envío: POSTea el lote al ALERT_WEBHOOK (URL de Make). Si ese secret falta y hay
alertas para mandar, el script CORTA con error (exit 1) en vez de seguir en
silencio: un workflow verde no debe significar "alerta enviada".

Pensado para GitHub Actions, una vez por día en días hábiles.
"""
import json, os, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

WORKER = "https://yahoo-proxy.webmaster-c89.workers.dev/"
CODE = os.environ.get("SEMAFORO_CODE", "SEMAFORONYSE2026")
WEBHOOK = os.environ.get("ALERT_WEBHOOK", "").strip()   # URL del escenario de Make
SITE = "https://carlostraseira.github.io/semaforo-nyse"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST_PATH = os.path.join(REPO_ROOT, "lista_top20.json")
STATE_PATH = os.path.join(REPO_ROOT, "alertas_estado.json")


def get_tv(ticker):
    """Consulta el Semáforo de Entrada (1S/1M) de un ticker vía el Worker."""
    url = WORKER + "?" + urllib.parse.urlencode({"tv": ticker, "k": CODE})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def label(v):
    """Valor -1..+1 → etiqueta TradingView (igual que prueba.html)."""
    if v is None: return "No data"
    if v >= 0.5:  return "Strong Buy"
    if v >= 0.1:  return "Buy"
    if v > -0.1:  return "Neutral"
    if v > -0.5:  return "Sell"
    return "Strong Sell"


def entrada_verdict(w, m):
    """Veredicto combinado del medidor TV (igual que prueba.html): ok/warn/fail/nodata."""
    vals = [x for x in (w, m) if x is not None]
    if not vals: return "nodata"
    if any(x <= -0.1 for x in vals): return "fail"        # alguna en venta
    if len(vals) == 2 and w >= 0.1 and m >= 0.1: return "ok"  # ambas comprando
    return "warn"                                          # mixto / neutral


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def build_email(alerts, now):
    """Arma asunto + cuerpo HTML del aviso (email-safe, estilos inline)."""
    n = len(alerts)
    if n == 1:
        subject = f"🟢 {alerts[0]['ticker']} entró en zona de compra · Semáforo de Entrada"
    else:
        subject = f"🟢 {n} empresas entraron en zona de compra · Semáforo de Entrada"

    blocks = ""
    for a in alerts:
        blocks += f"""
      <tr><td style="padding:0 0 14px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e6e6ef;border-left:4px solid #00b386;border-radius:10px;">
          <tr><td style="padding:16px 18px;font-family:Arial,Helvetica,sans-serif;">
            <div style="font-size:18px;font-weight:bold;color:#0c0c10;">{a['ticker']}
              <span style="font-size:13px;font-weight:normal;color:#6b6b85;">· {a['name']}</span></div>
            <div style="margin:8px 0 14px;font-size:13px;color:#333;">
              <strong>1 Semana:</strong> {a['w_label']} &nbsp;·&nbsp; <strong>1 Mes:</strong> {a['m_label']}
            </div>
            <a href="{a['entrada_url']}" style="display:inline-block;background:#00b386;color:#fff;text-decoration:none;font-size:13px;font-weight:bold;padding:9px 16px;border-radius:7px;font-family:Arial,sans-serif;">Ver el historial real de esta señal →</a>
            &nbsp;
            <a href="{a['tradingview_url']}" style="display:inline-block;color:#00875a;text-decoration:none;font-size:13px;padding:9px 8px;font-family:Arial,sans-serif;">Análisis en TradingView</a>
          </td></tr>
        </table>
      </td></tr>"""

    html = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f2f2f7;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f2f2f7;padding:24px 12px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
        <tr><td style="font-family:Arial,Helvetica,sans-serif;text-align:center;padding-bottom:6px;">
          <span style="font-size:22px;">🟢🟡🔴</span>
          <div style="font-size:20px;font-weight:bold;color:#0c0c10;margin-top:6px;">Semáforo de Entrada</div>
          <div style="font-size:13px;color:#6b6b85;margin-top:4px;">Una empresa de calidad acaba de entrar en zona de compra.</div>
        </td></tr>
        <tr><td style="padding:18px 0 6px;">
          <table width="100%" cellpadding="0" cellspacing="0">{blocks}
          </table>
        </td></tr>
        <tr><td style="font-family:Arial,Helvetica,sans-serif;background:#fff7e6;border:1px solid #ffe0a3;border-radius:10px;padding:14px 18px;font-size:13px;color:#664d00;">
          ⚖️ <strong>Antes de operar:</strong> calidad ✅ y momento 🟢 ya están. Falta tu tercer semáforo — calculá el <strong>Riesgo</strong> de la operación puntual y recién ahí decidí.
        </td></tr>
        <tr><td style="font-family:Arial,Helvetica,sans-serif;text-align:center;padding:20px 0 0;font-size:11px;color:#9090a0;">
          El Semáforo del Inversor · Aviso educativo, no es recomendación de inversión.<br>
          Consenso técnico de TradingView (~26 indicadores).
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
    return subject, html


def send(payload):
    """Envía el lote de alertas al webhook de Make.

    Si falta ALERT_WEBHOOK NO se traga el aviso: imprime el payload y corta con
    exit(1) para que el workflow quede en rojo y GitHub mande el mail de fallo.
    Como el estado se commitea en un paso posterior, al fallar tampoco se guarda
    → la misma alerta se vuelve a detectar mañana en vez de perderse.
    """
    if not WEBHOOK:
        print("ERROR: hay alertas para enviar pero falta el secret ALERT_WEBHOOK.")
        print("NO se envió nada. Payload que se habría enviado:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.exit(1)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(WEBHOOK, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"Webhook → HTTP {r.status}")


def main():
    watch = load_json(LIST_PATH, {}).get("companies", [])
    if not watch:
        print("ABORT: lista_top20.json vacío o ausente. Nada que vigilar.")
        sys.exit(1)

    prev = load_json(STATE_PATH, None)
    first_run = prev is None
    prev_states = (prev or {}).get("states", {})

    new_states, alerts, errors = {}, [], 0
    for c in watch:
        t = c["ticker"]
        try:
            j = get_tv(t)
            w = j.get("ratings", {}).get("1W")
            m = j.get("ratings", {}).get("1M")
            verdict = entrada_verdict(w, m)
            new_states[t] = verdict

            crossed = (verdict == "ok") and (prev_states.get(t) != "ok")
            flag = " ← 🟢 NUEVO" if (crossed and not first_run) else ""
            print(f"{t:6} {verdict:5} (1S {label(w)} / 1M {label(m)}){flag}")

            if crossed and not first_run:
                alerts.append({
                    "ticker": t,
                    "name": c.get("name", t),
                    "exchange": j.get("exchange", ""),
                    "w": w, "m": m,
                    "w_label": label(w), "m_label": label(m),
                    "entrada_url": f"{SITE}/prueba.html?symbol={urllib.parse.quote(t)}",
                    "tradingview_url": f"https://www.tradingview.com/symbols/{j.get('exchange','NYSE')}-{t}/technicals/",
                })
        except Exception as e:
            errors += 1
            # si falla un ticker, conservamos su estado anterior para no perder la referencia
            if t in prev_states:
                new_states[t] = prev_states[t]
            print(f"{t:6} ERROR {e}")
        time.sleep(0.4)

    now = datetime.now(timezone.utc)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated_iso": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "states": new_states}, f, ensure_ascii=False, indent=2)

    if first_run:
        print(f"\nPRIMERA CORRIDA: estado sembrado con {len(new_states)} empresas. No se envían alertas.")
        return

    print(f"\n{len(alerts)} alerta(s) nueva(s) · errores: {errors}")
    if alerts:
        subject, html = build_email(alerts, now)
        send({
            "type": "alertas_entrada",
            "generated_iso": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "count": len(alerts),
            "subject": subject,
            "html": html,
            "alerts": alerts,
        })
    else:
        print("Sin transiciones a verde hoy. Nada que enviar.")


if __name__ == "__main__":
    main()
