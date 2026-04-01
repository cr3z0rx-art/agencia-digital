---
name: lead-qualifier
description: Qualify, score, and prioritize leads from CSV data to identify who to contact first. Use when analyzing leads, deciding who to call, updating HOT/WARM/COLD status, or determining the right service for a prospect. Trigger on: "qualify leads", "score leads", "who should I call first", "calificar leads", "priorizar leads", "qué tan hot es", "analyze CSV", or any lead prioritization task.
---

# Lead Qualifier

Califica y prioriza leads del CSV para saber exactamente a quién contactar hoy y con qué servicio.

## Archivos de leads disponibles
```
leads/leads_latinos_usa.csv     — 4,007 leads (10 latinos HOT = prioridad máx)
leads/leads_minneapolis.csv     — 431 leads (41 HOT locales)
leads/leads_multiservice.csv    — 979 leads (698 para AI Receptionist)
```

---

## Scoring model

### Score HOT (contactar esta semana)
Cumple 2+ de:
- `status = HOT`
- `website = NO WEBSITE` (oportunidad landing)
- `rating >= 4.5` Y `reviews >= 50` (negocio activo)
- `is_latino = YES` (ventaja de idioma)
- `ghl_uploaded = NO` (aún no en GHL)

### Score WARM (contactar semana 2–3)
- `status = WARM`
- Tiene web pero sin SEO aparente
- `reviews < 50` — negocio más pequeño

### Score COLD (outreach masivo automatizado)
- `status = COLD`
- `reviews < 10`
- Sin señales de actividad

---

## Prioridad por combinación

| is_latino | status | website | Prioridad | Acción |
|---|---|---|---|---|
| YES | HOT | NO WEBSITE | 🔴 MÁXIMA | Llamar HOY en español |
| YES | HOT | tiene web | 🔴 ALTA | Llamar esta semana |
| POSSIBLE | HOT | NO WEBSITE | 🟠 ALTA | Email + llamada |
| NO | HOT | NO WEBSITE | 🟠 MEDIA-ALTA | Email en inglés |
| YES | WARM | cualquiera | 🟡 MEDIA | Secuencia email |
| NO | WARM | cualquiera | 🟡 BAJA-MEDIA | Outreach masivo |

---

## Servicio recomendado por perfil

| Condición | Servicio recomendado |
|---|---|
| `website = NO WEBSITE` | AI Receptionist (incluye web) |
| `reviews >= 100` + tiene web | Full AI Employee + SEO |
| `reviews >= 200` + web + buen rating | Full AI Employee + SEO → demo AI |
| `recommended_service` ya en CSV | Usar ese directamente |

---

## Análisis rápido de un CSV

Cuando te dé un CSV, ejecuta este análisis:

```python
# Filtros a reportar:
1. Total leads por status (HOT/WARM/COLD)
2. Latinos HOT sin subir a GHL
3. HOT sin web (prioridad para landing)
4. HOT con 100+ reseñas (AI Receptionist)
5. Top 10 leads por score compuesto:
   (rating * log(reviews+1)) * is_hot_multiplier
```

**Output del análisis:**
```
📊 RESUMEN DE LEADS
Total: X leads
HOT: X | WARM: X | COLD: X

🔴 ACCIÓN INMEDIATA (llamar HOY):
1. [nombre] — [ciudad] — [nicho] — [razón]
2. ...

📧 EMAIL ESTA SEMANA:
[lista de los siguientes 10]

🤖 OUTREACH MASIVO (semana 2–3):
X leads en secuencia GHL
```

---

## Columnas clave del CSV

| Columna | Valores posibles | Uso |
|---|---|---|
| `status` | HOT / WARM / COLD | Prioridad base |
| `is_latino` | YES / POSSIBLE / NO | Idioma + ventaja |
| `website` | URL / NO WEBSITE | Servicio a ofrecer |
| `rating` | 0–5 | Calidad del negocio |
| `reviews` | número | Volumen de actividad |
| `ghl_uploaded` | YES / NO | Si ya está en CRM |
| `outreach_language` | SPANISH / ENGLISH / SPANGLISH | Idioma del email |
| `recommended_service` | texto | Servicio sugerido |
| `pitch_line` | texto | Gancho personalizado |
| `contacted` | YES / NO | Si ya fue contactado |

---

## Output final — lista de acción

Siempre terminar con una lista ordenada:

```
HOY (llamada directa):
1. [nombre] | [teléfono] | [ciudad] | [nicho] | Hablar en: [idioma]
   → Pitch: "[pitch_line]"

MAÑANA (email + llamada):
...

ESTA SEMANA (solo email):
...
```
