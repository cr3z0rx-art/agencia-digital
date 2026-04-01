---
name: proposal-generator
description: Generate a commercial proposal (propuesta comercial) for a specific prospect after a sales call. Use when a lead asked for a proposal, after a demo call, or to send a summary with pricing. Trigger on: "generate proposal", "write proposal", "propuesta comercial", "manda la propuesta", "resumen de llamada", "quote for", or after completing a sales call.
---

# Proposal Generator

Genera la propuesta comercial post-llamada para enviar por email en menos de 1 hora tras el cierre o demo. Debe llegar en <1 hora de la llamada.

## Inputs necesarios
```
business_name, owner_name, city, niche,
plan_selected (AI Receptionist / Full AI Employee + SEO / + Lead Gen),
setup_price, monthly_price,
pain_points (lo que dijeron en la llamada),
guarantee_used,
call_summary (notas de la llamada),
idioma (español/inglés)
```

---

## Asunto del email

- ES: "Propuesta para [business_name] — según lo que hablamos"
- EN: "Proposal for [business_name] — as discussed"

---

## Estructura del email-propuesta

### Párrafo 1 — Recap de la llamada (2–3 líneas)
Resumir los 2–3 puntos de dolor específicos que mencionaron.
NO genérico. Usar sus palabras si las tienes.

**Ejemplo ES:**
```
"[Nombre], gracias por la llamada de hoy. Como hablamos,
el mayor problema ahora mismo es que pierdes llamadas
cuando estás en el trabajo, y no tienes tiempo de hacer
follow-up con todos los que contactan.

Aquí está exactamente lo que propongo para resolverlo:"
```

---

### Sección — El plan propuesto

```
━━━━━━━━━━━━━━━━━━━━━━━━━━
[NOMBRE DEL PLAN]
━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Setup: $[setup] (primer mes incluido)
📅 Retainer mensual: $[precio]/mes
⏱️ En funcionamiento en: 48 horas

LO QUE INCLUYE:
✓ [Feature 1]
✓ [Feature 2]
✓ [Feature 3]
...

GARANTÍA:
🛡️ [Garantía específica del plan]
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Sección — ROI simple (1 párrafo)

Calcular ROI basado en el nicho:

| Nicho | Ticket promedio | Cálculo ROI |
|---|---|---|
| Roofing | $12,000 | "1 techo extra al año = 16x el costo del plan" |
| HVAC | $3,500 | "2 trabajos extra = se paga solo en el primer mes" |
| Plumbing | $1,200 | "3 llamadas capturadas al mes = ROI positivo" |
| Remodeling | $25,000 | "1 proyecto extra = 30x el costo anual" |

---

### Sección — Próximos pasos

```
PRÓXIMOS PASOS:
1. Confirmar que quieres proceder → responde este email
2. Enviarte el contrato (1 página, firma digital)
3. Procesar el pago de setup: $[setup]
4. Inicio del onboarding: [fecha — 2 días desde hoy]
5. Sistema funcionando: [fecha — 48h después]

¿Alguna pregunta sobre la propuesta? Responde
directamente a este email o llámame: [phone]
```

---

### Cierre

**ES:**
```
Estoy listo para empezar esta semana. El cupo
de [mes] está casi lleno — acepto máximo 3 clientes
nuevos por mes para garantizar la calidad.

— Keyner
MultiVenza Digital
hello@multivenzadigital.com
```

**EN:**
```
I'm ready to get started this week. I take on a
maximum of 3 new clients per month to guarantee
quality — and [month] is almost full.

— Keyner
MultiVenza Digital
hello@multivenzadigital.com
```

---

## Add-on Lead Generation (si lo mencionaron)

Si hubo interés en Lead Gen, agregar sección:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━
ADD-ON OPCIONAL: Lead Generation
━━━━━━━━━━━━━━━━━━━━━━━━━━
Agrega campañas de Google Ads + Facebook Ads
que traen leads nuevos cada semana.

+ $300/mes (complemento a cualquier plan)
Incluye: setup de campañas + landing page + reporte semanal
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Reglas

- Enviar en <1 hora de la llamada (mientras el lead está "caliente")
- Sin attachments — todo en el cuerpo del email
- Una propuesta = un plan (no dar 3 opciones, confunde)
- El precio de setup es claro: TOTAL a pagar hoy
- Firma con nombre real, no "El Equipo de MultiVenza"
