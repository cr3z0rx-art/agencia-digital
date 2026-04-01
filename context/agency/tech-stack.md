# Stack Tecnológico

| Herramienta | Uso | Estado |
|---|---|---|
| GoHighLevel (GHL) | CRM, emails, SMS, pipeline, sitios web | Activo |
| Retell AI | Llamadas outbound con voz AI — agenda demos automáticamente | Activo |
| Claude AI (Anthropic API) | Calificar leads, generar emails | Por conectar |
| Google Maps API | Encontrar leads sin web | Activo |
| Python | Scripts de prospección y automatización | Activo |
| VS Code + Claude Code | Desarrollo del sistema | Activo |
| Stripe | Cobros y retainers | Integrado en GHL |
| Calendly | Agendamiento de demos | Integrado en GHL |
| Loom | Videos personalizados de prospección | Por implementar |

## Variables de entorno necesarias (.env)
```
ANTHROPIC_API_KEY=sk-ant-...
GHL_API_KEY=...
GHL_LOCATION_ID=...
GOOGLE_MAPS_API_KEY=...
RETELL_API_KEY=...
RETELL_AGENT_ID=...
RETELL_NUMBER=+1XXXXXXXXXX
GHL_PHONE_NUMBER=+1XXXXXXXXXX
```

## Lo que falta construir
1. email_generator.py — emails personalizados con Claude API
2. Templates de landing page por nicho en GHL Sites

## Construido
- ghl_client.py — wrapper GHL API
- upload_leads_to_ghl.py — CSV → GHL con tags automáticos
- retell_client.py / bulk_dialer.py — llamadas outbound con Retell AI
- webhook_server.py — recibe eventos de llamada y sincroniza en GHL
