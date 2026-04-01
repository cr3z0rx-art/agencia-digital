"""
============================================================
  test_call.py — Llamada de prueba con Retell AI
  Verifica que el agente, el audio y el prompt funcionen.

  USO:
    python ghl-integration/test_call.py --phone +1XXXXXXXXXX
    python ghl-integration/test_call.py --phone +1XXXXXXXXXX --dry-run
============================================================
"""

import os
import sys
import argparse
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GHL_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(ROOT / ".env")

RETELL_API_KEY     = os.getenv("RETELL_API_KEY", "")
RETELL_AGENT_ID    = os.getenv("RETELL_AGENT_ID", "")
RETELL_FROM_NUMBER = os.getenv("RETELL_NUMBER", "")
GHL_CALLBACK_NUMBER = os.getenv("GHL_PHONE_NUMBER", "")

RETELL_BASE_URL = "https://api.retellai.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def _headers():
    return {"Authorization": f"Bearer {RETELL_API_KEY}", "Content-Type": "application/json"}


def validate():
    missing = []
    if not RETELL_API_KEY:    missing.append("RETELL_API_KEY")
    if not RETELL_AGENT_ID:   missing.append("RETELL_AGENT_ID")
    if not RETELL_FROM_NUMBER: missing.append("RETELL_NUMBER")
    if missing:
        print(f"\n  ERROR: Faltan en .env: {', '.join(missing)}\n")
        sys.exit(1)

    resp = requests.get(f"{RETELL_BASE_URL}/get-agent/{RETELL_AGENT_ID}", headers=_headers())
    if not resp.ok:
        print(f"\n  ERROR: RETELL_AGENT_ID inválido ({resp.status_code})\n")
        sys.exit(1)

    agent_name = resp.json().get("agent_name", "desconocido")
    print(f"\n  Agente    : {agent_name} ({RETELL_AGENT_ID})")
    print(f"  Desde     : {RETELL_FROM_NUMBER}")
    print(f"  Callback  : {GHL_CALLBACK_NUMBER or 'no configurado'}\n")
    return agent_name


def make_test_call(to_number: str, dry_run: bool = False):
    agent_name = validate()

    print(f"{'='*50}")
    print(f"  TEST CALL — Asistente MultiVenza")
    print(f"{'='*50}")
    print(f"  Llamando a  : {to_number}")
    print(f"  Agente      : {agent_name}")
    print(f"  Modo        : {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*50}\n")

    if dry_run:
        print("  [DRY RUN] Todo OK — no se hizo ninguna llamada.")
        return

    payload = {
        "from_number": RETELL_FROM_NUMBER,
        "to_number":   to_number,
        "agent_id":    RETELL_AGENT_ID,
        "metadata": {
            "contact_id": "test-call",
            "nombre":     "Keyner (prueba)",
            "ciudad":     "Minneapolis",
        },
        "retell_llm_dynamic_variables": {
            "nombre_negocio":  "Keyner (prueba)",
            "ciudad":          "Minneapolis",
            "numero_callback": GHL_CALLBACK_NUMBER,
        },
    }

    resp = requests.post(f"{RETELL_BASE_URL}/v2/create-phone-call", json=payload, headers=_headers())

    if resp.ok:
        call = resp.json()
        call_id = call.get("call_id", "")
        print(f"  LLAMADA INICIADA")
        print(f"  call_id : {call_id}")
        print(f"  status  : {call.get('call_status', '')}")
        print(f"\n  Verifica en tu telefono — deberias recibir la llamada en segundos.")
        print(f"  Dashboard: https://app.retellai.com/calls/{call_id}\n")
    else:
        print(f"\n  ERROR {resp.status_code}: {resp.text[:400]}\n")
        print("  Causas comunes:")
        print("  - RETELL_NUMBER no registrado en tu cuenta de Retell")
        print("  - RETELL_AGENT_ID incorrecto")
        print("  - Numero destino en formato incorrecto (usar E.164: +1XXXXXXXXXX)\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Llamada de prueba con Retell AI")
    parser.add_argument("--phone",   required=True, help="Número a llamar en formato E.164 (+1XXXXXXXXXX)")
    parser.add_argument("--dry-run", action="store_true", help="Validar config sin hacer la llamada")
    args = parser.parse_args()

    if not args.phone.startswith("+"):
        print(f"\n  ERROR: El número debe estar en formato E.164 (ej: +19525550000)\n")
        sys.exit(1)

    make_test_call(args.phone, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
