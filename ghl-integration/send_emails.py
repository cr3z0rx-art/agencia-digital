"""
============================================================
  Send Emails — MultiVenza Digital
  Envía propuestas bilingües a leads con email confirmado.

  Fuente: leads/leads_contractors_emails.csv
  Lógica: genera email bilingüe (ES arriba, EN abajo) por lead

  Requiere en .env:
    SMTP_EMAIL=hello@multivenzadigital.com
    SMTP_PASSWORD=...
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587

  Uso:
    python ghl-integration/send_emails.py --dry-run   ← preview sin enviar
    python ghl-integration/send_emails.py             ← envía a todos
    python ghl-integration/send_emails.py --limit 5   ← envía solo 5
============================================================
"""

import csv
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import logging
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ghl-integration"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from email_generator import generate_proposal_bilingual
from ghl_client import send_email as ghl_send_email, create_contact, get_contact_by_phone

# ── Config ─────────────────────────────────────────────────
LEADS_CSV = ROOT / "leads" / "leads_with_emails.csv"
LOG_DIR   = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "send_emails.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

DELAY_BETWEEN_EMAILS = 3


# ── GHL Email ───────────────────────────────────────────────

def send_via_ghl(lead: dict, subject: str, html: str) -> bool:
    """
    Crea/busca el contacto en GHL y envía el email via Conversations API.
    Retorna True si exitoso.
    """
    import re
    name  = lead.get("name", "").strip()
    email = lead.get("email", "").strip()
    phone = lead.get("phone", "").strip()

    # Normalizar teléfono a E.164
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        phone_e164 = f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        phone_e164 = f"+{digits}"
    else:
        phone_e164 = phone

    # Buscar o crear contacto en GHL
    contact_id = None
    try:
        parts = name.split(" ", 1)
        first = parts[0]
        last  = parts[1] if len(parts) > 1 else ""
        payload = {"firstName": first, "lastName": last, "email": email}
        if phone_e164:
            payload["phone"] = phone_e164
        contact = create_contact(payload)
        contact_id = contact.get("id")
    except Exception as e:
        # Si ya existe, extraer contactId del error
        import re as _re, json as _json
        err_str = str(e)
        try:
            m = _re.search(r'\{.*\}', err_str, _re.DOTALL)
            if m:
                contact_id = _json.loads(m.group()).get("meta", {}).get("contactId")
        except Exception:
            pass
        if not contact_id:
            logging.error(f"  No se pudo obtener contact_id para {name}: {e}")
            return False

    try:
        ghl_send_email(contact_id, email, subject, html)
        return True
    except Exception as e:
        logging.error(f"  GHL email falló para {email}: {e}")
        return False


# ── MAIN ────────────────────────────────────────────────────

def load_leads():
    with open(LEADS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_leads(rows: list, fieldnames: list):
    with open(LEADS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(dry_run: bool = False, limit: int = None):
    rows = load_leads()
    fieldnames = list(rows[0].keys())

    # Solo leads sin contactar con email real
    pending = [
        r for r in rows
        if r.get("contacted", "").strip() == "NO"
        and r.get("email", "").strip() not in ("", "NO EMAIL", "N/A", "nan")
    ]

    if limit:
        pending = pending[:limit]

    logging.info(f"{'[DRY RUN] ' if dry_run else ''}Leads a contactar: {len(pending)}")

    sent = 0
    failed = 0

    for i, lead in enumerate(pending, 1):
        name  = lead.get("name", "").strip()
        email = lead.get("email", "").strip()

        # Inferir niche desde search_term si no tiene columna niche
        if not lead.get("niche"):
            search = lead.get("search_term", "").lower()
            if "roof" in search:
                lead["niche"] = "Roofing"
            elif "hvac" in search or "heat" in search:
                lead["niche"] = "HVAC"
            elif "plumb" in search:
                lead["niche"] = "Plumbing"
            else:
                lead["niche"] = "Remodeling"

        result = generate_proposal_bilingual(lead)
        subject = result["subject"]
        html    = result["html"]

        logging.info(f"[{i}/{len(pending)}] {name} -> {email}")
        logging.info(f"  Subject: {subject}")

        if dry_run:
            print(f"\n{'='*60}")
            print(f"TO:      {email}")
            print(f"SUBJECT: {subject}")
            print(f"BODY:\n{html.replace('<br>', chr(10)).replace('<hr style', '---<hr style')}")
            continue

        success = send_via_ghl(lead, subject, html)

        if success:
            # Marcar como contactado en CSV
            for row in rows:
                if row.get("email", "").strip() == email:
                    row["contacted"] = "YES"
                    break
            sent += 1
            logging.info(f"  OK Enviado")
        else:
            failed += 1
            logging.error(f"  FALLO")

        if i < len(pending):
            time.sleep(DELAY_BETWEEN_EMAILS)

    if not dry_run:
        save_leads(rows, fieldnames)
        logging.info(f"\nResumen: {sent} enviados | {failed} fallidos")
        logging.info(f"CSV actualizado → contacted=YES en {sent} leads")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview sin enviar")
    parser.add_argument("--limit",   type=int, default=None, help="Máximo de emails a enviar")
    parser.add_argument("--csv",     default=None, help="CSV alternativo (default: leads_with_emails.csv)")
    parser.add_argument("--delay",   type=int, default=3, help="Segundos entre emails (default: 3)")
    args = parser.parse_args()

    if args.csv:
        LEADS_CSV = ROOT / args.csv

    DELAY_BETWEEN_EMAILS = args.delay

    if not os.getenv("GHL_API_KEY") or not os.getenv("GHL_LOCATION_ID"):
        print("ERROR: Faltan GHL_API_KEY o GHL_LOCATION_ID en .env")
        sys.exit(1)

    run(dry_run=args.dry_run, limit=args.limit)
