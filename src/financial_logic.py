"""
Lógica financiera y análisis de presupuesto
"""
from typing import Dict, List, Tuple
from database import db
from localization import obtener_simbolo_moneda


class AnalizadorFinanciero:
    """Clase para analizar la situación financiera y generar consejos"""

    CATEGORIAS_PREDEFINIDAS = [
        "Food", "Transport", "Rent", "Services", "Education",
        "Health", "Clothing", "Entertainment", "Savings", "Other"
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

        # Simulate the new expense
        nuevo_gastado = resumen['total_gastado'] + monto

        # Calculate remaining considering budget + income - new total expenses
        total_disponible = resumen['presupuesto_mensual'] + resumen['total_ingresos']
        nuevo_restante = total_disponible - nuevo_gastado
        nuevo_porcentaje = (nuevo_gastado / total_disponible * 100) if total_disponible > 0 else 0

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

        consejo = f"""Great news! You received {simbolo_moneda}{monto:.2f}.

I suggest you separate your money like this:
    💚 {simbolo_moneda}{sugerencia_necesidades:.2f} for essentials (food, rent, services)
    💙 {simbolo_moneda}{sugerencia_deseos:.2f} for your personal expenses
    💛 {simbolo_moneda}{sugerencia_ahorro:.2f} for savings - it's your emergency fund!

    After this income, you'll have {simbolo_moneda}{resumen['dinero_restante'] + monto:.2f} available."""

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
                'mensaje': "You don't have any expenses registered this month yet. Start registering so I can help you better! 😊"
            }

        # Encontrar la categoría con más gasto
        categoria_mayor = max(categorias.items(), key=lambda x: x[1])
        porcentaje_mayor = (categoria_mayor[1] / resumen['total_gastado'] * 100) if resumen['total_gastado'] > 0 else 0

        # Calculate total available (budget + income)
        total_disponible = resumen['presupuesto_mensual'] + resumen['total_ingresos']

        # Construir mensaje de análisis
        analisis = f"""📊 Analysis of your monthly expenses:

💰 Total available: {simbolo_moneda}{total_disponible:.2f} (Budget: {simbolo_moneda}{resumen['presupuesto_mensual']:.2f} + Income: {simbolo_moneda}{resumen['total_ingresos']:.2f})
💸 You've spent: {simbolo_moneda}{resumen['total_gastado']:.2f}
📈 You have left: {simbolo_moneda}{resumen['dinero_restante']:.2f} ({100 - resumen['porcentaje_gastado']:.1f}%)

📌 Breakdown by categories:
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
        mensaje = f"Noted, you spent {simbolo_moneda}{monto:.2f} on {categoria}. "

        if nivel == "critico":
            mensaje += f"⚠️ Watch out! You've already spent {porcentaje:.1f}% of your budget. "
            mensaje += f"You only have {simbolo_moneda}{restante:.2f} left for the rest of the month. "
            mensaje += "It's time to be very careful with expenses. Can you review which purchases you can postpone?"

        elif nivel == "alto":
            mensaje += f"⚡ You've spent {porcentaje:.1f}%. You have {simbolo_moneda}{restante:.2f} left. "
            mensaje += "You're at a good pace, but try to watch small expenses these days."

        elif nivel == "medio":
            mensaje += f"You're doing well, {porcentaje:.1f}% of the budget spent. You have {simbolo_moneda}{restante:.2f} left. "
            mensaje += "Keep it up and you'll reach the end of the month smoothly. 😊"

        else:
            mensaje += f"Perfect! You have {simbolo_moneda}{restante:.2f} left ({100-porcentaje:.1f}% available). "
            mensaje += "You're managing your budget very well. Keep it up! 💪"

        return mensaje

    @staticmethod
    def _generar_consejo_categoria(categoria: str, monto: float, porcentaje: float, resumen: Dict, simbolo_moneda: str = "$") -> str:
        """Genera un consejo basado en la categoría con más gasto"""

        consejos_por_categoria = {
            "Food": f"I see {porcentaje:.1f}% goes to food ({simbolo_moneda}{monto:.2f}). Try buying more at the local market or look for deals on basic products. Cooking at home is always more economical than eating out.",

            "Transport": f"Transportation is taking {porcentaje:.1f}% ({simbolo_moneda}{monto:.2f}). Could you share rides with friends or use public transport instead of taxi when possible?",

            "Entertainment": f"I notice {porcentaje:.1f}% goes to entertainment ({simbolo_moneda}{monto:.2f}). It's good to enjoy, but this week try looking for free or more economical activities.",

            "Services": f"Services are taking {porcentaje:.1f}% ({simbolo_moneda}{monto:.2f}). Check if you can change plans or reduce some service you don't use that much.",

            "Clothing": f"Clothing has been {porcentaje:.1f}% of expenses ({simbolo_moneda}{monto:.2f}). Try looking at markets or second-hand stores. There are very good and economical options!",
        }

        consejo = consejos_por_categoria.get(
            categoria,
            f"The {categoria} category is where you spend the most ({porcentaje:.1f}%, {simbolo_moneda}{monto:.2f}). Try to find ways to reduce this expense a bit."
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

        # Compare against total available (budget + income)
        total_disponible = resumen['presupuesto_mensual'] + resumen['total_ingresos']
        deficit_proyectado = gasto_proyectado_mes - total_disponible

        # Gasto diario ideal para el resto del mes
        gasto_diario_ideal = resumen['dinero_restante'] / dias_restantes if dias_restantes > 0 else resumen['dinero_restante']

        if deficit_proyectado > 0:
            mensaje = f"""📉 Month projection:

We're on day {dia_actual} and you've spent {simbolo_moneda}{resumen['total_gastado']:.2f}.
Your daily average is {simbolo_moneda}{gasto_diario_promedio:.2f}.

⚠️ If you continue at this pace, you'll spend {simbolo_moneda}{gasto_proyectado_mes:.2f} this month.
That means you'd exceed your available money by {simbolo_moneda}{deficit_proyectado:.2f}.

💡 To finish the month well, you need to spend a maximum of {simbolo_moneda}{gasto_diario_ideal:.2f} per day for the remaining {dias_restantes} days.

Want to look together for ways to adjust your expenses?"""
        else:
            mensaje = f"""📊 Month projection:

You're doing great! We're on day {dia_actual} and you've spent {simbolo_moneda}{resumen['total_gastado']:.2f}.
Your daily average is {simbolo_moneda}{gasto_diario_promedio:.2f}.

✅ At this pace, you'll finish the month spending {simbolo_moneda}{gasto_proyectado_mes:.2f},
staying within your available money!

You can spend up to {simbolo_moneda}{gasto_diario_ideal:.2f} per day and you'll still be fine. Keep it up! 💪"""

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
