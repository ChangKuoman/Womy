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
        idioma = usuario.get('idioma', 'es')
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
                "respuesta_texto": "Disculpa, tuve un problema al entender tu mensaje. ¿Podrías reformularlo?",
                "respuesta_voz": "Disculpa amiga, no entendí bien tu mensaje. ¿Podrías decírmelo de otra forma?"
            }
        except Exception as e:
            print(f"❌ Error al procesar mensaje: {e}")
            import traceback
            traceback.print_exc()
            return {
                "accion": "error",
                "respuesta_texto": "Disculpa, tuve un problema al procesar tu mensaje. ¿Podrías intentar de nuevo?",
                "respuesta_voz": "Disculpa amiga, tuve un problema al procesar tu mensaje. ¿Podrías intentar de nuevo?"
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

    def _crear_prompt_sistema(self, resumen: Dict, idioma: str = "es", moneda: str = "USD") -> str:
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
            return "- Aún no hay gastos registrados"

        lineas = []
        for cat, monto in categorias.items():
            lineas.append(f"- {cat}: {simbolo_moneda}{monto:.2f}")
        return "\n".join(lineas)

    def _procesar_accion(self, user_id: str, resultado: Dict, idioma: str = "es", moneda: str = "USD") -> Dict:
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

        else:
            # Conversación general o consejo
            return resultado

    def _procesar_gasto(self, user_id: str, resultado: Dict, idioma: str = "es", moneda: str = "USD") -> Dict:
        """Procesa un registro de gasto"""
        try:
            monto = float(resultado.get("monto", 0))
        except (ValueError, TypeError):
            monto = 0

        categoria = resultado.get("categoria", "Otro")
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        if monto <= 0:
            return {
                "accion": "error",
                "respuesta_texto": "No pude identificar el monto. ¿Cuánto gastaste?",
                "respuesta_voz": "Amiga, no pude identificar el monto que gastaste. ¿Me lo puedes decir de nuevo por favor?"
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
            "respuesta_texto": f"✓ {simbolo_moneda}{monto:.2f} en {categoria}. Quedan {simbolo_moneda}{analisis['dinero_restante']:.2f}",
            "respuesta_voz": analisis['consejo']
        }

    def _procesar_ingreso(self, user_id: str, resultado: Dict, idioma: str = "es", moneda: str = "USD") -> Dict:
        """Procesa un registro de ingreso"""
        try:
            monto = float(resultado.get("monto", 0))
        except (ValueError, TypeError):
            monto = 0

        simbolo_moneda = obtener_simbolo_moneda(moneda)

        if monto <= 0:
            return {
                "accion": "error",
                "respuesta_texto": "No pude identificar el monto. ¿Cuánto recibiste?",
                "respuesta_voz": "Amiga, no pude identificar el monto que recibiste. ¿Me lo puedes decir de nuevo?"
            }

        print(f"💵 Registrando ingreso: {simbolo_moneda}{monto:.2f}")

        # Analizar el ingreso
        analisis = analizador.analizar_ingreso(user_id, monto, moneda)

        # Guardar en la base de datos
        db.guardar_movimiento(user_id, monto, "Ingreso", "ingreso")
        print(f"✅ Ingreso guardado en la base de datos")

        return {
            "accion": "registrar_ingreso",
            "monto": monto,
            "respuesta_texto": f"✓ Ingreso de {simbolo_moneda}{monto:.2f} registrado",
            "respuesta_voz": analisis['consejo']
        }

    def _procesar_consulta_resumen(self, user_id: str, idioma: str = "es", moneda: str = "USD") -> Dict:
        """Procesa una consulta de resumen"""
        resumen = db.obtener_resumen_mensual(user_id)
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        mensaje_texto = f"""💰 Resumen del mes:
Presupuesto: {simbolo_moneda}{resumen['presupuesto_mensual']:.2f}
Gastado: {simbolo_moneda}{resumen['total_gastado']:.2f}
Disponible: {simbolo_moneda}{resumen['dinero_restante']:.2f}"""

        mensaje_voz = f"""Aquí está tu resumen del mes amiga.
Tu presupuesto es de {simbolo_moneda}{resumen['presupuesto_mensual']:.2f}.
Has gastado {simbolo_moneda}{resumen['total_gastado']:.2f}, que es el {resumen['porcentaje_gastado']:.1f}%.
Te quedan {simbolo_moneda}{resumen['dinero_restante']:.2f} disponibles. """

        if resumen['porcentaje_gastado'] > 80:
            mensaje_voz += "Recuerda cuidar los gastos estos días para llegar bien a fin de mes."
        else:
            mensaje_voz += "Vas muy bien, sigue así."

        return {
            "accion": "consultar_resumen",
            "respuesta_texto": mensaje_texto,
            "respuesta_voz": mensaje_voz
        }

    def _procesar_analisis_categoria(self, user_id: str, idioma: str = "es", moneda: str = "USD") -> Dict:
        """Procesa un análisis por categoría"""
        analisis = analizador.analizar_por_categoria(user_id, moneda)
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        return {
            "accion": "analizar_categoria",
            "respuesta_texto": analisis['mensaje'][:200] + "...",  # Versión corta
            "respuesta_voz": analisis['mensaje']
        }

    def _procesar_proyeccion(self, user_id: str, idioma: str = "es", moneda: str = "USD") -> Dict:
        """Procesa una proyección de fin de mes"""
        proyeccion = analizador.proyeccion_fin_de_mes(user_id, moneda)
        simbolo_moneda = obtener_simbolo_moneda(moneda)

        return {
            "accion": "proyeccion",
            "respuesta_texto": f"Promedio diario: {simbolo_moneda}{proyeccion['gasto_diario_promedio']:.2f}",
            "respuesta_voz": proyeccion['mensaje']
        }

    def _procesar_configurar_presupuesto(self, user_id: str, resultado: Dict, idioma: str = "es", moneda: str = "USD") -> Dict:
        """Procesa la configuración de presupuesto"""
        try:
            monto = float(resultado.get("monto", 0))
        except (ValueError, TypeError):
            monto = 0

        simbolo_moneda = obtener_simbolo_moneda(moneda)

        if monto <= 0:
            return {
                "accion": "error",
                "respuesta_texto": "¿Cuál es tu presupuesto mensual?",
                "respuesta_voz": "¿Cuál es tu presupuesto mensual amiga?"
            }

        # Actualizar presupuesto en la base de datos
        db.actualizar_presupuesto(user_id, monto)
        print(f"✅ Presupuesto actualizado a {simbolo_moneda}{monto:.2f} para usuario {user_id}")

        # Obtener nuevo resumen
        resumen = db.obtener_resumen_mensual(user_id)

        return {
            "accion": "configurar_presupuesto",
            "monto": monto,
            "respuesta_texto": f"✓ Presupuesto configurado: {simbolo_moneda}{monto:.2f}/mes",
            "respuesta_voz": obtener_traduccion(idioma, "presupuesto_establecido", moneda=simbolo_moneda, monto=monto)
        }


# Instancia global del asistente
asistente = AsistenteFinanciero()
