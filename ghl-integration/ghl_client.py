"""
GHL Client — Wrapper para la API de GoHighLevel v2
Documentación: https://highlevel.stoplight.io/docs/integrations

Requiere en .env:
    GHL_API_KEY=...
    GHL_LOCATION_ID=...
"""

import os
import time
import logging
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

GHL_API_KEY     = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")

BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"


def _headers():
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Version": API_VERSION,
        "Content-Type": "application/json",
    }


def _handle_rate_limit(response, attempt=1):
    """Espera y reintenta si GHL devuelve 429 (rate limit)."""
    if response.status_code == 429 and attempt <= 3:
        wait = 2 ** attempt
        logging.warning(f"Rate limit GHL — esperando {wait}s (intento {attempt})")
        time.sleep(wait)
        return True
    return False


# ── Contactos ──────────────────────────────────────────────

def create_contact(payload: dict) -> dict:
    """
    Crea un contacto en GHL.

    Payload mínimo:
        {
            "locationId": "...",
            "firstName": "...",
            "lastName": "...",
            "phone": "...",
            "email": "...",        # opcional pero necesario para enviar emails
            "tags": ["tag1", "tag2"],
        }

    Retorna el objeto contacto de GHL o lanza excepción.
    """
    url = f"{BASE_URL}/contacts/"
    payload["locationId"] = GHL_LOCATION_ID

    for attempt in range(1, 4):
        resp = requests.post(url, json=payload, headers=_headers())
        if _handle_rate_limit(resp, attempt):
            continue
        if not resp.ok:
            raise Exception(f"{resp.status_code} — {resp.text[:500]}")
        return resp.json().get("contact", resp.json())

    raise Exception(f"Sin respuesta válida tras 3 intentos")


def get_contact_by_phone(phone: str) -> dict | None:
    """
    Busca un contacto por teléfono. Retorna el contacto o None si no existe.
    Úsalo para evitar duplicados antes de crear o para resolver contact_id.
    """
    url = f"{BASE_URL}/contacts/"
    params = {"locationId": GHL_LOCATION_ID, "query": phone}

    resp = requests.get(url, params=params, headers=_headers())
    if not resp.ok:
        resp.raise_for_status()
    contacts = resp.json().get("contacts", [])
    return contacts[0] if contacts else None


def update_contact(contact_id: str, payload: dict) -> dict:
    """Actualiza campos de un contacto existente (email, tags, etc.)."""
    url = f"{BASE_URL}/contacts/{contact_id}"
    resp = requests.put(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def add_note_to_contact(contact_id: str, note_body: str) -> dict:
    """Agrega una nota de texto a un contacto existente."""
    url = f"{BASE_URL}/contacts/{contact_id}/notes"
    payload = {"body": note_body, "userId": ""}

    resp = requests.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def update_contact_with_call_data(
    contact_id: str,
    summary: str,
    recording_url: str = "",
) -> dict:
    """
    Sube el resumen y la grabación de una llamada de Retell AI a un contacto en GHL.

    Siempre crea una Nota con el resumen + grabación.
    Adicionalmente intenta actualizar el campo personalizado 'call_summary' si existe.

    Retorna el resultado de la Nota creada.
    """
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── 1. Siempre crear Nota ──────────────────────────────
    note_lines = [
        f"=== Resumen de llamada Retell AI ({now}) ===",
        "",
        summary,
    ]
    if recording_url:
        note_lines += ["", f"Grabacion: {recording_url}"]

    result = add_note_to_contact(contact_id, "\n".join(note_lines))
    logging.info(f"update_contact_with_call_data: nota creada ({contact_id})")

    # ── 2. Intentar campo personalizado (opcional) ─────────
    try:
        custom_value = summary
        if recording_url:
            custom_value += f"\n\nGrabacion: {recording_url}"
        url     = f"{BASE_URL}/contacts/{contact_id}"
        payload = {"customFields": [{"key": "call_summary", "field_value": custom_value}]}
        resp = requests.put(url, json=payload, headers=_headers())
        if resp.ok:
            logging.info(f"update_contact_with_call_data: campo personalizado OK ({contact_id})")
        else:
            logging.debug(
                f"update_contact_with_call_data: campo personalizado no disponible "
                f"({resp.status_code}) — solo nota"
            )
    except Exception as e:
        logging.debug(f"update_contact_with_call_data: campo personalizado error — {e}")

    return result


def update_contact_tags(contact_id: str, tags: list[str]) -> dict:
    """Reemplaza todos los tags de un contacto."""
    url = f"{BASE_URL}/contacts/{contact_id}"
    payload = {"tags": tags}

    resp = requests.put(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


# ── Pipelines / Oportunidades ──────────────────────────────

def get_pipelines() -> list[dict]:
    """Retorna todos los pipelines de la ubicación."""
    url = f"{BASE_URL}/opportunities/pipelines"
    params = {"locationId": GHL_LOCATION_ID}
    resp = requests.get(url, params=params, headers=_headers())
    resp.raise_for_status()
    return resp.json().get("pipelines", [])


def get_pipeline_by_name(pipeline_name: str) -> dict | None:
    """Busca un pipeline por nombre exacto. Retorna None si no existe."""
    pipelines = get_pipelines()
    for p in pipelines:
        if p.get("name", "").strip().lower() == pipeline_name.strip().lower():
            return p
    return None


def get_stage_id(pipeline: dict, stage_name: str) -> str | None:
    """Busca el ID de una etapa dentro de un pipeline por nombre."""
    for stage in pipeline.get("stages", []):
        if stage.get("name", "").strip().lower() == stage_name.strip().lower():
            return stage.get("id")
    return None


def get_opportunities_by_contact(contact_id: str) -> list[dict]:
    """
    Busca oportunidades existentes para un contacto en cualquier pipeline.
    Retorna lista vacía si no tiene ninguna.
    """
    url = f"{BASE_URL}/opportunities/search"
    params = {"location_id": GHL_LOCATION_ID, "contact_id": contact_id}
    resp = requests.get(url, params=params, headers=_headers())
    if not resp.ok:
        return []
    return resp.json().get("opportunities", [])


def create_opportunity(
    contact_id: str,
    pipeline_id: str,
    stage_id: str,
    name: str,
    status: str = "open",
    monetary_value: int = 0,
) -> dict:
    """
    Crea una oportunidad (agrega el contacto a una etapa del pipeline).

    status: "open" | "won" | "lost" | "abandoned"
    monetary_value: valor del deal en USD (setup fee)
    """
    url = f"{BASE_URL}/opportunities/"
    payload = {
        "locationId":    GHL_LOCATION_ID,
        "pipelineId":    pipeline_id,
        "pipelineStageId": stage_id,
        "contactId":     contact_id,
        "name":          name,
        "status":        status,
        "monetaryValue": monetary_value,
    }
    resp = requests.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json().get("opportunity", resp.json())


# ── Validación de credenciales ──────────────────────────────

GHL_FROM_EMAIL = os.getenv("GHL_FROM_EMAIL", "")
GHL_FROM_NAME  = os.getenv("GHL_FROM_NAME",  "Keyner Guerrero | MultiVenza Digital")

SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))


def send_email_smtp(to_email: str, subject: str, html_body: str) -> None:
    """
    Envía email vía SMTP (Gmail/Google Workspace).
    Más confiable que GHL API — llega directo al inbox.

    Requiere en .env:
        SMTP_EMAIL=hello@multivenzadigital.com
        SMTP_PASSWORD=xxxx xxxx xxxx xxxx  (App Password de Google)
        SMTP_HOST=smtp.gmail.com
        SMTP_PORT=587
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise Exception("SMTP_EMAIL o SMTP_PASSWORD no están en .env")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{GHL_FROM_NAME} <{SMTP_EMAIL}>"
    msg["To"]      = to_email

    msg.attach(MIMEText(html_body.replace("<br>", "\n"), "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        logging.info(f"SMTP OK → {to_email}")


def send_email(contact_id: str, email_to: str, subject: str, html_body: str) -> dict:
    """
    Envía un email a un contacto vía GHL Conversations API.

    Requiere en .env:
        GHL_FROM_EMAIL=hello@multivenzadigital.com  (dirección conectada en GHL Email Services)
        GHL_FROM_NAME=Keyner | MultiVenza Digital    (nombre del remitente)

    El email FROM debe estar conectado en GHL → Settings → Email Services.
    """
    if not GHL_FROM_EMAIL:
        raise Exception(
            "GHL_FROM_EMAIL no está en .env. "
            "Agrega: GHL_FROM_EMAIL=hello@multivenzadigital.com"
        )

    url = f"{BASE_URL}/conversations/messages"
    payload = {
        "type":          "Email",
        "locationId":    GHL_LOCATION_ID,
        "contactId":     contact_id,
        "emailTo":       email_to,
        "emailFrom":     GHL_FROM_EMAIL,
        "emailFromName": GHL_FROM_NAME,
        "subject":       subject,
        "html":          html_body,
        "message":       html_body,
    }

    for attempt in range(1, 4):
        resp = requests.post(url, json=payload, headers=_headers())
        if _handle_rate_limit(resp, attempt):
            continue
        if not resp.ok:
            raise Exception(f"{resp.status_code} — {resp.text[:500]}")
        return resp.json()

    raise Exception("Sin respuesta válida al enviar email tras 3 intentos")


def validate_credentials() -> bool:
    """Verifica que las credenciales de GHL sean válidas."""
    if not GHL_API_KEY or not GHL_LOCATION_ID:
        logging.error("GHL_API_KEY o GHL_LOCATION_ID no están en .env")
        return False

    url = f"{BASE_URL}/locations/{GHL_LOCATION_ID}"
    resp = requests.get(url, headers=_headers())

    if resp.status_code == 200:
        name = resp.json().get("location", {}).get("name", "Unknown")
        logging.info(f"GHL conectado: {name}")
        return True

    logging.error(f"Credenciales inválidas: {resp.status_code} — {resp.text[:200]}")
    return False


def list_pipelines_diagnostic():
    """Imprime todos los pipelines y sus etapas con nombres exactos."""
    print("\n" + "="*60)
    print("  PIPELINES EN GHL")
    print("="*60)
    try:
        pipelines = get_pipelines()
        if not pipelines:
            print("  No se encontraron pipelines.")
            return
        for p in pipelines:
            print(f"\n  Pipeline: \"{p.get('name')}\"  (id: {p.get('id')})")
            for stage in p.get("stages", []):
                print(f"    Etapa: \"{stage.get('name')}\"  (id: {stage.get('id')})")
    except Exception as e:
        print(f"  ERROR: {e}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    list_pipelines_diagnostic()
