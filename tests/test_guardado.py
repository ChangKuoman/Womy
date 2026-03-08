"""
Script de prueba rápida para verificar que el bot guarda datos correctamente
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from ai_assistant import asistente
from database import db
from config import settings

print("=" * 70)
print("PRUEBA RÁPIDA - VERIFICACIÓN DE GUARDADO")
print("=" * 70)
print()

# ID de prueba
user_id = "test_user_999"

# Limpiar usuario de prueba anterior si existe
print("🧹 Limpiando datos de prueba anteriores...")
import sqlite3
conn = sqlite3.connect(settings.database_path)
cursor = conn.cursor()
cursor.execute("DELETE FROM movimientos WHERE whatsapp_id = ?", (user_id,))
cursor.execute("DELETE FROM usuarios WHERE whatsapp_id = ?", (user_id,))
conn.commit()
conn.close()
print()

# Pruebas
pruebas = [
    "Tengo un presupuesto de 1000 soles para el mes",
    "Mi renta es de 500",
    "Gasté 150 en comida",
    "¿Cuánto me queda?",
]

for i, mensaje in enumerate(pruebas, 1):
    print(f"{'='*70}")
    print(f"PRUEBA {i}: {mensaje}")
    print(f"{'='*70}")

    respuesta = asistente.procesar_mensaje(user_id, mensaje)

    print(f"\n📤 Respuesta del bot:")
    print(f"   Texto: {respuesta.get('respuesta_texto', 'N/A')}")
    print()

# Verificar en la base de datos
print("=" * 70)
print("VERIFICACIÓN EN BASE DE DATOS")
print("=" * 70)
print()

resumen = db.obtener_resumen_mensual(user_id)
print(f"💰 Presupuesto configurado: ${resumen['presupuesto_mensual']:.2f}")
print(f"💸 Total gastado: ${resumen['total_gastado']:.2f}")
print(f"✨ Dinero restante: ${resumen['dinero_restante']:.2f}")
print()

if resumen['gastos_por_categoria']:
    print("📋 Gastos por categoría:")
    for cat, monto in resumen['gastos_por_categoria'].items():
        print(f"   • {cat}: ${monto:.2f}")
else:
    print("⚠️  No hay gastos registrados")

print()
movimientos = db.obtener_ultimos_movimientos(user_id, 10)
print(f"📜 Total de movimientos registrados: {len(movimientos)}")
for mov in movimientos:
    tipo_emoji = "💸" if mov['tipo'] == 'gasto' else "💵"
    print(f"   {tipo_emoji} {mov['tipo'].upper()}: ${mov['monto']:.2f} - {mov['categoria']}")

print()
print("=" * 70)

if resumen['presupuesto_mensual'] > 0 and len(movimientos) > 0:
    print("✅ ÉXITO: El bot está guardando datos correctamente")
else:
    print("❌ PROBLEMA: El bot NO está guardando datos")
    print()
    print("Posibles causas:")
    print("1. La API de Featherless no está respondiendo correctamente")
    print("2. El formato JSON de respuesta no es el esperado")
    print("3. Hay un error en la configuración")

print("=" * 70)
