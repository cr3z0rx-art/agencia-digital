# Base de Datos de Leads

Total: 5,417 leads únicos en 3 CSVs — carpeta /leads/

## leads_minneapolis.csv (431 leads)
- Contratistas locales en Minneapolis, MN
- HOT: 41 | WARM: 186 | COLD: 204
- 41 HOT sin web → candidatos para visita/llamada personal esta semana
- Columnas: status, score, name, address, phone, website, rating, reviews, contacted

## leads_latinos_usa.csv (4,007 leads)
- Contratistas en 10 ciudades USA con detección de negocios latinos
- HOT: 461 | WARM: 1,762 | COLD: 1,784
- Latinos confirmados (is_latino=YES): 58
- Latinos HOT (prioridad máxima): 10 → contactar HOY en español
- Ciudades: Minneapolis, Chicago, Houston, Dallas, LA, Miami, Denver, Phoenix, Atlanta, NY
- Nichos: Roofing (1,377) | Remodeling (1,400) | HVAC (1,230)
- Columnas clave: is_latino, outreach_language, recommended_service, pitch_line, ghl_uploaded

## leads_multiservice.csv (979 leads)
- Negocios en Minneapolis con múltiples servicios
- HOT: 949 | WARM: 30
- 698 recomendados para AI Receptionist (promedio 438 reseñas, rating 4.76)
- 45 sin web (landing page) | 206 para SEO
- Top candidatos IA: Paul Bunyan Plumbing (6,749 reseñas), Standard Heating (6,500), Sela Roofing (647)

## Regla de no duplicados
Siempre verificar ghl_uploaded=NO antes de subir. Marcar YES al completar.
