"""
Script de prueba para el bot Telegram
Ejecuta: python tests/test_bot.py
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from ai_assistant import asistente
from database import db
from financial_logic import analizador

print("=" * 70)
print("🌸 AMIGA FINANCIERA - MODO DE PRUEBA")
print("=" * 70)
print()

# Crear un usuario de prueba
test_user_id = "test_user_123"
print("📝 Registrando usuario de prueba...")
db.registrar_usuario(test_user_id, "María Test", 2000.0)
print(f"✅ Usuario {test_user_id} registrado con presupuesto de $2000.00")
print()

# Lista de mensajes de prueba
mensajes_prueba = [
    "Hola, ¿cómo estás?",
    "Gasté 150 pesos en el mercado",
    "Compré ropa por 300 pesos",
    "Pagué 80 pesos de transporte",
    "¿Cuánto dinero me queda?",
    "¿En qué estoy gastando más?",
    "Me pagaron 2500 pesos",
    "¿Me alcanzará el dinero este mes?",
]

print("🤖 Probando diferentes conversaciones:\n")
print("=" * 70)

for i, mensaje in enumerate(mensajes_prueba, 1):
    print(f"\n💬 [{i}/{len(mensajes_prueba)}] Usuario: {mensaje}")
    print("-" * 70)

    try:
        # Procesar mensaje con la IA
        respuesta = asistente.procesar_mensaje(test_user_id, mensaje)

        # Mostrar respuesta
        print(f"🤖 Bot (texto): {respuesta.get('respuesta_texto', 'N/A')}")
        print(f"🎤 Bot (voz):   {respuesta.get('respuesta_voz', 'N/A')}")

        # Mostrar metadatos si hay
        if respuesta.get('accion'):
            print(f"📌 Acción: {respuesta['accion']}")
        if respuesta.get('monto'):
            print(f"💵 Monto: ${respuesta['monto']:.2f}")
        if respuesta.get('categoria'):
            print(f"🏷️  Categoría: {respuesta['categoria']}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("=" * 70)

# Mostrar resumen final
print("\n📊 RESUMEN FINANCIERO FINAL")
print("=" * 70)

resumen = db.obtener_resumen_mensual(test_user_id)

print(f"\n💰 Presupuesto mensual: ${resumen['presupuesto_mensual']:.2f}")
print(f"💸 Total gastado:       ${resumen['total_gastado']:.2f}")
print(f"✨ Dinero restante:     ${resumen['dinero_restante']:.2f}")
print(f"📈 Porcentaje gastado:  {resumen['porcentaje_gastado']:.1f}%")

if resumen['gastos_por_categoria']:
    print("\n📋 Gastos por categoría:")
    for categoria, monto in resumen['gastos_por_categoria'].items():
        porcentaje = (monto / resumen['total_gastado'] * 100) if resumen['total_gastado'] > 0 else 0
        print(f"   • {categoria}: ${monto:.2f} ({porcentaje:.1f}%)")

# Obtener proyección
print("\n🔮 Proyección de fin de mes:")
proyeccion = analizador.proyeccion_fin_de_mes(test_user_id)
print(f"   • Gasto diario promedio: ${proyeccion['gasto_diario_promedio']:.2f}")
print(f"   • Gasto proyectado mes:  ${proyeccion['gasto_proyectado_mes']:.2f}")
print(f"   • Gasto diario ideal:    ${proyeccion['gasto_diario_ideal']:.2f}")

if proyeccion['tiene_deficit']:
    print(f"   ⚠️  Déficit proyectado: ${proyeccion['deficit_proyectado']:.2f}")
else:
    print(f"   ✅ ¡Vas por buen camino!")

# Obtener últimos movimientos
print("\n📜 Últimos movimientos:")
movimientos = db.obtener_ultimos_movimientos(test_user_id, 5)
for mov in movimientos:
    tipo_emoji = "💸" if mov['tipo'] == 'gasto' else "💵"
    print(f"   {tipo_emoji} {mov['fecha'][:10]} | ${mov['monto']:.2f} | {mov['categoria']}")

print("\n" + "=" * 70)
print("✅ Prueba completada")
print("=" * 70)
print("\n💡 Tips:")
print("   • Los datos se guardan en 'finanzas_mujeres.db'")
print("   • Puedes ejecutar este script varias veces")
print("   • Modifica 'mensajes_prueba' para probar otros casos")
print()
