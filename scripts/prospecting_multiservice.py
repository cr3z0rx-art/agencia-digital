"""
============================================================
  Script de Prospección Multi-Servicio - Minneapolis, MN
  Detecta automáticamente qué servicio necesita cada negocio:
    - Diseño web / landing page
    - SEO y posicionamiento
    - Automatización con IA
============================================================
  SETUP:
    pip install requests pandas

  USO:
    1. Reemplaza YOUR_API_KEY_HERE con tu Google Maps API key
    2. Ejecuta: python prospecting_multiservice.py
    3. Abre leads_multiservice.csv — ya viene con el servicio
       recomendado para cada lead
============================================================
"""

import requests
import pandas as pd
import time
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIGURACIÓN  ← solo edita esta sección
# ─────────────────────────────────────────
API_KEY     = "AIzaSyCgXj-Tt1WyXzZH1aU1TFVBsjxapcDiODc"
OUTPUT_FILE = "leads_multiservice.csv"

# Negocios a buscar por categoría de servicio
SEARCHES = {

    "Diseño web / Landing page": [
        "general contractor Minneapolis",
        "roofing contractor Minneapolis",
        "plumber Minneapolis",
        "electrician Minneapolis",
        "painting contractor Minneapolis",
        "landscaping Minneapolis",
        "auto repair Minneapolis",
        "cleaning service Minneapolis",
    ],

    "SEO y posicionamiento": [
        "dentist Minneapolis",
        "chiropractor Minneapolis",
        "law firm Minneapolis",
        "accountant Minneapolis",
        "real estate agent Minneapolis",
        "insurance agent Minneapolis",
        "gym fitness Minneapolis",
        "restaurant Minneapolis",
    ],

    "Automatización con IA": [
        "dental clinic Minneapolis",
        "medical clinic Minneapolis",
        "auto shop Minneapolis",
        "hair salon Minneapolis",
        "spa Minneapolis",
        "property management Minneapolis",
        "moving company Minneapolis",
        "catering Minneapolis",
    ],
}
# ─────────────────────────────────────────

BASE_URL = "https://maps.googleapis.com/maps/api/place"


def search_places(query, page_token=None):
    params = {
        "query": query,
        "key": API_KEY,
        "type": "business",
    }
    if page_token:
        params["pagetoken"] = page_token
        time.sleep(2)
    resp = requests.get(f"{BASE_URL}/textsearch/json", params=params)
    resp.raise_for_status()
    return resp.json()


def get_place_details(place_id):
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,business_status",
        "key": API_KEY,
    }
    resp = requests.get(f"{BASE_URL}/details/json", params=params)
    resp.raise_for_status()
    return resp.json().get("result", {})


def detect_service(details, default_service):
    """
    Refina el servicio recomendado basándose en las señales del negocio.
    La categoría default viene del bloque SEARCHES, pero puede ajustarse.
    """
    has_website  = bool(details.get("website"))
    rating       = details.get("rating", 0) or 0
    reviews      = details.get("user_ratings_total", 0) or 0

    # Sin web → siempre landing page es la prioridad
    if not has_website:
        return "Diseño web / Landing page"

    # Tiene web pero pocas reseñas o rating bajo → SEO
    if has_website and (reviews < 30 or rating < 3.8):
        return "SEO y posicionamiento"

    # Tiene web y buenas reseñas pero es negocio de servicios → IA
    if has_website and reviews >= 30 and rating >= 3.8:
        return "Automatización con IA"

    return default_service


def score_lead(details, service):
    """Score de 1-10 según oportunidad de venta."""
    score = 5
    has_website = bool(details.get("website"))
    reviews     = details.get("user_ratings_total", 0) or 0
    rating      = details.get("rating", 0) or 0

    if service == "Diseño web / Landing page":
        if not has_website:
            score += 4
        if reviews < 20:
            score += 1

    elif service == "SEO y posicionamiento":
        if has_website and reviews < 30:
            score += 3
        if rating < 4.0:
            score += 1
        if reviews < 10:
            score += 1

    elif service == "Automatización con IA":
        if has_website and reviews >= 30:
            score += 2
        if rating >= 4.0:
            score += 1
        # Negocios muy ocupados (muchas reseñas) necesitan más automatización
        if reviews >= 100:
            score += 2

    return min(score, 10)


def qualify(score):
    if score >= 8:
        return "HOT"
    elif score >= 6:
        return "WARM"
    return "COLD"


def pitch_line(service, details):
    """Genera una línea de pitch corta y personalizada para el outreach."""
    name = details.get("name", "your business")
    reviews = details.get("user_ratings_total", 0) or 0

    if service == "Diseño web / Landing page":
        return f"We noticed {name} doesn't have a website — local competitors are winning online customers you're missing."

    elif service == "SEO y posicionamiento":
        if reviews < 20:
            return f"{name} has great potential but isn't showing up when Minneapolis customers search online."
        return f"With {reviews} reviews, {name} deserves to rank #1 in Minneapolis — SEO can get you there."

    elif service == "Automatización con IA":
        return f"Businesses like {name} are saving 10+ hours/week using AI to handle bookings, follow-ups, and customer messages."

    return ""


def run():
    print(f"\n{'='*58}")
    print(f"  Prospección Multi-Servicio — Minneapolis, MN")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*58}\n")

    all_leads = []
    seen_ids  = set()

    for default_service, terms in SEARCHES.items():
        print(f"\n  Categoría: {default_service}")
        print(f"  {'─'*50}")

        for term in terms:
            print(f"  Buscando: '{term}'...")
            page_token = None
            count = 0

            while count < 40:
                data = search_places(term, page_token)
                status = data.get("status")

                if status not in ("OK", "ZERO_RESULTS"):
                    print(f"    ⚠ API error: {status} — {data.get('error_message','')}")
                    break

                places = data.get("results", [])
                if not places:
                    break

                for place in places:
                    pid = place["place_id"]
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)

                    details = get_place_details(pid)
                    time.sleep(0.1)

                    service = detect_service(details, default_service)
                    score   = score_lead(details, service)
                    status_label = qualify(score)
                    pitch   = pitch_line(service, details)

                    lead = {
                        "status":          status_label,
                        "score":           score,
                        "recommended_service": service,
                        "pitch_line":      pitch,
                        "name":            details.get("name", ""),
                        "address":         details.get("formatted_address", ""),
                        "phone":           details.get("formatted_phone_number", ""),
                        "website":         details.get("website", "NO WEBSITE"),
                        "rating":          details.get("rating", ""),
                        "reviews":         details.get("user_ratings_total", 0),
                        "business_status": details.get("business_status", ""),
                        "search_term":     term,
                        "place_id":        pid,
                        "contacted":       "NO",
                        "ghl_uploaded":    "NO",
                        "notes":           "",
                    }
                    all_leads.append(lead)
                    count += 1

                    icon = "🔥" if status_label == "HOT" else ("✓" if status_label == "WARM" else "·")
                    web  = "NO WEB" if not details.get("website") else "has web"
                    print(f"    {icon} [{status_label:4s}] {details.get('name','')[:38]:38s}  {web:7s}  → {service[:25]}")

                page_token = data.get("next_page_token")
                if not page_token:
                    break

    # Ordenar: HOT primero, luego por score
    all_leads.sort(key=lambda x: (x["status"] != "HOT", x["status"] != "WARM", -x["score"]))

    if all_leads:
        df = pd.DataFrame(all_leads)
        df.to_csv(OUTPUT_FILE, index=False)

        hot   = sum(1 for l in all_leads if l["status"] == "HOT")
        warm  = sum(1 for l in all_leads if l["status"] == "WARM")
        no_web = sum(1 for l in all_leads if l["website"] == "NO WEBSITE")

        web_leads = sum(1 for l in all_leads if l["recommended_service"] == "Diseño web / Landing page")
        seo_leads = sum(1 for l in all_leads if l["recommended_service"] == "SEO y posicionamiento")
        ai_leads  = sum(1 for l in all_leads if l["recommended_service"] == "Automatización con IA")

        print(f"\n{'='*58}")
        print(f"  RESUMEN FINAL")
        print(f"{'='*58}")
        print(f"  Total leads únicos    : {len(all_leads)}")
        print(f"  HOT  (score 8-10)     : {hot}")
        print(f"  WARM (score 6-7)      : {warm}")
        print(f"  Sin sitio web         : {no_web}")
        print(f"  {'─'*40}")
        print(f"  → Diseño web          : {web_leads} leads")
        print(f"  → SEO                 : {seo_leads} leads")
        print(f"  → Automatización IA   : {ai_leads} leads")
        print(f"  {'─'*40}")
        print(f"  Archivo guardado      : {OUTPUT_FILE}")
        print(f"{'='*58}")
        print(f"""
  PRÓXIMOS PASOS:
  1. Abre {OUTPUT_FILE} en Excel
  2. Filtra por status = HOT
  3. Lee la columna 'pitch_line' — ya tiene el mensaje
     de apertura personalizado para cada negocio
  4. Sube los HOT leads a GHL y activa la secuencia
""")
    else:
        print("  No se encontraron leads. Verifica tu API key.")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n  ⚠ ERROR: Reemplaza YOUR_API_KEY_HERE con tu Google Maps API key.\n")
    else:
        run()
        
