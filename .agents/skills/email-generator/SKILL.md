---
name: email-generator
description: Generate personalized outreach emails for leads using Claude API — by niche, language (Spanish/English/Spanglish), and service. Use this skill whenever you need to write cold outreach emails, follow-up sequences, or any email copy for contactor leads. Trigger on: "generate email", "write email for", "outreach email", "email sequence", "follow-up email", or whenever a lead's data is available and contact is needed.
---

# Email Generator

Genera emails de outreach personalizados para contratistas usando la información del lead (nicho, idioma, situación web, ciudad).

## Contexto del negocio
- Agencia: MultiVenza Digital
- Servicios: AI Receptionist ($500/mes), Full AI Employee + SEO ($800/mes), Lead Gen add-on ($300/mes)
- Mercado: Contratistas latinos y negocios hispanos en USA
- Firma siempre como: **Keyner** | MultiVenza Digital | hello@multivenzadigital.com

---

## Reglas de idioma
| `outreach_language` del lead | Idioma del email |
|---|---|
| `SPANISH` | 100% español |
| `ENGLISH` | 100% inglés |
| `SPANGLISH` | Mix natural — saludos en español, cuerpo en inglés |

---

## Inputs que necesitas del lead
```
name, business_name, city, niche (roofing/hvac/plumbing/remodeling),
recommended_service, pitch_line, rating, reviews, website (o NO WEBSITE),
outreach_language
```

---

## Secuencia de 3 emails por lead

### Email 1 — Contacto inicial (día 0)
**Objetivo:** Captar atención, mostrar que hiciste tarea, generar curiosidad.
**Longitud:** 4–6 líneas. Nada más.
**Estructura:**
1. Referencia específica a su negocio (ciudad + nicho + situación real)
2. Dolor concreto que tienen (basado en `recommended_service`)
3. Resultado que logramos (garantía)
4. CTA único: agendar una llamada de 15 min

### Email 2 — Follow-up (día 3, sin respuesta)
**Objetivo:** Reiterar valor, agregar urgencia suave.
**Longitud:** 3–4 líneas.
**Estructura:**
1. Referencia al email anterior (sin disculparse)
2. Una stat o dato de dolor (ej: "80% of missed calls never call back")
3. CTA: mismo link de calendario

### Email 3 — Cierre (día 7, sin respuesta)
**Objetivo:** Último intento, puerta abierta.
**Longitud:** 2–3 líneas.
**Estructura:**
1. Menciona que es el último email
2. Ofrece algo concreto (demo gratuita, análisis)
3. CTA: link calendario

---

## Pitches por servicio

**AI Receptionist ($500/mes):**
- EN: "Every missed call is money someone else is making. I install a system that answers 24/7, books appointments, and follows up automatically."
- ES: "Cada llamada sin contestar es dinero que se va. Te instalo un sistema que responde 24/7, agenda citas y hace follow-up solo."

**Full AI Employee + SEO ($800/mes):**
- EN: "Your competitors are showing up on Google Maps. You're not. I fix that in 60 days — and add AI that handles calls and bookings."
- ES: "Tus competidores aparecen en Google Maps. Tú no. Lo arreglamos en 60 días — y agregamos IA que maneja llamadas y citas."

**No website:**
- EN: "Your competitors are getting customers online that you're missing. I build you a professional website in 7 days."
- ES: "Tus competidores consiguen clientes en Google que tú estás perdiendo. Te hago una web profesional en 7 días."

---

## Línea de asunto — fórmulas

| Situación | Asunto EN | Asunto ES |
|---|---|---|
| Sin web | "Your {niche} business is invisible on Google" | "Tu negocio de {nicho} es invisible en Google" |
| Muchas reseñas | "{reviews} reviews — are you answering all those calls?" | "{reviews} reseñas — ¿contestas todas esas llamadas?" |
| SEO | "3 {niche} competitors outranking you in {city}" | "3 competidores de {nicho} te superan en {city}" |
| Follow-up | "Quick follow-up — {business_name}" | "Seguimiento rápido — {business_name}" |

---

## Output format

Para cada lead, entrega:

```
LEAD: {business_name} — {city} — {niche}
IDIOMA: {outreach_language}
SERVICIO: {recommended_service}

--- EMAIL 1 (Día 0) ---
Asunto: ...
Cuerpo:
...

--- EMAIL 2 (Día 3) ---
Asunto: ...
Cuerpo:
...

--- EMAIL 3 (Día 7) ---
Asunto: ...
Cuerpo:
...
```

---

## Tono — qué evitar
- Sin frases de marketing vacías ("solutions", "leverage", "synergy")
- Sin mencionar precio en el primer email
- Sin adjuntar nada — solo texto + link
- Sin párrafos de más de 2 oraciones
- El dolor debe ser **específico** al negocio, no genérico
