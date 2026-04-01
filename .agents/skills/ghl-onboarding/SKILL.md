---
name: ghl-onboarding
description: Step-by-step GHL (GoHighLevel) configuration checklist for onboarding a new client by niche. Use when setting up GHL for a new client, configuring a pipeline, creating automations, or building a sub-account. Trigger on: "set up GHL", "configure GHL", "new client GHL", "onboarding checklist", "pipeline GHL", "configurar GHL", "subaccount", or any client setup task.
---

# GHL Onboarding — Checklist por Nicho

Configura un cliente en GoHighLevel en menos de 2 horas. Este skill cubre todo desde crear el sub-account hasta activar las automatizaciones.

## Inputs necesarios
```
client_name, niche (roofing/hvac/plumbing/remodeling),
plan (AI Receptionist / Full AI Employee + SEO),
city, phone, email, website_url (si tiene),
idioma_preferido (español/inglés)
```

---

## Paso 1 — Crear sub-account (5 min)

```
GHL → Agency Dashboard → + Add Location
- Business Name: [client_name]
- Address: [city, state]
- Phone: [phone]
- Email: [email]
- Timezone: America/Chicago (o la correcta)
- Industry: Home Services
```

---

## Paso 2 — Pipeline de ventas (10 min)

Crear pipeline llamado "Leads Entrantes":

| Etapa | Acción |
|---|---|
| 1. Lead Nuevo | Auto-asigna usuario |
| 2. Contactado | SMS enviado |
| 3. Demo Agendada | Calendario confirmado |
| 4. Llamada de Cierre | Notificación a Keyner |
| 5. Contrato Enviado | DocuSign triggered |
| 6. Cliente Activo | Onboarding iniciado |
| 7. Perdido | Tag + nota de razón |

---

## Paso 3 — Configurar calendario (10 min)

```
Calendars → + New Calendar
- Name: "Llamada Gratuita 15 min" / "Free 15-min Call"
- Duration: 15 min
- Buffer after: 15 min
- Availability: Lun-Vie 9am–6pm CST
- Confirmation email: activar
- Reminder SMS: 1h antes
- Link: copiar y guardar
```

---

## Paso 4 — Missed Call Text-Back (5 min)

```
Automations → + New Workflow
Trigger: "Inbound Call — Status: No Answer"
Action 1 (0 min): SMS
  → "Hola, vi que llamaste a [business_name].
     Estoy con un cliente ahora.
     ¿Te llamo en 30 min? — [owner_name]"
Action 2 (30 min, si no responde): SMS
  → "¿Sigues disponible? Puedo llamarte ahora."
```

---

## Paso 5 — Chat Widget (10 min)

```
Sites → Chat Widget → + New Widget
- Greeting: "Hola 👋 ¿En qué te puedo ayudar?"
- Bot Name: "Asistente de [business_name]"
- Color: naranja (#F47B20) o teal (#1A9E8F)
- Activar: Conversation AI
- Instrucción al bot:
  "Eres el asistente de [business_name] en [city].
   Ayuda a los clientes a agendar citas para
   servicios de [niche]. Si alguien quiere una
   cita, envíalos al calendario: [link]"
```

---

## Paso 6 — Secuencia de follow-up (15 min)

```
Automations → + New Workflow
Trigger: "Form Submitted" / "Lead Created"

Email 1 (inmediato): Confirmación recibida
SMS 1 (5 min): "Recibí tu mensaje, te contacto pronto"
SMS 2 (24h, si no hay respuesta): follow-up
Email 2 (48h): recordatorio + link calendario
SMS 3 (72h): último intento
```

---

## Paso 7 — Reviews automáticas (10 min)

```
Automations → + New Workflow
Trigger: "Opportunity Stage Changed → Cliente Activo"
Wait: 7 días
SMS: "Hola [nombre], ¿cómo fue tu experiencia con
     [business_name]? Si quedaste satisfecho, una
     reseña en Google nos ayuda mucho 🙏 [google_link]"
```

---

## Paso 8 — Landing page en GHL Sites (30 min)

Solo si el plan incluye web. Usar template del nicho:

```
Sites → Funnels → + New Funnel
- Template: usar template de nicho (ver templates/)
- Dominio: conectar o usar el de GHL
- Integrar: formulario de contacto → pipeline
- Integrar: botón de calendario → Calendar Link
```

**Templates por nicho:**
- Roofing: templates/landing-agencia/roofing-template.html
- HVAC: templates/landing-agencia/hvac-template.html
- Plumbing: templates/landing-agencia/plumbing-template.html
- Remodeling: templates/landing-agencia/remodeling-template.html

---

## Paso 9 — SEO Local (solo Full AI Employee + SEO)

```
1. Google Business Profile:
   - Verificar propiedad del cliente
   - Completar: horarios, fotos (mín 10), descripción, servicios
   - Agregar productos/servicios con precios

2. GHL → Reputation Management:
   - Conectar Google Business
   - Activar solicitudes automáticas de reseñas
   - Responder todas las reseñas existentes

3. Citations (sitios de directorios):
   - Yelp, Bing Places, Apple Maps, BBB
   - Mismo NAP (Name, Address, Phone) en todos
```

---

## Paso 10 — Prueba final (10 min)

Antes de entregar al cliente:
- [ ] Enviar lead de prueba al formulario
- [ ] Verificar que llegue al pipeline
- [ ] Llamar al número y verificar missed call text-back
- [ ] Abrir chat widget y verificar bot responde
- [ ] Confirmar email de confirmación llega
- [ ] Revisar calendario funciona y bloquea horarios

---

## Entrega al cliente

Email de bienvenida con:
1. Acceso al dashboard (usuario + contraseña)
2. Link del calendario para compartir
3. Link del chat widget instalado
4. Qué esperar en los primeros 7 días
5. Número de WhatsApp de soporte: [keyner_phone]

Tiempo total de setup: ~2 horas por cliente
