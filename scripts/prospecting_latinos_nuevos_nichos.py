"""
============================================================
  Prospección — Nuevos Nichos Latinos en USA
  Nichos: Legal · Salud · Restaurantes · Real Estate
          Plomería · Pintura · Lawn Care · Limpieza · Préstamos

  Ciudades: expansión más allá del script original
  Detecta automáticamente negocios con nombres/keywords latinos

  USO:
    python scripts/prospecting_latinos_nuevos_nichos.py
    python scripts/prospecting_latinos_nuevos_nichos.py --nichos legal salud
    python scripts/prospecting_latinos_nuevos_nichos.py --ciudad "San Antonio, TX"
    python scripts/prospecting_latinos_nuevos_nichos.py --limit 50
============================================================
"""

import requests
import csv
import time
import re
import argparse
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────
API_KEY     = "AIzaSyCgXj-Tt1WyXzZH1aU1TFVBsjxapcDiODc"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "leads" / "leads_nuevos_nichos.csv"

# Ciudades con alta concentración latina en USA
CITIES = [
    "Minneapolis, MN",
    "San Antonio, TX",
    "El Paso, TX",
    "McAllen, TX",
    "Laredo, TX",
    "Salinas, CA",
    "Fresno, CA",
    "San Jose, CA",
    "Santa Ana, CA",
    "Oxnard, CA",
    "Hialeah, FL",
    "Orlando, FL",
    "Albuquerque, NM",
    "Chicago, IL",
    "Houston, TX",
    "Dallas, TX",
    "Miami, FL",
    "Denver, CO",
    "Phoenix, AZ",
]

# Nichos nuevos con términos de búsqueda
SEARCH_TERMS = {
    "Legal": [
        "abogado inmigracion",
        "abogado latino",
        "immigration attorney hispanic",
        "notario publico latino",
        "abogado accidentes hispano",
    ],
    "Salud": [
        "clinica latina",
        "doctor hispano",
        "medico latino",
        "clinica hispana",
        "dentista latino",
        "dentista hispano",
    ],
    "Restaurante": [
        "restaurante mexicano",
        "restaurante latino",
        "taqueria",
        "comida latina",
        "pupuseria",
        "restaurante centroamericano",
    ],
    "Real Estate": [
        "realtor latino",
        "agente inmobiliario hispano",
        "real estate agent latino",
        "corredor inmobiliario hispano",
        "bienes raices latino",
    ],
    "Plomeria": [
        "plomero latino",
        "plumber hispano",
        "plomeria latina",
        "plumbing latino",
    ],
    "Pintura": [
        "pintor latino",
        "painter hispanic",
        "pintura contratista hispano",
        "painting contractor latino",
    ],
    "Lawn Care": [
        "jardinero latino",
        "lawn care hispano",
        "landscaping latino",
        "corte de cesped latino",
    ],
    "Limpieza": [
        "limpieza de casas latina",
        "cleaning service hispano",
        "servicio limpieza latino",
        "house cleaning hispanic",
    ],
    "Prestamos": [
        "prestamos hispano",
        "financial services latino",
        "servicios financieros hispano",
        "credit union latino",
    ],
}
# ─────────────────────────────────────────

BASE_URL = "https://maps.googleapis.com/maps/api/place"

# ── Detección de nombres latinos ──────────────────────────

LATIN_SURNAMES = {
    "garcia","rodriguez","martinez","hernandez","lopez","gonzalez","perez",
    "sanchez","ramirez","torres","flores","rivera","gomez","diaz","reyes",
    "morales","jimenez","ruiz","alvarez","romero","vargas","mendoza","castillo",
    "ramos","ortega","chavez","moreno","medina","aguilar","vega","castro",
    "guerrero","mendez","silva","rojas","leon","herrera","delgado","nunez",
    "contreras","soto","rios","espinoza","padilla","fuentes","carrillo",
    "corona","salazar","campos","mejia","santiago","velasquez","avila",
    "acosta","molina","serrano","figueroa","cabrera","pena","suarez",
    "macias","murillo","trejo","lara","sandoval","meza","ibarra","ochoa",
    "baquero","becerra","benitez","jacobson",
}

LATIN_FIRST_NAMES = {
    "juan","jose","carlos","miguel","luis","jorge","francisco","antonio",
    "manuel","alejandro","pedro","marco","mario","roberto","ricardo",
    "sergio","fernando","pablo","rafael","arturo","hector","keyner",
    "hugo","oscar","andres","felipe","javier","raul","ruben","ernesto",
    "maria","ana","rosa","guadalupe","carmen","patricia","lucia","elena",
    "diana","laura","sofia","isabel","claudia","veronica","adriana",
    "jessica","alejandra","daniela","fernanda","cristina","monica",
    "gerardo","raul","artemisa","quintin",
}

LATIN_KEYWORDS = {
    "latino","latina","hispano","hispana","espanol","espanola",
    "mexicano","mexicana","centroamericano","guatemalteco","salvadoreno",
    "hondureno","nicaraguense","colombiano","venezolano","peruano",
    "ecuatoriano","dominicano","puertorriqueno","cubano",
    "hermanos","hermanas","familia","brothers","hijos","hijo",
    "vaquita","abogada","clinica","taqueria","pupuseria",
}

SPANISH_WORDS = {
    "construccion","remodelacion","techado","calefaccion","plomeria",
    "pintura","limpieza","jardineria","prestamos","seguros","inmobiliaria",
    "bienes","raices","servicios","grupo","equipo","empresa","compania",
    "soluciones","pro","plus","express","rapido","bueno","grande",
    "nuevo","primera","premier","quality","quality",
}


def is_latino(name: str) -> str:
    name_lower = name.lower()
    words = re.split(r"[\s&\-,.']+", name_lower)

    for word in words:
        if word in LATIN_SURNAMES:
            return "YES"
        if word in LATIN_FIRST_NAMES:
            return "YES"
        if word in LATIN_KEYWORDS:
            return "YES"
        if word in SPANISH_WORDS:
            return "POSSIBLE"

    return "NO"


def score_lead(place: dict, niche: str, latino: str) -> int:
    score = 0
    rating  = float(place.get("rating", 0) or 0)
    reviews = int(place.get("user_ratings_total", 0) or 0)

    if latino == "YES":
        score += 5
    elif latino == "POSSIBLE":
        score += 2

    if rating >= 4.5:
        score += 2
    elif rating >= 4.0:
        score += 1

    if reviews >= 50:
        score += 2
    elif reviews >= 10:
        score += 1

    website = place.get("website", "")
    if not website:
        score += 1  # sin web → oportunidad de landing

    return score


def pitch_line(name: str, city: str, niche: str, has_web: bool, reviews: int) -> str:
    city_short = city.split(",")[0]
    if not has_web:
        return (
            f"Hola, vi que {name} no tiene pagina web todavia. "
            f"Sus competidores en {city_short} estan consiguiendo clientes en Google que usted esta perdiendo."
        )
    elif reviews >= 50:
        return (
            f"{name} tiene {reviews} resenas — eso significa que su telefono suena. "
            f"Le instalo un sistema que contesta, califica y agenda automaticamente 24/7."
        )
    else:
        return (
            f"{name} ya tiene presencia en Google pero puede aparecer mas arriba en {city_short}. "
            f"Le instalo SEO local + IA que responde llamadas automaticamente."
        )


def search_places(query: str, city: str) -> list:
    results = []
    params = {
        "query": f"{query} in {city}",
        "key":   API_KEY,
        "type":  "establishment",
    }
    url = f"{BASE_URL}/textsearch/json"

    while True:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            break

        for place in data.get("results", []):
            results.append(place)

        next_token = data.get("next_page_token")
        if not next_token:
            break

        params = {"pagetoken": next_token, "key": API_KEY}
        time.sleep(2)

    return results


def load_existing(output_file: Path) -> set:
    if not output_file.exists():
        return set()
    seen = set()
    with open(output_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row.get("place_id", "").strip()
            if pid:
                seen.add(pid)
    return seen


FIELDNAMES = [
    "status","score","is_latino","outreach_language","niche",
    "recommended_service","pitch_line","name","city","address",
    "phone","website","rating","reviews","business_status",
    "search_term","place_id","contacted","ghl_uploaded","email","notes",
]


def run(selected_nichos: list = None, extra_city: str = None, limit: int = 0):
    cities  = CITIES + ([extra_city] if extra_city else [])
    nichos  = selected_nichos or list(SEARCH_TERMS.keys())
    seen    = load_existing(OUTPUT_FILE)
    total   = 0
    nuevos  = 0

    file_exists = OUTPUT_FILE.exists()
    fout = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fout, fieldnames=FIELDNAMES)
    if not file_exists:
        writer.writeheader()

    print(f"\n{'='*60}")
    print(f"  Prospección Nuevos Nichos Latinos")
    print(f"  Nichos:   {', '.join(nichos)}")
    print(f"  Ciudades: {len(cities)}")
    print(f"  Ya en CSV: {len(seen)} leads")
    print(f"{'='*60}\n")

    try:
        for city in cities:
            for niche in nichos:
                if niche not in SEARCH_TERMS:
                    continue
                for term in SEARCH_TERMS[niche]:
                    print(f"  Buscando: '{term}' en {city}...")
                    places = search_places(term, city)

                    for place in places:
                        total += 1
                        pid = place.get("place_id", "")
                        if pid in seen:
                            continue

                        name    = place.get("name", "")
                        address = place.get("formatted_address", "")
                        rating  = place.get("rating", "")
                        reviews = int(place.get("user_ratings_total", 0) or 0)
                        website = place.get("website", "")
                        phone   = place.get("formatted_phone_number", "")
                        status  = place.get("business_status", "OPERATIONAL")

                        latino   = is_latino(name)
                        sc       = score_lead(place, niche, latino)
                        has_web  = bool(website)
                        lang     = "Espanol" if latino in ("YES", "POSSIBLE") else "English"

                        if not has_web:
                            service = "Diseno web / Landing page"
                        elif reviews >= 100:
                            service = "Automatizacion con IA"
                        elif reviews < 20:
                            service = "SEO y posicionamiento"
                        else:
                            service = "Automatizacion con IA"

                        lead_status = "HOT" if sc >= 5 else "WARM" if sc >= 3 else "COLD"

                        row = {
                            "status":               lead_status,
                            "score":                sc,
                            "is_latino":            latino,
                            "outreach_language":    lang,
                            "niche":                niche,
                            "recommended_service":  service,
                            "pitch_line":           pitch_line(name, city, niche, has_web, reviews),
                            "name":                 name,
                            "city":                 city,
                            "address":              address,
                            "phone":                phone,
                            "website":              website,
                            "rating":               rating,
                            "reviews":              reviews,
                            "business_status":      status,
                            "search_term":          term,
                            "place_id":             pid,
                            "contacted":            "NO",
                            "ghl_uploaded":         "NO",
                            "email":                "",
                            "notes":                "",
                        }
                        writer.writerow(row)
                        seen.add(pid)
                        nuevos += 1

                        if limit and nuevos >= limit:
                            raise StopIteration

                    time.sleep(1)
    except StopIteration:
        pass
    finally:
        fout.close()

    print(f"\n{'='*60}")
    print(f"  RESUMEN")
    print(f"  Encontrados en Google Maps: {total}")
    print(f"  Nuevos en CSV:              {nuevos}")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"{'='*60}\n")

    # Mini resumen de HOT por nicho
    if nuevos > 0:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            all_rows = list(csv.DictReader(f))
        nuevos_rows = all_rows[-nuevos:]
        from collections import Counter
        hot_by_niche = Counter(r["niche"] for r in nuevos_rows if r["status"] == "HOT")
        latinos_hot  = [r for r in nuevos_rows if r["status"] == "HOT" and r["is_latino"] in ("YES","POSSIBLE")]
        print(f"  HOT por nicho: {dict(hot_by_niche)}")
        print(f"  Latinos HOT:   {len(latinos_hot)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nichos", nargs="+", default=None,
                        help="Nichos a buscar: legal salud restaurante real_estate plomeria pintura lawn_care limpieza prestamos")
    parser.add_argument("--ciudad", default=None, help="Ciudad extra a agregar")
    parser.add_argument("--limit",  type=int, default=0, help="Maximo de leads nuevos")
    args = parser.parse_args()
    run(selected_nichos=args.nichos, extra_city=args.ciudad, limit=args.limit)
