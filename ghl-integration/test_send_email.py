"""
Test de envío de email con 1 lead real.
Crea el contacto en GHL y envía el email — muestra la respuesta completa de la API.

USO:
    python ghl-integration/test_send_email.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from ghl_client import validate_credentials, create_contact, update_contact, send_email, GHL_FROM_EMAIL
from email_generator import generate_proposal

TEST_LEAD = {
    "name":                 "Test Contractor GHL",
    "city":                 "Minneapolis, MN",
    "niche":                "Roofing",
    "recommended_service":  "Automatización con IA",
    "pitch_line":           "Test lead — diagnóstico de envío de email.",
    "reviews":              100,
    "rating":               4.8,
    "website":              "https://example.com",
    "outreach_language":    "Inglés",
    "phone":                "+16125550000",   # número de prueba
    "email":                "hello@multivenzadigital.com",  # ← enviar a TI MISMO para verificar
    "address":              "123 Test St, Minneapolis, MN",
}

print("\n" + "="*60)
print("  TEST — GHL Email Send")
print("="*60)
print(f"  FROM:    {GHL_FROM_EMAIL or 'NO CONFIGURADO — agrega GHL_FROM_EMAIL en .env'}")
print(f"  TO:      {TEST_LEAD['email']}")
print(f"  Lead:    {TEST_LEAD['name']}")
print()

if not GHL_FROM_EMAIL:
    print("ERROR: GHL_FROM_EMAIL no está en .env")
    print("Agrega: GHL_FROM_EMAIL=hello@multivenzadigital.com")
    sys.exit(1)

# 1. Validar credenciales
print("1. Validando credenciales GHL...")
if not validate_credentials():
    print("   ERROR: credenciales inválidas")
    sys.exit(1)
print("   OK\n")

# 2. Crear contacto de prueba (o reusar existente)
print("2. Creando contacto de prueba en GHL...")
try:
    contact = create_contact({
        "firstName": "Test",
        "lastName":  "EmailDiag",
        "phone":     TEST_LEAD["phone"],
        "email":     TEST_LEAD["email"],
        "tags":      ["test-diagnostico"],
    })
    contact_id = contact.get("id")
    print(f"   OK — contact_id: {contact_id}\n")
except Exception as e:
    # Si ya existe, extraer el ID del mensaje de error
    error_str = str(e)
    import re
    match = re.search(r'"contactId":"(\w+)"', error_str)
    if match:
        contact_id = match.group(1)
        print(f"   Contacto ya existe — reusando contact_id: {contact_id}")
        # Actualizar email al correcto
        try:
            update_contact(contact_id, {"email": TEST_LEAD["email"]})
            print(f"   Email actualizado a {TEST_LEAD['email']}\n")
        except Exception as ue:
            print(f"   Advertencia al actualizar email: {ue}\n")
    else:
        print(f"   ERROR creando contacto: {e}\n")
        sys.exit(1)

# 3. Generar propuesta
print("3. Generando propuesta...")
proposal = generate_proposal(TEST_LEAD)
print(f"   Subject: {proposal['subject']}")
print(f"   Body preview: {proposal['html'][:100].replace('<br>', ' ')}...\n")

# 4. Enviar email — mostrar respuesta completa
print("4. Enviando email vía GHL API...")
import requests, os
from ghl_client import BASE_URL, GHL_LOCATION_ID, _headers, GHL_FROM_NAME

payload = {
    "type":          "Email",
    "locationId":    GHL_LOCATION_ID,
    "contactId":     contact_id,
    "emailTo":       TEST_LEAD["email"],
    "emailFrom":     GHL_FROM_EMAIL,
    "emailFromName": GHL_FROM_NAME,
    "subject":       proposal["subject"],
    "html":          proposal["html"],
    "message":       proposal["html"],
}

print(f"   Endpoint: POST {BASE_URL}/conversations/messages")
print(f"   Payload:\n{json.dumps({k: v if k != 'html' else v[:80]+'...' for k, v in payload.items()}, indent=4)}\n")

resp = requests.post(f"{BASE_URL}/conversations/messages", json=payload, headers=_headers())

print(f"   HTTP Status: {resp.status_code}")
print(f"   Response:\n{json.dumps(resp.json(), indent=4)}")

if resp.ok:
    print("\n  RESULTADO: Email enviado. Revisa tu bandeja de entrada.")
else:
    print("\n  RESULTADO: Error al enviar. Ver respuesta arriba para diagnóstico.")

print("="*60 + "\n")
