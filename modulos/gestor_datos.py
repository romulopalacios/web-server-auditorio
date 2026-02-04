"""
Capa de Persistencia - DatabaseManager
Arquitectura: Repository Pattern con manejo robusto de excepciones
"""
import sqlite3
import datetime
import os
import logging
from typing import Optional, List, Dict, Tuple

# Configuración de logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gestiona todas las operaciones de persistencia del sistema.
    Implementa patrón Repository para aislar la lógica de acceso a datos.
    """
    
    def __init__(self, db_path: str = "database/auditorio.db"):
        self.db_path = db_path
        self._verificar_carpeta()
        self._inicializar_tablas()
        logger.info(f"DatabaseManager inicializado: {db_path}")

    def _verificar_carpeta(self) -> None:
        """Crea la carpeta database si no existe"""
        carpeta = os.path.dirname(self.db_path)
        if carpeta and not os.path.exists(carpeta):
            os.makedirs(carpeta)
            logger.info(f"Carpeta creada: {carpeta}")

    def _inicializar_tablas(self) -> None:
        """
        Crea la estructura relacional completa si no existe.
        Incluye tabla de auditoría mejorada y tabla de estado del sistema.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de auditoría mejorada
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs_auditoria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                        nivel TEXT NOT NULL DEFAULT 'INFO',
                        usuario TEXT,
                        evento TEXT NOT NULL,
                        estado_previo TEXT,
                        estado_nuevo TEXT,
                        detalles TEXT,
                        origen_ip TEXT,
                        user_agent TEXT,
                        duracion_ms INTEGER
                    )
                ''')
                
                # Tabla de estado del sistema (reemplaza estado en RAM)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS estado_sistema (
                        clave TEXT PRIMARY KEY,
                        valor TEXT NOT NULL,
                        actualizado DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de usuarios con roles
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        rol TEXT NOT NULL DEFAULT 'operador',
                        nombre_completo TEXT,
                        email TEXT,
                        activo INTEGER DEFAULT 1,
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ultimo_acceso DATETIME
                    )
                ''')
                
                # Tabla de configuraciones del sistema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS configuraciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        clave TEXT UNIQUE NOT NULL,
                        valor TEXT NOT NULL,
                        tipo TEXT DEFAULT 'string',
                        descripcion TEXT,
                        categoria TEXT,
                        actualizado DATETIME DEFAULT CURRENT_TIMESTAMP,
                        actualizado_por TEXT
                    )
                ''')
                
                # Tabla de sesiones para auditoría avanzada
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sesiones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER NOT NULL,
                        fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                        fecha_fin DATETIME,
                        ip_origen TEXT,
                        user_agent TEXT,
                        activa INTEGER DEFAULT 1,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    )
                ''')
                
                # Inicializar estado por defecto si está vacío
                cursor.execute("SELECT COUNT(*) FROM estado_sistema")
                if cursor.fetchone()[0] == 0:
                    estado_inicial = [
                        ('modo_actual', 'STANDBY'),
                        ('carga_cpu', '5%'),
                        ('latencia', '0ms'),
                        ('sistema_activo', 'true')
                    ]
                    cursor.executemany(
                        "INSERT INTO estado_sistema (clave, valor) VALUES (?, ?)",
                        estado_inicial
                    )
                
                # Insertar usuarios por defecto si no existen
                cursor.execute("SELECT COUNT(*) FROM usuarios")
                if cursor.fetchone()[0] == 0:
                    from werkzeug.security import generate_password_hash
                    usuarios_default = [
                        ('admin', generate_password_hash('admin123'), 'admin', 'Administrador del Sistema', 'admin@universidad.edu'),
                        ('operador', generate_password_hash('oper123'), 'operador', 'Operador de Audio', 'operador@universidad.edu')
                    ]
                    cursor.executemany(
                        "INSERT INTO usuarios (username, password_hash, rol, nombre_completo, email) VALUES (?, ?, ?, ?, ?)",
                        usuarios_default
                    )
                
                # Insertar configuraciones por defecto
                cursor.execute("SELECT COUNT(*) FROM configuraciones")
                if cursor.fetchone()[0] == 0:
                    configs_default = [
                        ('max_volumen', '100', 'integer', 'Volumen máximo permitido', 'audio'),
                        ('timeout_sesion', '3600', 'integer', 'Tiempo de sesión en segundos', 'seguridad'),
                        ('modo_debug', 'false', 'boolean', 'Activar modo debug', 'sistema'),
                        ('backup_automatico', 'true', 'boolean', 'Realizar backup automático', 'sistema')
                    ]
                    cursor.executemany(
                        "INSERT INTO configuraciones (clave, valor, tipo, descripcion, categoria) VALUES (?, ?, ?, ?, ?)",
                        configs_default
                    )
                
                # Índices para optimización de consultas
                # Verificar si la columna usuario existe antes de crear índice
                cursor.execute("PRAGMA table_info(logs_auditoria)")
                columns = [col[1] for col in cursor.fetchall()]
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_logs_fecha 
                    ON logs_auditoria(fecha DESC)
                ''')
                
                if 'usuario' in columns:
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_logs_usuario 
                        ON logs_auditoria(usuario)
                    ''')
                
                # Índices adicionales para las nuevas tablas
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_usuarios_username 
                    ON usuarios(username)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sesiones_usuario 
                    ON sesiones(usuario_id, activa)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_configuraciones_categoria 
                    ON configuraciones(categoria)
                ''')
                
                conn.commit()
                logger.info("Estructura de base de datos inicializada correctamente")
                
        except sqlite3.Error as e:
            logger.error(f"Error al inicializar tablas: {e}")
            raise

    def registrar_evento(
        self,
        evento: str,
        detalles: str,
        ip: str,
        nivel: str = "INFO",
        usuario: Optional[str] = None,
        estado_previo: Optional[str] = None,
        estado_nuevo: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Inserta un log de auditoría con información completa.
        
        Args:
            evento: Tipo de evento (ej: CAMBIO_MODO, LOGIN, ERROR)
            detalles: Descripción detallada del evento
            ip: Dirección IP del cliente
            nivel: Nivel de log (INFO, WARNING, ERROR, CRITICAL)
            usuario: Usuario que ejecutó la acción
            estado_previo: Estado del sistema antes del cambio
            estado_nuevo: Estado del sistema después del cambio
            user_agent: User-Agent del navegador/cliente
            
        Returns:
            True si se registró correctamente, False en caso de error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cursor.execute('''
                    INSERT INTO logs_auditoria 
                    (fecha, nivel, usuario, evento, estado_previo, estado_nuevo, 
                     detalles, origen_ip, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (now, nivel, usuario, evento, estado_previo, estado_nuevo, 
                      detalles, ip, user_agent))
                
                conn.commit()
                logger.debug(f"Evento registrado: {evento} por {usuario or 'anónimo'}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error al registrar evento: {e}")
            return False

    def obtener_ultimos_logs(self, limite: int = 20) -> List[Tuple]:
        """
        Recupera el historial de eventos para el dashboard.
        
        Args:
            limite: Número máximo de registros a devolver
            
        Returns:
            Lista de tuplas con los logs ordenados por fecha descendente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, fecha, nivel, usuario, evento, detalles, origen_ip
                    FROM logs_auditoria 
                    ORDER BY id DESC 
                    LIMIT ?
                ''', (limite,))
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error al obtener logs: {e}")
            return []
    
    # ==================== MÉTODOS PARA ADMINISTRACIÓN ====================
    
    def obtener_todos_usuarios(self) -> List[Dict]:
        """Obtiene todos los usuarios del sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, rol, nombre_completo, email, activo, 
                           fecha_creacion, ultimo_acceso
                    FROM usuarios 
                    ORDER BY fecha_creacion DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener usuarios: {e}")
            return []
    
    def crear_usuario(self, username: str, password_hash: str, rol: str, 
                     nombre_completo: str = None, email: str = None) -> bool:
        """Crea un nuevo usuario"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO usuarios (username, password_hash, rol, nombre_completo, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, rol, nombre_completo, email))
                conn.commit()
                logger.info(f"Usuario creado: {username}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al crear usuario: {e}")
            return False
    
    def actualizar_usuario(self, user_id: int, datos: Dict) -> bool:
        """Actualiza datos de un usuario"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                campos = ', '.join([f"{k} = ?" for k in datos.keys()])
                valores = list(datos.values()) + [user_id]
                cursor.execute(f'''
                    UPDATE usuarios SET {campos} WHERE id = ?
                ''', valores)
                conn.commit()
                logger.info(f"Usuario actualizado: ID {user_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al actualizar usuario: {e}")
            return False
    
    def eliminar_usuario(self, user_id: int) -> bool:
        """Elimina (desactiva) un usuario"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = ?", (user_id,))
                conn.commit()
                logger.info(f"Usuario desactivado: ID {user_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al eliminar usuario: {e}")
            return False
    
    def buscar_logs(self, filtros: Dict, limite: int = 50) -> List[Dict]:
        """Busca logs con filtros avanzados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM logs_auditoria WHERE 1=1"
                params = []
                
                if filtros.get('usuario'):
                    query += " AND usuario LIKE ?"
                    params.append(f"%{filtros['usuario']}%")
                
                if filtros.get('nivel'):
                    query += " AND nivel = ?"
                    params.append(filtros['nivel'])
                
                if filtros.get('fecha_desde'):
                    query += " AND fecha >= ?"
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    query += " AND fecha <= ?"
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('evento'):
                    query += " AND evento LIKE ?"
                    params.append(f"%{filtros['evento']}%")
                
                query += f" ORDER BY id DESC LIMIT ?"
                params.append(limite)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al buscar logs: {e}")
            return []
    
    def eliminar_logs_antiguos(self, dias: int = 30) -> int:
        """Elimina logs más antiguos que X días"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                fecha_limite = datetime.datetime.now() - datetime.timedelta(days=dias)
                cursor.execute('''
                    DELETE FROM logs_auditoria 
                    WHERE fecha < ?
                ''', (fecha_limite.strftime('%Y-%m-%d %H:%M:%S'),))
                eliminados = cursor.rowcount
                conn.commit()
                logger.info(f"Logs eliminados: {eliminados}")
                return eliminados
        except sqlite3.Error as e:
            logger.error(f"Error al eliminar logs: {e}")
            return 0
    
    # ==================== MÉTODOS PARA ANALÍTICAS ====================
    
    def obtener_estadisticas_generales(self) -> Dict:
        """Obtiene estadísticas generales del sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de logs
                cursor.execute("SELECT COUNT(*) FROM logs_auditoria")
                total_logs = cursor.fetchone()[0]
                
                # Usuarios activos
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1")
                usuarios_activos = cursor.fetchone()[0]
                
                # Eventos por nivel
                cursor.execute('''
                    SELECT nivel, COUNT(*) as cantidad 
                    FROM logs_auditoria 
                    GROUP BY nivel
                ''')
                eventos_nivel = dict(cursor.fetchall())
                
                # Cambios de modo hoy
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM logs_auditoria 
                    WHERE evento = 'CAMBIO_MODO' 
                    AND DATE(fecha) = DATE('now')
                ''')
                cambios_hoy = cursor.fetchone()[0]
                
                return {
                    'total_logs': total_logs,
                    'usuarios_activos': usuarios_activos,
                    'eventos_nivel': eventos_nivel,
                    'cambios_hoy': cambios_hoy
                }
        except sqlite3.Error as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}
    
    def obtener_actividad_por_usuario(self, limite: int = 10) -> List[Dict]:
        """Obtiene usuarios más activos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT usuario, COUNT(*) as total_acciones,
                           MAX(fecha) as ultima_accion
                    FROM logs_auditoria 
                    WHERE usuario IS NOT NULL
                    GROUP BY usuario 
                    ORDER BY total_acciones DESC 
                    LIMIT ?
                ''', (limite,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener actividad por usuario: {e}")
            return []
    
    def obtener_eventos_por_dia(self, dias: int = 7) -> List[Dict]:
        """Obtiene eventos agrupados por día"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DATE(fecha) as dia, COUNT(*) as total_eventos,
                           SUM(CASE WHEN nivel = 'ERROR' THEN 1 ELSE 0 END) as errores,
                           SUM(CASE WHEN nivel = 'WARNING' THEN 1 ELSE 0 END) as warnings
                    FROM logs_auditoria 
                    WHERE fecha >= datetime('now', '-' || ? || ' days')
                    GROUP BY DATE(fecha) 
                    ORDER BY dia ASC
                ''', (dias,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener eventos por día: {e}")
            return []
    
    def obtener_cambios_modo_timeline(self, limite: int = 20) -> List[Dict]:
        """Obtiene historial de cambios de modo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fecha, usuario, estado_previo, estado_nuevo, detalles
                    FROM logs_auditoria 
                    WHERE evento = 'CAMBIO_MODO'
                    ORDER BY fecha DESC 
                    LIMIT ?
                ''', (limite,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener timeline de cambios: {e}")
            return []
    
    def obtener_uso_por_modo(self) -> List[Dict]:
        """Obtiene estadísticas de uso por modo del auditorio"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT estado_nuevo as modo, COUNT(*) as total_usos,
                           COUNT(DISTINCT usuario) as usuarios_distintos
                    FROM logs_auditoria 
                    WHERE evento = 'CAMBIO_MODO' AND estado_nuevo IS NOT NULL
                    GROUP BY estado_nuevo
                    ORDER BY total_usos DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener uso por modo: {e}")
            return []
    
    # ==================== CONFIGURACIONES ====================
    
    def obtener_configuraciones(self, categoria: str = None) -> List[Dict]:
        """Obtiene configuraciones del sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if categoria:
                    cursor.execute('''
                        SELECT * FROM configuraciones 
                        WHERE categoria = ? 
                        ORDER BY clave
                    ''', (categoria,))
                else:
                    cursor.execute('SELECT * FROM configuraciones ORDER BY categoria, clave')
                
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener configuraciones: {e}")
            return []
    
    def actualizar_configuracion(self, clave: str, valor: str, usuario: str = None) -> bool:
        """Actualiza una configuración"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE configuraciones 
                    SET valor = ?, actualizado = CURRENT_TIMESTAMP, actualizado_por = ?
                    WHERE clave = ?
                ''', (valor, usuario, clave))
                conn.commit()
                logger.info(f"Configuración actualizada: {clave} = {valor}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al actualizar configuración: {e}")
            return False


    def obtener_estado(self) -> Dict[str, str]:
        """
        Obtiene el estado actual del sistema desde la base de datos.
        Esta función reemplaza el diccionario global en RAM.
        
        Returns:
            Diccionario con el estado completo del sistema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT clave, valor FROM estado_sistema")
                return dict(cursor.fetchall())
                
        except sqlite3.Error as e:
            logger.error(f"Error al obtener estado: {e}")
            return {
                "modo_actual": "ERROR",
                "carga_cpu": "0%",
                "latencia": "0ms"
            }

    def actualizar_estado(self, estado: Dict[str, str]) -> bool:
        """
        Actualiza el estado del sistema en la base de datos.
        Thread-safe: múltiples workers pueden llamar esta función sin conflictos.
        
        Args:
            estado: Diccionario con los valores a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for clave, valor in estado.items():
                    cursor.execute('''
                        INSERT INTO estado_sistema (clave, valor, actualizado)
                        VALUES (?, ?, ?)
                        ON CONFLICT(clave) DO UPDATE SET 
                            valor = excluded.valor,
                            actualizado = excluded.actualizado
                    ''', (clave, valor, now))
                
                conn.commit()
                logger.debug(f"Estado actualizado: {list(estado.keys())}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error al actualizar estado: {e}")
            return False

    def obtener_estadisticas(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del sistema para reportes.
        
        Returns:
            Diccionario con métricas del sistema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de eventos
                cursor.execute("SELECT COUNT(*) FROM logs_auditoria")
                total_eventos = cursor.fetchone()[0]
                
                # Eventos por nivel
                cursor.execute('''
                    SELECT nivel, COUNT(*) 
                    FROM logs_auditoria 
                    GROUP BY nivel
                ''')
                eventos_por_nivel = dict(cursor.fetchall())
                
                return {
                    "total_eventos": total_eventos,
                    "eventos_por_nivel": eventos_por_nivel
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}