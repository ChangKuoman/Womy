"""
Test rápido de la lógica multiidioma sin OpenAI
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from database import db
from config import settings
from localization import obtener_traduccion, obtener_simbolo_moneda, IDIOMAS_SOPORTADOS, MONEDAS_SOPORTADAS

print("=" * 80)
print("🌍 PRUEBA DE SISTEMA MULTIIDIOMA Y MULTIMONEDA")
print("=" * 80)

# Limpiar usuarios de prueba
print("\n🧹 Limpiando usuarios de prueba anteriores...")
import sqlite3
try:
    conn = sqlite3.connect(settings.database_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE whatsapp_id LIKE 'test_%'")
    conn.commit()
    conn.close()
    print("✅ Base de datos limpiada")
except Exception as e:
    print(f"⚠️  No se pudo limpiar: {e}")

print("\n" + "=" * 80)
print("TEST 1: Crear usuario Español + MXN")
print("=" * 80)

user1 = "test_mexico_001"
db.registrar_usuario(user1, "María López", 3000, "es", "MXN", onboarding_completo=1)
usuario1 = db.obtener_usuario(user1)
print(f"✓ Usuario creado: {usuario1['nombre']}")
print(f"  - ID: {usuario1['whatsapp_id']}")
print(f"  - Idioma: {usuario1['idioma']}")
print(f"  - Moneda: {usuario1['moneda']}")
print(f"  - Presupuesto: {obtener_simbolo_moneda(usuario1['moneda'])}{usuario1['presupuesto_mensual']:.2f}")

# Probar traducciones
print(f"\n📝 Traducciones en Español:")
print(f"  - Bienvenida: {obtener_traduccion('es', 'idioma_seleccionado')}")
print(f"  - Moneda: {obtener_traduccion('es', 'moneda_seleccionada', moneda='Peso Mexicano')}")

print("\n" + "=" * 80)
print("TEST 2: Crear usuario Português + BRL")
print("=" * 80)

user2 = "test_brasil_001"
db.registrar_usuario(user2, "João Silva", 2000, "pt", "BRL", onboarding_completo=1)
usuario2 = db.obtener_usuario(user2)
print(f"✓ Usuario creado: {usuario2['nombre']}")
print(f"  - ID: {usuario2['whatsapp_id']}")
print(f"  - Idioma: {usuario2['idioma']}")
print(f"  - Moneda: {usuario2['moneda']}")
print(f"  - Presupuesto: {obtener_simbolo_moneda(usuario2['moneda'])}{usuario2['presupuesto_mensual']:.2f}")

print(f"\n📝 Traducciones en Português:")
print(f"  - Bienvenida: {obtener_traduccion('pt', 'idioma_seleccionado')}")
print(f"  - Moneda: {obtener_traduccion('pt', 'moneda_seleccionada', moneda='Real Brasileño')}")

print("\n" + "=" * 80)
print("TEST 3: Crear usuario English + USD")
print("=" * 80)

user3 = "test_usa_001"
db.registrar_usuario(user3, "Sarah Johnson", 1500, "en", "USD", onboarding_completo=1)
usuario3 = db.obtener_usuario(user3)
print(f"✓ Usuario creado: {usuario3['nombre']}")
print(f"  - ID: {usuario3['whatsapp_id']}")
print(f"  - Idioma: {usuario3['idioma']}")
print(f"  - Moneda: {usuario3['moneda']}")
print(f"  - Presupuesto: {obtener_simbolo_moneda(usuario3['moneda'])}{usuario3['presupuesto_mensual']:.2f}")

print(f"\n📝 Traducciones en English:")
print(f"  - Bienvenida: {obtener_traduccion('en', 'idioma_seleccionado')}")
print(f"  - Moneda: {obtener_traduccion('en', 'moneda_seleccionada', moneda='US Dollar')}")

print("\n" + "=" * 80)
print("TEST 4: Crear usuario Français + EUR")
print("=" * 80)

user4 = "test_france_001"
db.registrar_usuario(user4, "Sophie Martin", 1800, "fr", "EUR", onboarding_completo=1)
usuario4 = db.obtener_usuario(user4)
print(f"✓ Usuario creado: {usuario4['nombre']}")
print(f"  - ID: {usuario4['whatsapp_id']}")
print(f"  - Idioma: {usuario4['idioma']}")
print(f"  - Moneda: {usuario4['moneda']}")
print(f"  - Presupuesto: {obtener_simbolo_moneda(usuario4['moneda'])}{usuario4['presupuesto_mensual']:.2f}")

print(f"\n📝 Traducciones en Français:")
print(f"  - Bienvenida: {obtener_traduccion('fr', 'idioma_seleccionado')}")
print(f"  - Moneda: {obtener_traduccion('fr', 'moneda_seleccionada', moneda='Euro')}")

print("\n" + "=" * 80)
print("TEST 5: Detección de usuario nuevo")
print("=" * 80)

test_new_user = "new_user_test"
print(f"¿Es usuario nuevo? {db.es_usuario_nuevo(test_new_user)}")
db.registrar_usuario(test_new_user, "Nueva Usuario", 1000, "es", "USD", onboarding_completo=0)
print(f"Después de registrar (sin onboarding): {db.es_usuario_nuevo(test_new_user)}")
db.actualizar_idioma_moneda(test_new_user, "es", "USD")
print(f"Después de actualizar idioma/moneda: {db.es_usuario_nuevo(test_new_user)}")

print("\n" + "=" * 80)
print("TEST 6: Símbolos de moneda")
print("=" * 80)

print("\n📊 Símbolos de moneda soportados:")
monedas_test = ["USD", "EUR", "MXN", "BRL", "PEN", "ARS", "CLP"]
for moneda in monedas_test:
    simbolo = obtener_simbolo_moneda(moneda)
    print(f"  {moneda}: {simbolo}")

print("\n" + "=" * 80)
print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
print("=" * 80)

# Mostrar resumen de usuarios en BD
print("\n📊 Resumen de usuarios en base de datos:")
print("-" * 80)
usuarios_test = [user1, user2, user3, user4]
for user_id in usuarios_test:
    u = db.obtener_usuario(user_id)
    if u:
        print(f"✓ {u['nombre']:20} | {u['idioma']:2} | {u['moneda']:3} | Onboarding: {u.get('onboarding_completo', 0)}")

print("=" * 80)
