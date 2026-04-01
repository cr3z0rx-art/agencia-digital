"""
============================================================
  Email Generator — Signal-Based Outreach (MultiVenza Digital)
  Lógica de decisión primero, template después.

  Señales disponibles por lead:
    website   — "NO WEBSITE" o URL
    reviews   — número de reseñas en Google
    is_latino — YES / POSSIBLE / NO
    niche     — Roofing, HVAC, Remodeling, Plumbing
    city      — ciudad del negocio

  Decisión de template:
    NO WEBSITE              → Template A (landing page)
    website + reviews >= 100 → Template B (AI Receptionist)
    website + reviews < 20   → Template C (SEO local)
    website + reviews 20-99  → Template B (AI Receptionist, default)

  Idioma:
    is_latino YES/POSSIBLE  → Español
    resto                   → Inglés

  Reglas fijas:
    - NUNCA abrir con "Soy Keyner de MultiVenza Digital"
    - NUNCA listar los 3 servicios — 1 servicio por email
    - Subject siempre incluye nombre del negocio + ciudad o señal
    - CTA siempre: "¿Tiene 15 minutos esta semana?" / "Worth 15 minutes this week?"

  Requiere en .env:
    ANTHROPIC_API_KEY=sk-ant-...  (opcional — activa personalización con IA)

  USO standalone:
    python ghl-integration/email_generator.py
============================================================
"""

import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

FIRMA_PLAIN = "— MultiVenza Success Team | MultiVenza Digital | hello@multivenzadigital.com"

FIRMA_HTML = """
<table cellpadding="0" cellspacing="0" border="0" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#333333;max-width:480px;border-top:2px solid #00A3AD;padding-top:14px;margin-top:24px;">
  <tr>
    <td style="padding-right:16px;vertical-align:top;">
      <!-- Logo SVG inline — compatible iOS/Android -->
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="background:#0A0F14;border-radius:8px;padding:8px 10px;text-align:center;">
            <svg width="36" height="36" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polygon points="19,4 34,30 4,30" fill="#FF8200" opacity=".9"/>
              <polygon points="19,12 29,28 9,28" fill="#00A3AD"/>
            </svg>
          </td>
        </tr>
      </table>
    </td>
    <td style="vertical-align:top;">
      <p style="margin:0 0 2px;font-size:15px;font-weight:700;color:#0A0F14;">MultiVenza Success Team</p>
      <p style="margin:0 0 6px;font-size:12px;color:#555555;">Client Success &nbsp;|&nbsp; <strong style="color:#00A3AD;">MultiVenza Digital</strong></p>
      <p style="margin:0 0 4px;font-size:12px;color:#555555;">&#128205; Bloomington, Minnesota</p>
      <p style="margin:0 0 10px;font-size:12px;color:#555555;">✉ <a href="mailto:hello@multivenzadigital.com" style="color:#00A3AD;text-decoration:none;">hello@multivenzadigital.com</a></p>
      <!-- CTA button -->
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="background:#FF8200;border-radius:6px;padding:0;">
            <a href="https://multivenzadigital.com" target="_blank"
               style="display:inline-block;padding:8px 16px;font-size:12px;font-weight:700;color:#ffffff;text-decoration:none;font-family:Arial,Helvetica,sans-serif;">
              ▶ Ver cómo funciona la IA en 60 segundos
            </a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding-top:12px;">
      <p style="margin:0;font-size:10px;color:#999999;font-style:italic;">
        Helping Latino Contractors grow with AI. MultiVenza LLC.
      </p>
    </td>
  </tr>
</table>
"""
LANDING_URL = "https://multivenzadigital.com"
PRECIO = "$499/mes"


# ─────────────────────────────────────────
#  LÓGICA DE DECISIÓN
# ─────────────────────────────────────────

def decide_template_and_language(lead: dict) -> tuple[str, str]:
    """
    Decide qué template usar y en qué idioma basado en las señales del lead.
    Retorna (template_key, lang) donde lang es "es" o "en".
    """
    website  = str(lead.get("website", "NO WEBSITE")).strip()
    reviews  = int(lead.get("reviews", 0) or 0)
    is_latino = str(lead.get("is_latino", "NO")).strip().upper()

    has_website = website not in ("NO WEBSITE", "", "N/A", "None")

    # Señal → template
    if not has_website:
        template = "no_website"
    elif reviews >= 100:
        template = "ai_receptionist"
    elif reviews < 20:
        template = "seo"
    else:
        # 20-99 reviews con web → AI Receptionist es el pitch más fuerte
        template = "ai_receptionist"

    # Idioma
    lang = "es" if is_latino in ("YES", "POSSIBLE") else "en"

    return template, lang


# ─────────────────────────────────────────
#  TEMPLATES SIGNAL-BASED
# ─────────────────────────────────────────

def _template_no_website_es(lead: dict) -> dict:
    name    = lead.get("name", "su negocio")
    city    = lead.get("city", "").split(",")[0]
    niche   = lead.get("niche", "contratista")
    reviews = int(lead.get("reviews", 0) or 0)

    review_line = (
        f"Vi que {name} tiene {reviews} resenas en Google — eso me dice que su trabajo es bueno y que sus clientes los recomiendan."
        if reviews > 0
        else f"Vi {name} en Google Maps."
    )

    subject = f"{name} — sus competidores en {city} si aparecen en Google. Usted no."
    body = f"""\
Hola,

{review_line}

El problema: cuando alguien en {city} busca "{niche} cerca de mi", {name} no aparece porque no tiene sitio web. Sus competidores estan capturando esos clientes ahora mismo.

Le instalamos un Sistema de IA Bilingue completo: pagina profesional lista en 7 dias, recepcionista IA que contesta 24/7, agenda citas y da seguimiento automatico.

Todo por {PRECIO} — sin contratos largos. La inversion inicial la definimos juntos en una demo de 15 minutos.

Garantia: si no captura su primera llamada en 48 horas, le devolvemos el dinero.

Ver si su negocio califica: {LANDING_URL}

{FIRMA_PLAIN}"""
    return {"subject": subject, "html": body.replace("\n", "<br>") + FIRMA_HTML}


def _template_no_website_en(lead: dict) -> dict:
    name    = lead.get("name", "your business")
    city    = lead.get("city", "").split(",")[0]
    niche   = lead.get("niche", "contractor")
    reviews = int(lead.get("reviews", 0) or 0)

    review_line = (
        f"{name} has {reviews} Google reviews — proof your work is solid."
        if reviews > 0
        else f"I found {name} on Google Maps."
    )

    subject = f"{name} — your competitors in {city} are showing up on Google. You're not."
    body = f"""\
Hi,

{review_line}

The problem: when someone in {city} searches "{niche} near me", {name} doesn't show up — no website means Google ignores you. Your competitors are picking up those leads right now.

We install a complete Bilingual AI System: professional website live in 7 days, AI receptionist that answers 24/7, books appointments and follows up automatically.

All for {PRECIO} per month — no long-term contracts. We define the initial investment together on a 15-minute demo.

Guarantee: if you don't capture your first call within 48 hours, full refund.

See if your business qualifies: {LANDING_URL}

{FIRMA_PLAIN}"""
    return {"subject": subject, "html": body.replace("\n", "<br>") + FIRMA_HTML}


def _template_ai_receptionist_es(lead: dict) -> dict:
    name    = lead.get("name", "su negocio")
    city    = lead.get("city", "").split(",")[0]
    niche   = lead.get("niche", "contratista")
    reviews = int(lead.get("reviews", 0) or 0)
    rating  = lead.get("rating", "")

    subject = f"{name} — {reviews} resenas y su telefono suena. Quien contesta a las 9pm?"
    body = f"""\
Hola,

{name} tiene {reviews} resenas y {rating} estrellas en {city} — eso los pone entre los mejores contratistas de {niche} en la zona.

Eso tambien significa que su telefono suena mucho. La pregunta es: que pasa con esas llamadas cuando estan en un trabajo o son las 9pm del domingo?

Cada llamada perdida en {niche} es un contrato de $5,000-$15,000 que va al que conteste primero.

Nuestro Sistema de IA Bilingue responde en menos de 30 segundos, califica al cliente y agenda la cita — automaticamente, 24/7. Acceso total por {PRECIO}, sin contratos largos. La inversion inicial la definimos en una demo de 15 minutos.

Ver si su negocio califica: {LANDING_URL}

{FIRMA_PLAIN}"""
    return {"subject": subject, "html": body.replace("\n", "<br>") + FIRMA_HTML}


def _template_ai_receptionist_en(lead: dict) -> dict:
    name    = lead.get("name", "your business")
    city    = lead.get("city", "").split(",")[0]
    niche   = lead.get("niche", "contractor")
    reviews = int(lead.get("reviews", 0) or 0)
    rating  = lead.get("rating", "")

    subject = f"{name} — {reviews} reviews means your phone rings. Who answers at 9pm?"
    body = f"""\
Hi,

{name} has {reviews} reviews and {rating} stars in {city} — top tier {niche} contractor in the area.

That also means your phone rings a lot. What happens when you're on a job or it's 9pm on a Sunday?

Every missed call in {niche} is a $5,000-$15,000 job going to whoever picks up next.

Our Bilingual AI System responds within 30 seconds, qualifies the lead, and books the appointment — automatically, 24/7. Full access for {PRECIO}/month, no long-term contracts. We define the initial investment together on a 15-minute demo.

See if your business qualifies: {LANDING_URL}

{FIRMA_PLAIN}"""
    return {"subject": subject, "html": body.replace("\n", "<br>") + FIRMA_HTML}


def _template_seo_es(lead: dict) -> dict:
    name    = lead.get("name", "su negocio")
    city    = lead.get("city", "").split(",")[0]
    niche   = lead.get("niche", "contratista")
    reviews = int(lead.get("reviews", 0) or 0)

    subject = f"{name} tiene web — pero Google todavia no la ve en {city}"
    body = f"""\
Hola,

{name} ya tiene sitio web — eso es bueno. Pero con {reviews} resenas, cuando alguien busca "{niche} en {city}", probablemente no aparecen en la primera pagina de Google.

El 80% de los contratos nuevos en su nicho vienen de busquedas en Google Maps. Si no estan en el top 3, esos trabajos van a la competencia.

Nuestro Sistema de IA Bilingue lo cubre todo: SEO local para posicionarlos en el top 3 de {city} en 30 dias + recepcionista IA que contesta 24/7, califica clientes y agenda citas automaticamente.

Todo incluido por {PRECIO} — sin contratos largos. La inversion inicial la definimos en una demo de 15 minutos.

Ver si su negocio califica: {LANDING_URL}

{FIRMA_PLAIN}"""
    return {"subject": subject, "html": body.replace("\n", "<br>") + FIRMA_HTML}


def _template_seo_en(lead: dict) -> dict:
    name    = lead.get("name", "your business")
    city    = lead.get("city", "").split(",")[0]
    niche   = lead.get("niche", "contractor")
    reviews = int(lead.get("reviews", 0) or 0)

    subject = f"{name} has a website — Google just doesn't see it yet in {city}"
    body = f"""\
Hi,

{name} already has a website — good start. But with {reviews} Google reviews, when someone searches "{niche} in {city}", you're probably not on the first page.

80% of new contracts in your niche come from Google Maps searches. If you're not in the top 3, those jobs go to whoever is.

Our Bilingual AI System covers everything: local SEO to rank you in the top 3 in {city} within 30 days + AI receptionist that answers 24/7, qualifies leads, and books appointments automatically.

All included for {PRECIO}/month — no long-term contracts. We define the initial investment together on a 15-minute demo.

See if your business qualifies: {LANDING_URL}

{FIRMA_PLAIN}"""
    return {"subject": subject, "html": body.replace("\n", "<br>") + FIRMA_HTML}


# Setup fees por template (usados para el valor monetario en GHL pipeline)
SERVICE_VALUES = {
    "no_website":      499,
    "ai_receptionist": 499,
    "seo":             499,
}

# Mapa de templates
TEMPLATE_FN = {
    ("no_website",     "es"): _template_no_website_es,
    ("no_website",     "en"): _template_no_website_en,
    ("ai_receptionist","es"): _template_ai_receptionist_es,
    ("ai_receptionist","en"): _template_ai_receptionist_en,
    ("seo",            "es"): _template_seo_es,
    ("seo",            "en"): _template_seo_en,
}


# ─────────────────────────────────────────
#  GENERADOR CON CLAUDE API
# ─────────────────────────────────────────

def _generate_with_claude(lead: dict, template: str, lang: str) -> dict:
    """
    Personaliza el email con Claude API usando el template como base.
    Si falla, cae al template estático.
    """
    import anthropic

    client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    name     = lead.get("name", "")
    city     = lead.get("city", "").split(",")[0]
    niche    = lead.get("niche", "")
    reviews  = int(lead.get("reviews", 0) or 0)
    rating   = lead.get("rating", "")
    website  = lead.get("website", "NO WEBSITE")
    has_web  = website not in ("NO WEBSITE", "", "N/A", "None")

    TEMPLATE_CONTEXT = {
        "no_website":      "No tiene sitio web — pitch: Sistema de IA Bilingue completo (web en 7 dias + recepcionista IA 24/7). Precio: $499/mes. NO mencionar setup ni precios de instalacion.",
        "ai_receptionist": "Tiene web y muchas resenas — pitch: recepcionista IA 24/7 que contesta, califica y agenda automaticamente. Precio: $499/mes. NO mencionar setup ni precios de instalacion.",
        "seo":             "Tiene web pero pocas resenas — pitch: SEO local top 3 Google Maps en 30 dias + recepcionista IA 24/7. Precio: $499/mes. NO mencionar setup ni precios de instalacion.",
    }

    lang_instruction = (
        "Escribe en español natural para un contratista latino. Usa 'usted'. Sin tildes ni caracteres especiales."
        if lang == "es"
        else "Write in English. Professional but direct."
    )

    prompt = f"""\
Eres parte del equipo de MultiVenza Digital.

Escribe un email corto de prospeccion para este contratista:

NEGOCIO: {name}
CIUDAD: {city}
NICHO: {niche}
RESENAS GOOGLE: {reviews} ({rating} estrellas)
TIENE WEB: {"Si" if has_web else "No"}
SERVICIO: {TEMPLATE_CONTEXT[template]}

REGLAS ESTRICTAS:
- {lang_instruction}
- NUNCA abrir con "Soy Keyner" ni con el nombre de la agencia
- Abrir con una observacion especifica sobre su negocio usando los datos arriba
- Maximo 120 palabras en el cuerpo
- Mencionar 1 numero concreto (resenas, dias, porcentaje) en el primer parrafo
- El unico precio a mencionar es $499/mes — NUNCA mencionar setup, instalacion ni otros precios
- Incluir esta URL al final como CTA: {LANDING_URL}
- CTA final EXACTO antes de la URL: {"Ver si su negocio califica:" if lang == "es" else "See if your business qualifies:"}
- Firma: {FIRMA_PLAIN}
- Subject: incluir nombre del negocio + senial especifica (no generica)

Devuelve SOLO JSON sin markdown:
{{"subject": "...", "body": "..."}}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return {
        "subject": data["subject"],
        "html":    data["body"].replace("\n", "<br>") + FIRMA_HTML,
    }


# ─────────────────────────────────────────
#  FUNCIÓN PÚBLICA
# ─────────────────────────────────────────

def generate_proposal(lead: dict, lang: str = None) -> dict:
    """
    Genera email de propuesta para un lead en un idioma específico.
    1. Decide template + idioma según señales del lead (o usa lang override)
    2. Si hay ANTHROPIC_API_KEY → personaliza con Claude
    3. Si no → usa template estático signal-based

    Retorna: {"subject": str, "html": str}
    """
    template, detected_lang = decide_template_and_language(lead)
    lang = lang or detected_lang

    if ANTHROPIC_API_KEY:
        try:
            lead_with_lang = {**lead, "is_latino": "YES" if lang == "es" else "NO"}
            return _generate_with_claude(lead_with_lang, template, lang)
        except Exception as e:
            logging.warning(f"Claude API fallo, usando template: {e}")

    fn = TEMPLATE_FN.get((template, lang))
    if not fn:
        fn = TEMPLATE_FN[("ai_receptionist", "en")]

    return fn(lead)


def generate_proposal_bilingual(lead: dict) -> dict:
    """
    Genera un email único con el mensaje en español arriba e inglés abajo.
    Retorna: {"subject": str, "html": str}
    """
    template, _ = decide_template_and_language(lead)

    es = generate_proposal(lead, lang="es")
    en = generate_proposal(lead, lang="en")

    # Subject en inglés (más probable que pase filtros de spam)
    subject = en["subject"]

    divider = (
        "<br><br>"
        "<hr style='border:none;border-top:1px solid #ccc;margin:24px 0'>"
        "<p style='color:#888;font-size:12px;margin:0 0 16px'>— English version below —</p>"
    )

    html = es["html"] + divider + en["html"]

    return {"subject": subject, "html": html}


# ─────────────────────────────────────────
#  TEST — DRY RUN 5 LEADS
# ─────────────────────────────────────────

if __name__ == "__main__":

    TEST_LEADS = [
        # A — Sin web, Latino
        {
            "name": "Hermanos HVAC",
            "city": "Chicago, IL",
            "niche": "HVAC",
            "reviews": 3,
            "rating": 3.7,
            "website": "NO WEBSITE",
            "is_latino": "YES",
        },
        # B — Muchas reseñas, tiene web, no latino
        {
            "name": "Sela Roofing & Remodeling",
            "city": "Minneapolis, MN",
            "niche": "Roofing",
            "reviews": 647,
            "rating": 4.8,
            "website": "https://selaroofing.com",
            "is_latino": "NO",
        },
        # C — Pocas reseñas, tiene web, no latino
        {
            "name": "Nordic Construction LLC",
            "city": "Minneapolis, MN",
            "niche": "Remodeling",
            "reviews": 12,
            "rating": 4.5,
            "website": "https://nordicconstructionllc.com",
            "is_latino": "NO",
        },
        # Extra — Sin web, no latino
        {
            "name": "CENTRO TECNICO LATINO USA",
            "city": "Houston, TX",
            "niche": "HVAC",
            "reviews": 8,
            "rating": 4.2,
            "website": "NO WEBSITE",
            "is_latino": "YES",
        },
        # Extra — Reseñas medias, tiene web, Latino
        {
            "name": "Ojeda Drywall & Painting",
            "city": "Minneapolis, MN",
            "niche": "Painting",
            "reviews": 45,
            "rating": 4.9,
            "website": "https://ojedadrywall.com",
            "is_latino": "YES",
        },
    ]

    print("\n" + "="*65)
    print("  DRY RUN — Signal-Based Email Generator")
    print("="*65)

    for lead in TEST_LEADS:
        template, lang = decide_template_and_language(lead)
        result = generate_proposal(lead)

        has_web = lead["website"] != "NO WEBSITE"
        reviews = lead["reviews"]
        signal = (
            "NO WEBSITE" if not has_web
            else f"reviews={reviews} ({'>=100' if reviews >= 100 else '<20' if reviews < 20 else '20-99'})"
        )

        print(f"\nLEAD:     {lead['name']} | {lead['city']}")
        print(f"SENIAL:   {signal} | is_latino={lead['is_latino']}")
        print(f"TEMPLATE: {template} | IDIOMA: {lang}")
        print(f"SUBJECT:  {result['subject']}")
        print(f"BODY:\n{result['html'].replace('<br>', chr(10))}")
        print("-"*65)
