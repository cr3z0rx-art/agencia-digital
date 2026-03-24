# Skills Backlog

Skills a construir en .claude/skills/ — ordenados por impacto en el cuello de botella (entrega).

## Prioridad Alta — desbloquean la Fase 1 y 2

| Skill | Descripción | Archivo destino |
|---|---|---|
| `csv-to-ghl` | Subir leads del CSV a GHL con tags automáticos (nicho, is_latino, status) | ghl-integration/upload_leads_to_ghl.py |
| `email-generator` | Generar emails de outreach personalizados con Claude API — por nicho e idioma | ghl-integration/email_generator.py |
| `ghl-onboarding` | Template de configuración GHL por nicho — roofing, HVAC, plomería, remodeling — clonable en 30 min | references/sops/ |
| `sales-call-script` | Script de llamada de ventas por nicho — desde saludo hasta cierre | templates/ |

## Prioridad Media — escalan la Fase 2 y 3

| Skill | Descripción | Archivo destino |
|---|---|---|
| `lead-qualifier` | Calificar y scorear nuevos leads automáticamente con Claude API | scripts/ |
| `loom-script` | Generar script personalizado de video Loom por lead | templates/ |
| `proposal-generator` | Template de propuesta comercial por paquete — Starter, Growth, Pro, Elite | templates/ |
| `landing-page-copy` | Generar copy de landing page por nicho en inglés y español | templates/ |

## Prioridad Baja — operaciones en curso

| Skill | Descripción | Archivo destino |
|---|---|---|
| `onboarding-template` | Email de bienvenida y formulario por nicho para clientes nuevos | templates/ |
| `monthly-report` | Reporte mensual automático de resultados para enviar al cliente | templates/ |
| `retainer-followup` | Mensajes mensuales de seguimiento y pedido de referidos mes 3 | templates/ |
