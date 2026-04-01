---
name: monthly-report
description: Generate a monthly results report to send to active clients showing what was accomplished and what's next. Use at the end of each month, when a client asks for results, or when preparing the retainer renewal conversation. Trigger on: "monthly report", "reporte mensual", "qué le mando al cliente", "resultados del mes", "client report", or any client reporting task.
---

# Monthly Report Generator

Genera el reporte mensual para enviar a clientes activos. Mantiene la relación, justifica el retainer, y siembra el terreno para referidos en el mes 3.

## Inputs necesarios
```
client_name, business_name, niche, city,
plan (AI Receptionist / Full AI Employee + SEO),
month, year,
calls_captured (número),
leads_from_web (número),
appointments_booked (número),
reviews_new (número),
reviews_total (número),
google_ranking_current (posición en Maps, si aplica),
google_ranking_start (posición inicial, si aplica),
sms_sent (número),
emails_sent (número),
top_win (el mejor resultado del mes — 1 línea),
next_month_plan (qué viene el próximo mes)
```

---

## Asunto del email

- ES: "Tu reporte de [mes] — [business_name] 📊"
- EN: "[Month] Results for [business_name] 📊"

---

## Estructura del reporte

### Apertura (2–3 líneas)

**ES:**
```
"Hola [nombre], aquí está tu resumen de [mes].
Fue un buen mes — aquí los números:"
```

**EN:**
```
"Hey [nombre], here's your [month] summary.
Good month — here are the numbers:"
```

---

### Métricas del mes

```
━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RESULTADOS DE [MES YYYY]
[business_name]
━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 Llamadas capturadas por IA: [calls_captured]
🌐 Leads desde el sitio web: [leads_from_web]
📅 Citas agendadas automáticamente: [appointments_booked]
⭐ Nuevas reseñas de Google: [reviews_new] (Total: [reviews_total])
💬 SMS enviados en seguimiento: [sms_sent]
📧 Emails de follow-up: [emails_sent]

[SI TIENE SEO]:
🗺️ Posición en Google Maps: [google_ranking_current]
   (Empezamos en posición [google_ranking_start])
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### El mejor momento del mes (1 párrafo)

Destacar el `top_win` con contexto:

**ES:**
```
"El mejor momento de este mes: [top_win].
Ese es exactamente el tipo de resultado que
buscamos cada mes."
```

---

### ROI del mes (si aplica)

Calcular retorno basado en niche ticket:

```
[Si calls_captured > 0]:
"Si convertiste el 30% de las [calls_captured] llamadas
capturadas (conservador para [niche]), eso son
[calls_captured * 0.3] trabajos adicionales estimados.
A [ticket_promedio] por trabajo = $[revenue_estimado]
vs $[monthly_price]/mes de retainer."
```

---

### Próximo mes

```
━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 PRÓXIMO MES: [next_month_plan]
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Cierre + pedido de referido (MES 3+)

**Solo a partir del mes 3:**

**ES:**
```
"¿Conoces a algún otro contratista o negocio local
que pueda beneficiarse de lo mismo que tú tienes?
Si nos refieres a alguien que se convierte en cliente,
te damos un mes gratis. 🙏

Cualquier pregunta, escríbeme directamente aquí.

— Keyner
MultiVenza Digital"
```

**EN:**
```
"Do you know any other contractors or local businesses
that could benefit from what you have?
If you refer someone who becomes a client, we'll give
you a free month. 🙏

Any questions, reply directly to this email.

— Keyner
MultiVenza Digital"
```

---

## Cuándo enviar

- Día 1–3 de cada mes (por el mes anterior)
- Siempre un email — no PDF adjunto (más fácil de leer en móvil)
- Si los números son bajos: honesto + plan de mejora específico

## Regla de oro

El cliente paga $500–$800/mes. El reporte justifica ese gasto mostrando actividad real. Si no tienes números reales todavía, muestra actividad del sistema (SMS enviados, emails, configuraciones).
