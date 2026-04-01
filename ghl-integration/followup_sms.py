"""
============================================================
  Follow-up SMS — Día 2 sin respuesta
  Lee logs/ghl_upload_log.csv, identifica contactos subidos
  hace 48h+ que no han avanzado de etapa "Nuevo Lead",
  y les envía un SMS de seguimiento.

  USO:
    python ghl-integration/followup_sms.py
    python ghl-integration/followup_sms.py --dry-run
    python ghl-integration/followup_sms.py --hours 24   (cambiar ventana de tiempo)

  AUTOMATIZACIÓN:
    Correr diariamente — GHL Workflow lo puede hacer con trigger
    o cron job externo.
============================================================
"""

import sys
import csv
import logging
import argparse
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GHL_DIR))

from dotenv import load_dotenv
load_dotenv()

from ghl_client import (
    BASE_URL, GHL_LOCATION_ID, _headers, _handle_rate_limit,
    validate_credentials, get_pipeline_by_name, get_stage_id,
)

# ── Config ────────────────────────────────────────────────
PIPELINE_NAME    = "Contratistas Latinos"
FOLLOWUP_STAGE   = "Nuevo Lead"       # solo contactar si siguen aquí
ADVANCE_TO_STAGE = "Contactado"       # mover a esta etapa tras el SMS
FROM_PHONE       = "+16125996825"     # número GHL de la agencia
DELAY_HOURS      = 48                 # horas sin respuesta antes del SMS
DELAY_BETWEEN    = 2.0                # segundos entre envíos

LOG_DIR      = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
RUN_TS       = datetime.now().strftime("%Y%m%d_%H%M%S")
text_log     = LOG_DIR / f"followup_sms_{RUN_TS}.log"
SMS_LOG_PATH = LOG_DIR / "followup_sms_log.csv"
SMS_LOG_COLS = ["fecha", "nombre", "telefono", "idioma", "resultado", "error"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(text_log, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# ── Mensajes SMS por idioma ───────────────────────────────

SMS_TEMPLATES = {
    "Español": (
        "Hola, soy Keyner de MultiVenza Digital. "
        "Le envié un email hace 2 días sobre cómo conseguir más clientes para su negocio en Google. "
        "¿Tuvo oportunidad de verlo? Con gusto le explico en 10 minutos. "
        "Responda este mensaje o llámeme. — Keyner"
    ),
    "Inglés": (
        "Hi, this is Keyner from MultiVenza Digital. "
        "I emailed you 2 days ago about getting more customers through Google. "
        "Did you get a chance to read it? Happy to walk you through it in 10 minutes. "
        "Reply here or give me a call. — Keyner"
    ),
    "Spanglish": (
        "Hi! Soy Keyner de MultiVenza Digital. "
        "Le mandé un email sobre cómo crecer su negocio online. "
        "¿Lo vio? Solo toma 10 minutos — reply aquí o llámeme. — Keyner"
    ),
}


# ── GHL API helpers ───────────────────────────────────────

def send_sms(contact_id: str, phone: str, message: str) -> dict:
    """Envía SMS a un contacto vía GHL."""
    url = f"{BASE_URL}/conversations/messages"
    payload = {
        "type":       "SMS",
        "locationId": GHL_LOCATION_ID,
        "contactId":  contact_id,
        "message":    message,
        "fromNumber": FROM_PHONE,
        "toNumber":   phone,
    }
    for attempt in range(1, 4):
        resp = requests.post(url, json=payload, headers=_headers())
        if _handle_rate_limit(resp, attempt):
            continue
        if not resp.ok:
            raise Exception(f"{resp.status_code} — {resp.text[:300]}")
        return resp.json()
    raise Exception("Sin respuesta válida tras 3 intentos")


def get_opportunity_by_contact(contact_id: str) -> dict | None:
    """Busca la oportunidad activa de un contacto en el pipeline."""
    url = f"{BASE_URL}/opportunities/search"
    params = {"location_id": GHL_LOCATION_ID, "contact_id": contact_id}
    resp = requests.get(url, params=params, headers=_headers())
    if not resp.ok:
        return None
    opps = resp.json().get("opportunities", [])
    return opps[0] if opps else None


def move_to_stage(opportunity_id: str, pipeline_id: str, stage_id: str):
    """Mueve una oportunidad a otra etapa del pipeline."""
    url = f"{BASE_URL}/opportunities/{opportunity_id}"
    payload = {"pipelineId": pipeline_id, "pipelineStageId": stage_id}
    resp = requests.put(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def write_sms_log(row: dict):
    file_exists = SMS_LOG_PATH.exists()
    with open(SMS_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SMS_LOG_COLS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ── Cargar leads subidos hace 48h+ ────────────────────────

def load_pending_followup(hours: int) -> list[dict]:
    """
    Lee ghl_upload_log.csv y retorna leads subidos hace >= hours
    que aún no han recibido SMS (no están en followup_sms_log.csv).
    """
    upload_log = LOG_DIR / "ghl_upload_log.csv"
    if not upload_log.exists():
        logging.warning("No se encontró logs/ghl_upload_log.csv")
        return []

    cutoff = datetime.now() - timedelta(hours=hours)

    # Cargar leads subidos
    uploaded = []
    with open(upload_log, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("resultado", "") != "OK":
                continue
            try:
                ts = datetime.strptime(row["fecha"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if ts <= cutoff:
                uploaded.append(row)

    # Cargar ya contactados por SMS
    already_sms = set()
    if SMS_LOG_PATH.exists():
        with open(SMS_LOG_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("resultado") == "OK":
                    already_sms.add(row["telefono"])

    pending = [r for r in uploaded if r.get("telefono", "") not in already_sms]
    return pending


# ── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SMS follow-up día 2")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--hours",   type=int, default=DELAY_HOURS,
                        help=f"Horas sin respuesta (default: {DELAY_HOURS})")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Follow-up SMS — día 2")
    print(f"  Ventana:  leads subidos hace ≥ {args.hours}h sin SMS")
    print(f"  Pipeline: {PIPELINE_NAME} / {FOLLOWUP_STAGE} → {ADVANCE_TO_STAGE}")
    print(f"  Modo:     {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    if not args.dry_run:
        if not validate_credentials():
            sys.exit(1)

    # Obtener IDs de etapas
    pipeline_id = contacted_stage_id = None
    if not args.dry_run:
        pipeline = get_pipeline_by_name(PIPELINE_NAME)
        if pipeline:
            pipeline_id       = pipeline["id"]
            contacted_stage_id = get_stage_id(pipeline, ADVANCE_TO_STAGE)

    pending = load_pending_followup(args.hours)
    logging.info(f"Leads pendientes de follow-up: {len(pending)}")

    if not pending:
        print("  No hay leads que necesiten follow-up todavía.")
        return

    sent = failed = 0

    for lead in pending:
        name    = lead.get("nombre", "")[:40]
        phone   = lead.get("telefono", "")
        lang    = lead.get("idioma", "Inglés") if "idioma" in lead else "Inglés"
        cid     = lead.get("ghl_contact_id", "")

        # Determinar idioma por nombre si la columna no existe
        if "idioma" not in lead:
            lang = "Español"  # conservador — mejor español que inglés con latinos

        sms_text = SMS_TEMPLATES.get(lang, SMS_TEMPLATES["Inglés"])

        print(f"  {name} | {phone} | {lang}")

        if args.dry_run:
            logging.info(f"  [DRY RUN] SMS a {name}: {sms_text[:80]}...")
            sent += 1
            continue

        try:
            send_sms(cid, phone, sms_text)
            sent += 1
            logging.info(f"  SMS enviado → {phone}")

            # Mover etapa en pipeline
            if pipeline_id and contacted_stage_id and cid:
                opp = get_opportunity_by_contact(cid)
                if opp:
                    move_to_stage(opp["id"], pipeline_id, contacted_stage_id)
                    logging.info(f"  Etapa → {ADVANCE_TO_STAGE}")

            write_sms_log({
                "fecha":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nombre":    name,
                "telefono":  phone,
                "idioma":    lang,
                "resultado": "OK",
                "error":     "",
            })

        except Exception as e:
            failed += 1
            logging.error(f"  ERROR {name}: {e}")
            write_sms_log({
                "fecha":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nombre":    name,
                "telefono":  phone,
                "idioma":    lang,
                "resultado": "ERROR",
                "error":     str(e)[:200],
            })

        time.sleep(DELAY_BETWEEN)

    print(f"\n{'='*60}")
    print(f"  SMS enviados : {sent}")
    print(f"  Fallidos     : {failed}")
    print(f"  Log          : logs/followup_sms_{RUN_TS}.log")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
