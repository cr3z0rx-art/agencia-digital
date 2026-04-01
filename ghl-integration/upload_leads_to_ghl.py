"""
============================================================
  Upload Leads to GHL — CSV → GoHighLevel
  Sube leads con email a GHL y envía propuesta personalizada.

  Flujo completo:
    1. Lee leads/leads_with_emails.csv (output de scrape_emails.py)
    2. Filtra: email válido + ghl_uploaded=NO + status=HOT
    3. Crea contacto en GHL (con email, tags, nota, pipeline)
    4. Envía email de propuesta personalizada vía GHL
    5. Marca ghl_uploaded=YES en el CSV

  SETUP:
    pip install requests pandas python-dotenv anthropic

  .env requerido:
    GHL_API_KEY=...
    GHL_LOCATION_ID=...
    ANTHROPIC_API_KEY=...  (para propuestas con IA)

  USO:
    python ghl-integration/upload_leads_to_ghl.py
    python ghl-integration/upload_leads_to_ghl.py --dry-run
    python ghl-integration/upload_leads_to_ghl.py --status HOT
    python ghl-integration/upload_leads_to_ghl.py --no-email  (subir sin enviar email)
    python ghl-integration/upload_leads_to_ghl.py --csv leads/leads_with_emails.csv
============================================================
"""

import re
import sys
import csv
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Fix encoding en terminales Windows (cp1252 no soporta caracteres latinos)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

# ── Import ghl_client desde la misma carpeta ──────────────
ROOT    = Path(__file__).resolve().parent.parent
GHL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GHL_DIR))

from ghl_client import (
    validate_credentials,
    create_contact,
    get_contact_by_phone,
    add_note_to_contact,
    get_pipeline_by_name,
    get_stage_id,
    get_opportunities_by_contact,
    create_opportunity,
    send_email_smtp,
)

# ── Import generador de propuestas ────────────────────────
sys.path.insert(0, str(GHL_DIR))
from email_generator import generate_proposal_bilingual, decide_template_and_language, SERVICE_VALUES

# ── Configuración ─────────────────────────────────────────
PIPELINE_NAME = "Contratistas Latinos"
STAGE_NAME    = "Nuevo Lead"

# ── Logging texto ─────────────────────────────────────────
LOG_DIR      = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
RUN_TS       = datetime.now().strftime("%Y%m%d_%H%M%S")
text_log     = LOG_DIR / f"ghl_upload_{RUN_TS}.log"
CSV_LOG_PATH = LOG_DIR / "ghl_upload_log.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(text_log, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

CSV_LOG_HEADERS = ["fecha", "nombre", "email", "telefono", "nicho", "ciudad",
                   "resultado", "email_enviado", "ghl_contact_id", "pipeline", "error"]

def _reset_log_if_stale():
    """Recrea el log CSV si no tiene las columnas correctas."""
    if not CSV_LOG_PATH.exists():
        return
    with open(CSV_LOG_PATH, encoding="utf-8") as f:
        first_line = f.readline()
    existing_headers = [h.strip() for h in first_line.split(",")]
    if existing_headers != CSV_LOG_HEADERS:
        CSV_LOG_PATH.rename(CSV_LOG_PATH.with_suffix(".old.csv"))
        logging.info("Log CSV recreado con headers actualizados (backup: ghl_upload_log.old.csv)")


def write_csv_log(row_data: dict):
    """Agrega una fila al log CSV. Crea el archivo con headers si no existe."""
    file_exists = CSV_LOG_PATH.exists()
    with open(CSV_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_LOG_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)


# ── Notificación interna — Latino HOT ─────────────────────

NOTIFY_EMAIL = "hello@multivenzadigital.com"

def notify_latino_hot(name: str, city: str, niche: str, phone: str, contact_id: str) -> None:
    """
    Envía notificación inmediata a hello@multivenzadigital.com cuando se sube
    un lead con tags 'latino' + 'hot'. Solo necesita SMTP configurado en .env.
    """
    now      = datetime.now().strftime("%Y-%m-%d %H:%M")
    ghl_link = f"https://app.gohighlevel.com/contacts/{contact_id}" if contact_id else "N/A"

    subject = f"🔥 Latino HOT subido: {name} — {city}"
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#0A0F14;color:#F0F0F0;border-radius:12px;overflow:hidden">
  <div style="background:#00A3AD;padding:20px 28px">
    <p style="margin:0;font-size:.85rem;color:rgba(255,255,255,.8);letter-spacing:.05em">MULTIVENZA DIGITAL — ALERTA INTERNA</p>
    <h1 style="margin:6px 0 0;font-size:1.4rem;font-weight:800">🔥 Latino HOT detectado</h1>
  </div>
  <div style="padding:28px">
    <table style="width:100%;border-collapse:collapse">
      <tr><td style="padding:8px 0;color:#8A9BAE;font-size:.85rem;width:110px">Negocio</td>
          <td style="padding:8px 0;font-weight:700;font-size:1rem">{name}</td></tr>
      <tr><td style="padding:8px 0;color:#8A9BAE;font-size:.85rem">Ciudad</td>
          <td style="padding:8px 0">{city or "—"}</td></tr>
      <tr><td style="padding:8px 0;color:#8A9BAE;font-size:.85rem">Nicho</td>
          <td style="padding:8px 0">{niche or "—"}</td></tr>
      <tr><td style="padding:8px 0;color:#8A9BAE;font-size:.85rem">Teléfono</td>
          <td style="padding:8px 0">{phone or "—"}</td></tr>
      <tr><td style="padding:8px 0;color:#8A9BAE;font-size:.85rem">Subido</td>
          <td style="padding:8px 0">{now}</td></tr>
    </table>
    <div style="margin-top:24px">
      <a href="{ghl_link}" style="display:inline-block;background:#FF8200;color:#fff;font-weight:700;padding:12px 24px;border-radius:8px;text-decoration:none;font-size:.9rem">
        Ver en CRM →
      </a>
    </div>
    <p style="margin-top:20px;font-size:.8rem;color:#8A9BAE">
      Este lead habla español. Prioridad: llamada directa hoy.
    </p>
  </div>
</div>
"""
    try:
        send_email_smtp(NOTIFY_EMAIL, subject, html)
        logging.info(f"  NOTIF enviada a {NOTIFY_EMAIL} — Latino HOT: {name}")
    except Exception as e:
        logging.warning(f"  NOTIF fallida para {name}: {e}")


# ── Helpers ───────────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """
    Convierte cualquier formato de teléfono USA a E.164 (+1XXXXXXXXXX).
    (773) 387-7394 → +17733877394
    773-387-7394   → +17733877394
    """
    if not phone or phone.strip().lower() == "nan":
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return phone  # devolver tal cual si no reconoce el formato


def parse_name(full_name: str) -> tuple[str, str]:
    """'Garcia Roofing LLC' → first='Garcia', last='Roofing LLC'"""
    parts = full_name.strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def build_tags(row: pd.Series) -> list[str]:
    tags = []

    niche = str(row.get("niche", "")).strip()
    if niche:
        tags.append(niche.lower().replace(" ", "-").replace("/", "-"))

    is_latino = str(row.get("is_latino", "NO")).strip().upper()
    if is_latino == "YES":
        tags.append("latino")
    elif is_latino == "POSSIBLE":
        tags.append("posible-latino")

    status = str(row.get("status", "")).strip().upper()
    if status:
        tags.append(status.lower())

    service = str(row.get("recommended_service", "")).strip()
    SERVICE_TAG_MAP = {
        "Diseño web / Landing page": "servicio-web",
        "SEO y posicionamiento":     "servicio-seo",
        "Automatización con IA":     "servicio-ia",
    }
    tag = SERVICE_TAG_MAP.get(service)
    if tag:
        tags.append(tag)

    lang = str(row.get("outreach_language", "")).strip()
    if lang:
        tags.append(f"idioma-{lang.lower()}")

    return tags


def build_note(row: pd.Series) -> str:
    return "\n".join([
        "=== Lead importado desde CSV ===",
        f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "PITCH:",
        str(row.get("pitch_line", "")),
        "",
        "DATOS:",
        f"  Nicho:    {row.get('niche', '')}",
        f"  Ciudad:   {row.get('city', '')}",
        f"  Servicio: {row.get('recommended_service', '')}",
        f"  Rating:   {row.get('rating', '')} ({row.get('reviews', 0)} reseñas)",
        f"  Web:      {row.get('website', '')}",
        f"  Score:    {row.get('score', '')}",
        f"  is_latino:{row.get('is_latino', '')}",
        f"  Idioma:   {row.get('outreach_language', '')}",
    ])


def upload_lead(
    row: pd.Series,
    pipeline_id: str | None,
    stage_id: str | None,
    dry_run: bool = False,
    send_proposal: bool = True,
) -> tuple[bool, str, bool, str]:
    """
    Sube un lead a GHL y envía propuesta por email.
    Retorna (éxito, contact_id, email_enviado, mensaje_error).
    """
    name    = str(row.get("name", "")).strip()
    phone   = normalize_phone(str(row.get("phone", "")).strip())
    website = str(row.get("website", "NO WEBSITE")).strip()
    email   = str(row.get("email", "")).strip()

    if not phone:
        return False, "", False, "sin teléfono"

    if dry_run:
        tags = build_tags(row)
        logging.info(f"  [DRY RUN] {name} | email: {email or 'N/A'} | Tags: {tags}")
        return True, "dry-run", False, ""

    # Crear contacto (maneja duplicados automáticamente)
    contact_id  = None
    is_duplicate = False
    try:
        first, last = parse_name(name)
        tags = build_tags(row)

        payload = {
            "firstName": first,
            "lastName":  last,
            "phone":     phone,
            "address1":  str(row.get("address", "")),
            "city":      str(row.get("city", "")),
            "website":   "" if website == "NO WEBSITE" else website,
            "tags":      tags,
        }
        if email and email.lower() not in ("no email", "error", "nan", "none", "n/a", ""):
            payload["email"] = email

        contact    = create_contact(payload)
        contact_id = contact.get("id")

        if not contact_id:
            return False, "", False, "GHL no devolvio ID de contacto"

    except Exception as e:
        # GHL devuelve 400 con meta.contactId cuando ya existe el contacto
        import re, json as _json
        err_str = str(e)
        # Intentar extraer contactId del JSON de error
        try:
            json_match = re.search(r'\{.*\}', err_str, re.DOTALL)
            if json_match:
                err_data   = _json.loads(json_match.group())
                contact_id = err_data.get("meta", {}).get("contactId")
        except Exception:
            pass

        if contact_id:
            is_duplicate = True
            logging.info(f"  Duplicado — reusando contactId: {contact_id}")
        else:
            logging.error(f"  ERROR creando contacto '{name}': {e}")
            return False, "", False, f"error creando contacto: {e}"

    # Agregar nota con pitch (siempre — nuevo o duplicado)
    try:
        note_prefix = "[DUPLICADO — email reenviado]\n\n" if is_duplicate else ""
        add_note_to_contact(contact_id, note_prefix + build_note(row))
    except Exception as e:
        logging.warning(f"  Nota fallida para {name}: {e}")

    # Notificación interna si es Latino HOT
    tags = build_tags(row)
    if "latino" in tags and "hot" in tags:
        notify_latino_hot(
            name       = name,
            city       = str(row.get("city", "")),
            niche      = str(row.get("niche", "")),
            phone      = phone,
            contact_id = contact_id,
        )

    # Asignar a pipeline con valor monetario
    pipeline_ok = False
    if pipeline_id and stage_id:
        try:
            template, _ = decide_template_and_language(row.to_dict())
            deal_value   = SERVICE_VALUES.get(template, 500)

            # Si es duplicado, verificar si ya tiene una opportunity antes de crear
            if is_duplicate:
                existing = get_opportunities_by_contact(contact_id)
                if existing:
                    pipeline_ok = True
                    logging.info(f"  Pipeline OK (oportunidad ya existe) | deal_value: ${deal_value}")
                else:
                    create_opportunity(contact_id, pipeline_id, stage_id, name,
                                       monetary_value=deal_value)
                    pipeline_ok = True
                    logging.info(f"  Pipeline OK (nueva oportunidad) | deal_value: ${deal_value}")
            else:
                create_opportunity(contact_id, pipeline_id, stage_id, name,
                                   monetary_value=deal_value)
                pipeline_ok = True
                logging.info(f"  Pipeline OK | deal_value: ${deal_value}")
        except Exception as e:
            logging.warning(f"  Pipeline fallido para {name}: {e}")
    else:
        logging.warning(f"  Pipeline '{PIPELINE_NAME}' no encontrado — contacto creado sin pipeline")

    # Enviar propuesta por email
    email_sent = False
    if send_proposal and email and email.lower() not in ("no email", "error", "nan", "none", "n/a", ""):
        try:
            proposal = generate_proposal_bilingual(row.to_dict())
            send_email_smtp(email, proposal["subject"], proposal["html"])
            email_sent = True
            logging.info(f"  EMAIL enviado -> {email}")
        except Exception as e:
            logging.warning(f"  Email fallido para {name}: {e}")

    # Actualizar tags en GHL según resultado del email
    try:
        from ghl_client import update_contact_tags, _headers, BASE_URL
        import requests as _req
        r_tags = _req.get(f"{BASE_URL}/contacts/{contact_id}", headers=_headers())
        current_tags = r_tags.json().get("contact", {}).get("tags", []) if r_tags.ok else []
        if email_sent:
            email_tag = "email-enviado"
        elif not email or email.lower() in ("no email", "error", "nan", "none", "n/a", ""):
            email_tag = "sin-email"
        else:
            email_tag = "email-fallido"
        update_contact_tags(contact_id, list(set(current_tags + [email_tag])))
        logging.info(f"  Tag GHL -> {email_tag}")
    except Exception as e:
        logging.warning(f"  Tag email fallido para {name}: {e}")

    dup_tag    = " [DUPLICADO]" if is_duplicate else ""
    status_msg = "OK" if pipeline_ok else "OK (sin pipeline)"
    logging.info(f"  {status_msg}{dup_tag}  {name} | ID: {contact_id} | email_sent: {email_sent}")
    return True, contact_id, email_sent, ""


# ── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sube leads a GHL y envía propuesta por email")
    parser.add_argument("--csv",           default="leads/leads_with_emails.csv",
                        help="CSV a procesar (default: leads/leads_with_emails.csv)")
    parser.add_argument("--status",        default="HOT")
    parser.add_argument("--all-languages", action="store_true",
                        help="Incluir todos los idiomas (por defecto solo is_latino=YES/POSSIBLE)")
    parser.add_argument("--no-email",      action="store_true",
                        help="Subir contactos a GHL sin enviar email")
    parser.add_argument("--dry-run",       action="store_true",
                        help="Simular sin subir nada a GHL")
    parser.add_argument("--limit",         type=int, default=0,
                        help="Procesar solo los primeros N leads")
    args = parser.parse_args()

    csv_path = ROOT / args.csv

    send_proposal = not args.no_email

    print(f"\n{'='*60}")
    print(f"  Upload Leads -> GHL + Propuesta Email")
    print(f"  CSV:      {args.csv}")
    print(f"  Filtro:   status={args.status}" + (" + latino=YES/POSSIBLE" if not args.all_languages else ""))
    print(f"  Pipeline: {PIPELINE_NAME} / {STAGE_NAME}")
    print(f"  Email:    {'SI — propuesta personalizada' if send_proposal else 'NO'}")
    print(f"  Modo:     {'DRY RUN (sin cambios)' if args.dry_run else 'LIVE'}")
    print(f"  Log CSV:  logs/ghl_upload_log.csv")
    print(f"{'='*60}\n")

    # Verificar y resetear log si headers cambiaron
    _reset_log_if_stale()

    # Validar credenciales
    if not args.dry_run:
        if not validate_credentials():
            print("\n  ERROR: Credenciales GHL inválidas. Revisa tu .env\n")
            sys.exit(1)

    # Buscar pipeline y stage
    pipeline_id = stage_id = None
    if not args.dry_run:
        pipeline = get_pipeline_by_name(PIPELINE_NAME)
        if pipeline:
            pipeline_id = pipeline.get("id")
            stage_id    = get_stage_id(pipeline, STAGE_NAME)
            if stage_id:
                logging.info(f"Pipeline encontrado: '{PIPELINE_NAME}' / '{STAGE_NAME}'")
            else:
                logging.warning(f"Etapa '{STAGE_NAME}' no encontrada en pipeline '{PIPELINE_NAME}' — se usara la primera etapa disponible")
                stages = pipeline.get("stages", [])
                if stages:
                    stage_id = stages[0].get("id")
        else:
            logging.warning(f"Pipeline '{PIPELINE_NAME}' no existe en GHL — los contactos se crean sin pipeline.")
            logging.warning("Crea el pipeline manualmente en GHL y vuelve a correr el script.")

    # Cargar CSV
    if not csv_path.exists():
        print(f"\n  ERROR: CSV no encontrado: {csv_path}\n")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    logging.info(f"CSV cargado: {len(df)} leads totales")

    # Filtrar
    mask = (df["ghl_uploaded"].str.upper() == "NO") & (df["status"].str.upper() == args.status.upper())

    # Solo leads con email válido — solo si vamos a enviar propuesta
    if send_proposal and "email" in df.columns:
        mask &= (~df["email"].isin(["NO EMAIL", "ERROR", "", "nan"]))
        mask &= df["email"].notna()

    # Solo latinos (si el CSV tiene columna is_latino)
    if not args.all_languages and "is_latino" in df.columns:
        mask &= df["is_latino"].str.upper().isin(["YES", "POSSIBLE"])

    pending = df[mask].copy()
    if args.limit:
        pending = pending.head(args.limit)
        logging.info(f"Leads pendientes: {len(pending)} (limit={args.limit})")
    else:
        logging.info(f"Leads pendientes: {len(pending)}")

    if pending.empty:
        print(f"  No hay leads pendientes con estos filtros.")
        print(f"  Filtros activos: status={args.status}, ghl_uploaded=NO, email válido")
        return

    emails_count = pending["email"].notna().sum() if "email" in pending.columns else 0
    logging.info(f"Leads pendientes: {len(pending)} | Con email: {emails_count}")

    # Subir
    success_ids  = []
    emails_sent  = 0
    failed       = 0

    for idx, row in pending.iterrows():
        name  = str(row.get("name", ""))[:40]
        email = str(row.get("email", "N/A"))
        print(f"  [{idx:4d}] {name} | {email}")

        ok, contact_id, email_ok, error_msg = upload_lead(
            row, pipeline_id, stage_id,
            dry_run=args.dry_run,
            send_proposal=send_proposal,
        )

        if email_ok:
            emails_sent += 1

        log_row = {
            "fecha":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nombre":         str(row.get("name", "")),
            "email":          str(row.get("email", "")),
            "telefono":       str(row.get("phone", "")),
            "nicho":          str(row.get("niche", "")),
            "ciudad":         str(row.get("city", "")),
            "resultado":      "OK" if ok else f"SKIP/ERROR: {error_msg}",
            "email_enviado":  "SI" if email_ok else "NO",
            "ghl_contact_id": contact_id,
            "pipeline":       f"{PIPELINE_NAME}/{STAGE_NAME}" if ok and pipeline_id else "",
            "error":          error_msg,
        }
        write_csv_log(log_row)

        if ok:
            success_ids.append(idx)
        else:
            failed += 1

    # Actualizar CSV
    if success_ids and not args.dry_run:
        df.loc[success_ids, "ghl_uploaded"] = "YES"
        df.to_csv(csv_path, index=False)
        logging.info(f"CSV actualizado: {len(success_ids)} marcados ghl_uploaded=YES")

    # Resumen
    print(f"\n{'='*60}")
    print(f"  RESUMEN")
    print(f"{'='*60}")
    print(f"  Procesados    : {len(pending)}")
    print(f"  Subidos GHL   : {len(success_ids)}")
    print(f"  Emails enviados: {emails_sent}")
    print(f"  Fallidos      : {failed}")
    if not args.dry_run:
        print(f"  CSV           : ghl_uploaded=YES en {len(success_ids)} leads")
    print(f"  Log texto     : logs/{text_log.name}")
    print(f"  Log CSV       : logs/ghl_upload_log.csv")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
