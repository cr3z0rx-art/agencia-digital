# Stack Tecnológico

| Herramienta | Uso | Estado |
|---|---|---|
| GoHighLevel (GHL) | CRM, emails, SMS, pipeline, sitios web | Activo |
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
```

## Lo que falta construir
1. ghl_client.py — wrapper de la API de GHL
2. upload_leads_to_ghl.py — CSV → GHL con tags automáticos
3. email_generator.py — emails personalizados con Claude API
4. Templates de landing page por nicho en GHL Sites
