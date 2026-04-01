"""
============================================================
  Retell AI Webhook Server
  Recibe eventos de llamadas y sincroniza resultados en GHL.

  Eventos procesados:
    - call_ended → sube resumen + grabación, mueve pipeline si sentimiento positivo

  .env requerido:
    RETELL_WEBHOOK_SECRET=clave_...
    GHL_API_KEY=...
    GHL_LOCATION_ID=...

  USO:
    pip install flask python-dotenv requests
    python ghl-integration/webhook_server.py

  PRODUCCIÓN (recomendado):
    gunicorn -w 2 -b 0.0.0.0:5050 "webhook_server:app"

  URL a registrar en Retell AI:
    https://{NGROK_DOMAIN}/retell-webhook

  ARRANQUE RAPIDO (Windows):
    Doble clic en start-server.bat
    (levanta ngrok + servidor juntos)
============================================================
"""

import os
import sys
import hmac
import hashlib
import logging
import requests as req
from pathlib import Path

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ── Path setup ─────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GHL_DIR))
load_dotenv(ROOT / ".env")

from ghl_client import (
    update_contact_with_call_data,
    update_contact_tags,
    get_opportunities_by_contact,
    get_pipeline_by_name,
    get_stage_id,
    create_contact,
    update_contact,
    create_opportunity,
    GHL_LOCATION_ID,
    _headers,
    BASE_URL,
)

# ── Config ─────────────────────────────────────────────────
RETELL_SECRET           = os.getenv("RETELL_WEBHOOK_SECRET", "")
RETELL_API_KEY          = os.getenv("RETELL_API_KEY", "")
RETELL_AGENT_ID         = os.getenv("RETELL_AGENT_ID", "")          # Agente OUTBOUND (formulario web)
RETELL_INBOUND_AGENT_ID = os.getenv("RETELL_INBOUND_AGENT_ID", "")  # Agente INBOUND (número de teléfono)
RETELL_FROM_NUMBER      = os.getenv("RETELL_NUMBER", "")
GHL_CALLBACK_NUMBER     = os.getenv("GHL_PHONE_NUMBER", "")
HOT_STAGE_NAME      = "HOT Lead"
PIPELINE_NAME       = "Contratistas Latinos"
NEW_LEAD_STAGE_NAME = os.getenv("GHL_NEW_LEAD_STAGE", "Nuevo Lead")

RETELL_BASE_URL = "https://api.retellai.com"

APPT_KEYWORDS_ES = ["cita confirmada", "confirmada", "confirmado", "agendado", "agendada"]
APPT_KEYWORDS_EN = ["appointment confirmed", "confirmed", "booked", "scheduled"]

# ── Logging ────────────────────────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "retell_webhook.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

app = Flask(__name__)

# ── CORS — intercepta preflight OPTIONS antes que Flask lo maneje ──
from flask import make_response

@app.before_request
def _handle_options():
    if request.method == "OPTIONS":
        resp = make_response("", 200)
        resp.headers["Access-Control-Allow-Origin"]  = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
        return resp

@app.after_request
def _add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    return response


# ── GHL web-lead helpers ────────────────────────────────────

def _ghl_search_contact(query: str) -> dict | None:
    """Busca un contacto en GHL por email o teléfono. Retorna el primer resultado o None."""
    resp = req.get(
        f"{BASE_URL}/contacts/",
        params={"locationId": GHL_LOCATION_ID, "query": query},
        headers=_headers(),
    )
    if not resp.ok:
        return None
    contacts = resp.json().get("contacts", [])
    return contacts[0] if contacts else None


def _ghl_upsert_web_lead(phone: str, nombre: str, email: str, ciudad: str, language: str) -> tuple[str, list]:
    """
    Busca el contacto en GHL por email (primero) o teléfono (fallback).
    - Si existe: agrega tags, retorna (contact_id, existing_tags)
    - Si no existe: crea contacto nuevo, retorna (contact_id, [])
    """
    WEB_TAGS = ["Interesado_Sistema_Completo", "web-lead", "Llamada_Pendiente"]

    contact = None
    if email:
        contact = _ghl_search_contact(email)
    if not contact and phone:
        contact = _ghl_search_contact(phone)

    if contact:
        contact_id    = contact.get("id", "")
        existing_tags = contact.get("tags", [])
        new_tags = list(set(existing_tags + WEB_TAGS))
        update_contact_tags(contact_id, new_tags)
        if email and not contact.get("email"):
            update_contact(contact_id, {"email": email})
        logging.info(f"GHL upsert: contacto existente actualizado — {contact_id}")
        return contact_id, existing_tags

    # Crear contacto nuevo
    parts      = nombre.strip().split(" ", 1)
    first_name = parts[0]
    last_name  = parts[1] if len(parts) > 1 else ""
    payload: dict = {
        "firstName": first_name,
        "lastName":  last_name,
        "phone":     phone,
        "tags":      WEB_TAGS,
        "source":    "Web Form",
    }
    if email:
        payload["email"] = email
    if ciudad:
        payload["city"] = ciudad

    new_contact = create_contact(payload)
    contact_id  = new_contact.get("id", "")
    logging.info(f"GHL upsert: contacto nuevo creado — {contact_id} ({nombre})")
    return contact_id, []


def _ghl_create_opportunity_if_needed(contact_id: str, nombre: str) -> None:
    """
    Crea una oportunidad en la etapa 'Nuevo Lead' del pipeline principal
    solo si el contacto no tiene ninguna oportunidad abierta todavía.
    """
    try:
        existing = get_opportunities_by_contact(contact_id)
        if existing:
            logging.info(f"GHL oportunidad: ya existe para {contact_id} — omitiendo")
            return

        pipeline = get_pipeline_by_name(PIPELINE_NAME)
        if not pipeline:
            logging.warning(f"GHL oportunidad: pipeline '{PIPELINE_NAME}' no encontrado")
            return

        stage_id = get_stage_id(pipeline, NEW_LEAD_STAGE_NAME)
        if not stage_id:
            logging.warning(f"GHL oportunidad: etapa '{NEW_LEAD_STAGE_NAME}' no encontrada en '{PIPELINE_NAME}'")
            return

        create_opportunity(
            contact_id  = contact_id,
            pipeline_id = pipeline["id"],
            stage_id    = stage_id,
            name        = f"Web Lead — {nombre}",
            status      = "open",
        )
        logging.info(f"GHL oportunidad: creada en '{NEW_LEAD_STAGE_NAME}' para {contact_id}")
    except Exception as e:
        logging.warning(f"GHL oportunidad: error — {e}")


# ── Retell call helper ──────────────────────────────────────

def _fire_retell_call(
    to_number: str,
    contact_id: str,
    nombre: str,
    ciudad: str,
    language: str,
    begin_message: str,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
) -> dict:
    """
    Dispara una llamada outbound via Retell AI.
    Pasa first_name / last_name como dynamic variables para el saludo personalizado.
    """
    payload = {
        "from_number": RETELL_FROM_NUMBER,
        "to_number":   to_number,
        "agent_id":    RETELL_AGENT_ID,
        "begin_message": begin_message,
        "metadata": {
            "contact_id": contact_id,
            "nombre":     nombre,
            "ciudad":     ciudad,
            "language":   language,
            "email":      email,
        },
        "retell_llm_dynamic_variables": {
            "initial_greeting":  begin_message,
            "language":          language,
            "numero_callback":   GHL_CALLBACK_NUMBER,
        },
    }
    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type":  "application/json",
    }
    resp = req.post(f"{RETELL_BASE_URL}/v2/create-phone-call", json=payload, headers=headers)
    if not resp.ok:
        raise Exception(f"{resp.status_code} — {resp.text[:300]}")
    return resp.json()


def _appointment_confirmed(summary: str, language: str) -> bool:
    """Detecta si el cliente confirmó una cita en la conversación."""
    summary_lower = summary.lower()
    keywords = APPT_KEYWORDS_EN if language == "en" else APPT_KEYWORDS_ES
    return any(kw in summary_lower for kw in keywords)


# ── Verificación de firma ───────────────────────────────────

def _verify_signature(raw_body: bytes, header_sig: str) -> bool:
    """
    Retell firma cada request con HMAC-SHA256 del body usando el webhook secret.
    Header: x-retell-signature
    """
    if not RETELL_SECRET:
        logging.warning("RETELL_WEBHOOK_SECRET no configurado — omitiendo verificación")
        return True

    expected = hmac.new(
        RETELL_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, header_sig or "")


# ── Helpers de pipeline ─────────────────────────────────────

def _move_to_hot_lead(contact_id: str) -> bool:
    """
    Mueve la primera oportunidad del contacto a la etapa 'HOT Lead'.
    Retorna True si tuvo éxito.
    """
    import requests as req

    pipeline = get_pipeline_by_name(PIPELINE_NAME)
    if not pipeline:
        logging.warning(f"Pipeline '{PIPELINE_NAME}' no encontrado")
        return False

    stage_id = get_stage_id(pipeline, HOT_STAGE_NAME)
    if not stage_id:
        logging.warning(f"Etapa '{HOT_STAGE_NAME}' no encontrada en pipeline '{PIPELINE_NAME}'")
        return False

    opps = get_opportunities_by_contact(contact_id)
    if not opps:
        logging.warning(f"Contacto {contact_id} no tiene oportunidades — no se puede mover")
        return False

    opp_id = opps[0].get("id")
    url     = f"https://services.leadconnectorhq.com/opportunities/{opp_id}"
    payload = {"pipelineStageId": stage_id}

    from ghl_client import _headers
    resp = req.put(url, json=payload, headers=_headers())
    if resp.ok:
        logging.info(f"Oportunidad {opp_id} movida a '{HOT_STAGE_NAME}'")
        return True

    logging.error(f"Error moviendo oportunidad: {resp.status_code} — {resp.text[:200]}")
    return False


# ── Procesador de eventos ───────────────────────────────────

def _process_call_ended(payload: dict) -> dict:
    """
    Procesa el evento call_ended de Retell AI.

    Estructura esperada del payload:
    {
      "event": "call_ended",
      "call": {
        "metadata": {
          "contact_id": "abc123",
          "nombre": "Garcia Roofing",
          "ciudad": "Minneapolis"
        },
        "call_analysis": {
          "call_summary": "...",
          "agent_sentiment": "Positive" | "Neutral" | "Negative"
        },
        "recording_url": "https://..."
      }
    }
    """
    call         = payload.get("call", {})
    metadata     = call.get("metadata", {})
    analysis     = call.get("call_analysis", {})

    contact_id    = metadata.get("contact_id", "")
    nombre        = metadata.get("nombre", "Desconocido")
    ciudad        = metadata.get("ciudad", "—")
    language      = metadata.get("language", "es")
    summary       = analysis.get("call_summary", "Sin resumen disponible")
    sentiment     = analysis.get("agent_sentiment", "")
    recording_url = call.get("recording_url", "")

    if not contact_id:
        logging.warning("call_ended recibido sin contact_id en metadata — ignorado")
        return {"status": "skipped", "reason": "no contact_id"}

    logging.info(f"Llamada finalizada para el negocio: {nombre} en {ciudad}")
    logging.info(f"  contact_id: {contact_id} | sentimiento: {sentiment} | grabacion: {'SI' if recording_url else 'NO'}")

    # 1. Subir resumen y grabación a GHL
    update_contact_with_call_data(
        contact_id    = contact_id,
        summary       = summary,
        recording_url = recording_url,
    )

    # 2. Agregar tag con resultado de la llamada
    try:
        from ghl_client import update_contact_tags, update_contact, _headers, BASE_URL, GHL_LOCATION_ID

        r = req.get(f"{BASE_URL}/contacts/{contact_id}", headers=_headers())
        current_tags = r.json().get("contact", {}).get("tags", []) if r.ok else []

        sentiment_tag = {
            "Positive": "llamada-positiva",
            "Neutral":  "llamada-neutral",
            "Negative": "llamada-negativa",
        }.get(sentiment, "llamada-completada")

        new_tags = list(set(current_tags + [sentiment_tag, "retell-llamada"]))
        update_contact_tags(contact_id, new_tags)
        logging.info(f"Tags actualizados: {sentiment_tag}")
    except Exception as e:
        logging.warning(f"Error actualizando tags: {e}")

    # 3. Score tag basado en calificación del lead
    try:
        from ghl_client import _headers, BASE_URL
        summary_lower = summary.lower()

        # Detectar proyectos por mes en el resumen
        score_tag = None
        if any(kw in summary_lower for kw in ["5 proyectos", "6 proyectos", "7 proyectos", "8 proyectos",
                                                "10 proyectos", "más de 5", "more than 5", "5 projects",
                                                "10 projects", "presupuesto", "budget", "tiene el dinero"]):
            score_tag = "score-alto"   # +20 pts — lead con presupuesto o volumen alto
        elif any(kw in summary_lower for kw in ["3 proyectos", "4 proyectos", "3 projects", "4 projects",
                                                  "quiere escalar", "wants to grow", "más clientes", "more leads"]):
            score_tag = "score-medio"  # lead calificado base
        elif sentiment in ("Negative",) or any(kw in summary_lower for kw in ["no le interesa", "not interested",
                                                                                "muy ocupado", "no tiene tiempo"]):
            score_tag = "score-bajo"

        if score_tag:
            r_sc = req.get(f"{BASE_URL}/contacts/{contact_id}", headers=_headers())
            sc_tags = r_sc.json().get("contact", {}).get("tags", []) if r_sc.ok else []
            update_contact_tags(contact_id, list(set(sc_tags + [score_tag])))
            logging.info(f"Score tag agregado: {score_tag}")
    except Exception as e:
        logging.warning(f"Error agregando score tag: {e}")

    # 4. Detectar cita confirmada → tag Cita_Confirmada_IA
    appt_confirmed = _appointment_confirmed(summary, language)
    if appt_confirmed:
        try:
            r2 = req.get(f"{BASE_URL}/contacts/{contact_id}", headers=_headers())
            current_tags2 = r2.json().get("contact", {}).get("tags", []) if r2.ok else []
            if "Cita_Confirmada_IA" not in current_tags2:
                update_contact_tags(contact_id, list(set(current_tags2 + ["Cita_Confirmada_IA"])))
                logging.info(f"Tag 'Cita_Confirmada_IA' agregado a {contact_id}")
        except Exception as e:
            logging.warning(f"Error agregando tag Cita_Confirmada_IA: {e}")

    # 4. Si sentimiento positivo → mover a HOT Lead
    moved = False
    if sentiment == "Positive":
        moved = _move_to_hot_lead(contact_id)

    return {
        "status":              "ok",
        "negocio":             nombre,
        "ciudad":              ciudad,
        "contact_id":          contact_id,
        "sentiment":           sentiment,
        "score_tag":           score_tag if 'score_tag' in dir() else None,
        "recording_saved":     bool(recording_url),
        "appointment_confirmed": appt_confirmed,
        "moved_to_hot":        moved,
    }


# ── Rutas Flask ─────────────────────────────────────────────

@app.route("/retell-webhook", methods=["POST"])
def retell_webhook():
    raw_body   = request.get_data()
    header_sig = request.headers.get("x-retell-signature", "")

    if not _verify_signature(raw_body, header_sig):
        logging.warning(f"Firma inválida — request rechazado | sig: {header_sig[:20]}...")
        return jsonify({"error": "Invalid signature"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    event = payload.get("event", "")
    logging.info(f"Webhook recibido: {event}")

    if event == "call_ended":
        result = _process_call_ended(payload)
        return jsonify(result), 200

    # Otros eventos — acusar recibo sin procesar
    logging.info(f"Evento '{event}' recibido pero no procesado")
    return jsonify({"status": "ignored", "event": event}), 200


def _cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

@app.route("/web-lead-trigger", methods=["POST", "OPTIONS"])
def web_lead_trigger():
    """
    Recibe el formulario HTML de multivenzadigital.com y:
      1. Crea o actualiza el contacto en GHL (upsert por email/teléfono)
      2. Verifica anti-duplicado (no llamar si ya tiene cita o fue contactado)
      3. Crea Oportunidad en etapa 'Nuevo Lead' si no existe
      4. Dispara llamada Retell AI (en hilo separado para responder 200 rápido)
    """
    if request.method == "OPTIONS":
        return _cors(jsonify({}))

    try:
        data = request.get_json(force=True)
    except Exception:
        return _cors(jsonify({"error": "Invalid JSON"}))

    phone    = data.get("phone", "").strip()
    nombre   = data.get("nombre", "").strip() or "amigo"
    email    = data.get("email", "").strip()
    ciudad   = data.get("ciudad", "").strip()
    language = data.get("language", "es").strip().lower()

    if not phone:
        return _cors(jsonify({"error": "phone es requerido"}))

    # ── 1. GHL: crear o actualizar contacto (sync, ~300ms) ───
    contact_id    = ""
    existing_tags = []
    try:
        contact_id, existing_tags = _ghl_upsert_web_lead(phone, nombre, email, ciudad, language)
    except Exception as e:
        logging.warning(f"web-lead-trigger: GHL upsert falló — {e}")

    # ── 2. Anti-duplicado ────────────────────────────────────
    SKIP_TAGS = {"retell-llamada", "Cita_Confirmada_IA"}
    matched = SKIP_TAGS & set(existing_tags)
    if matched:
        logging.info(f"web-lead-trigger: omitido — tags previos: {matched}")
        return _cors(jsonify({"status": "skipped", "reason": f"tags: {matched}"}))

    if not RETELL_API_KEY or not RETELL_AGENT_ID or not RETELL_FROM_NUMBER:
        logging.error("web-lead-trigger: faltan credenciales Retell en .env")
        return _cors(jsonify({"error": "Retell no configurado"}))

    # ── 3. Saludo OUTBOUND — Layla se presenta por nombre ──────
    # El agente OUTBOUND usa este begin_message personalizado.
    # Sin variables {{}} — el Global Prompt de Retell las leía literalmente.
    if language == "en":
        begin_message = (
            "Hi! I'm Layla with MultiVenza Digital, calling from Minnesota. "
            "We're reaching out because you requested a free demo on our website a moment ago. "
            "Am I speaking with the business owner?"
        )
    else:
        begin_message = (
            "¡Hola! Soy Layla de MultiVenza Digital, llamando desde Minnesota. "
            "Le contactamos porque solicitó una demo gratuita en nuestra página hace un momento. "
            "¿Hablo con el dueño del negocio?"
        )

    logging.info(f"web-lead-trigger: {full_name} ({phone}) | idioma: {language} | contact: {contact_id}")

    # ── 5. Operaciones pesadas en hilo separado ──────────────
    def _async_work():
        # Crear oportunidad en 'Nuevo Lead'
        if contact_id:
            _ghl_create_opportunity_if_needed(contact_id, nombre)

        # Disparar llamada Retell con first_name / last_name como dynamic variables
        try:
            result  = _fire_retell_call(
                to_number     = phone,
                contact_id    = contact_id,
                nombre        = nombre,
                ciudad        = ciudad,
                language      = language,
                begin_message = begin_message,
                email         = email,
                first_name    = first_name,
                last_name     = last_name,
            )
            call_id = result.get("call_id", "")
            logging.info(f"web-lead-trigger [async]: llamada iniciada — call_id: {call_id}")
        except Exception as e:
            logging.error(f"web-lead-trigger [async]: error Retell — {e}")

    import threading
    threading.Thread(target=_async_work, daemon=True).start()

    return _cors(jsonify({"status": "ok", "contact_id": contact_id, "message": "call_queued"}))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "retell-webhook"}), 200


# ── Entry point ─────────────────────────────────────────────

if __name__ == "__main__":
    if not RETELL_SECRET:
        logging.warning("RETELL_WEBHOOK_SECRET no está en .env — el servidor correrá SIN verificación de firma")

    port = int(os.getenv("PORT", 5050))
    logging.info(f"Retell Webhook Server iniciando en http://0.0.0.0:{port}")
    logging.info(f"  POST /retell-webhook     <- eventos de llamada de Retell AI")
    logging.info(f"  POST /web-lead-trigger   <- dispara llamada OUTBOUND desde formulario web")
    logging.info(f"  Agente OUTBOUND: {RETELL_AGENT_ID or 'NO CONFIGURADO'}")
    logging.info(f"  Agente INBOUND:  {RETELL_INBOUND_AGENT_ID or 'NO CONFIGURADO — configurar en Retell dashboard'}")
    logging.info(f"  Pipeline: {PIPELINE_NAME} -> '{HOT_STAGE_NAME}' (sentimiento positivo)")
    app.run(host="0.0.0.0", port=port, debug=False)
