# Skill: csv-to-ghl

Sube leads del CSV a GHL con tags automáticos, verifica duplicados, carga el pitch en notas y marca ghl_uploaded=YES.

---

## Archivos
- `ghl-integration/ghl_client.py` — wrapper API (crear, buscar, notar contactos)
- `ghl-integration/upload_leads_to_ghl.py` — script principal

## Prerequisitos
`.env` con:
```
GHL_API_KEY=...
GHL_LOCATION_ID=...
```

```bash
pip install requests pandas python-dotenv
```

---

## Uso

### Caso más común — 10 latinos HOT pendientes
```bash
python ghl-integration/upload_leads_to_ghl.py
```
Filtra automáticamente: `status=HOT` + `is_latino=YES` + `ghl_uploaded=NO`

### Simular antes de subir (recomendado la primera vez)
```bash
python ghl-integration/upload_leads_to_ghl.py --dry-run
```

### Subir todos los HOT (todos los idiomas)
```bash
python ghl-integration/upload_leads_to_ghl.py --all-languages
```

### CSV diferente o status diferente
```bash
python ghl-integration/upload_leads_to_ghl.py --csv leads/leads_minneapolis.csv --status HOT
python ghl-integration/upload_leads_to_ghl.py --csv leads/leads_multiservice.csv --all-languages
```

---

## Qué hace por cada lead
1. Verifica `ghl_uploaded=NO` — skip si ya fue subido
2. Verifica duplicado por teléfono en GHL — skip si ya existe
3. Crea contacto con: nombre, teléfono, dirección, ciudad, web
4. Agrega tags: `nicho`, `hot/warm/cold`, `latino/posible-latino`, `servicio-web/seo/ia`, `idioma-español/english`
5. Agrega nota con: pitch_line, nicho, ciudad, servicio, rating, score
6. Marca `ghl_uploaded=YES` en el CSV

## Log
Cada ejecución genera `logs/ghl_upload_YYYYMMDD_HHMMSS.log`

---

## Cómo conseguir GHL_API_KEY y GHL_LOCATION_ID

**GHL_API_KEY:**
1. GHL → Settings → Company → Integrations → API Keys
2. Crear nuevo key → copiar

**GHL_LOCATION_ID:**
1. GHL → cualquier página de tu sub-cuenta
2. La URL tiene este formato: `app.gohighlevel.com/location/XXXXXXXX/...`
3. El ID es ese `XXXXXXXX`

O en Settings → Business Info → Location ID
