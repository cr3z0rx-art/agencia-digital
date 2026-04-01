"""
============================================================
  Retell AI Client — Inicia llamadas outbound
  Asistente MultiVenza llama a leads usando número de Retell.

  ARQUITECTURA DE NÚMEROS (importante):
  ┌─────────────────────────────────────────────────────┐
  │  RETELL_NUMBER  →  hace las llamadas AI outbound    │
  │  GHL +14783752006  →  SMS, WhatsApp, callbacks      │
  └─────────────────────────────────────────────────────┘
  El número de GHL NO puede ser el caller ID en Retell
  sin SIP trunk propio. GHL no expone su Twilio subyacente.
  Solución: comprar número en Retell (~$1/mes) y usarlo
  solo para llamadas. Los callbacks llegan a GHL y se
  graban automáticamente si tienes Call Recording activo.

  .env requerido:
    RETELL_API_KEY=key_...
    RETELL_AGENT_ID=agent_...
    RETELL_NUMBER=+1XXXXXXXXXX   (número comprado en Retell Dashboard)
    GHL_PHONE_NUMBER=+14783752006 (número GHL — SMS/WhatsApp/callbacks)

  USO:
    python ghl-integration/retell_client.py --phone +17635550000 --contact-id abc123 --nombre "Garcia Roofing" --ciudad Minneapolis
    python ghl-integration/retell_client.py --csv leads/leads_latinos_usa.csv --limit 5
    python ghl-integration/retell_client.py --csv leads/leads_latinos_usa.csv --limit 5 --dry-run
============================================================
"""

import os
import sys
import csv
import time
import logging
import argparse
import requests
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ── Path setup ─────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GHL_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(ROOT / ".env")

# ── Config ─────────────────────────────────────────────────
RETELL_API_KEY     = os.getenv("RETELL_API_KEY", "")
RETELL_AGENT_ID    = os.getenv("RETELL_AGENT_ID", "")
RETELL_FROM_NUMBER = os.getenv("RETELL_NUMBER", "")      # número comprado en Retell
GHL_CALLBACK_NUMBER = os.getenv("GHL_PHONE_NUMBER", "")  # +14783752006 — SMS/WhatsApp/callbacks

RETELL_BASE_URL   = "https://api.retellai.com"
CALL_DELAY_SEC    = 5   # segundos entre llamadas para no saturar

# ── Logging ────────────────────────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
RUN_TS  = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"retell_calls_{RUN_TS}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# ── Log CSV ────────────────────────────────────────────────
CALL_LOG_PATH    = LOG_DIR / "retell_call_log.csv"
CALL_LOG_HEADERS = ["fecha", "nombre", "ciudad", "phone", "contact_id",
                    "call_id", "resultado", "error"]

def _write_call_log(row: dict):
    exists = CALL_LOG_PATH.exists()
    with open(CALL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CALL_LOG_HEADERS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


# ── API de Retell ───────────────────────────────────────────

def _retell_headers() -> dict:
    return {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type":  "application/json",
    }


def create_call(
    to_number:  str,
    contact_id: str,
    nombre:     str = "",
    ciudad:     str = "",
) -> dict:
    """
    Inicia una llamada outbound via Retell AI.

    Retell llama a `to_number` con el agente configurado en RETELL_AGENT_ID.
    El metadata se pasa al webhook al terminar la llamada.

    Retorna el objeto call de Retell con call_id, status, etc.
    """
    url     = f"{RETELL_BASE_URL}/v2/create-phone-call"
    payload = {
        "from_number": RETELL_FROM_NUMBER,
        "to_number":   to_number,
        "agent_id":    RETELL_AGENT_ID,
        "metadata": {
            "contact_id": contact_id,
            "nombre":     nombre,
            "ciudad":     ciudad,
        },
        "retell_llm_dynamic_variables": {
            "nombre_negocio":   nombre,
            "ciudad":           ciudad,
            "numero_callback":  GHL_CALLBACK_NUMBER,  # el agente puede decirle al lead este número
        },
    }

    resp = requests.post(url, json=payload, headers=_retell_headers())

    if not resp.ok:
        raise Exception(f"{resp.status_code} — {resp.text[:300]}")

    return resp.json()


def get_call_status(call_id: str) -> dict:
    """Consulta el estado actual de una llamada en Retell."""
    url  = f"{RETELL_BASE_URL}/v2/get-call/{call_id}"
    resp = requests.get(url, headers=_retell_headers())
    resp.raise_for_status()
    return resp.json()


# ── Verificación de consentimiento SMS / DNC ───────────────

def check_sms_consent(contact_id: str) -> tuple[bool, str]:
    """
    Verifica si un contacto en GHL tiene el tag 'DNC' (Do Not Call/Contact).

    Retorna:
      (True,  "ok")         — puede ser llamado
      (False, "DNC")        — tiene tag DNC, saltarse
      (False, "api_error")  — no se pudo verificar, saltar por precaución

    Uso legal: nunca llamar a contactos con DNC antes de tener consentimiento
    explícito. Parte del cumplimiento TCPA + A2P 10DLC.
    """
    from ghl_client import _headers, BASE_URL

    try:
        resp = requests.get(f"{BASE_URL}/contacts/{contact_id}", headers=_headers())
        if not resp.ok:
            logging.warning(f"  check_sms_consent: no se pudo verificar {contact_id} ({resp.status_code}) — saltando")
            return False, "api_error"

        tags = resp.json().get("contact", {}).get("tags", [])
        tags_lower = [t.lower() for t in tags]

        if "dnc" in tags_lower:
            logging.info(f"  SKIP {contact_id} — tag DNC encontrado")
            return False, "DNC"

        return True, "ok"

    except Exception as e:
        logging.warning(f"  check_sms_consent error: {e} — saltando por precaución")
        return False, "api_error"


# ── Normalización de teléfono ───────────────────────────────

def _normalize_phone(phone: str) -> str:
    import re
    if not phone or str(phone).lower() in ("nan", ""):
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return phone


# ── Lógica de llamada individual ────────────────────────────

def call_lead(
    phone:      str,
    contact_id: str,
    nombre:     str,
    ciudad:     str,
    dry_run:    bool = False,
) -> tuple[bool, str]:
    """
    Inicia la llamada a un lead. Retorna (éxito, call_id o error).
    """
    phone = _normalize_phone(phone)
    if not phone:
        logging.warning(f"  SKIP {nombre} — teléfono inválido")
        return False, "sin teléfono"

    if dry_run:
        logging.info(f"  [DRY RUN] Llamaría a: {nombre} | {ciudad} | {phone} | contact: {contact_id}")
        return True, "dry-run"

    # Verificar consentimiento — saltar si tiene tag DNC
    if contact_id:
        allowed, reason = check_sms_consent(contact_id)
        if not allowed:
            return False, f"bloqueado ({reason})"

    try:
        result  = create_call(phone, contact_id, nombre, ciudad)
        call_id = result.get("call_id", "")
        logging.info(f"  LLAMADA INICIADA | {nombre} | {phone} | call_id: {call_id}")
        return True, call_id
    except Exception as e:
        logging.error(f"  ERROR {nombre}: {e}")
        return False, str(e)


# ── Procesamiento desde CSV ─────────────────────────────────

def call_from_csv(csv_path: Path, limit: int = 0, dry_run: bool = False):
    """
    Lee leads del CSV y llama a los HOT latinos que:
    - tienen ghl_uploaded=YES (ya están en GHL con contact_id)
    - tienen retell_called=NO (no han sido llamados aún)
    - tienen teléfono válido
    """
    if not csv_path.exists():
        logging.error(f"CSV no encontrado: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # Agregar columna retell_called si no existe
    if "retell_called" not in df.columns:
        df["retell_called"] = "NO"

    # Agregar columna retell_call_id si no existe
    if "retell_call_id" not in df.columns:
        df["retell_call_id"] = ""

    # Filtro: subidos a GHL + no llamados + HOT
    mask = (
        (df["ghl_uploaded"].str.upper() == "YES") &
        (df["retell_called"].str.upper() == "NO") &
        (df["status"].str.upper() == "HOT")
    )
    pending = df[mask].copy()

    if limit:
        pending = pending.head(limit)

    logging.info(f"CSV: {len(df)} total | {len(pending)} pendientes para llamar")

    if pending.empty:
        logging.info("No hay leads pendientes para llamar.")
        return

    called_ids = []
    ok_count   = 0
    fail_count = 0

    for idx, row in pending.iterrows():
        nombre     = str(row.get("name", "")).strip()
        ciudad     = str(row.get("city", "")).strip()
        phone      = str(row.get("phone", "")).strip()
        contact_id = str(row.get("ghl_contact_id", "")).strip()

        logging.info(f"[{idx}] {nombre} | {ciudad} | {phone}")

        ok, call_id = call_lead(phone, contact_id, nombre, ciudad, dry_run=dry_run)

        _write_call_log({
            "fecha":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nombre":     nombre,
            "ciudad":     ciudad,
            "phone":      phone,
            "contact_id": contact_id,
            "call_id":    call_id if ok else "",
            "resultado":  "OK" if ok else "ERROR",
            "error":      "" if ok else call_id,
        })

        if ok:
            ok_count += 1
            called_ids.append((idx, call_id))
        else:
            fail_count += 1

        if not dry_run and ok:
            time.sleep(CALL_DELAY_SEC)

    # Marcar como llamados en el CSV
    if called_ids and not dry_run:
        for idx, call_id in called_ids:
            df.loc[idx, "retell_called"]  = "YES"
            df.loc[idx, "retell_call_id"] = call_id
        df.to_csv(csv_path, index=False)
        logging.info(f"CSV actualizado: {len(called_ids)} marcados retell_called=YES")

    print(f"\n{'='*50}")
    print(f"  Llamadas iniciadas : {ok_count}")
    print(f"  Fallidas           : {fail_count}")
    print(f"  Log CSV            : logs/retell_call_log.csv")
    print(f"{'='*50}\n")


# ── Validación de credenciales ──────────────────────────────

def validate_retell_credentials() -> bool:
    if not RETELL_API_KEY:
        logging.error("RETELL_API_KEY no está en .env")
        return False
    if not RETELL_AGENT_ID:
        logging.error("RETELL_AGENT_ID no está en .env")
        return False
    if not RETELL_FROM_NUMBER:
        logging.error(
            "RETELL_NUMBER no está en .env\n"
            "  → Compra un número en Retell Dashboard (~$1/mes)\n"
            "  → Agrégalo al .env como RETELL_NUMBER=+1XXXXXXXXXX"
        )
        return False

    # Verificar que el agente existe
    url  = f"{RETELL_BASE_URL}/get-agent/{RETELL_AGENT_ID}"
    resp = requests.get(url, headers=_retell_headers())
    if not resp.ok:
        logging.error(f"Credenciales Retell inválidas: {resp.status_code}")
        return False

    name = resp.json().get("agent_name", "")
    logging.info(f"Retell conectado — Agente: '{name}'")

    # Verificar que GHL_PHONE_NUMBER está importado en Retell
    # Retell exige que el from_number sea un número comprado o importado en la cuenta.
    # Un número de GHL no puede usarse directamente — debe importarse via SIP trunk.
    # Docs: https://docs.retellai.com/deploy/twilio
    phone_url  = f"{RETELL_BASE_URL}/v2/list-phone-numbers"
    phone_resp = requests.get(phone_url, headers=_retell_headers())
    if phone_resp.ok:
        registered = [p.get("phone_number") for p in phone_resp.json()]
        if RETELL_FROM_NUMBER in registered:
            logging.info(f"Número {RETELL_FROM_NUMBER} registrado en Retell — OK")
        else:
            logging.warning(
                f"AVISO: {RETELL_FROM_NUMBER} NO está registrado en Retell.\n"
                f"  La llamada fallará con error 422.\n"
                f"  Opciones:\n"
                f"    1. Comprar un número en Retell Dashboard (~$2/mes)\n"
                f"    2. Importar via SIP trunk: https://docs.retellai.com/deploy/twilio\n"
                f"  Números registrados actualmente: {registered or '(ninguno)'}"
            )
            return False

    return True


# ── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Inicia llamadas Retell AI a leads de GHL")

    # Modo CSV
    parser.add_argument("--csv",        default="leads/leads_latinos_usa.csv")
    parser.add_argument("--limit",      type=int, default=0,
                        help="Máximo de llamadas a iniciar (0 = sin límite)")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Ver a quién llamaría sin hacer nada")

    # Modo contacto individual
    parser.add_argument("--phone",      help="Número a llamar (+1XXXXXXXXXX)")
    parser.add_argument("--contact-id", help="contact_id en GHL")
    parser.add_argument("--nombre",     default="", help="Nombre del negocio")
    parser.add_argument("--ciudad",     default="", help="Ciudad")

    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  Retell AI — Llamadas Outbound")
    print(f"  Agente : {RETELL_AGENT_ID or 'NO CONFIGURADO'}")
    print(f"  Desde  : {RETELL_FROM_NUMBER or 'NO CONFIGURADO'}")
    print(f"  Modo   : {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*50}\n")

    if not args.dry_run:
        if not validate_retell_credentials():
            sys.exit(1)

    # Modo llamada individual
    if args.phone:
        if not args.contact_id:
            logging.error("--contact-id es requerido con --phone")
            sys.exit(1)
        ok, call_id = call_lead(
            phone      = args.phone,
            contact_id = args.contact_id,
            nombre     = args.nombre,
            ciudad     = args.ciudad,
            dry_run    = args.dry_run,
        )
        if ok:
            print(f"  Llamada iniciada. call_id: {call_id}")
        else:
            print(f"  Error: {call_id}")
        return

    # Modo CSV
    call_from_csv(ROOT / args.csv, limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
