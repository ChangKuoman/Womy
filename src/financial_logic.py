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

    @staticmethod
    def generar_consejo_gastos(user_id: str, moneda: str = "USD") -> Dict:
        """
        Genera un consejo personalizado basado en los patrones de gasto actual

        Returns:
            Dict con el consejo personalizado basado en gastos
        """
        simbolo_moneda = obtener_simbolo_moneda(moneda)
        resumen = db.obtener_resumen_mensual(user_id)
        categorias = resumen['gastos_por_categoria']

        # Si no hay gastos, dar consejo genérico
        if not categorias or resumen['total_gastado'] == 0:
            consejo_texto = "You haven't registered any expenses yet. Once you start tracking them, I'll provide personalized advice! 📊"
            consejo_voz = "You haven't registered any expenses yet. Once you start tracking them, I'll provide personalized advice based on your spending patterns!"
            return {
                'consejo_texto': consejo_texto,
                'consejo_voz': consejo_voz
            }

        # Calcular total disponible (presupuesto + ingresos)
        total_disponible = resumen['presupuesto_mensual'] + resumen['total_ingresos']

        # Encontrar categoría con mayor gasto
        categoria_mayor = max(categorias.items(), key=lambda x: x[1])
        porcentaje_mayor = (categoria_mayor[1] / resumen['total_gastado'] * 100) if resumen['total_gastado'] > 0 else 0

        # Generar consejos específicos
        consejos_especificos = []

        # 1. Consejo sobre categoría con mayor gasto
        if porcentaje_mayor > 40:
            consejo_categoria = AnalizadorFinanciero._generar_consejo_categoria(
                categoria_mayor[0], categoria_mayor[1], porcentaje_mayor, resumen, simbolo_moneda
            )
            consejos_especificos.append(consejo_categoria)

        # 2. Consejo sobre presupuesto general
        if resumen['porcentaje_gastado'] > 80:
            consejos_especificos.append(f"⚠️ You're at {resumen['porcentaje_gastado']:.1f}% of your budget! Start being more careful to avoid running out of money before the month ends.")
        elif resumen['porcentaje_gastado'] > 60:
            consejos_especificos.append(f"📌 You've used {resumen['porcentaje_gastado']:.1f}% of your budget. You still have {simbolo_moneda}{resumen['dinero_restante']:.2f} left - use it wisely!")
        else:
            consejos_especificos.append(f"✨ Great! You're only at {resumen['porcentaje_gastado']:.1f}% of your budget. Keep managing well!")

        # 3. Buscar oportunidades de ahorro en categorías
        for categoria, monto in sorted(categorias.items(), key=lambda x: x[1], reverse=True)[1:3]:
            porcentaje = (monto / resumen['total_gastado'] * 100) if resumen['total_gastado'] > 0 else 0
            if porcentaje > 15:
                if categoria == "Food":
                    consejos_especificos.append(f"💰 You also spend {porcentaje:.1f}% on food. Consider meal planning to save money!")
                elif categoria == "Transport":
                    consejos_especificos.append(f"🚕 Another area to watch: {porcentaje:.1f}% on transport. Could you carpool more?")
                elif categoria == "Entertainment":
                    consejos_especificos.append(f"🎬 You spend {porcentaje:.1f}% on entertainment. Try free activities too!")

        # 4. Consejo sobre ingresos
        if resumen['total_ingresos'] > 0:
            ratio_gastos_ingresos = (resumen['total_gastado'] / resumen['total_ingresos'] * 100) if resumen['total_ingresos'] > 0 else 0
            if ratio_gastos_ingresos > 80:
                consejos_especificos.append(f"📊 Your expenses are {ratio_gastos_ingresos:.1f}% of your income. Look for ways to increase savings!")

        # 5. Consejo sobre dinero restante
        if resumen['dinero_restante'] > 0:
            consejo_ahorro = f"💡 You have {simbolo_moneda}{resumen['dinero_restante']:.2f} left this month. Why not save it for emergencies?"
            consejos_especificos.append(consejo_ahorro)

        # Construir respuesta
        consejo_texto = "\n\n".join(consejos_especificos[:3]) if consejos_especificos else "Keep tracking your spending!"

        consejo_voz = " ".join(consejos_especificos[:2]) if len(consejos_especificos) > 0 else "Keep tracking your spending and I'll give you better advice!"

        return {
            'consejo_texto': consejo_texto,
            'consejo_voz': consejo_voz,
            'num_consejos': len(consejos_especificos)
        }

    @staticmethod
    def explicar_termino_financiero(termino: str) -> Dict:
        """
        Explica un término financiero en lenguaje simple

        Args:
            termino: El término financiero a explicar

        Returns:
            Dict con la explicación del término
        """
        # Diccionario de términos financieros con explicaciones simples
        terminos = {
            "budget": {
                "explicacion": "A budget is a plan for your money. It shows how much money you have and how you'll use it. Think of it as a roadmap for your spending!",
                "ejemplo": "Example: You earn $1000 this month, so your budget might be $300 for food, $200 for rent, and $500 for other things."
            },
            "presupuesto": {
                "explicacion": "Un presupuesto es un plan para tu dinero. Muestra cuánto dinero tienes y cómo lo usarás. ¡Es como un mapa de ruta para tus gastos!",
                "ejemplo": "Ejemplo: Ganas $1000 este mes, así que tu presupuesto podría ser $300 para comida, $200 para alquiler, y $500 para otras cosas."
            },
            "income": {
                "explicacion": "Income is the money you earn or receive. It could be from a job, a business, or any source of money coming in.",
                "ejemplo": "Example: Your monthly salary, a bonus, or money from selling something."
            },
            "ingreso": {
                "explicacion": "Ingreso es el dinero que ganas o recibes. Puede ser de un trabajo, un negocio, o cualquier fuente de dinero que entra.",
                "ejemplo": "Ejemplo: Tu salario mensual, un bono, o dinero de vender algo."
            },
            "expense": {
                "explicacion": "An expense is money you spend. It's any money that goes out of your pocket for something you need or want.",
                "ejemplo": "Example: Buying food, paying rent, or getting new clothes."
            },
            "gasto": {
                "explicacion": "Gasto es dinero que gastas. Es cualquier dinero que sale de tu bolsillo para algo que necesitas o quieres.",
                "ejemplo": "Ejemplo: Comprar comida, pagar alquiler, o conseguir ropa nueva."
            },
            "savings": {
                "explicacion": "Savings is money you keep and don't spend. It's important to save money for emergencies or future goals!",
                "ejemplo": "Example: If you earn $100 and only spend $80, you saved $20."
            },
            "ahorro": {
                "explicacion": "Ahorro es dinero que guardas y no gastas. ¡Es importante ahorrar para emergencias o metas futuras!",
                "ejemplo": "Ejemplo: Si ganas $100 y solo gastas $80, ahorras $20."
            },
            "debt": {
                "explicacion": "Debt is money you owe to someone. If you borrow money and promise to pay it back, that's a debt.",
                "ejemplo": "Example: A loan from a bank or money borrowed from a friend."
            },
            "deuda": {
                "explicacion": "Deuda es dinero que debes a alguien. Si pides prestado dinero y prometes devolverlo, eso es una deuda.",
                "ejemplo": "Ejemplo: Un préstamo de un banco o dinero prestado de un amigo."
            },
            "interest": {
                "explicacion": "Interest is extra money you pay when you borrow money. It's the cost of borrowing.",
                "ejemplo": "Example: If you borrow $100 at 10% interest, you'll pay back $110."
            },
            "interes": {
                "explicacion": "Interés es dinero extra que pagas cuando pides prestado dinero. Es el costo de pedir prestado.",
                "ejemplo": "Ejemplo: Si pides prestado $100 al 10% de interés, pagarás $110."
            },
            "investment": {
                "explicacion": "An investment is when you use money to buy something that could grow in value or make more money for you.",
                "ejemplo": "Example: Buying stocks, a business, or real estate."
            },
            "inversion": {
                "explicacion": "Una inversión es cuando usas dinero para comprar algo que podría crecer en valor o hacerte más dinero.",
                "ejemplo": "Ejemplo: Comprar acciones, un negocio, o bienes raíces."
            },
            "emergency fund": {
                "explicacion": "An emergency fund is money you save for unexpected problems. It's your safety net!",
                "ejemplo": "Example: If your car breaks down or you lose your job, you have money saved."
            },
            "fondo de emergencia": {
                "explicacion": "Un fondo de emergencia es dinero que ahorras para problemas inesperados. ¡Es tu red de seguridad!",
                "ejemplo": "Ejemplo: Si tu auto se daña o pierdes tu trabajo, tienes dinero ahorrado."
            },
            "paycheck": {
                "explicacion": "A paycheck is the money you receive for working. It's your income from your job.",
                "ejemplo": "Example: Your monthly or weekly salary."
            },
            "pago": {
                "explicacion": "Un pago es el dinero que recibes por trabajar. Es tu ingreso de tu trabajo.",
                "ejemplo": "Ejemplo: Tu salario mensual o semanal."
            },
        }

        # Buscar el término (case-insensitive)
        termino_lower = termino.lower().strip()

        # Intentar encontrar coincidencia exacta
        if termino_lower in terminos:
            info = terminos[termino_lower]
            return {
                'termino': termino_lower,
                'encontrado': True,
                'explicacion_texto': f"💡 {termino}:\n{info['explicacion']}\n\n{info['ejemplo']}",
                'explicacion_voz': f"About {termino}: {info['explicacion']} {info['ejemplo']}"
            }

        # Intentar encontrar coincidencia parcial
        for clave in terminos.keys():
            if termino_lower in clave or clave in termino_lower:
                info = terminos[clave]
                return {
                    'termino': clave,
                    'encontrado': True,
                    'explicacion_texto': f"💡 {clave}:\n{info['explicacion']}\n\n{info['ejemplo']}",
                    'explicacion_voz': f"About {clave}: {info['explicacion']} {info['ejemplo']}"
                }

        # Si no encontró el término
        return {
            'termino': termino,
            'encontrado': False,
            'explicacion_texto': f"I don't have information about '{termino}' yet, but keep learning about money! 📚 Ask me about: budget, income, savings, debt, interest, emergency fund, etc.",
            'explicacion_voz': f"I don't have information about that term yet, but I can help explain common financial words. Try asking about budget, income, savings, debt, or emergency fund."
        }


# Instancia global del analizador
analizador = AnalizadorFinanciero()
