# -*- coding: utf-8 -*-
"""
Alertas del Semáforo — vigilancia diaria del Semáforo de ENTRADA.

Toma las empresas que ya pasaron el Semáforo de Calidad (las de lista_top20.json)
y revisa su Semáforo de Entrada (precio contra su media de 200, con zona de duda
de ±2 ATR — la misma regla que entrada.html) vía el Worker. Cuando una PASA a
luz verde, dispara una alerta — una sola vez, en la transición, y no más de una
cada 30 días por empresa, para no spamear si oscila en el borde.

El Semáforo de Riesgo NO se automatiza (depende de la operación puntual): la
alerta avisa "buena empresa + buen momento → calculá stop y tamaño y decidí".

Estado entre corridas en alertas_estado.json (commiteado por el workflow).
Primera corrida (o cambio de regla, ver STATE_VERSION) = se "siembra" el estado
sin enviar nada.

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

BANDA_ATR = 2           # zona de duda: ±2 respiraciones diarias alrededor de la media de 200
STATE_VERSION = 2       # v1 = consenso TradingView (ok/warn/fail) · v2 = media de 200 (g/a/r)
DIAS_SILENCIO = 30      # no re-avisar la misma empresa antes de 30 días


def get_hist(ticker):
    """Histórico diario (320 ruedas de máximo/mínimo/cierre) vía el Worker."""
    url = WORKER + "?" + urllib.parse.urlencode({"hist": ticker, "k": CODE})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def luz_entrada(j):
    """Luz del Semáforo de Entrada — la MISMA regla que entrada.html:
    precio contra su media de 200 ruedas, con zona de duda de ±2 ATR(14).
    Devuelve (luz, distancia a la media), con luz en g/a/r."""
    h, l, c = j["h"], j["l"], j["c"]
    n = len(c)
    if n < 200:
        raise ValueError(f"historial insuficiente ({n} ruedas)")
    tr = [max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])) for i in range(n - 14, n)]
    price = c[-1]
    atr = sum(tr) / 14 / price
    sma = sum(c[-200:]) / 200
    dist = price / sma - 1
    banda = BANDA_ATR * atr
    luz = "g" if dist > banda else ("r" if dist < -banda else "a")
    return luz, dist


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
        subject = f"🟢 {alerts[0]['ticker']} pasó a luz verde · Semáforo de Entrada"
    else:
        subject = f"🟢 {n} empresas pasaron a luz verde · Semáforo de Entrada"

    blocks = ""
    for a in alerts:
        blocks += f"""
      <tr><td style="padding:0 0 14px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e6e6ef;border-left:4px solid #00b386;border-radius:10px;">
          <tr><td style="padding:16px 18px;font-family:Arial,Helvetica,sans-serif;">
            <div style="font-size:18px;font-weight:bold;color:#0c0c10;">{a['ticker']}
              <span style="font-size:13px;font-weight:normal;color:#6b6b85;">· {a['name']}</span></div>
            <div style="margin:8px 0 14px;font-size:13px;color:#333;line-height:1.5;">
              Está <strong>{a['dist_txt']} arriba de su media de 200</strong>, fuera de la zona de duda. Podés entrar con tu tamaño normal.
            </div>
            <a href="{a['entrada_url']}" style="display:inline-block;background:#00b386;color:#fff;text-decoration:none;font-size:13px;font-weight:bold;padding:9px 16px;border-radius:7px;font-family:Arial,sans-serif;">Ver el Semáforo de Entrada →</a>
            &nbsp;
            <a href="{a['riesgo_url']}" style="display:inline-block;color:#00875a;text-decoration:none;font-size:13px;padding:9px 8px;font-family:Arial,sans-serif;">Calcular stop y tamaño</a>
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
          <div style="font-size:13px;color:#6b6b85;margin-top:4px;">Una empresa de calidad acaba de pasar a luz verde.</div>
        </td></tr>
        <tr><td style="padding:18px 0 6px;">
          <table width="100%" cellpadding="0" cellspacing="0">{blocks}
          </table>
        </td></tr>
        <tr><td style="font-family:Arial,Helvetica,sans-serif;background:#fff7e6;border:1px solid #ffe0a3;border-radius:10px;padding:14px 18px;font-size:13px;color:#664d00;">
          ⚖️ <strong>Antes de operar:</strong> calidad ✅ y momento 🟢 ya están. Falta tu tercer semáforo — calculá en el <strong>Semáforo de Riesgo</strong> dónde va el stop y cuántas acciones comprar, y recién ahí decidí.
        </td></tr>
        <tr><td style="font-family:Arial,Helvetica,sans-serif;text-align:center;padding:20px 0 0;font-size:11px;color:#9090a0;">
          El Semáforo del Inversor · Aviso educativo, no es recomendación de inversión.<br>
          Verde no quiere decir “va a subir”: quiere decir terreno más calmo. El stop va siempre.
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
    # Cambio de regla (v1 TradingView → v2 media de 200): los estados viejos no son
    # comparables, así que se vuelve a sembrar sin enviar nada.
    first_run = prev is None or prev.get("version") != STATE_VERSION
    prev_states = {} if first_run else prev.get("states", {})
    last_alert = {} if first_run else dict(prev.get("last_alert", {}))

    now = datetime.now(timezone.utc)
    hoy = now.date()
    new_states, alerts, errors = {}, [], 0
    for c in watch:
        t = c["ticker"]
        try:
            luz, dist = luz_entrada(get_hist(t))
            new_states[t] = luz

            crossed = (luz == "g") and (prev_states.get(t) != "g")
            ult = last_alert.get(t)
            reciente = bool(ult) and (hoy - datetime.strptime(ult, "%Y-%m-%d").date()).days < DIAS_SILENCIO
            avisa = crossed and not first_run and not reciente
            if avisa:
                flag = " ← 🟢 NUEVO"
            elif crossed and reciente:
                flag = f" (verde de nuevo; ya avisada el {ult})"
            else:
                flag = ""
            print(f"{t:6} {luz}  {100*dist:+6.1f}% vs media 200{flag}")

            if avisa:
                last_alert[t] = hoy.isoformat()
                alerts.append({
                    "ticker": t,
                    "name": c.get("name", t),
                    "luz": luz,
                    "dist": round(dist, 4),
                    "dist_txt": f"{100*dist:.1f}%".replace(".", ","),
                    "entrada_url": f"{SITE}/entrada.html?symbol={urllib.parse.quote(t)}",
                    "riesgo_url": f"{SITE}/calculadora.html?symbol={urllib.parse.quote(t)}",
                })
        except Exception as e:
            errors += 1
            # si falla un ticker, conservamos su estado anterior para no perder la referencia
            if t in prev_states:
                new_states[t] = prev_states[t]
            print(f"{t:6} ERROR {e}")
        time.sleep(0.4)

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"updated_iso": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "version": STATE_VERSION,
                   "states": new_states,
                   "last_alert": last_alert}, f, ensure_ascii=False, indent=2)

    if first_run:
        print(f"\nPRIMERA CORRIDA (o cambio de regla): estado sembrado con {len(new_states)} empresas. "
              "No se envían alertas.")
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
