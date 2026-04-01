# SOP — Secuencia de Follow-up en GHL

Configura esto UNA VEZ en GHL. Después corre solo para cada lead nuevo.

---

## Secuencia completa (9 etapas del flujo de ventas)

| Día | Acción | Canal | Trigger |
|-----|--------|-------|---------|
| 0 | Email propuesta personalizada | Email | Script Python (automático al subir lead) |
| 2 | SMS follow-up | SMS | GHL Workflow (configurar abajo) |
| 6 | Video Loom | Email | GHL Workflow (configurar abajo) |
| — | Demo agendada | Calendly | Lead responde → etapa "Demo Agendada" |
| — | Llamada de cierre | Teléfono | ÚNICA intervención manual |
| — | Contrato + pago | DocuSign + Stripe | GHL automático |

---

## Cómo configurar el Workflow en GHL

### Workflow 1 — SMS día 2

**Automation → Workflows → + New Workflow**

Nombre: `Follow-up SMS Día 2 — Contratistas`

**Trigger:**
- Trigger: `Contact Tag Added`
- Tag: `hot` (se agrega al subir el lead con el script)

**Actions:**
1. `Wait` → 2 days
2. `If/Else` → Condition: `Contact replied` = No (verificar si hubo respuesta)
3. Si NO respondió:
   - `Send SMS` → usar template abajo
4. `Update Contact Stage` → mover a `Contactado`

**Template SMS (español):**
```
Hola, soy Keyner de MultiVenza Digital.
Le envié un email hace 2 días sobre cómo conseguir más clientes para su negocio en Google.
¿Tuvo oportunidad de verlo? Con gusto le explico en 10 minutos.
Responda este mensaje o llámeme. — Keyner
```

**Template SMS (inglés):**
```
Hi, this is Keyner from MultiVenza Digital.
I emailed you 2 days ago about getting more customers through Google.
Did you get a chance to read it? Happy to walk you through it in 10 minutes.
Reply here or give me a call. — Keyner
```

---

### Workflow 2 — Loom día 6

**Automation → Workflows → + New Workflow**

Nombre: `Follow-up Loom Día 6 — Contratistas`

**Trigger:**
- Trigger: `Pipeline Stage Changed`
- Pipeline: `Contratistas Latinos`
- Stage: `Contactado`

**Actions:**
1. `Wait` → 4 days (4 días después del SMS del día 2 = día 6 total)
2. `If/Else` → Condition: `Opportunity Stage` = `Contactado` (no avanzó)
3. Si sigue en `Contactado`:
   - `Send Email` → template Loom abajo
4. `Update Contact Stage` → mover a `Interesado` (optimista — GHL lo moverá atrás si no responde)

**Template Email Loom:**
```
Asunto: Hice un video de 2 minutos para [Nombre del negocio]

Hola,

Grabé un video corto que muestra exactamente cómo [Nombre del negocio]
aparece hoy en Google versus sus competidores.

[LINK AL LOOM AQUÍ]

Solo 2 minutos. Vale la pena verlo.

Si quiere hablamos — solo responda este email.

— Keyner Guerrero
MultiVenza Digital
hello@multivenzadigital.com
```

---

### Workflow 3 — Demo reminder

**Trigger:** Pipeline Stage = `Demo Agendada`

**Actions:**
1. `Wait` → 1 hour before appointment (usar campo de fecha de la cita)
2. `Send SMS` → "Hola, le recuerdo nuestra llamada de hoy a las [hora]. Aquí el link: [Calendly link]"

---

## Alternativa: Correr el script Python manualmente cada día

Si prefieres no configurar los workflows en GHL ahora:

```bash
# Correr cada mañana — envía SMS a los que llevan 48h sin respuesta
python ghl-integration/followup_sms.py

# Ver quién necesita follow-up sin enviar nada
python ghl-integration/followup_sms.py --dry-run
```

---

## Estado actual de automatización

| Paso | Método | Status |
|------|--------|--------|
| Email día 0 | Script Python | Construido |
| SMS día 2 | Script Python | Construido |
| SMS día 2 automático | GHL Workflow | Por configurar |
| Loom día 6 | GHL Workflow | Por configurar |
| Demo reminder | GHL Workflow | Por configurar |
