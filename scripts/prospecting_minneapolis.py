"""
============================================================
  Script de Prospección - Contratistas en Minneapolis, MN
  Usa Google Maps Places API para encontrar negocios
  sin sitio web o con presencia digital deficiente.
============================================================
  SETUP:
    pip install requests pandas
  
  USO:
    1. Reemplaza YOUR_API_KEY_HERE con tu Google Maps API key
    2. Ejecuta: python prospecting_minneapolis.py
    3. Abre el archivo leads_minneapolis.csv generado
============================================================
"""

import requests
import pandas as pd
import time
import csv
import os
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIGURACIÓN  ← solo edita esta sección
# ─────────────────────────────────────────
API_KEY     = "AIzaSyCgXj-Tt1WyXzZH1aU1TFVBsjxapcDiODc"
CITY        = "Minneapolis, MN"
SEARCH_TERMS = [
    "general contractor Minneapolis",
    "roofing contractor Minneapolis",
    "plumber Minneapolis",
    "electrician Minneapolis",
    "remodeling contractor Minneapolis",
    "HVAC contractor Minneapolis",
    "painting contractor Minneapolis",
    "landscaping contractor Minneapolis",
]
OUTPUT_FILE = "leads_minneapolis.csv"
MAX_RESULTS_PER_SEARCH = 60   # máximo 60 por término (3 páginas de 20)
MIN_RATING_TO_INCLUDE  = 0    # incluir todos (sube a 3.5 para filtrar los peores)
# ─────────────────────────────────────────

BASE_URL = "https://maps.googleapis.com/maps/api/place"


def search_places(query, page_token=None):
    """Busca negocios usando Places API Text Search."""
    params = {
        "query": query,
        "key": API_KEY,
        "type": "business",
    }
    if page_token:
        params["pagetoken"] = page_token
        time.sleep(2)  # Google requiere espera antes de usar next_page_token

    resp = requests.get(f"{BASE_URL}/textsearch/json", params=params)
    resp.raise_for_status()
    return resp.json()


def get_place_details(place_id):
    """Obtiene detalles adicionales de un lugar: website, phone, hours."""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,business_status",
        "key": API_KEY,
    }
    resp = requests.get(f"{BASE_URL}/details/json", params=params)
    resp.raise_for_status()
    return resp.json().get("result", {})


def score_lead(details):
    """
    Asigna un score de 1-10 al lead basado en señales de presencia digital débil.
    Mayor score = mayor oportunidad de venta.
    """
    score = 5  # base

    # Sin sitio web → máxima oportunidad
    if not details.get("website"):
        score += 4
    # Pocas reseñas → negocio pequeño, más fácil de cerrar
    reviews = details.get("user_ratings_total", 0)
    if reviews < 20:
        score += 2
    elif reviews < 50:
        score += 1
    # Rating bajo → puede necesitar más que solo web (reputación)
    rating = details.get("rating", 0)
    if 0 < rating < 3.5:
        score -= 1  # cliente potencialmente difícil

    return min(score, 10)


def qualify_lead(details, score):
    """Devuelve etiqueta de calificación basada en score."""
    if score >= 8:
        return "HOT"
    elif score >= 6:
        return "WARM"
    else:
        return "COLD"


def already_collected(place_id, seen_ids):
    """Evita duplicados."""
    return place_id in seen_ids


def run_prospecting():
    print(f"\n{'='*55}")
    print(f"  Prospección: Contratistas en {CITY}")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    all_leads = []
    seen_ids  = set()

    for term in SEARCH_TERMS:
        print(f"  Buscando: '{term}'...")
        page_token = None
        results_this_term = 0

        while results_this_term < MAX_RESULTS_PER_SEARCH:
            data = search_places(term, page_token)

            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                print(f"    ⚠ API error: {data.get('status')} — {data.get('error_message','')}")
                break

            places = data.get("results", [])
            if not places:
                break

            for place in places:
                place_id = place["place_id"]
                if already_collected(place_id, seen_ids):
                    continue
                seen_ids.add(place_id)

                # Obtener detalles completos
                details = get_place_details(place_id)
                time.sleep(0.1)  # rate limit amigable

                rating  = details.get("rating", 0)
                if rating and rating < MIN_RATING_TO_INCLUDE:
                    continue

                score  = score_lead(details)
                status = qualify_lead(details, score)

                lead = {
                    "status":        status,
                    "score":         score,
                    "name":          details.get("name", ""),
                    "address":       details.get("formatted_address", ""),
                    "phone":         details.get("formatted_phone_number", ""),
                    "website":       details.get("website", "NO WEBSITE"),
                    "rating":        details.get("rating", ""),
                    "reviews":       details.get("user_ratings_total", 0),
                    "business_status": details.get("business_status", ""),
                    "search_term":   term,
                    "place_id":      place_id,
                    "contacted":     "NO",
                    "notes":         "",
                }
                all_leads.append(lead)
                results_this_term += 1

                icon = "🔥" if status == "HOT" else ("✓" if status == "WARM" else "·")
                web_label = "NO WEB" if not details.get("website") else "has web"
                print(f"    {icon} [{status:4s}] {details.get('name','')[:40]:40s}  {web_label}")

            page_token = data.get("next_page_token")
            if not page_token:
                break

        print(f"    → {results_this_term} leads encontrados para este término\n")

    # Ordenar por score descendente
    all_leads.sort(key=lambda x: x["score"], reverse=True)

    # Guardar CSV
    if all_leads:
        df = pd.DataFrame(all_leads)
        df.to_csv(OUTPUT_FILE, index=False)
        
        hot  = sum(1 for l in all_leads if l["status"] == "HOT")
        warm = sum(1 for l in all_leads if l["status"] == "WARM")
        no_web = sum(1 for l in all_leads if l["website"] == "NO WEBSITE")

        print(f"\n{'='*55}")
        print(f"  RESUMEN FINAL")
        print(f"{'='*55}")
        print(f"  Total leads únicos : {len(all_leads)}")
        print(f"  HOT  (score 8-10)  : {hot}")
        print(f"  WARM (score 6-7)   : {warm}")
        print(f"  Sin sitio web      : {no_web}")
        print(f"  Archivo guardado   : {OUTPUT_FILE}")
        print(f"{'='*55}\n")
        print("  PRÓXIMO PASO: Abre el CSV y empieza por los HOT leads.")
        print("  Busca su web en Google — si dice 'NO WEBSITE' son tu target #1.\n")
    else:
        print("  No se encontraron leads. Verifica tu API key y que la Places API esté activa.")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n  ⚠ ERROR: Reemplaza YOUR_API_KEY_HERE con tu Google Maps API key real.\n")
    else:
        run_prospecting()
