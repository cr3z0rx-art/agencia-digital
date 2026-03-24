# Reglas de la Agencia

## Leads y GHL
- Siempre verificar ghl_uploaded=NO antes de subir leads a GHL
- Marcar ghl_uploaded=YES al completar la subida
- No crear duplicados — verificar por nombre + teléfono antes de subir

## Seguridad
- Nunca hardcodear API keys — siempre usar .env
- Nunca commitear archivos .env o credenciales al repositorio

## Outreach
- Español primero con latinos (is_latino=YES)
- Spanglish con posibles latinos (is_latino=POSSIBLE)
- Inglés con el resto
- Un nicho a la vez — no mezclar todo desde el día 1

## Operaciones
- El cuello de botella es la entrega, no los leads — máx 8–12 proyectos simultáneos
- Siempre logear en logs/ cada acción del sistema
- No escalar Fase 2 sin al menos 1 cierre validado en Fase 1

## Archivos
- No borrar — archivar en archives/
- Los CSVs de leads van en leads/ y están en .gitignore
