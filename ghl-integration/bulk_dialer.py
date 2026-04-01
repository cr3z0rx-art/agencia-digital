"""
============================================================
  bulk_dialer.py — Llamadas masivas controladas a leads HOT
  Llama a los primeros N leads HOT de leads_latinos_usa.csv
  usando Retell AI. Busca el contact_id en GHL por teléfono.

  PREREQUISITO:
    - Leads deben estar en GHL (ghl_uploaded=YES)
    - RETELL_API_KEY, RETELL_AGENT_ID, RETELL_NUMBER en .env
    - Webhook server corriendo y registrado en Retell Dashboard

  USO:
    # Prueba controlada — primeros 5 leads HOT
    python ghl-integration/bulk_dialer.py --limit 5 --dry-run
    python ghl-integration/bulk_dialer.py --limit 5

    # CSV distinto
    python ghl-integration/bulk_dialer.py --csv leads/leads_minneapolis.csv --limit 10
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

from ghl_client import get_contact_by_phone

# ── Config ─────────────────────────────────────────────────
RETELL_API_KEY     = os.getenv("RETELL_API_KEY", "")
RETELL_AGENT_ID    = os.getenv("RETELL_AGENT_ID", "")
RETELL_FROM_NUMBER = os.getenv("RETELL_NUMBER", "")
GHL_CALLBACK_NUMBER = os.getenv("GHL_PHONE_NUMBER", "")

RETELL_BASE_URL = "https://api.retellai.com"
CALL_DELAY_SEC  = 8    # segundos entre llamadas para no saturar Retell

# ── Logging ────────────────────────────────────────────────
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
RUN_TS  = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"bulk_dialer_{RUN_TS}.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# ── Log CSV ────────────────────────────────────────────────
DIAL_LOG_PATH    = LOG_DIR / "bulk_dialer_log.csv"
DIAL_LOG_HEADERS = ["fecha", "nombre", "ciudad", "phone", "contact_id",
                    "call_id", "resultado", "error"]

def _write_dial_log(row: dict):
    exists = DIAL_LOG_PATH.exists()
    with open(DIAL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DIAL_LOG_HEADERS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


# ── Helpers ────────────────────────────────────────────────

def _retell_headers() -> dict:
    return {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type":  "application/json",
    }


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


def _lookup_contact_id(phone: str) -> str:
    """Busca el contact_id en GHL por número de teléfono."""
    try:
        contact = get_contact_by_phone(phone)
        if contact:
            return contact.get("id", "")
    except Exception as e:
        logging.warning(f"  lookup_contact_id({phone}): {e}")
    return ""


def _is_dnc(contact_id: str) -> bool:
    """Retorna True si el contacto tiene el tag 'DNC' en GHL."""
    if not contact_id:
        return False
    try:
        from ghl_client import _headers, BASE_URL
        resp = requests.get(f"{BASE_URL}/contacts/{contact_id}", headers=_headers())
        if resp.ok:
            tags = [t.lower() for t in resp.json().get("contact", {}).get("tags", [])]
            return "dnc" in tags
    except Exception as e:
        logging.warning(f"  _is_dnc({contact_id}): {e} — saltando por precaución")
        return True  # saltar si no podemos verificar
    return False


def _create_retell_call(to_number: str, contact_id: str, nombre: str, ciudad: str) -> dict:
    """Inicia la llamada via Retell AI."""
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
            "nombre_negocio":  nombre,
            "ciudad":          ciudad,
            "numero_callback": GHL_CALLBACK_NUMBER,
        },
    }
    resp = requests.post(url, json=payload, headers=_retell_headers())
    if not resp.ok:
        raise Exception(f"{resp.status_code} — {resp.text[:300]}")
    return resp.json()


# ── Validación ─────────────────────────────────────────────

def validate() -> bool:
    missing = []
    if not RETELL_API_KEY:     missing.append("RETELL_API_KEY")
    if not RETELL_AGENT_ID:    missing.append("RETELL_AGENT_ID")
    if not RETELL_FROM_NUMBER: missing.append("RETELL_NUMBER")
    if missing:
        logging.error(f"Faltan en .env: {', '.join(missing)}")
        return False

    resp = requests.get(f"{RETELL_BASE_URL}/get-agent/{RETELL_AGENT_ID}",
                        headers=_retell_headers())
    if not resp.ok:
        logging.error(f"RETELL_AGENT_ID invalido: {resp.status_code}")
        return False

    name = resp.json().get("agent_name", "")
    logging.info(f"Retell OK — Agente: '{name}' | Desde: {RETELL_FROM_NUMBER}")
    return True


# ── Lógica principal ────────────────────────────────────────

def dial_leads(csv_path: Path, limit: int = 5, dry_run: bool = False):
    """
    Lee los primeros `limit` leads HOT del CSV y los llama.

    Filtros aplicados:
      - status = HOT
      - ghl_uploaded = YES  (ya están en GHL)
      - teléfono válido

    Si retell_called no existe en el CSV, la columna se agrega automáticamente.
    """
    if not csv_path.exists():
        logging.error(f"CSV no encontrado: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    if "retell_called" not in df.columns:
        df["retell_called"] = "NO"
    if "retell_call_id" not in df.columns:
        df["retell_call_id"] = ""
    if "ghl_contact_id" not in df.columns:
        df["ghl_contact_id"] = ""

    mask = (
        (df["status"].str.upper() == "HOT") &
        (df["ghl_uploaded"].str.upper() == "YES") &
        (df["retell_called"].str.upper() != "YES")
    )
    pending = df[mask].copy().head(limit)

    logging.info(f"CSV: {len(df)} total | {len(pending)} seleccionados para esta tanda")

    if pending.empty:
        logging.info("No hay leads pendientes.")
        return

    ok_count   = 0
    fail_count = 0
    called_ids = []   # (df_idx, call_id, contact_id)

    for idx, row in pending.iterrows():
        nombre = str(row.get("name", "")).strip()
        ciudad = str(row.get("city", "")).strip()
        phone  = _normalize_phone(str(row.get("phone", "")))

        print(f"\n[{ok_count + fail_count + 1}/{len(pending)}] {nombre} | {ciudad} | {phone}")

        if not phone:
            logging.warning(f"  SKIP — telefono invalido")
            fail_count += 1
            _write_dial_log({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "nombre": nombre, "ciudad": ciudad, "phone": phone,
                             "contact_id": "", "call_id": "", "resultado": "SKIP",
                             "error": "sin telefono"})
            continue

        # Buscar contact_id en GHL si no está en el CSV
        contact_id = str(row.get("ghl_contact_id", "")).strip()
        if not contact_id or contact_id.lower() == "nan":
            logging.info(f"  Buscando contact_id en GHL por telefono...")
            contact_id = _lookup_contact_id(phone)
            if contact_id:
                df.loc[idx, "ghl_contact_id"] = contact_id
                logging.info(f"  contact_id encontrado: {contact_id}")
            else:
                logging.warning(f"  No se encontro el contacto en GHL — llamando sin contact_id")

        if dry_run:
            logging.info(f"  [DRY RUN] Llamaria a: {nombre} | {ciudad} | {phone} | id: {contact_id or '(buscando en vivo)'}")
            ok_count += 1
            continue

        # Verificar DNC
        if contact_id and _is_dnc(contact_id):
            logging.info(f"  SKIP — tag DNC encontrado")
            fail_count += 1
            _write_dial_log({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "nombre": nombre, "ciudad": ciudad, "phone": phone,
                             "contact_id": contact_id, "call_id": "",
                             "resultado": "SKIP", "error": "DNC"})
            continue

        # Iniciar llamada
        try:
            result  = _create_retell_call(phone, contact_id, nombre, ciudad)
            call_id = result.get("call_id", "")
            logging.info(f"  LLAMADA INICIADA — call_id: {call_id}")
            ok_count += 1
            called_ids.append((idx, call_id, contact_id))
            _write_dial_log({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "nombre": nombre, "ciudad": ciudad, "phone": phone,
                             "contact_id": contact_id, "call_id": call_id,
                             "resultado": "OK", "error": ""})
            time.sleep(CALL_DELAY_SEC)
        except Exception as e:
            logging.error(f"  ERROR: {e}")
            fail_count += 1
            _write_dial_log({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "nombre": nombre, "ciudad": ciudad, "phone": phone,
                             "contact_id": contact_id, "call_id": "",
                             "resultado": "ERROR", "error": str(e)[:200]})

    # Actualizar CSV
    if called_ids and not dry_run:
        for idx, call_id, contact_id in called_ids:
            df.loc[idx, "retell_called"]  = "YES"
            df.loc[idx, "retell_call_id"] = call_id
            if contact_id:
                df.loc[idx, "ghl_contact_id"] = contact_id
        df.to_csv(csv_path, index=False)
        logging.info(f"CSV actualizado: {len(called_ids)} marcados retell_called=YES")

    print(f"\n{'='*50}")
    print(f"  Llamadas iniciadas : {ok_count}")
    print(f"  Fallidas / saltadas: {fail_count}")
    print(f"  Log detallado      : logs/bulk_dialer_{RUN_TS}.log")
    print(f"  Log CSV            : logs/bulk_dialer_log.csv")
    print(f"{'='*50}\n")


# ── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Llama a los primeros N leads HOT via Retell AI"
    )
    parser.add_argument("--csv",     default="leads/leads_latinos_usa.csv",
                        help="Ruta al CSV de leads")
    parser.add_argument("--limit",   type=int, default=5,
                        help="Maximo de llamadas a iniciar (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simular sin hacer llamadas reales")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  Bulk Dialer — MultiVenza Digital")
    print(f"  CSV    : {args.csv}")
    print(f"  Limite : {args.limit} llamadas")
    print(f"  Modo   : {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*50}\n")

    if not args.dry_run:
        if not validate():
            sys.exit(1)

    dial_leads(ROOT / args.csv, limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
