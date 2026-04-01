"""
Enriquece leads_nuevos_nichos.csv con website + phone via Google Maps Place Details API.
Actualiza el CSV in-place. Reanuda desde donde quedó.

USO:
  python scripts/enrich_leads.py
  python scripts/enrich_leads.py --limit 200
"""
import csv, time, requests, argparse, sys
from pathlib import Path

API_KEY = "AIzaSyCgXj-Tt1WyXzZH1aU1TFVBsjxapcDiODc"
ROOT    = Path(__file__).resolve().parent.parent
CSV_IN  = ROOT / "leads" / "leads_nuevos_nichos.csv"

def get_details(place_id: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    r = requests.get(url, params={
        "place_id": place_id,
        "fields":   "website,formatted_phone_number",
        "key":      API_KEY,
    }, timeout=10)
    result = r.json().get("result", {})
    return {
        "website": result.get("website", ""),
        "phone":   result.get("formatted_phone_number", ""),
    }

def run(limit=0):
    with open(CSV_IN, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Solo los que no tienen website ni phone aún
    pending = [r for r in rows if not r.get("website","").strip() and r.get("place_id","").strip()]
    if limit:
        pending = pending[:limit]

    print(f"Total leads: {len(rows)} | Pendientes de enriquecer: {len(pending)}")

    enriched = 0
    for i, row in enumerate(pending, 1):
        pid = row["place_id"].strip()
        try:
            details = get_details(pid)
            # Actualizar en rows original
            for r in rows:
                if r["place_id"] == pid:
                    r["website"] = details["website"]
                    r["phone"]   = details["phone"]
                    break
            if details["website"] or details["phone"]:
                enriched += 1
            if i % 20 == 0:
                print(f"  [{i}/{len(pending)}] enriquecidos con datos: {enriched}")
                # Guardar progreso cada 20
                with open(CSV_IN, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
        except Exception as e:
            print(f"  Error en {pid}: {e}")
        time.sleep(0.1)

    # Guardar final
    with open(CSV_IN, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    con_web = [r for r in rows if r.get("website","").strip()]
    con_phone = [r for r in rows if r.get("phone","").strip()]
    print(f"\nResumen:")
    print(f"  Con website: {len(con_web)}")
    print(f"  Con telefono: {len(con_phone)}")
    print(f"  CSV actualizado: {CSV_IN}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    run(limit=args.limit)
