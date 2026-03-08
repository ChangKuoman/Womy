"""
Bot de Telegram - Amiga Financiera
====================================

Bot implementado con Telegram Bot API.

CONFIGURACIÓN (2 minutos):
1. Abre Telegram
2. Busca @BotFather
3. Envía /newbot
4. Sigue las instrucciones (elige un nombre y username)
5. Copia el token que te da
6. Pégalo en el archivo .env como TELEGRAM_TOKEN=tu_token_aqui
7. ¡Listo! Ejecuta este script

No necesitas:
- ❌ Cuenta empresarial
- ❌ Verificación
- ❌ Servidor público
- ❌ Webhooks
- ❌ Configuración complicada
"""
import time
from telegram_handler import telegram_handler
from ai_assistant import asistente
from voice_generator import generador_voz
from audio_transcriber import transcriptor
from database import db
from config import settings


def procesar_mensaje(chat_id: str, user_id: str, texto: str, nombre: str):
    """
    Procesa un mensaje del usuario

    Args:
        chat_id: ID del chat de Telegram
        user_id: ID del usuario
        texto: Texto del mensaje
        nombre: Nombre del usuario
    """
    try:
        print(f"📨 Mensaje de {nombre} ({user_id}): {texto}")

        # Procesar con la IA
        respuesta = asistente.procesar_mensaje(user_id, texto)

        # Enviar respuesta (solo texto por defecto)
        texto_respuesta = respuesta.get('respuesta_texto') or respuesta.get('respuesta_voz', 'Entendido 👍')

        # Formatear el mensaje con HTML
        mensaje_formateado = formatear_mensaje(texto_respuesta)

        telegram_handler.enviar_mensaje(chat_id, mensaje_formateado)

        # CONFIGURACIÓN DE AUDIO VIA .env
        # ENVIAR_AUDIO_RESPUESTA=true|false
        ENVIAR_AUDIO = settings.enviar_audio_respuesta

        # Generar y enviar audio (consume créditos de ElevenLabs)
        if ENVIAR_AUDIO and settings.elevenlabs_api_key and len(respuesta.get('respuesta_voz', '')) > 50:
            texto_voz = respuesta.get('respuesta_voz', '')
            audio_path = generador_voz.generar_audio(texto_voz)

            if audio_path:
                telegram_handler.enviar_audio(chat_id, audio_path)
                print(f"🎤 Audio enviado a {nombre}")

        print(f"✅ Respuesta enviada a {nombre}")

    except Exception as e:
        print(f"❌ Error al procesar mensaje: {e}")
        telegram_handler.enviar_mensaje(
            chat_id,
            "Sorry friend, I had a problem. Could you try again? 😊"
        )


def formatear_mensaje(texto: str) -> str:
    """Formatea el mensaje para Telegram con HTML básico"""
    # Reemplazar emojis de cifras por HTML
    texto = texto.replace('💰', '💰').replace('📊', '📊').replace('✅', '✅')

    # Si tiene "Resumen del mes:" hacer el título en negrita
    if 'Monthly Summary:' in texto:
        texto = texto.replace('Monthly Summary:', '<b>💰 Monthly Summary:</b>')

    if 'Analysis of your' in texto:
        texto = texto.replace('Analysis of your', '<b>📊 Analysis of your</b>')

    if 'Proyección del mes:' in texto:
        texto = texto.replace('Proyección del mes:', '<b>🔮 Proyección del mes:</b>')

    return texto


def main():
    """Función principal del bot"""
    print("=" * 70)
    print("🌸 AMIGA FINANCIERA - BOT DE TELEGRAM")
    print("=" * 70)
    print()

    # Verificar configuración
    if not settings.telegram_token:
        print("❌ ERROR: Token de Telegram no configurado")
        print()
        print("📝 Pasos para configurar:")
        print("1. Abre Telegram y busca @BotFather")
        print("2. Envía /newbot y sigue las instrucciones")
        print("3. Copia el token que te da")
        print("4. Agrega al archivo .env: TELEGRAM_TOKEN=tu_token_aqui")
        print("5. Ejecuta este script de nuevo")
        print()
        return

    if not settings.featherless_api_key:
        print("⚠️ ADVERTENCIA: Featherless API key no configurado")
        print("   El bot no podrá procesar mensajes sin esto")
        print("   Regístrate gratis en: https://featherless.ai")
        print()
        return

    print("✅ Configuración verificada")
    print(f"✅ Bot conectado exitosamente")
    print()
    print("=" * 70)
    print("🤖 Bot activo - Esperando mensajes...")
    print("💡 Presiona Ctrl+C para detener")
    print("=" * 70)
    print()

    # Obtener información del bot
    try:
        response = telegram_handler.obtener_actualizaciones()
        print(f"📱 Bot listo para recibir mensajes")
        print(f"💬 Busca tu bot en Telegram y envía /start")
        print()
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return

    # Polling loop
    offset = None
    mensaje_bienvenida_enviado = set()

    try:
        while True:
            # Obtener nuevas actualizaciones
            actualizaciones = telegram_handler.obtener_actualizaciones(offset)

            for update in actualizaciones:
                # Actualizar offset
                offset = update.get('update_id', 0) + 1

                # Extraer mensaje
                mensaje_info = telegram_handler.extraer_mensaje(update)

                if not mensaje_info:
                    continue

                chat_id = mensaje_info['chat_id']
                user_id = mensaje_info['user_id']
                texto = mensaje_info['text']
                nombre = mensaje_info['first_name']

                # Si el mensaje es de voz, transcribirlo primero
                if mensaje_info.get('tiene_voz'):
                    if not settings.aceptar_audio_entrada:
                        telegram_handler.enviar_mensaje(
                            chat_id,
                            "Por favor, envía tu mensaje como texto 📝"
                        )
                        continue

                    print(f"🎤 Mensaje de voz recibido de {nombre}")

                    voice_info = mensaje_info.get('voice')
                    if voice_info:
                        file_id = voice_info.get('file_id')

                        # Descargar el audio
                        audio_path = telegram_handler.descargar_audio(file_id)

                        if audio_path:
                            # Obtener idioma del usuario
                            usuario = db.obtener_usuario(user_id)
                            idioma = usuario.get('idioma', 'en') if usuario else 'en'

                            # Transcribir el audio (intenta Groq primero, luego Fish Audio)
                            texto_transcrito = transcriptor.transcribir_audio(audio_path, idioma)

                            if texto_transcrito:
                                texto = texto_transcrito
                                print(f"📝 Transcripción: {texto}")

                                # Limpiar el archivo de audio temporal
                                transcriptor.limpiar_audio_temporal(audio_path)
                            else:
                                telegram_handler.enviar_mensaje(
                                    chat_id,
                                    "Sorry, I couldn't understand your audio 😕 Could you write it?"
                                )
                                continue
                        else:
                            telegram_handler.enviar_mensaje(
                                chat_id,
                                "There was a problem downloading your audio 😕"
                            )
                            continue

                # Comando /start
                if texto == '/start':
                    if user_id not in mensaje_bienvenida_enviado:
                        mensaje_bienvenida = f"""Hello {nombre}! 🌸

I'm your <b>Financial Friend</b>, I'm here to help you manage your money.

<b>What can I do for you?</b>
💰 Register your expenses and income
📊 Show you where you spend the most
💡 Give you tips to save
🔮 Project how the month will end

<b>Examples of how to talk to me:</b>
• "I spent 50 dollars on food"
• "I got paid 2000 dollars"
• "How much do I have left?"
• "Where do I spend the most?"
• "Set my budget to 3000"

¡Adelante, cuéntame sobre tus finanzas! 💪"""

                        telegram_handler.enviar_mensaje(chat_id, mensaje_bienvenida)
                        mensaje_bienvenida_enviado.add(user_id)
                    continue

                # Comando /ayuda
                if texto == '/ayuda' or texto == '/help':
                    mensaje_ayuda = """<b>📚 Comandos disponibles:</b>

/start - Mensaje de bienvenida
/ayuda - Esta ayuda
/resumen - Ver tu resumen del mes
/categorias - Ver gastos por categoría

<b>Ejemplos de conversación:</b>
• "Gasté 150 en el mercado"
• "Compré ropa por 300"
• "Me pagaron hoy"
• "¿Me alcanzará el dinero?"
• "Quiero cambiar mi presupuesto a 2500"

¡Solo escríbeme naturalmente! 😊"""

                    telegram_handler.enviar_mensaje(chat_id, mensaje_ayuda)
                    continue

                # Comando /resumen
                if texto == '/resumen':
                    procesar_mensaje(chat_id, user_id, "¿Cuánto me queda?", nombre)
                    continue

                # Comando /categorias
                if texto == '/categorias':
                    procesar_mensaje(chat_id, user_id, "¿En qué gasto más?", nombre)
                    continue

                # Mensaje normal
                if texto.strip():
                    procesar_mensaje(chat_id, user_id, texto, nombre)

            # Pequeña pausa para no saturar la API
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("👋 Bot detenido por el usuario")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Error en el bot: {e}")


if __name__ == "__main__":
    main()
