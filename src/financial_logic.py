"""
Lógica financiera y análisis de presupuesto
"""
from typing import Dict, List, Tuple
from database import db
from localization import obtener_simbolo_moneda


class AnalizadorFinanciero:
    """Clase para analizar la situación financiera y generar consejos"""

    CATEGORIAS_PREDEFINIDAS = [
        "Comida", "Transporte", "Renta", "Servicios", "Educación",
        "Salud", "Ropa", "Entretenimiento", "Ahorro", "Otro"
    ]

    @staticmethod
    def analizar_gasto(user_id: str, monto: float, categoria: str, moneda: str = "USD") -> Dict:
        """
        Analiza un gasto y genera un consejo personalizado

        Returns:
            Dict con el análisis y consejo generado
        """
        simbolo_moneda = obtener_simbolo_moneda(moneda)
        resumen = db.obtener_resumen_mensual(user_id)

        # Simular el nuevo gasto
        nuevo_gastado = resumen['total_gastado'] + monto
        nuevo_restante = resumen['presupuesto_mensual'] - nuevo_gastado
        nuevo_porcentaje = (nuevo_gastado / resumen['presupuesto_mensual'] * 100) if resumen['presupuesto_mensual'] > 0 else 0

        # Determinar el nivel de alerta
        nivel_alerta = AnalizadorFinanciero._determinar_nivel_alerta(nuevo_porcentaje, nuevo_restante)

        # Generar consejo
        consejo = AnalizadorFinanciero._generar_consejo_gasto(
            monto, categoria, nuevo_restante, nuevo_porcentaje, nivel_alerta, resumen, simbolo_moneda
        )

        return {
            'monto': monto,
            'categoria': categoria,
            'dinero_restante': nuevo_restante,
            'porcentaje_gastado': nuevo_porcentaje,
            'nivel_alerta': nivel_alerta,
            'consejo': consejo
        }

    @staticmethod
    def analizar_ingreso(user_id: str, monto: float, moneda: str = "USD") -> Dict:
        """
        Analiza un ingreso y sugiere distribución

        Returns:
            Dict con sugerencias de distribución del ingreso
        """
        simbolo_moneda = obtener_simbolo_moneda(moneda)
        resumen = db.obtener_resumen_mensual(user_id)

        # Regla 50/30/20 adaptada
        sugerencia_necesidades = monto * 0.50  # Gastos esenciales
        sugerencia_deseos = monto * 0.30  # Gastos personales
        sugerencia_ahorro = monto * 0.20  # Ahorro

        consejo = f"""¡Qué buenas noticias! Recibiste {simbolo_moneda}{monto:.2f}.

Te sugiero separar tu dinero así:
    💚 {simbolo_moneda}{sugerencia_necesidades:.2f} para lo esencial (comida, renta, servicios)
    💙 {simbolo_moneda}{sugerencia_deseos:.2f} para tus gastos personales
    💛 {simbolo_moneda}{sugerencia_ahorro:.2f} para tu ahorro - ¡es tu fondo de emergencia!

    Después de este ingreso, tendrás {simbolo_moneda}{resumen['dinero_restante'] + monto:.2f} disponible."""

        return {
            'monto': monto,
            'sugerencia_necesidades': sugerencia_necesidades,
            'sugerencia_deseos': sugerencia_deseos,
            'sugerencia_ahorro': sugerencia_ahorro,
            'nuevo_disponible': resumen['dinero_restante'] + monto,
            'consejo': consejo
        }

    @staticmethod
    def analizar_por_categoria(user_id: str, moneda: str = "USD") -> Dict:
        """
        Analiza los gastos por categoría y genera recomendaciones

        Returns:
            Dict con análisis detallado por categoría
        """
        simbolo_moneda = obtener_simbolo_moneda(moneda)
        resumen = db.obtener_resumen_mensual(user_id)
        categorias = resumen['gastos_por_categoria']

        if not categorias:
            return {
                'mensaje': "Aún no tienes gastos registrados este mes. ¡Empieza a registrar para que pueda ayudarte mejor! 😊"
            }

        # Encontrar la categoría con más gasto
        categoria_mayor = max(categorias.items(), key=lambda x: x[1])
        porcentaje_mayor = (categoria_mayor[1] / resumen['total_gastado'] * 100) if resumen['total_gastado'] > 0 else 0

        # Construir mensaje de análisis
        analisis = f"""📊 Análisis de tus gastos del mes:

💰 Has gastado {simbolo_moneda}{resumen['total_gastado']:.2f} de {simbolo_moneda}{resumen['presupuesto_mensual']:.2f}
📈 Te queda {simbolo_moneda}{resumen['dinero_restante']:.2f} ({100 - resumen['porcentaje_gastado']:.1f}%)

📌 Desglose por categorías:
"""

        for cat, monto in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (monto / resumen['total_gastado'] * 100) if resumen['total_gastado'] > 0 else 0
            analisis += f"\n• {cat}: {simbolo_moneda}{monto:.2f} ({porcentaje:.1f}%)"

        # Agregar consejo personalizado
        consejo = AnalizadorFinanciero._generar_consejo_categoria(
            categoria_mayor[0], categoria_mayor[1], porcentaje_mayor, resumen, simbolo_moneda
        )

        analisis += f"\n\n💡 {consejo}"

        return {
            'total_gastado': resumen['total_gastado'],
            'dinero_restante': resumen['dinero_restante'],
            'categorias': categorias,
            'categoria_mayor': categoria_mayor[0],
            'monto_mayor': categoria_mayor[1],
            'mensaje': analisis
        }

    @staticmethod
    def _determinar_nivel_alerta(porcentaje_gastado: float, dinero_restante: float) -> str:
        """Determina el nivel de alerta según el gasto"""
        if porcentaje_gastado >= 95:
            return "critico"
        elif porcentaje_gastado >= 80:
            return "alto"
        elif porcentaje_gastado >= 60:
            return "medio"
        else:
            return "normal"

    @staticmethod
    def _generar_consejo_gasto(monto: float, categoria: str, restante: float,
                               porcentaje: float, nivel: str, resumen: Dict, simbolo_moneda: str = "$") -> str:
        """Genera un consejo personalizado según el gasto"""

        # Mensaje base
        mensaje = f"Anotado, gastaste {simbolo_moneda}{monto:.2f} en {categoria}. "

        if nivel == "critico":
            mensaje += f"⚠️ ¡Ojo! Ya gastaste el {porcentaje:.1f}% de tu presupuesto. "
            mensaje += f"Solo te quedan {simbolo_moneda}{restante:.2f} para el resto del mes. "
            mensaje += "Es momento de ser muy cuidadosa con los gastos. ¿Puedes revisar qué compras puedes posponer?"

        elif nivel == "alto":
            mensaje += f"⚡ Llevas {porcentaje:.1f}% gastado. Te quedan {simbolo_moneda}{restante:.2f}. "
            mensaje += "Vas a buen ritmo, pero intenta cuidar los gastos hormiga estos días."

        elif nivel == "medio":
            mensaje += f"Vas bien, llevas {porcentaje:.1f}% del presupuesto. Te quedan {simbolo_moneda}{restante:.2f}. "
            mensaje += "Sigue así y llegarás tranquila a fin de mes. 😊"

        else:
            mensaje += f"¡Perfecto! Te quedan {simbolo_moneda}{restante:.2f} ({100-porcentaje:.1f}% disponible). "
            mensaje += "Vas muy bien con tu presupuesto. ¡Sigue así! 💪"

        return mensaje

    @staticmethod
    def _generar_consejo_categoria(categoria: str, monto: float, porcentaje: float, resumen: Dict, simbolo_moneda: str = "$") -> str:
        """Genera un consejo basado en la categoría con más gasto"""

        consejos_por_categoria = {
            "Comida": f"Veo que {porcentaje:.1f}% se va en comida ({simbolo_moneda}{monto:.2f}). Intenta comprar más en el mercado local o buscar ofertas en productos básicos. Cocinar en casa siempre sale más económico que comer fuera.",

            "Transporte": f"El transporte se está llevando {porcentaje:.1f}% ({simbolo_moneda}{monto:.2f}). ¿Podrías compartir viajes con amigas o usar transporte público en lugar de taxi cuando sea posible?",

            "Entretenimiento": f"Noto que {porcentaje:.1f}% se va en entretenimiento ({simbolo_moneda}{monto:.2f}). Está bien disfrutar, pero esta semana intenta buscar actividades gratuitas o más económicas.",

            "Servicios": f"Los servicios están tomando {porcentaje:.1f}% ({simbolo_moneda}{monto:.2f}). Revisa si puedes cambiar de plan o reducir algún servicio que no uses tanto.",

            "Ropa": f"La ropa ha sido {porcentaje:.1f}% del gasto ({simbolo_moneda}{monto:.2f}). Intenta buscar en mercados o tiendas de segunda mano. ¡Hay opciones muy buenas y económicas!",
        }

        consejo = consejos_por_categoria.get(
            categoria,
            f"La categoría {categoria} es donde más gastas ({porcentaje:.1f}%, {simbolo_moneda}{monto:.2f}). Intenta buscar formas de reducir un poco este gasto."
        )

        return consejo

    @staticmethod
    def proyeccion_fin_de_mes(user_id: str, moneda: str = "USD") -> Dict:
        """
        Proyecta cómo terminará el mes según el gasto actual

        Returns:
            Dict con la proyección y recomendaciones
        """
        import datetime

        simbolo_moneda = obtener_simbolo_moneda(moneda)
        resumen = db.obtener_resumen_mensual(user_id)

        # Calcular días del mes
        hoy = datetime.datetime.now()
        dias_en_mes = (datetime.date(hoy.year, hoy.month + 1, 1) - datetime.timedelta(days=1)).day
        dia_actual = hoy.day
        dias_restantes = dias_en_mes - dia_actual

        # Gasto diario promedio
        gasto_diario_promedio = resumen['total_gastado'] / dia_actual if dia_actual > 0 else 0

        # Proyección
        gasto_proyectado_mes = gasto_diario_promedio * dias_en_mes
        deficit_proyectado = gasto_proyectado_mes - resumen['presupuesto_mensual']

        # Gasto diario ideal para el resto del mes
        gasto_diario_ideal = resumen['dinero_restante'] / dias_restantes if dias_restantes > 0 else resumen['dinero_restante']

        if deficit_proyectado > 0:
            mensaje = f"""📉 Proyección del mes:

Llevamos {dia_actual} días y has gastado {simbolo_moneda}{resumen['total_gastado']:.2f}.
Tu promedio diario es {simbolo_moneda}{gasto_diario_promedio:.2f}.

⚠️ Si sigues a este ritmo, gastarás {simbolo_moneda}{gasto_proyectado_mes:.2f} este mes.
Eso significa que te excederías por {simbolo_moneda}{deficit_proyectado:.2f}.

💡 Para llegar bien a fin de mes, necesitas gastar máximo {simbolo_moneda}{gasto_diario_ideal:.2f} por día estos {dias_restantes} días restantes.

¿Quieres que busquemos juntas formas de ajustar tus gastos?"""
        else:
            mensaje = f"""📊 Proyección del mes:

¡Vas muy bien! Llevamos {dia_actual} días y has gastado {simbolo_moneda}{resumen['total_gastado']:.2f}.
Tu promedio diario es {simbolo_moneda}{gasto_diario_promedio:.2f}.

✅ A este ritmo, terminarás el mes gastando {simbolo_moneda}{gasto_proyectado_mes:.2f},
¡quedándote dentro de tu presupuesto!

Puedes gastar hasta {simbolo_moneda}{gasto_diario_ideal:.2f} por día y seguirás bien. ¡Sigue así! 💪"""

        return {
            'gasto_actual': resumen['total_gastado'],
            'dias_transcurridos': dia_actual,
            'dias_restantes': dias_restantes,
            'gasto_diario_promedio': gasto_diario_promedio,
            'gasto_proyectado_mes': gasto_proyectado_mes,
            'gasto_diario_ideal': gasto_diario_ideal,
            'tiene_deficit': deficit_proyectado > 0,
            'deficit_proyectado': deficit_proyectado if deficit_proyectado > 0 else 0,
            'mensaje': mensaje
        }


# Instancia global del analizador
analizador = AnalizadorFinanciero()
