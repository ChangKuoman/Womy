"""
Gestión de la base de datos SQLite para el sistema financiero
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from config import settings


class Database:
    """Clase para manejar todas las operaciones de base de datos"""

    def __init__(self, db_path: str = None):
        """Inicializa la conexión a la base de datos"""
        self.db_path = db_path or settings.database_path
        self.inicializar_db()

    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
        return conn

    def inicializar_db(self):
        """Crea las tablas si no existen"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Tabla de usuarias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                whatsapp_id TEXT PRIMARY KEY,
                nombre TEXT,
                presupuesto_mensual REAL DEFAULT 1000.0,
                idioma TEXT DEFAULT 'en',
                moneda TEXT DEFAULT 'USD',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                onboarding_completo INTEGER DEFAULT 0
            )
        ''')

        # Agregar columnas si no existen (para usuarios existentes)
        try:
            cursor.execute('ALTER TABLE usuarios ADD COLUMN idioma TEXT DEFAULT "en"')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE usuarios ADD COLUMN moneda TEXT DEFAULT "USD"')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE usuarios ADD COLUMN onboarding_completo INTEGER DEFAULT 0')
        except:
            pass

        # Tabla de movimientos (gastos e ingresos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                whatsapp_id TEXT NOT NULL,
                monto REAL NOT NULL,
                categoria TEXT NOT NULL,
                tipo TEXT NOT NULL, -- 'ingreso' o 'gasto'
                descripcion TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(whatsapp_id) REFERENCES usuarios(whatsapp_id)
            )
        ''')

        # Tabla de metas de ahorro
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metas_ahorro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                whatsapp_id TEXT NOT NULL,
                nombre_meta TEXT NOT NULL,
                monto_objetivo REAL NOT NULL,
                monto_actual REAL DEFAULT 0.0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_objetivo TIMESTAMP,
                activa INTEGER DEFAULT 1,
                FOREIGN KEY(whatsapp_id) REFERENCES usuarios(whatsapp_id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")

    def registrar_usuario(self, whatsapp_id: str, nombre: str = None, presupuesto_mensual: float = 1000.0,
                         idioma: str = "en", moneda: str = "USD", onboarding_completo: int = 0):
        """Registra un nuevo usuario o actualiza si ya existe"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute('SELECT whatsapp_id FROM usuarios WHERE whatsapp_id = ?', (whatsapp_id,))
        exists = cursor.fetchone()

        if not exists:
            # Only insert if user doesn't exist - don't overwrite existing data
            cursor.execute('''
                INSERT INTO usuarios (whatsapp_id, nombre, presupuesto_mensual, idioma, moneda, onboarding_completo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (whatsapp_id, nombre, presupuesto_mensual, idioma, moneda, onboarding_completo))

        conn.commit()
        conn.close()

    def es_usuario_nuevo(self, whatsapp_id: str) -> bool:
        """Verifica si es un usuario nuevo"""
        usuario = self.obtener_usuario(whatsapp_id)
        if not usuario:
            return True
        return usuario.get('onboarding_completo', 0) == 0

    def actualizar_idioma_moneda(self, whatsapp_id: str, idioma: str, moneda: str):
        """Actualiza el idioma y moneda de un usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE usuarios
            SET idioma = ?, moneda = ?, onboarding_completo = 1
            WHERE whatsapp_id = ?
        ''', (idioma, moneda, whatsapp_id))

        conn.commit()
        conn.close()

    def obtener_usuario(self, whatsapp_id: str) -> Optional[Dict]:
        """Obtiene los datos de un usuario"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE whatsapp_id = ?', (whatsapp_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def actualizar_presupuesto(self, whatsapp_id: str, nuevo_presupuesto: float):
        """Actualiza el presupuesto mensual de una usuaria"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE usuarios
            SET presupuesto_mensual = ?
            WHERE whatsapp_id = ?
        ''', (nuevo_presupuesto, whatsapp_id))

        conn.commit()
        conn.close()

    def guardar_movimiento(self, whatsapp_id: str, monto: float, categoria: str,
                          tipo: str, descripcion: str = None):
        """Guarda un nuevo movimiento (gasto o ingreso)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO movimientos (whatsapp_id, monto, categoria, tipo, descripcion)
            VALUES (?, ?, ?, ?, ?)
        ''', (whatsapp_id, monto, categoria, tipo, descripcion))

        conn.commit()
        conn.close()

    def obtener_resumen_mensual(self, whatsapp_id: str) -> Dict:
        """Obtiene el resumen financiero del mes actual"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total gastado en el mes
        cursor.execute('''
            SELECT COALESCE(SUM(monto), 0) as total_gastado
            FROM movimientos
            WHERE whatsapp_id = ?
            AND tipo = 'gasto'
            AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
        ''', (whatsapp_id,))
        total_gastado = cursor.fetchone()['total_gastado']

        # Total de ingresos en el mes
        cursor.execute('''
            SELECT COALESCE(SUM(monto), 0) as total_ingresos
            FROM movimientos
            WHERE whatsapp_id = ?
            AND tipo = 'ingreso'
            AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
        ''', (whatsapp_id,))
        total_ingresos = cursor.fetchone()['total_ingresos']

        # Obtener presupuesto
        cursor.execute('SELECT presupuesto_mensual FROM usuarios WHERE whatsapp_id = ?', (whatsapp_id,))
        usuario = cursor.fetchone()
        presupuesto = usuario['presupuesto_mensual'] if usuario else 1000.0

        print(f"📊 DEBUG - obtener_resumen_mensual para {whatsapp_id}:")
        print(f"   Presupuesto en BD: {presupuesto}")
        print(f"   Total ingresos: {total_ingresos}")
        print(f"   Total gastado: {total_gastado}")

        # Gastos por categoría
        cursor.execute('''
            SELECT categoria, SUM(monto) as total
            FROM movimientos
            WHERE whatsapp_id = ?
            AND tipo = 'gasto'
            AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
            GROUP BY categoria
            ORDER BY total DESC
        ''', (whatsapp_id,))

        categorias = {}
        for row in cursor.fetchall():
            categorias[row['categoria']] = row['total']

        conn.close()

        # Calculate remaining money: budget + income - expenses
        restante = presupuesto + total_ingresos - total_gastado

        # Calculate percentage based on total available (budget + income)
        total_disponible = presupuesto + total_ingresos
        porcentaje_gastado = (total_gastado / total_disponible * 100) if total_disponible > 0 else 0

        return {
            'presupuesto_mensual': presupuesto,
            'total_gastado': total_gastado,
            'total_ingresos': total_ingresos,
            'dinero_restante': restante,
            'porcentaje_gastado': porcentaje_gastado,
            'gastos_por_categoria': categorias
        }

    def obtener_ultimos_movimientos(self, whatsapp_id: str, limite: int = 10) -> List[Dict]:
        """Obtiene los últimos movimientos de una usuaria"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM movimientos
            WHERE whatsapp_id = ?
            ORDER BY fecha DESC
            LIMIT ?
        ''', (whatsapp_id, limite))

        movimientos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return movimientos

    def crear_meta_ahorro(self, whatsapp_id: str, nombre_meta: str, monto_objetivo: float):
        """Crea una nueva meta de ahorro"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO metas_ahorro (whatsapp_id, nombre_meta, monto_objetivo)
            VALUES (?, ?, ?)
        ''', (whatsapp_id, nombre_meta, monto_objetivo))

        conn.commit()
        conn.close()

    def actualizar_meta_ahorro(self, meta_id: int, monto_ahorrado: float):
        """Actualiza el monto ahorrado en una meta"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE metas_ahorro
            SET monto_actual = monto_actual + ?
            WHERE id = ?
        ''', (monto_ahorrado, meta_id))

        conn.commit()
        conn.close()

    def obtener_metas_activas(self, whatsapp_id: str) -> List[Dict]:
        """Obtiene las metas de ahorro activas de una usuaria"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM metas_ahorro
            WHERE whatsapp_id = ? AND activa = 1
            ORDER BY fecha_creacion DESC
        ''', (whatsapp_id,))

        metas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return metas


# Instancia global de la base de datos
db = Database()
