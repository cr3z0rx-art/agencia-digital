"""
============================================================
  Email Scraper — Leads con Website
  Lee los 3 CSVs, visita cada website y extrae emails.
  Guarda progreso incrementalmente en leads_with_emails.csv

  SETUP:
    pip install requests beautifulsoup4 lxml

  USO:
    python scripts/scrape_emails.py

  OUTPUT:
    leads/leads_with_emails.csv — todos los leads con website
                                   + columna email (o NO EMAIL)

  OPCIONES:
    --csv latinos     solo leads_latinos_usa.csv
    --csv minneapolis solo leads_minneapolis.csv
    --csv multiservice solo leads_multiservice.csv
    --status HOT      solo leads con ese status
    --latino          solo is_latino YES o POSSIBLE (latinos_usa)
    --limit 50        procesar solo los primeros N leads
    --resume          retomar desde donde quedó (default: ON)
============================================================
"""

import csv
import re
import time
import logging
import argparse
import os
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────

LEADS_DIR   = os.path.join(os.path.dirname(__file__), '..', 'leads')
OUTPUT_FILE = os.path.join(LEADS_DIR, 'leads_with_emails.csv')
LOG_FILE    = os.path.join(os.path.dirname(__file__), '..', 'logs', 'scrape_emails.log')

TIMEOUT     = 8       # segundos por request
DELAY       = 1.2     # segundos entre requests (ser amable con los servidores)
MAX_RETRIES = 2

# Páginas adicionales a visitar si la home no tiene email
CONTACT_PATHS = ['/contact', '/contact-us', '/contacto', '/about', '/about-us', '/nosotros']

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Dominios de email que NO queremos (son genéricos o irrelevantes)
SKIP_DOMAINS = {
    'sentry.io', 'wixpress.com', 'example.com', 'yourdomain.com',
    'domain.com', 'email.com', 'placeholder.com', 'test.com',
    'squarespace.com', 'wordpress.com', 'godaddy.com',
    'googleapis.com', 'google.com', 'facebook.com', 'twitter.com',
    'instagram.com', 'linkedin.com', 'yelp.com', 'angi.com',
    'homeadvisor.com', 'thumbtack.com', 'w3.org', 'schema.org',
}

# ─────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────
#  FUNCIONES DE SCRAPING
# ─────────────────────────────────────────

def fetch_html(url: str, session: requests.Session) -> str | None:
    """Descarga el HTML de una URL. Devuelve None si falla."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            return None
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                log.debug(f"  FAIL {url}: {type(e).__name__}")
            time.sleep(0.5)
    return None


def extract_emails_from_html(html: str) -> list[str]:
    """Extrae emails del HTML, filtrando dominios genéricos."""
    soup = BeautifulSoup(html, 'lxml')

    # Eliminar scripts y estilos antes de buscar texto
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()

    text = soup.get_text(separator=' ')
    raw_emails = EMAIL_RE.findall(text)

    # También buscar en atributos href="mailto:..."
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].strip()
            if email:
                raw_emails.append(email)

    # Limpiar y filtrar
    clean = []
    seen = set()
    for email in raw_emails:
        email = email.lower().strip().rstrip('.')
        domain = email.split('@')[-1]
        if domain in SKIP_DOMAINS:
            continue
        if email in seen:
            continue
        seen.add(email)
        clean.append(email)

    return clean


def scrape_website_firecrawl(url: str) -> str:
    """
    Usa Firecrawl API para scraping con JavaScript rendering.
    Retorna el primer email encontrado o 'NO EMAIL'.
    """
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        result = app.scrape(url, formats=["markdown"])
        content = ""
        if hasattr(result, "markdown"):
            content = result.markdown or ""
        elif isinstance(result, dict):
            content = result.get("markdown", "") or result.get("content", "") or ""

        if content:
            raw_emails = EMAIL_RE.findall(content)
            clean = []
            seen = set()
            for email in raw_emails:
                email = email.lower().strip().rstrip('.')
                domain = email.split('@')[-1]
                if domain in SKIP_DOMAINS:
                    continue
                if email in seen:
                    continue
                seen.add(email)
                clean.append(email)
            if clean:
                preferred = [e for e in clean if any(k in e for k in ('info', 'contact', 'hello', 'office', 'admin', 'hola', 'ventas', 'sales'))]
                return preferred[0] if preferred else clean[0]
    except Exception as e:
        log.debug(f"  Firecrawl error: {e}")
    return 'NO EMAIL'


def scrape_website(url: str, session: requests.Session) -> str:
    """
    Primero intenta con Firecrawl (JS rendering).
    Si falla o no hay API key, usa BeautifulSoup como fallback.
    """
    if not url.startswith('http'):
        url = 'https://' + url

    # Firecrawl primero si hay API key
    if FIRECRAWL_API_KEY:
        result = scrape_website_firecrawl(url)
        if result != 'NO EMAIL':
            return result

    # Fallback: BeautifulSoup clásico
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    pages_to_try = [url] + [urljoin(base, p) for p in CONTACT_PATHS]

    for page_url in pages_to_try:
        html = fetch_html(page_url, session)
        if not html:
            continue
        emails = extract_emails_from_html(html)
        if emails:
            preferred = [e for e in emails if any(k in e for k in ('info', 'contact', 'hello', 'office', 'admin', 'hola', 'ventas', 'sales'))]
            return preferred[0] if preferred else emails[0]
        time.sleep(0.3)

    return 'NO EMAIL'


# ─────────────────────────────────────────
#  CARGA DE LEADS
# ─────────────────────────────────────────

def load_leads(csv_filter: str | None, status_filter: str | None, latino_only: bool) -> list[dict]:
    """
    Carga leads de los 3 CSVs y aplica filtros.
    Solo incluye leads con website válido.
    Agrega columna 'source_csv' para tracking.
    """
    files = {
        'latinos':     os.path.join(LEADS_DIR, 'leads_latinos_usa.csv'),
        'minneapolis': os.path.join(LEADS_DIR, 'leads_minneapolis.csv'),
        'multiservice': os.path.join(LEADS_DIR, 'leads_multiservice.csv'),
        'nuevos':      os.path.join(LEADS_DIR, 'leads_nuevos_nichos.csv'),
    }

    if csv_filter:
        files = {k: v for k, v in files.items() if k == csv_filter}

    all_leads = []

    for key, path in files.items():
        with open(path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            website = row.get('website', '').strip()
            if not website or website == 'NO WEBSITE' or not website.startswith('http'):
                continue

            if status_filter and row.get('status', '').upper() != status_filter.upper():
                continue

            if latino_only and key == 'latinos':
                is_lat = row.get('is_latino', '').upper()
                if is_lat not in ('YES', 'POSSIBLE'):
                    continue

            row['source_csv'] = key
            all_leads.append(row)

    return all_leads


# ─────────────────────────────────────────
#  CARGA DE PROGRESO ANTERIOR
# ─────────────────────────────────────────

def load_done_urls() -> set[str]:
    """Lee el output file y devuelve el set de websites ya procesados."""
    if not os.path.exists(OUTPUT_FILE):
        return set()
    done = set()
    with open(OUTPUT_FILE, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            url = row.get('website', '').strip()
            if url:
                done.add(url)
    return done


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Scrape emails from lead websites')
    parser.add_argument('--csv',     choices=['latinos', 'minneapolis', 'multiservice', 'nuevos'], help='CSV a procesar')
    parser.add_argument('--status',  help='Filtrar por status: HOT, WARM, COLD')
    parser.add_argument('--latino',  action='store_true', help='Solo latinos (is_latino YES/POSSIBLE)')
    parser.add_argument('--limit',   type=int, default=0, help='Procesar solo los primeros N leads')
    parser.add_argument('--no-resume', action='store_true', help='Ignorar progreso anterior y empezar de cero')
    parser.add_argument('--output', default=None, help='Archivo de salida alternativo (default: leads_with_emails.csv)')
    args = parser.parse_args()

    global OUTPUT_FILE
    if args.output:
        OUTPUT_FILE = os.path.join(LEADS_DIR, args.output)

    # Cargar leads
    leads = load_leads(args.csv, args.status, args.latino)
    log.info(f"Leads con website encontrados: {len(leads)}")

    # Filtrar ya procesados (resume)
    done_urls = set()
    if not args.no_resume:
        done_urls = load_done_urls()
        if done_urls:
            log.info(f"Retomando — {len(done_urls)} ya procesados, quedan {len(leads) - len(done_urls)} pendientes")

    pending = [r for r in leads if r.get('website', '') not in done_urls]

    if args.limit:
        pending = pending[:args.limit]
        log.info(f"Modo --limit: procesando {len(pending)} leads")

    if not pending:
        log.info("Nada nuevo que procesar.")
        return

    # Ordenar: HOT primero, luego latinos YES, luego el resto
    def sort_key(r):
        s = 0 if r.get('status') == 'HOT' else (1 if r.get('status') == 'WARM' else 2)
        l = 0 if r.get('is_latino') == 'YES' else (1 if r.get('is_latino') == 'POSSIBLE' else 2)
        return (s, l)

    pending.sort(key=sort_key)

    # Definir columnas output
    sample = leads[0]
    base_cols = list(sample.keys())
    if 'email' not in base_cols:
        base_cols = base_cols + ['email']
    if 'source_csv' not in base_cols:
        base_cols = base_cols + ['source_csv']

    # Abrir output en modo append si hay progreso previo
    mode = 'a' if done_urls and not args.no_resume else 'w'
    output_f = open(OUTPUT_FILE, mode, newline='', encoding='utf-8')
    writer = csv.DictWriter(output_f, fieldnames=base_cols, extrasaction='ignore')
    if mode == 'w':
        writer.writeheader()

    session = requests.Session()
    session.max_redirects = 5

    found   = 0
    no_email = 0
    errors  = 0
    start   = datetime.now()

    log.info(f"Iniciando scraping de {len(pending)} leads...")
    log.info("-" * 60)

    for i, lead in enumerate(pending, 1):
        name    = lead.get('name', 'N/A')
        website = lead.get('website', '')
        source  = lead.get('source_csv', '')
        status  = lead.get('status', '')
        is_lat  = lead.get('is_latino', '')

        lat_tag = f" [LATINO]" if is_lat == 'YES' else (" [POSIBLE]" if is_lat == 'POSSIBLE' else "")
        log.info(f"[{i}/{len(pending)}] {status}{lat_tag} | {name[:45]}")
        log.info(f"  {website[:70]}")

        try:
            email = scrape_website(website, session)
        except Exception as e:
            email = 'ERROR'
            errors += 1
            log.warning(f"  ERROR: {e}")

        if email not in ('NO EMAIL', 'ERROR'):
            found += 1
            log.info(f"  EMAIL: {email}")
        else:
            no_email += 1
            log.info(f"  {email}")

        lead['email'] = email
        writer.writerow(lead)
        output_f.flush()

        time.sleep(DELAY)

    output_f.close()

    elapsed = (datetime.now() - start).seconds
    log.info("=" * 60)
    log.info(f"COMPLETADO en {elapsed}s")
    log.info(f"  Procesados: {len(pending)}")
    log.info(f"  Con email:  {found}  ({found/len(pending)*100:.1f}%)")
    log.info(f"  Sin email:  {no_email}")
    log.info(f"  Errores:    {errors}")
    log.info(f"  Output:     {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
