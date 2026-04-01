---
name: landing-page-copy
description: Generate landing page copy by niche and language for GHL Sites or HTML templates. Use when building a landing page for a client, writing hero headlines, service descriptions, or any web copy for a contractor niche. Trigger on: "landing page copy", "write copy for", "hero headline", "web copy", "copy para landing", "texto para la web", "niche landing", or when configuring a client's GHL site.
---

# Landing Page Copy Generator

Genera copy completo para landing pages de contratistas por nicho — en inglés, español, o bilingüe. Listo para pegar en GHL Sites o en el template HTML.

## Inputs
```
niche (roofing/hvac/plumbing/remodeling),
business_name, city, state,
owner_name (opcional),
has_reviews (sí/no), review_count (si tiene),
main_service (ej: "roof replacement", "emergency HVAC"),
guarantee (ej: "work guaranteed or money back"),
idioma (en/es/bilingual)
```

---

## Secciones del copy

### 1. Hero Headline (H1)

**Roofing:**
- EN: "New Roof in [City]? Get a Free Estimate Today."
- ES: "¿Necesitas Techo Nuevo en [City]? Estimado Gratis Hoy."

**HVAC:**
- EN: "Fast, Reliable HVAC Service in [City] — 24/7"
- ES: "Servicio de HVAC Rápido y Confiable en [City] — 24/7"

**Plumbing:**
- EN: "Emergency Plumber in [City] — We Respond in 60 Minutes"
- ES: "Plomero de Emergencia en [City] — Respondemos en 60 Minutos"

**Remodeling:**
- EN: "[City]'s Trusted Remodeling Contractor — Licensed & Insured"
- ES: "Contratista de Remodelación de Confianza en [City] — Con Licencia"

---

### 2. Hero Subheadline

**Fórmula:** [Negocio] + [servicio principal] + [prueba social si tiene] + [CTA implícito]

**Ejemplos:**
- EN: "[business_name] has served [city] homeowners for [X] years. [review_count] 5-star reviews. Licensed, insured, and ready today."
- ES: "[business_name] lleva [X] años sirviendo a familias en [city]. [review_count] reseñas de 5 estrellas. Con licencia, asegurado, y listo hoy."

---

### 3. Badges de confianza (debajo del hero)

| EN | ES |
|---|---|
| ✓ Licensed & Insured | ✓ Con Licencia y Asegurado |
| ✓ Free Estimates | ✓ Estimados Gratis |
| ✓ [X]+ 5-Star Reviews | ✓ [X]+ Reseñas de 5 Estrellas |
| ✓ Serving [City] Since [Year] | ✓ Sirviendo [City] desde [Year] |
| ✓ Same-Day Service Available | ✓ Servicio el Mismo Día |

---

### 4. Por qué elegirnos (3 puntos)

**Estructura:** Ícono + Título corto + 1 línea de descripción

**Roofing:**
```
🏠 Expert Installation
   30+ years roofing experience in [state] weather.

⚡ Fast Turnaround
   Most jobs completed in 1–3 days.

🛡️ Lifetime Workmanship Warranty
   We stand behind every shingle we install.
```

**HVAC:**
```
🌡️ 24/7 Emergency Service
   We pick up the phone at 2am. No extra charge.

⭐ Factory-Certified Technicians
   Trained on all major brands.

💰 Upfront Pricing
   No surprises. Quote before we start.
```

**Plumbing:**
```
🔧 60-Minute Response
   We're in [city] — not 2 hours away.

📋 Same-Day Diagnosis
   We find the problem and fix it, same visit.

✅ Work Guaranteed
   [guarantee]
```

**Remodeling:**
```
🏆 Licensed General Contractor
   [state] license #[number if known].

📐 Design + Build in One
   From plans to final walkthrough, we handle it.

🤝 No Subcontractors
   Your own crew from start to finish.
```

---

### 5. CTA principal

**Fórmula:** Verbo de acción + beneficio inmediato + urgencia suave

- EN: "Get Your Free Estimate — We Respond in Under 1 Hour"
- ES: "Obtén tu Estimado Gratis — Respondemos en Menos de 1 Hora"

**Botón:**
- EN: "Schedule Free Estimate" / "Call Now — Free Quote"
- ES: "Agendar Estimado Gratis" / "Llamar Ahora — Cotización Gratis"

---

### 6. Sección de garantía (si aplica)

```
🛡️ Our Guarantee / Nuestra Garantía

EN: "If you're not completely satisfied with our work,
    we'll make it right — or refund your money. Simple."

ES: "Si no quedas completamente satisfecho con nuestro
    trabajo, lo corregimos — o te devolvemos el dinero."
```

---

### 7. Footer / Contacto

```
[business_name]
📍 Serving [city] and surrounding areas
📞 [phone]
✉️ [email]
⭐ [reviews] reviews on Google — [rating]/5
```

---

## Reglas de copy

- Sin tecnicismos — hablar como habla el cliente
- Una acción por CTA (no "Llama o envía email o visítanos")
- El número de teléfono visible en el hero y en el footer
- Máximo 3 puntos de beneficio (el cerebro no procesa más)
- Usar "tú" en español, nunca "usted" para contratistas locales
- Las garantías deben ser específicas ("7 días" no "rápido")
