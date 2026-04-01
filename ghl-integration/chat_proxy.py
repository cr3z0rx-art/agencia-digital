"""
============================================================
  chat_proxy.py — Proxy seguro para el chat widget de Claude
  Evita exponer la ANTHROPIC_API_KEY en el frontend.

  SETUP:
    pip install fastapi uvicorn anthropic python-dotenv

  USO:
    python ghl-integration/chat_proxy.py
    # Corre en http://localhost:8080

  PRODUCCION:
    uvicorn ghl-integration.chat_proxy:app --host 0.0.0.0 --port 8080
============================================================
"""

import os
import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ghl-integration"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

try:
    import anthropic
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError:
    print("\nFalta instalar dependencias:")
    print("  pip install fastapi uvicorn anthropic python-dotenv\n")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CALENDAR_URL = "https://api.leadconnectorhq.com/widget/booking/AyyxvGu2X1mfbhS4OlXj"

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

# ── FastAPI app ──────────────────────────────────────────
app = FastAPI(title="MultiVenza Chat Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # En producción: ["https://www.multivenzadigital.com"]
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# ── System prompt ────────────────────────────────────────
SYSTEM_PROMPT = f"""You are MultiVenza Digital's AI assistant. You help contractors and Latino businesses in the USA understand our services and pricing.

## MultiVenza Digital — Services & Pricing

### Plan 1: AI Receptionist
- Setup: $1,000 (one-time)
- Monthly: $500/mo
- What it does: AI answers calls, texts, and WhatsApp messages 24/7. Books appointments, sends follow-ups automatically. Customer never goes to voicemail again.
- Best for: Businesses missing calls, HVAC, plumbing, roofing contractors

### Plan 2: Full AI Employee + SEO
- Setup: $1,500 (one-time)
- Monthly: $800/mo
- What it does: Everything in AI Receptionist PLUS local SEO — Google Maps ranking, Google Business optimization, so customers find you before competitors.
- Best for: Businesses that want both AI automation AND to rank higher on Google

### Add-on: Lead Generation
- No setup fee
- Monthly: from $300/mo
- What it does: We find local businesses that need your services and bring qualified leads to you.
- Can be added to any plan.

## Rules
- Detect the visitor's language from their message. Respond in SPANISH if they write in Spanish, ENGLISH otherwise.
- Be warm and direct — like a knowledgeable friend, not a salesperson.
- Never hard-sell. Give honest, concise answers.
- For every response, end with the calendar CTA:
  - Spanish: "¿Tiene 15 minutos esta semana? [Agenda una llamada gratis]({CALENDAR_URL})"
  - English: "Worth 15 minutes this week? [Book a free call]({CALENDAR_URL})"
- If you don't know the answer or the question is very specific, say:
  - Spanish: "Para eso es mejor hablar directo. [Agenda una llamada gratis]({CALENDAR_URL}) y te explicamos todo."
  - English: "For that it's best to talk directly. [Book a free call]({CALENDAR_URL}) and we'll explain everything."
- Keep responses concise — max 3-4 sentences plus the CTA. No walls of text.
- You represent Keyner Guerrero, CEO of MultiVenza Digital (hello@multivenzadigital.com).
"""

# ── Models ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []   # [{"role": "user"|"assistant", "content": "..."}]

class ChatResponse(BaseModel):
    reply: str

# ── Endpoint ─────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # Build conversation history (max last 6 exchanges to keep context manageable)
    messages = req.history[-12:] if req.history else []
    messages.append({"role": "user", "content": req.message})

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        reply = response.content[0].text
        logging.info(f"Chat | user: {req.message[:60]!r} | reply: {reply[:60]!r}")
        return ChatResponse(reply=reply)

    except anthropic.APIStatusError as e:
        logging.error(f"Anthropic API error: {e}")
        raise HTTPException(status_code=502, detail="AI service unavailable")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MultiVenza Chat Proxy"}


# ── Run directly ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("  MultiVenza Chat Proxy")
    print("  http://localhost:8080")
    print("  POST /chat  — send messages")
    print("  GET  /health — status check")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
