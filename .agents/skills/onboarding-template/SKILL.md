---
name: onboarding-template
description: Generate the welcome email and onboarding instructions for a new client after they sign and pay. Use immediately after a deal closes, when a client signs the contract, or when preparing the onboarding flow. Trigger on: "onboarding email", "welcome email", "nuevo cliente", "cerré un cliente", "client signed", "client paid", "bienvenida cliente", or after any successful close.
---

# Onboarding Template

Email de bienvenida + instrucciones de onboarding para enviar inmediatamente después de que el cliente pague. Define expectativas y activa la confianza desde el día 1.

## Timing
- Enviar en los primeros 30 minutos después del pago
- Seguimiento en 24h para confirmar que recibió acceso

---

## Inputs
```
owner_name, business_name, niche, city,
plan (AI Receptionist / Full AI Employee + SEO),
setup_date (fecha inicio), live_date (fecha de entrega),
phone_client, email_client,
ghl_login_url, ghl_user, ghl_password,
calendar_link,
keyner_phone (para soporte WhatsApp)
```

---

## Asunto del email

- ES: "¡Bienvenido a MultiVenza Digital, [nombre]! — Tu onboarding empieza hoy"
- EN: "Welcome to MultiVenza Digital, [nombre]! — Your onboarding starts today"

---

## Email de bienvenida

**ES:**
```
Hola [nombre],

¡Bienvenido a bordo! Estamos trabajando en
[business_name] desde ahora mismo.

Aquí está todo lo que necesitas saber:

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 TU ACCESO A GHL
━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard: [ghl_login_url]
Usuario: [ghl_user]
Contraseña: [ghl_password]

(Cámbiala al entrar si quieres)

━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 TU CALENDARIO
━━━━━━━━━━━━━━━━━━━━━━━━━━
Comparte este link con tus clientes para
que agenden directamente:
[calendar_link]

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ QUÉ PASA AHORA
━━━━━━━━━━━━━━━━━━━━━━━━━━
Hoy: Inicio del setup de tu sistema
[live_date]: Tu sistema está funcionando

[SI TIENE SEO]:
Primeras 2 semanas: Optimización de Google Business
Mes 1–2: Escalada de posición en Google Maps
Mes 2–3: Top 3 en tu área (garantizado)

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 LO QUE NECESITO DE TI
━━━━━━━━━━━━━━━━━━━━━━━━━━
Para completar el setup, necesito que me
mandes por WhatsApp:

[ ] Acceso a tu Google Business Profile
    (te explico cómo en 2 min si necesitas)
[ ] Tu logo (si tienes) o un color favorito
[ ] Horario de atención de tu negocio
[ ] Servicios principales que ofreces

WhatsApp: [keyner_phone]

━━━━━━━━━━━━━━━━━━━━━━━━━━

Cualquier pregunta, escríbeme directamente
a este email o al WhatsApp de arriba.

¡Vamos a crecer [business_name]!

— Keyner
MultiVenza Digital
hello@multivenzadigital.com
```

---

**EN:**
```
Hey [nombre],

Welcome aboard! We're already working on
[business_name] as of right now.

Here's everything you need to know:

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 YOUR GHL ACCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard: [ghl_login_url]
Username: [ghl_user]
Password: [ghl_password]

━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 YOUR BOOKING LINK
━━━━━━━━━━━━━━━━━━━━━━━━━━
Share this with your customers to
book appointments directly:
[calendar_link]

━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ WHAT HAPPENS NEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━
Today: System setup begins
[live_date]: Your system goes live

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 WHAT I NEED FROM YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━
To complete setup, please send me via WhatsApp:

[ ] Access to your Google Business Profile
[ ] Your logo (if you have one)
[ ] Your business hours
[ ] Your main services

WhatsApp: [keyner_phone]

━━━━━━━━━━━━━━━━━━━━━━━━━━

Any questions, reply to this email or
message me on WhatsApp above.

Let's grow [business_name]!

— Keyner
MultiVenza Digital
hello@multivenzadigital.com
```

---

## Seguimiento 24h

Si no enviaron los materiales en 24h:

**ES:** "Hola [nombre], ¿recibiste el email de ayer? Para tener tu sistema listo en [live_date], necesito los datos de arriba hoy. ¿Tienes 5 minutos?"

**EN:** "Hey [nombre], did you get my email? To have everything live by [live_date] I need those details today. Got 5 min?"
