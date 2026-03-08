"""
Script de prueba para el bot Telegram
Prueba multiidioma y multimoneda
Ejecuta: python tests/test_multiidioma.py
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from ai_assistant import asistente
from database import db

print("=" * 70)
print("🌸 AMIGA FINANCIERA - PRUEBA MULTIIDIOMA Y MULTIMONEDA")
print("=" * 70)
print()

# Test 1: Usuario NUEVO - Selecciona Español y Pesos Mexicanos
print("\n" + "="*70)
print("TEST 1: Usuario Nuevo - Español + MXN (Peso Mexicano)")
print("="*70)
usuario1 = "user_mexico_001"

# Primer mensaje: selecciona idioma y moneda
print("\n👤 Usuario escribe: 'es MXN'")
respuesta = asistente.procesar_mensaje(usuario1, "es MXN")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Segundo mensaje: configura presupuesto
print("👤 Usuario escribe: 'Mi presupuesto es 3000'")
respuesta = asistente.procesar_mensaje(usuario1, "Mi presupuesto es 3000")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Tercer mensaje: registra ingreso
print("👤 Usuario escribe: 'Me pagaron 2500'")
respuesta = asistente.procesar_mensaje(usuario1, "Me pagaron 2500")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Cuarto mensaje: registra gasto
print("👤 Usuario escribe: 'Gasté 150 en comida'")
respuesta = asistente.procesar_mensaje(usuario1, "Gasté 150 en comida")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Quinto mensaje: consulta resumen
print("👤 Usuario escribe: '¿Cuánto me queda?'")
respuesta = asistente.procesar_mensaje(usuario1, "¿Cuánto me queda?")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Test 2: Usuario NUEVO - Selecciona Português + BRL
print("\n" + "="*70)
print("TEST 2: Usuária Nova - Português + BRL (Real Brasileño)")
print("="*70)
usuario2 = "user_brasil_001"

# Primer mensaje: selecciona idioma y moneda
print("\n👤 Usuária escreve: 'pt BRL'")
respuesta = asistente.procesar_mensaje(usuario2, "pt BRL")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Segundo mensaje: configura presupuesto
print("👤 Usuária escreve: 'Meu orçamento é 2000'")
respuesta = asistente.procesar_mensaje(usuario2, "Meu orçamento é 2000")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Tercer mensaje: registra gasto
print("👤 Usuária escreve: 'Gastei 250 em comida'")
respuesta = asistente.procesar_mensaje(usuario2, "Gastei 250 em comida")
print(f"🤖 Bot responde (texto):\n{respuesta['respuesta_texto']}\n")

# Test 3: Usuario NUEVO - Selecciona English + USD
print("\n" + "="*70)
print("TEST 3: New User - English + USD (US Dollar)")
print("="*70)
usuario3 = "user_usa_001"

# First message: select language and currency
print("\n👤 User writes: 'en USD'")
respuesta = asistente.procesar_mensaje(usuario3, "en USD")
print(f"🤖 Bot responds (text):\n{respuesta['respuesta_texto']}\n")

# Second message: configure budget
print("👤 User writes: 'My budget is 1500'")
respuesta = asistente.procesar_mensaje(usuario3, "My budget is 1500")
print(f"🤖 Bot responds (text):\n{respuesta['respuesta_texto']}\n")

# Third message: register expense
print("👤 User writes: 'I spent 45 on groceries'")
respuesta = asistente.procesar_mensaje(usuario3, "I spent 45 on groceries")
print(f"🤖 Bot responds (text):\n{respuesta['respuesta_texto']}\n")

# Test 4: Usuario NUEVO - Selecciona Français + EUR
print("\n" + "="*70)
print("TEST 4: Nouvel Utilisateur - Français + EUR (Euro)")
print("="*70)
usuario4 = "user_france_001"

# Premier message: sélectionne la langue et la devise
print("\n👤 Utilisateur écrit: 'fr EUR'")
respuesta = asistente.procesar_mensaje(usuario4, "fr EUR")
print(f"🤖 Bot répond (texte):\n{respuesta['respuesta_texto']}\n")

# Deuxième message: configure le budget
print("👤 Utilisateur écrit: 'Mon budget est 1800'")
respuesta = asistente.procesar_mensaje(usuario4, "Mon budget est 1800")
print(f"🤖 Bot répond (texte):\n{respuesta['respuesta_texto']}\n")

print("\n" + "="*70)
print("✅ PRUEBAS MULTIIDIOMA COMPLETADAS")
print("="*70)

# Mostrar información de usuarios
print("\n📊 Resumen de usuarios creados:")
print("-" * 70)
usuarios = [
    ("user_mexico_001", "Español", "MXN"),
    ("user_brasil_001", "Português", "BRL"),
    ("user_usa_001", "English", "USD"),
    ("user_france_001", "Français", "EUR"),
]
for user_id, idioma, moneda in usuarios:
    usuario = db.obtener_usuario(user_id)
    if usuario:
        print(f"✓ {user_id}: {idioma} | {moneda}")
        print(f"  Presupuesto: {moneda} {usuario.get('presupuesto_mensual', 'N/A')}")
