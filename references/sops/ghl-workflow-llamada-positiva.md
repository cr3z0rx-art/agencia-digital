# SOP — Workflow GHL: Llamada Positiva → HOT Lead + SMS

Configura esto UNA VEZ en GHL. Se dispara automáticamente cada vez que
Retell AI termina una llamada con sentimiento positivo.

---

## Dónde configurarlo

**Automation → Workflows → + New Workflow → Start from Scratch**

Nombre: `Retell — Llamada Positiva → HOT Lead + SMS`

---

## TRIGGER

**Tipo:** `Contact Tag Added`

| Campo | Valor |
|---|---|
| Tag | `llamada-positiva` |
| Filter | (ninguno adicional) |

> Este tag lo agrega automáticamente webhook_server.py al recibir
> un evento call_ended con agent_sentiment = "Positive".

---

## ACCIÓN 1 — Mover oportunidad a HOT Lead

**Tipo:** `Update Opportunity`

| Campo | Valor |
|---|---|
| Pipeline | Contratistas Latinos |
| Stage | HOT Lead |
| Opportunity | (primera activa del contacto) |

> Nota: el webhook_server.py ya intenta hacer esto por API. Este workflow
> es el respaldo — si la etapa no existe en el momento del webhook,
> GHL lo reintenta desde aquí.

---

## ACCIÓN 2 — Send SMS

**Tipo:** `Send SMS`

**Template español** (usar cuando el contacto tiene tag `idioma-es` o `latino`):

```
Hola {{contact.first_name}}, soy Keyner de MultiVenza Digital.

Acabo de ver que tuviste interés en nuestro sistema de recepción automática — me alegra mucho.

¿Te gustaría ver cómo funciona en 15 minutos? Aquí puedes elegir el horario que te convenga:

👉 https://calendly.com/multivenzadigital/demo

Cualquier duda, respóndeme aquí directo. — Keyner
```

**Template inglés** (usar cuando el contacto NO tiene tag `latino`):

```
Hi {{contact.first_name}}, this is Keyner from MultiVenza Digital.

I saw you had a chance to connect with us — great to hear from you.

Want to see the system live in 15 minutes? Pick a time that works for you:

👉 https://calendly.com/multivenzadigital/demo

Feel free to reply here with any questions. — Keyner
```

> Tip: usa un If/Else antes del SMS para elegir el template según el tag
> `idioma-es` o `latino`. Ver sección avanzada abajo.

---

## CONFIGURACIÓN COMPLETA (con If/Else por idioma)

```
[TRIGGER] Contact Tag Added → "llamada-positiva"
    │
    ▼
[ACTION 1] Update Opportunity Stage → "HOT Lead"
    │
    ▼
[ACTION 2] If/Else
    │   Condition: Contact Tag contains "latino" OR "idioma-es"
    │
    ├── YES → [Send SMS] Template español
    │
    └── NO  → [Send SMS] Template inglés
```

---

## Configuración del SMS en GHL

1. En la acción Send SMS, selecciona **"Use Custom Message"**
2. Pega el template correspondiente
3. `{{contact.first_name}}` se reemplaza automáticamente con el nombre del contacto
4. Reemplaza el link de Calendly por tu URL real

---

## Verificar que funciona

Después de configurar, haz una prueba manual:

1. Abre cualquier contacto en GHL que tenga oportunidad activa
2. Agrega manualmente el tag `llamada-positiva`
3. Verifica que:
   - La oportunidad se mueve a **HOT Lead**
   - El contacto recibe el SMS en segundos

---

## Estado de automatización Retell + GHL

| Paso | Método | Status |
|---|---|---|
| Llamada termina → resumen a GHL | webhook_server.py | Construido |
| Tag llamada-positiva agregado | webhook_server.py | Construido |
| Oportunidad → HOT Lead (API) | webhook_server.py | Construido |
| Oportunidad → HOT Lead (respaldo) | GHL Workflow | **Por configurar** |
| SMS de invitación a demo | GHL Workflow | **Por configurar** |
