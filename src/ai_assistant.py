"""
Integración con Featherless.ai para procesamiento de lenguaje natural
"""
import json
from typing import Dict, Optional
from openai import OpenAI
from config import settings
from database import db
from financial_logic import analizador
from localization import TRADUCCIONES, obtener_traduccion, obtener_simbolo_moneda, IDIOMAS_SOPORTADOS, MONEDAS_SOPORTADAS


class AsistenteFinanciero:
    """Asistente de IA para procesar mensajes y generar respuestas"""

    def __init__(self):
        """Inicializa el cliente de Featherless"""
        self.client = OpenAI(
            base_url=settings.featherless_base_url,
            api_key=settings.featherless_api_key
        )
        self.model = settings.featherless_model

    def procesar_mensaje(self, user_id: str, mensaje_usuario: str) -> Dict:
        """
        Procesa un mensaje del usuario y genera una respuesta apropiada

        Args:
            user_id: ID del usuario
            mensaje_usuario: Mensaje enviado por el usuario

        Returns:
            Dict con la respuesta generada y metadatos
        """
        # Verificar si es usuario nuevo
        if db.es_usuario_nuevo(user_id):
            return self._procesar_onboarding(user_id, mensaje_usuario)

        # Asegurar que el usuario existe
        usuario = db.obtener_usuario(user_id)
        if not usuario:
            db.registrar_usuario(user_id)
            usuario = db.obtener_usuario(user_id)

        # Obtener idioma y moneda del usuario
        idioma = usuario.get('idioma', 'en')
        moneda = usuario.get('moneda', 'USD')

        # Obtener contexto financiero
        resumen = db.obtener_resumen_mensual(user_id)

        # Crear prompt con contexto
        prompt_sistema = self._crear_prompt_sistema(resumen, idioma, moneda)

        try:
            # Llamada a Featherless
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": mensaje_usuario}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=500
            )

            # Parsear respuesta JSON
            contenido = response.choices[0].message.content
            print(f"🤖 Respuesta de IA: {contenido}")  # Debug
            resultado = json.loads(contenido)

            # Debug: mostrar qué acción identificó
            print(f"📋 Acción identificada: {resultado.get('accion')}")
            print(f"💵 Monto extraído: {resultado.get('monto')}")
            print(f"🏷️ Categoría: {resultado.get('categoria')}")

            # Procesar según el tipo de acción
            respuesta_final = self._procesar_accion(user_id, resultado, idioma, moneda)

            return respuesta_final

        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
            print(f"Contenido recibido: {contenido}")
            return {
                "accion": "error",
                "respuesta_texto": "Sorry, I had trouble understanding your message. Could you rephrase it?",
                "respuesta_voz": "Sorry friend, I didn't quite understand your message. Could you say it in another way?"
            }
        except Exception as e:
            print(f"❌ Error al procesar mensaje: {e}")
            import traceback
            traceback.print_exc()
            return {
                "accion": "error",
                "respuesta_texto": "Sorry, I had a problem processing your message. Could you try again?",
                "respuesta_voz": "Sorry friend, I had a problem processing your message. Could you try again?"
            }

    def _procesar_onboarding(self, user_id: str, mensaje_usuario: str) -> Dict:
        """Procesa el onboarding de un usuario nuevo"""
        # Registrar usuario con valores por defecto
        db.registrar_usuario(user_id, onboarding_completo=0)

        # Verificar si el mensaje contiene idioma y moneda
        palabras = mensaje_usuario.strip().split()

        idioma_encontrado = None
        moneda_encontrada = None

        # Buscar idioma y moneda en el mensaje
        for palabra in palabras:
            # Limpiamos puntuacion comun para aceptar entradas como "es, usd" o "es-USD"
            token = palabra.strip(" ,.;:!?()[]{}\"'")
            token_idioma = token.lower()
            token_moneda = token.upper()

            if token_idioma in IDIOMAS_SOPORTADOS:
                idioma_encontrado = token_idioma
            elif token_moneda in MONEDAS_SOPORTADAS:
                moneda_encontrada = token_moneda

        # Si falta información, pedir al usuario
        if not idioma_encontrado or not moneda_encontrada:
            return {
                "accion": "onboarding",
                "respuesta_texto": obtener_traduccion("es", "bienvenida_nuevo"),
                "respuesta_voz": obtener_traduccion("es", "bienvenida_nuevo")
            }

        # Guardar preferencias del usuario
        db.actualizar_idioma_moneda(user_id, idioma_encontrado, moneda_encontrada)

        # Dar bienvenida con el idioma elegido
        resp_idioma = obtener_traduccion(idioma_encontrado, "idioma_seleccionado")
        resp_moneda = obtener_traduccion(idioma_encontrado, "moneda_seleccionada",
                                        moneda=MONEDAS_SOPORTADAS[moneda_encontrada][1])
        resp_presupuesto = obtener_traduccion(idioma_encontrado, "bienvenida_configurada")

        respuesta_completa = f"{resp_idioma}\n{resp_moneda}\n\n{resp_presupuesto}"

        return {
            "accion": "onboarding_completado",
            "respuesta_texto": respuesta_completa,
            "respuesta_voz": respuesta_completa
        }

    def _crear_prompt_sistema(self, resumen: Dict, idioma: str = "en", moneda: str = "USD") -> str:
        """Crea el prompt del sistema con el contexto financiero"""
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        # Obtener template de traducción
        template = obtener_traduccion(idioma, "prompt_principal",
            moneda=simbolo_moneda,
            presupuesto_mensual=resumen['presupuesto_mensual'],
            total_gastado=resumen['total_gastado'],
            dinero_restante=resumen['dinero_restante'],
            porcentaje_gastado=resumen['porcentaje_gastado'],
            gastos_por_categoria=self._formatear_categorias(resumen['gastos_por_categoria'], simbolo_moneda)
        )

        return template

    def _formatear_categorias(self, categorias: Dict, simbolo_moneda: str = "$") -> str:
        """Formatea las categorías para el prompt"""
        if not categorias:
            return "- No expenses registered yet"

        lineas = []
        for cat, monto in categorias.items():
            lineas.append(f"- {cat}: {simbolo_moneda}{monto:.2f}")
        return "\n".join(lineas)

    def _procesar_accion(self, user_id: str, resultado: Dict, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa la acción identificada por la IA"""
        accion = resultado.get("accion", "conversacion")

        if accion == "registrar_gasto":
            return self._procesar_gasto(user_id, resultado, idioma, moneda)

        elif accion == "registrar_ingreso":
            return self._procesar_ingreso(user_id, resultado, idioma, moneda)

        elif accion == "consultar_resumen":
            return self._procesar_consulta_resumen(user_id, idioma, moneda)

        elif accion == "analizar_categoria":
            return self._procesar_analisis_categoria(user_id, idioma, moneda)

        elif accion == "proyeccion":
            return self._procesar_proyeccion(user_id, idioma, moneda)

        elif accion == "configurar_presupuesto":
            return self._procesar_configurar_presupuesto(user_id, resultado, idioma, moneda)

        elif accion == "consejo_general":
            return self._procesar_consejo_general(user_id, idioma, moneda)

        elif accion == "explicar_termino":
            return self._procesar_explicar_termino(resultado, idioma, moneda)

        else:
            # Conversación general o consejo
            return resultado

    def _procesar_gasto(self, user_id: str, resultado: Dict, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa un registro de gasto"""
        try:
            monto = float(resultado.get("monto", 0))
        except (ValueError, TypeError):
            monto = 0

        categoria = resultado.get("categoria", "Other")
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        if monto <= 0:
            return {
                "accion": "error",
                "respuesta_texto": "I couldn't identify the amount. How much did you spend?",
                "respuesta_voz": "Friend, I couldn't identify the amount you spent. Could you tell me again please?"
            }

        print(f"💸 Registrando gasto: {simbolo_moneda}{monto:.2f} en {categoria}")

        # Analizar el gasto
        analisis = analizador.analizar_gasto(user_id, monto, categoria, moneda)

        # Guardar en la base de datos
        db.guardar_movimiento(user_id, monto, categoria, "gasto")
        print(f"✅ Gasto guardado en la base de datos")

        return {
            "accion": "registrar_gasto",
            "monto": monto,
            "categoria": categoria,
            "dinero_restante": analisis['dinero_restante'],
            "respuesta_texto": f"✓ {simbolo_moneda}{monto:.2f} on {categoria}. Remaining {simbolo_moneda}{analisis['dinero_restante']:.2f}",
            "respuesta_voz": analisis['consejo']
        }

    def _procesar_ingreso(self, user_id: str, resultado: Dict, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa un registro de ingreso"""
        try:
            monto = float(resultado.get("monto", 0))
        except (ValueError, TypeError):
            monto = 0

        simbolo_moneda = obtener_simbolo_moneda(moneda)

        if monto <= 0:
            return {
                "accion": "error",
                "respuesta_texto": "I couldn't identify the amount. How much did you receive?",
                "respuesta_voz": "Friend, I couldn't identify the amount you received. Could you tell me again?"
            }

        print(f"💵 Registrando ingreso: {simbolo_moneda}{monto:.2f}")

        # Analizar el ingreso
        analisis = analizador.analizar_ingreso(user_id, monto, moneda)

        # Guardar en la base de datos
        db.guardar_movimiento(user_id, monto, "Income", "ingreso")
        print(f"✅ Ingreso guardado en la base de datos")

        return {
            "accion": "registrar_ingreso",
            "monto": monto,
            "respuesta_texto": f"✓ Income of {simbolo_moneda}{monto:.2f} registered",
            "respuesta_voz": analisis['consejo']
        }

    def _procesar_consulta_resumen(self, user_id: str, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa una consulta de resumen"""
        resumen = db.obtener_resumen_mensual(user_id)
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        mensaje_texto = f"""💰 Monthly Summary:
Budget: {simbolo_moneda}{resumen['presupuesto_mensual']:.2f}
Spent: {simbolo_moneda}{resumen['total_gastado']:.2f}
Available: {simbolo_moneda}{resumen['dinero_restante']:.2f}"""

        mensaje_voz = f"""Here's your monthly summary friend.
Your budget is {simbolo_moneda}{resumen['presupuesto_mensual']:.2f}.
You've spent {simbolo_moneda}{resumen['total_gastado']:.2f}, which is {resumen['porcentaje_gastado']:.1f}%.
You have {simbolo_moneda}{resumen['dinero_restante']:.2f} available. """

        if resumen['porcentaje_gastado'] > 80:
            mensaje_voz += "Remember to watch your spending these days to finish the month well."
        else:
            mensaje_voz += "You're doing great, keep it up."

        return {
            "accion": "consultar_resumen",
            "respuesta_texto": mensaje_texto,
            "respuesta_voz": mensaje_voz
        }

    def _procesar_analisis_categoria(self, user_id: str, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa un análisis por categoría"""
        analisis = analizador.analizar_por_categoria(user_id, moneda)
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        return {
            "accion": "analizar_categoria",
            "respuesta_texto": analisis['mensaje'],
            "respuesta_voz": analisis['mensaje']
        }

    def _procesar_proyeccion(self, user_id: str, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa una proyección de fin de mes"""
        proyeccion = analizador.proyeccion_fin_de_mes(user_id, moneda)
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        return {
            "accion": "proyeccion",
            "respuesta_texto": f"Daily average: {simbolo_moneda}{proyeccion['gasto_diario_promedio']:.2f}",
            "respuesta_voz": proyeccion['mensaje']
        }

    def _procesar_configurar_presupuesto(self, user_id: str, resultado: Dict, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa la configuración de presupuesto"""
        try:
            monto = float(resultado.get("monto", 0))
        except (ValueError, TypeError):
            monto = 0

        simbolo_moneda = obtener_simbolo_moneda(moneda)

        print(f"📊 DEBUG - Configurando presupuesto:")
        print(f"   User ID: {user_id}")
        print(f"   Monto extraído por IA: {resultado.get('monto')}")
        print(f"   Monto convertido a float: {monto}")

        if monto <= 0:
            return {
                "accion": "error",
                "respuesta_texto": "What's your monthly budget?",
                "respuesta_voz": "What's your monthly budget friend?"
            }

        # Actualizar presupuesto en la base de datos
        db.actualizar_presupuesto(user_id, monto)
        print(f"✅ Presupuesto actualizado a {simbolo_moneda}{monto:.2f} para usuario {user_id}")

        # Obtener nuevo resumen
        resumen = db.obtener_resumen_mensual(user_id)

        return {
            "accion": "configurar_presupuesto",
            "monto": monto,
            "respuesta_texto": f"✓ Budget configured: {simbolo_moneda}{monto:.2f}/month",
            "respuesta_voz": obtener_traduccion(idioma, "presupuesto_establecido", moneda=simbolo_moneda, monto=monto)
        }

    def _procesar_consejo_general(self, user_id: str, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa una solicitud de consejo basada en gastos"""
        consejo = analizador.generar_consejo_gastos(user_id, moneda)

        return {
            "accion": "consejo_general",
            "respuesta_texto": consejo['consejo_texto'],
            "respuesta_voz": consejo['consejo_voz']
        }

    def _procesar_explicar_termino(self, resultado: Dict, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Procesa una solicitud de explicación de término financiero"""
        termino = resultado.get("termino", "")

        if not termino:
            return {
                "accion": "explicar_termino",
                "respuesta_texto": "Which financial term would you like to learn about? Ask me about: budget, income, savings, debt, interest, investment, emergency fund, etc.",
                "respuesta_voz": "Which financial term would you like me to explain? You can ask me about common terms like budget, income, or savings."
            }

        explicacion = analizador.explicar_termino_financiero(termino)

        # Si no encontró explicación predefinida, usar IA para generar una
        if not explicacion['encontrado']:
            return self._generar_explicacion_ia(termino, idioma, moneda)

        return {
            "accion": "explicar_termino",
            "termino": explicacion['termino'],
            "respuesta_texto": explicacion['explicacion_texto'],
            "respuesta_voz": explicacion['explicacion_voz']
        }

    def _generar_explicacion_ia(self, termino: str, idioma: str = "en", moneda: str = "USD") -> Dict:
        """Genera una explicación de término usando IA"""
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        # Prompt en el idioma del usuario
        prompts_ia = {
            "es": f"""Explica de forma simple y amigable el término financiero "{termino}" para una mujer sin experiencia bancaria.
La explicación debe:
1. Ser muy simple, usando palabras cotidianas
2. Incluir un ejemplo práctico
3. Ser en español
4. No usar términos bancarios complicados
5. Ser motivadora y positiva

Responde en formato:
EXPLICACIÓN: [explicación simple]
EJEMPLO: [ejemplo práctico]""",

            "en": f"""Explain the financial term "{termino}" in simple and friendly language for a woman with no banking experience.
The explanation must:
1. Be very simple, using everyday words
2. Include a practical example
3. Be in English
4. Not use complicated banking terms
5. Be motivating and positive

Respond in format:
EXPLANATION: [simple explanation]
EXAMPLE: [practical example]""",

            "pt": f"""Explique o termo financeiro "{termino}" de forma simples e amigável para uma mulher sem experiência bancária.
A explicação deve:
1. Ser muito simples, usando palavras do dia a dia
2. Incluir um exemplo prático
3. Ser em português
4. Não usar termos bancários complicados
5. Ser motivadora e positiva

Responda em formato:
EXPLICAÇÃO: [explicação simples]
EXEMPLO: [exemplo prático]""",

            "fr": f"""Expliquez le terme financier "{termino}" de manière simple et conviviale pour une femme sans expérience bancaire.
L'explication doit:
1. Être très simple, en utilisant des mots courants
2. Inclure un exemple pratique
3. Être en français
4. Ne pas utiliser de termes bancaires compliqués
5. Être motivant et positif

Répondez au format:
EXPLICATION: [explication simple]
EXEMPLE: [exemple pratique]"""
        }

        prompt = prompts_ia.get(idioma, prompts_ia["en"])

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful financial educator explaining terms to people with no banking experience. Be kind, simple, and encouraging."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            contenido = response.choices[0].message.content
            print(f"🤖 Explicación IA generada para '{termino}': {contenido[:100]}...")

            # Parsear la respuesta
            lineas = contenido.split("\n")
            explicacion_texto = ""
            ejemplo_texto = ""

            for linea in lineas:
                if "EXPLICACIÓN" in linea.upper() or "EXPLANATION" in linea.upper() or "EXPLICATION" in linea.upper():
                    explicacion_texto = linea.split(":", 1)[1].strip() if ":" in linea else linea
                elif "EJEMPLO" in linea.upper() or "EXAMPLE" in linea.upper():
                    ejemplo_texto = linea.split(":", 1)[1].strip() if ":" in linea else linea

            # Si no se parseó correctamente, usar todo como explicación
            if not explicacion_texto:
                explicacion_texto = contenido[:200]

            respuesta_texto = f"💡 {termino}:\n{explicacion_texto}"
            if ejemplo_texto:
                respuesta_texto += f"\n\n{ejemplo_texto}"

            respuesta_voz = f"{explicacion_texto} {ejemplo_texto}".strip()

            return {
                "accion": "explicar_termino",
                "termino": termino,
                "respuesta_texto": respuesta_texto,
                "respuesta_voz": respuesta_voz
            }

        except Exception as e:
            print(f"❌ Error al generar explicación con IA: {e}")
            return {
                "accion": "explicar_termino",
                "termino": termino,
                "respuesta_texto": f"I couldn't find a predefined explanation for '{termino}', but here's what I can tell you: This is a financial term that relates to money management. Would you like me to explain a different term or help with something else?",
                "respuesta_voz": f"I couldn't find a specific explanation for that term right now. Would you like to ask about other common financial terms like budget or savings?"
            }


# Instancia global del asistente
asistente = AsistenteFinanciero()
