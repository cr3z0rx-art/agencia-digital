"""
============================================================
  resend_emails_via_ghl.py
  Lee logs/ghl_upload_log.csv, genera propuesta personalizada
  para cada contacto y envía el email via GHL Conversations API
  (para que queden registrados en GHL Conversations).

  USO:
    python ghl-integration/resend_emails_via_ghl.py
    python ghl-integration/resend_emails_via_ghl.py --dry-run
    python ghl-integration/resend_emails_via_ghl.py --dry-run --limit 3
    python ghl-integration/resend_emails_via_ghl.py --limit 10
============================================================
"""

import sys
import csv
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = ROOT / "ghl-integration"
sys.path.insert(0, str(GHL_DIR))

from dotenv import load_dotenv
load_dotenv()

from ghl_client import send_email
from email_generator import generate_proposal, decide_template_and_language

LOG_DIR = ROOT / "logs"
UPLOAD_LOG  = LOG_DIR / "ghl_upload_log.csv"
RESEND_LOG  = LOG_DIR / "resend_ghl_log.csv"
LEADS_CSV   = ROOT / "leads" / "leads_contractors_emails.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

RESEND_HEADERS = ["fecha", "nombre", "email", "contact_id", "template", "lang",
                  "subject", "resultado", "error"]


def write_resend_log(row: dict):
    file_exists = RESEND_LOG.exists()
    with open(RESEND_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESEND_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)



def normalize_log_row(row: dict) -> dict:
    """
    El log tiene dos formatos mezclados:
      Formato viejo (header):  fecha,nombre,telefono,nicho,ciudad,resultado,ghl_contact_id,pipeline,error
      Formato nuevo (datos):   fecha,nombre,email,telefono,nicho,ciudad,resultado,email_enviado,ghl_contact_id,pipeline,error

    Cuando el CSV tiene header viejo pero filas nuevas, las columnas se desplazan.
    Detectamos el formato por el campo 'telefono': si contiene '@' es una fila nueva.
    """
    telefono_raw = row.get("telefono", "")
    if "@" in telefono_raw:
        # Fila nueva leída con header viejo — reconstruir mapeo correcto
        return {
            "nombre":        row.get("nombre", ""),
            "email":         row.get("telefono", ""),      # email ocupa slot de telefono
            "telefono":      row.get("nicho", ""),          # phone ocupa slot de nicho
            "nicho":         row.get("ciudad", ""),         # nicho ocupa slot de ciudad
            "ciudad":        row.get("resultado", ""),      # ciudad ocupa slot de resultado
            "resultado":     row.get("ghl_contact_id", ""), # resultado ocupa slot de contact_id
            "email_enviado": row.get("pipeline", ""),       # email_enviado ocupa slot de pipeline
            "ghl_contact_id": row.get("error", ""),         # contact_id ocupa slot de error
        }
    # Fila vieja: formato correcto
    return row


def load_upload_log() -> list[dict]:
    """Lee el log y retorna contactos validos (resultado=OK, contactId real)."""
    if not UPLOAD_LOG.exists():
        logging.error(f"No existe: {UPLOAD_LOG}")
        sys.exit(1)

    contacts = []
    seen_ids = set()
    with open(UPLOAD_LOG, encoding="utf-8") as f:
        for raw_row in csv.DictReader(f):
            row = normalize_log_row(raw_row)
            contact_id = row.get("ghl_contact_id", "").strip()
            if (row.get("resultado") == "OK"
                    and contact_id
                    and contact_id != "dry-run"
                    and contact_id not in seen_ids):
                seen_ids.add(contact_id)
                contacts.append(row)
    return contacts


def build_leads_index() -> dict:
    """Crea index phone -> row desde leads_contractors_emails.csv para obtener website/reviews."""
    index = {}
    if not LEADS_CSV.exists():
        return index
    with open(LEADS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            phone = row.get("phone", "").strip()
            if phone:
                # Normalizar a dígitos para comparación
                digits = "".join(c for c in phone if c.isdigit())
                index[digits] = row
    return index


def normalize_digits(phone: str) -> str:
    return "".join(c for c in phone if c.isdigit())


def build_lead_dict(log_row: dict, leads_index: dict) -> dict:
    """
    Construye el dict completo del lead para decide_template_and_language.
    Prioriza datos del CSV original. Fallback a defaults conservadores.
    """
    phone_digits = normalize_digits(log_row.get("telefono", ""))
    original = leads_index.get(phone_digits, {})

    website = original.get("website", "YES").strip()
    if not website or website.lower() in ("nan", ""):
        website = "YES"  # conservative default → triggers ai_receptionist, not no_website

    try:
        reviews = int(float(original.get("reviews", 50) or 50))
    except (ValueError, TypeError):
        reviews = 50  # conservative middle-ground → ai_receptionist template

    # Inferir is_latino desde tags del log o nombre
    nombre = log_row.get("nombre", "").lower()
    is_latino = "NO"
    tags_str = log_row.get("pipeline", "").lower()
    if "latino" in nombre or "hermanos" in nombre or "hispano" in nombre:
        is_latino = "YES"

    return {
        "name":      log_row.get("nombre", ""),
        "niche":     original.get("search_term", log_row.get("nicho", "")),
        "city":      log_row.get("ciudad", original.get("address", "")),
        "website":   website,
        "reviews":   reviews,
        "is_latino": is_latino,
        "email":     log_row.get("email", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Previsualiza sin enviar emails")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limita el numero de contactos a procesar")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Resend Emails via GHL API")
    print(f"  Modo: {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.limit:
        print(f"  Limit: {args.limit}")
    print(f"{'='*60}\n")

    contacts = load_upload_log()
    leads_index = build_leads_index()

    logging.info(f"Contactos en upload log: {len(contacts)}")
    logging.info(f"Leads en CSV original: {len(leads_index)}")

    if args.limit:
        contacts = contacts[:args.limit]

    sent = skipped = failed = 0

    for contact in contacts:
        contact_id = contact.get("ghl_contact_id", "").strip()
        name       = contact.get("nombre", "")[:50]

        # Email puede estar en el log (formato nuevo) o en el CSV original (via phone)
        email = contact.get("email", "").strip()
        if not email:
            phone_digits = normalize_digits(contact.get("telefono", ""))
            orig = leads_index.get(phone_digits, {})
            email = orig.get("email", "").strip()

        if not email:
            logging.warning(f"  Sin email: {name}")
            skipped += 1
            continue

        lead_dict = build_lead_dict(contact, leads_index)
        template, lang = decide_template_and_language(lead_dict)

        proposal = generate_proposal(lead_dict)
        subject  = proposal.get("subject", f"Propuesta para {name}")
        html     = proposal.get("html", "")

        logging.info(f"  {name[:40]} | {template}/{lang} | {email}")
        if args.dry_run:
            print(f"    Subject: {subject}")
            print(f"    Preview: {html[:120].replace(chr(10),' ')}...")
            print()
            sent += 1
            write_resend_log({
                "fecha":      datetime.now().isoformat(),
                "nombre":     name,
                "email":      email,
                "contact_id": contact_id,
                "template":   template,
                "lang":       lang,
                "subject":    subject,
                "resultado":  "DRY_RUN",
                "error":      "",
            })
            time.sleep(0.2)
            continue

        try:
            send_email(contact_id, email, subject, html)
            ok = True
        except Exception as e:
            logging.warning(f"  GHL send_email error: {e}")
            ok = False
        resultado = "OK" if ok else "FALLO"

        write_resend_log({
            "fecha":      datetime.now().isoformat(),
            "nombre":     name,
            "email":      email,
            "contact_id": contact_id,
            "template":   template,
            "lang":       lang,
            "subject":    subject,
            "resultado":  resultado,
            "error":      "" if ok else "GHL API error",
        })

        if ok:
            sent += 1
            logging.info(f"    OK -> {email}")
        else:
            failed += 1
            logging.warning(f"    FALLO -> {email}")

        time.sleep(0.8)  # rate limit safety

    print(f"\n{'='*60}")
    print(f"  Enviados  : {sent}")
    print(f"  Sin email : {skipped}")
    print(f"  Fallidos  : {failed}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
