"""
============================================================
  Script de Prospección — Contratistas Latinos en USA
  Nichos: Roofing · Remodeling · HVAC
  Cobertura: Todo USA (ciudades configurables)
  Detecta automáticamente negocios con nombres latinos
============================================================
  SETUP:
    pip install requests pandas

  USO:
    1. Reemplaza YOUR_API_KEY_HERE con tu Google Maps API key
    2. Ajusta CITIES si quieres agregar o quitar ciudades
    3. Ejecuta: python prospecting_latinos_usa.py
    4. Abre leads_latinos_usa.csv — ya viene con:
       - is_latino (YES/NO/POSSIBLE)
       - idioma recomendado para el outreach
       - pitch_line personalizado en español o inglés
============================================================
"""

import requests
import pandas as pd
import time
import re
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIGURACIÓN  ← edita esta sección
# ─────────────────────────────────────────
API_KEY     = "AIzaSyCgXj-Tt1WyXzZH1aU1TFVBsjxapcDiODc"
OUTPUT_FILE = "leads_latinos_usa.csv"

# Ciudades con alta concentración de contratistas latinos
# Puedes agregar cualquier ciudad de USA
CITIES = [
    "Minneapolis, MN",
    "Chicago, IL",
    "Houston, TX",
    "Dallas, TX",
    "Los Angeles, CA",
    "Miami, FL",
    "Denver, CO",
    "Phoenix, AZ",
    "Atlanta, GA",
    "New York, NY",
]

# Términos de búsqueda en inglés y español por nicho
SEARCH_TERMS = {
    "Roofing": [
        "roofing contractor",
        "roofing company",
        "techo contratista",
        "techeros",
        "roof repair latino",
        "roofing hispano",
    ],
    "Remodeling": [
        "remodeling contractor",
        "home remodeling",
        "construccion general",
        "contratista remodelacion",
        "home renovation latino",
        "remodeling hispano",
    ],
    "HVAC": [
        "HVAC contractor",
        "heating cooling contractor",
        "aire acondicionado contratista",
        "calefaccion reparacion",
        "HVAC latino",
        "HVAC hispano",
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
    "acosta","molina","serrano","figueroa","cabrera","guerrero","pena",
    "macias","murillo","trejo","lara","sandoval","meza","ibarra","ochoa",
}

LATIN_FIRST_NAMES = {
    "juan","jose","carlos","miguel","luis","jorge","francisco","antonio",
    "manuel","alejandro","pedro","marco","mario","roberto","ricardo",
    "Eduardo","sergio","fernando","pablo","rafael","arturo","hector",
    "hugo","oscar","andres","felipe","javier","raul","ruben","ernesto",
    "maria","ana","rosa","guadalupe","carmen","patricia","lucia","elena",
    "diana","laura","sofia","isabel","claudia","veronica","adriana",
    "jessica","alejandra","daniela","fernanda","cristina","monica",
}

LATIN_KEYWORDS = {
    "latino","latina","hispano","hispana","español","española",
    "mexicano","mexicana","centroamericano","guatemalteco","salvadoreno",
    "hondureno","nicaraguense","colombiano","venezolano","peruano",
    "ecuatoriano","dominicano","puertorriqueno","cubano",
    "hermanos","hermanas","familia","brothers","hijos","hijo",
    "grupo","servicios","construcciones","remodelaciones","techados",
    "sol","luna","aguila","estrella","paloma","azteca","maya",
}

LATIN_BUSINESS_WORDS = {
    "construcciones","remodelaciones","techados","servicios","grupo",
    "hermanos","familia","empresa","compania",
}


def detect_latino(name):
    """
    Analiza el nombre del negocio y retorna:
    - 'YES'      : claramente latino
    - 'POSSIBLE' : señales débiles
    - 'NO'       : sin señales
    """
    if not name:
        return "NO", 0

    name_lower = name.lower()
    words = re.findall(r"[a-záéíóúüñ]+", name_lower)
    score = 0
    reasons = []

    # Apellidos latinos en el nombre del negocio
    for w in words:
        if w in LATIN_SURNAMES:
            score += 4
            reasons.append(f"apellido:{w}")
            break

    # Nombres de pila latinos
    for w in words:
        if w in LATIN_FIRST_NAMES:
            score += 2
            reasons.append(f"nombre:{w}")
            break

    # Palabras clave explícitas (latino, hispano, etc.)
    for w in words:
        if w in LATIN_KEYWORDS:
            score += 5
            reasons.append(f"keyword:{w}")
            break

    # Palabras de negocio en español
    for w in words:
        if w in LATIN_BUSINESS_WORDS:
            score += 3
            reasons.append(f"negocio_es:{w}")
            break

    # Caracteres con tilde o ñ → fuerte señal
    if re.search(r"[áéíóúüñ]", name_lower):
        score += 3
        reasons.append("acento_esp")

    # "& Sons", "& Hijos", "Hermanos" son señales de empresa familiar
    if re.search(r"\bhermanos\b|\bhijos\b|\bfamilia\b", name_lower):
        score += 3
        reasons.append("familia")

    if score >= 5:
        return "YES", score
    elif score >= 2:
        return "POSSIBLE", score
    else:
        return "NO", score


def search_places(query, page_token=None):
    params = {"query": query, "key": API_KEY, "type": "business"}
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


def score_lead(details, niche):
    score = 5
    has_web = bool(details.get("website"))
    reviews = details.get("user_ratings_total", 0) or 0
    rating  = details.get("rating", 0) or 0

    if not has_web:
        score += 4
    if reviews < 20:
        score += 2
    elif reviews < 50:
        score += 1
    if niche == "HVAC" and not has_web:
        score += 1  # urgencia extra en HVAC
    if rating and rating < 3.5:
        score -= 1

    return min(score, 10)


def qualify(score):
    if score >= 8:  return "HOT"
    if score >= 6:  return "WARM"
    return "COLD"


def recommended_service(details, niche):
    has_web = bool(details.get("website"))
    reviews = details.get("user_ratings_total", 0) or 0
    rating  = details.get("rating", 0) or 0

    if not has_web:
        return "Diseño web / Landing page"
    if has_web and (reviews < 30 or rating < 3.8):
        return "SEO y posicionamiento"
    return "Automatización con IA"


def build_pitch(details, niche, is_latino, service):
    """Genera pitch en español, inglés o spanglish según detección."""
    name    = details.get("name", "tu negocio")
    reviews = details.get("user_ratings_total", 0) or 0
    has_web = bool(details.get("website"))

    if is_latino == "YES":
        # Pitch en español
        if service == "Diseño web / Landing page":
            return (f"Hola, vi que {name} no tiene página web todavía. "
                    f"Sus competidores están consiguiendo clientes en Google que usted está perdiendo. "
                    f"Le puedo crear un sitio profesional en menos de una semana.")
        elif service == "SEO y posicionamiento":
            return (f"Hola, {name} tiene potencial pero no aparece cuando los clientes buscan "
                    f"en Google en su área. Con SEO local puede estar en el top 3 en 60 días.")
        else:
            return (f"Hola, negocios como {name} están ahorrando 10+ horas a la semana "
                    f"con un asistente de IA que responde llamadas y agenda citas automáticamente.")
    elif is_latino == "POSSIBLE":
        # Spanglish / bilingual
        if service == "Diseño web / Landing page":
            return (f"Hi! We noticed {name} doesn't have a website yet — "
                    f"también hablamos español si prefiere. "
                    f"We can build you a professional site in less than a week.")
        elif service == "SEO y posicionamiento":
            return (f"Hi! {name} has great reviews but isn't showing up on Google searches in your area. "
                    f"Podemos cambiar eso — SEO local gets you to the top 3 in 60 days.")
        else:
            return (f"Hi! Businesses like {name} are saving 10+ hours/week with AI "
                    f"that handles calls and bookings automatically — lo configuramos en un día.")
    else:
        # Inglés
        if service == "Diseño web / Landing page":
            return (f"Hi! We noticed {name} doesn't have a website — "
                    f"local competitors are winning the online customers you're missing. "
                    f"We can build a professional site in under a week.")
        elif service == "SEO y posicionamiento":
            return (f"Hi! {name} has great potential but isn't ranking on Google in your area. "
                    f"Local SEO can get you to the top 3 results in 60 days.")
        else:
            return (f"Hi! Businesses like {name} are saving 10+ hours/week using AI "
                    f"to handle calls, follow-ups, and bookings automatically.")


def run():
    print(f"\n{'='*60}")
    print(f"  Prospección Contratistas Latinos — Todo USA")
    print(f"  Nichos: Roofing · Remodeling · HVAC")
    print(f"  Ciudades: {len(CITIES)}")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    all_leads = []
    seen_ids  = set()

    for city in CITIES:
        print(f"\n  CIUDAD: {city}")
        print(f"  {'─'*50}")

        for niche, terms in SEARCH_TERMS.items():
            print(f"\n    Nicho: {niche}")

            for term in terms:
                query = f"{term} {city}"
                print(f"      Buscando: '{query}'...")
                page_token = None
                count = 0

                while count < 40:
                    try:
                        data = search_places(query, page_token)
                    except Exception as e:
                        print(f"        ⚠ Error: {e}")
                        break

                    api_status = data.get("status")
                    if api_status == "ZERO_RESULTS":
                        break
                    if api_status not in ("OK",):
                        print(f"        ⚠ API: {api_status} — {data.get('error_message','')}")
                        break

                    for place in data.get("results", []):
                        pid = place["place_id"]
                        if pid in seen_ids:
                            continue
                        seen_ids.add(pid)

                        try:
                            details = get_place_details(pid)
                        except Exception:
                            continue
                        time.sleep(0.1)

                        is_latino, latino_score = detect_latino(details.get("name", ""))

                        score   = score_lead(details, niche)
                        qlabel  = qualify(score)
                        service = recommended_service(details, niche)
                        pitch   = build_pitch(details, niche, is_latino, service)
                        lang    = "Español" if is_latino == "YES" else ("Spanglish" if is_latino == "POSSIBLE" else "English")

                        lead = {
                            "status":              qlabel,
                            "score":               score,
                            "is_latino":           is_latino,
                            "latino_score":        latino_score,
                            "outreach_language":   lang,
                            "niche":               niche,
                            "recommended_service": service,
                            "pitch_line":          pitch,
                            "name":                details.get("name", ""),
                            "city":                city,
                            "address":             details.get("formatted_address", ""),
                            "phone":               details.get("formatted_phone_number", ""),
                            "website":             details.get("website", "NO WEBSITE"),
                            "rating":              details.get("rating", ""),
                            "reviews":             details.get("user_ratings_total", 0),
                            "business_status":     details.get("business_status", ""),
                            "search_term":         term,
                            "place_id":            pid,
                            "contacted":           "NO",
                            "ghl_uploaded":        "NO",
                            "notes":               "",
                        }
                        all_leads.append(lead)
                        count += 1

                        icon  = "🔥" if qlabel == "HOT" else ("✓" if qlabel == "WARM" else "·")
                        lat   = "LATINO" if is_latino == "YES" else ("posible" if is_latino == "POSSIBLE" else "")
                        web   = "NO WEB" if not details.get("website") else "web"
                        print(f"      {icon} [{qlabel:4s}] {details.get('name','')[:35]:35s} {web:6s} {lat}")

                    page_token = data.get("next_page_token")
                    if not page_token:
                        break

    # Ordenar: Latinos HOT primero, luego POSSIBLE HOT, luego resto
    def sort_key(l):
        latino_order = {"YES": 0, "POSSIBLE": 1, "NO": 2}
        status_order = {"HOT": 0, "WARM": 1, "COLD": 2}
        return (latino_order[l["is_latino"]], status_order[l["status"]], -l["score"])

    all_leads.sort(key=sort_key)

    if all_leads:
        df = pd.DataFrame(all_leads)
        df.to_csv(OUTPUT_FILE, index=False)

        total     = len(all_leads)
        hot       = sum(1 for l in all_leads if l["status"] == "HOT")
        warm      = sum(1 for l in all_leads if l["status"] == "WARM")
        latinos   = sum(1 for l in all_leads if l["is_latino"] == "YES")
        posibles  = sum(1 for l in all_leads if l["is_latino"] == "POSSIBLE")
        no_web    = sum(1 for l in all_leads if l["website"] == "NO WEBSITE")
        lat_hot   = sum(1 for l in all_leads if l["is_latino"] == "YES" and l["status"] == "HOT")

        roofing   = sum(1 for l in all_leads if l["niche"] == "Roofing")
        remodel   = sum(1 for l in all_leads if l["niche"] == "Remodeling")
        hvac      = sum(1 for l in all_leads if l["niche"] == "HVAC")

        print(f"\n{'='*60}")
        print(f"  RESUMEN FINAL")
        print(f"{'='*60}")
        print(f"  Total leads únicos     : {total}")
        print(f"  HOT  (score 8-10)      : {hot}")
        print(f"  WARM (score 6-7)       : {warm}")
        print(f"  Sin sitio web          : {no_web}")
        print(f"  {'─'*40}")
        print(f"  Negocios LATINOS       : {latinos}")
        print(f"  Posibles latinos       : {posibles}")
        print(f"  LATINOS HOT (prioridad): {lat_hot}  ← empieza aquí")
        print(f"  {'─'*40}")
        print(f"  Roofing leads          : {roofing}")
        print(f"  Remodeling leads       : {remodel}")
        print(f"  HVAC leads             : {hvac}")
        print(f"  {'─'*40}")
        print(f"  Archivo guardado       : {OUTPUT_FILE}")
        print(f"{'='*60}")
        print(f"""
  PRÓXIMOS PASOS:
  1. Abre {OUTPUT_FILE} en Excel
  2. Filtra: is_latino = YES  y  status = HOT
  3. Esos son tus primeros 20 contactos esta semana
  4. La columna pitch_line ya tiene el mensaje en español
  5. Sube esos leads a GHL y activa la secuencia
""")
    else:
        print("  No se encontraron leads. Verifica tu API key.")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n  ⚠ ERROR: Reemplaza YOUR_API_KEY_HERE con tu Google Maps API key real.\n")
    else:
        run()
