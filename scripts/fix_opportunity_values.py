"""
============================================================
  fix_opportunity_values.py
  Lee logs/ghl_upload_log.csv, busca cada oportunidad en GHL
  por contactId y actualiza monetaryValue según el template
  del lead (no_website=1500, ai_receptionist=500, seo=500).

  USO:
    python scripts/fix_opportunity_values.py
    python scripts/fix_opportunity_values.py --dry-run
============================================================
"""

import sys
import csv
import time
import logging
import argparse
import requests
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = ROOT / "ghl-integration"
sys.path.insert(0, str(GHL_DIR))

from dotenv import load_dotenv
load_dotenv()

from ghl_client import BASE_URL, GHL_LOCATION_ID, _headers, _handle_rate_limit
from email_generator import decide_template_and_language, SERVICE_VALUES

LOG_DIR = ROOT / "logs"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_opportunities_by_contact(contact_id: str) -> list[dict]:
    """Busca todas las oportunidades de un contacto."""
    url    = f"{BASE_URL}/opportunities/search"
    params = {"location_id": GHL_LOCATION_ID, "contact_id": contact_id}
    resp   = requests.get(url, params=params, headers=_headers())
    if not resp.ok:
        return []
    return resp.json().get("opportunities", [])


def update_opportunity_value(opp_id: str, value: int) -> bool:
    """Actualiza el monetaryValue de una oportunidad."""
    url     = f"{BASE_URL}/opportunities/{opp_id}"
    payload = {"monetaryValue": value}
    for attempt in range(1, 4):
        resp = requests.put(url, json=payload, headers=_headers())
        if _handle_rate_limit(resp, attempt):
            continue
        return resp.ok
    return False


def load_leads_from_log() -> list[dict]:
    """Lee el upload log y retorna leads con contactId."""
    log_path = LOG_DIR / "ghl_upload_log.csv"
    if not log_path.exists():
        logging.error(f"No se encontro: {log_path}")
        sys.exit(1)

    leads = []
    with open(log_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("resultado") == "OK" and row.get("ghl_contact_id"):
                leads.append(row)
    return leads


def build_lead_dict(log_row: dict) -> dict:
    """Reconstruye un dict de lead desde el log para decide_template_and_language."""
    # El log tiene: nombre, telefono, nicho, ciudad, ghl_contact_id
    # Necesitamos website e is_latino para la decision — los inferimos del nicho/nombre
    # Si no hay datos suficientes, usamos ai_receptionist como default (87% de los leads)
    return {
        "name":     log_row.get("nombre", ""),
        "niche":    log_row.get("nicho", ""),
        "city":     log_row.get("ciudad", ""),
        "website":  "YES",       # los 87 leads subidos TODOS tenian website
        "reviews":  100,         # default conservador → ai_receptionist
        "is_latino": "NO",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Fix Opportunity Values")
    print(f"  Modo: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'='*60}\n")

    leads = load_leads_from_log()
    logging.info(f"Leads en upload log: {len(leads)}")

    updated = skipped = failed = 0

    for lead in leads:
        name       = lead.get("nombre", "")[:40]
        contact_id = lead.get("ghl_contact_id", "")

        lead_dict        = build_lead_dict(lead)
        template, _      = decide_template_and_language(lead_dict)
        expected_value   = SERVICE_VALUES.get(template, 500)

        opps = get_opportunities_by_contact(contact_id)

        if not opps:
            logging.warning(f"  Sin oportunidad: {name}")
            skipped += 1
            time.sleep(0.3)
            continue

        opp    = opps[0]
        opp_id = opp.get("id")
        current_value = opp.get("monetaryValue", 0)

        if current_value == expected_value:
            logging.info(f"  OK (ya correcto ${expected_value}): {name}")
            skipped += 1
            time.sleep(0.3)
            continue

        logging.info(f"  {name} | ${current_value} -> ${expected_value} [{template}]")

        if not args.dry_run:
            ok = update_opportunity_value(opp_id, expected_value)
            if ok:
                updated += 1
            else:
                logging.warning(f"  FALLO update: {name}")
                failed += 1
        else:
            updated += 1

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  Actualizados : {updated}")
    print(f"  Ya correctos : {skipped}")
    print(f"  Fallidos     : {failed}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
