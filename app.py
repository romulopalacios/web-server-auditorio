"""
Sistema de Control de Auditorio - Arquitectura Empresarial
Autor: Ingeniería TI
Versión: 2.0 Professional Edition
Arquitectura: MVC + Repository Pattern + Security Layer
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

# Importaciones locales
from modulos.gestor_datos import DatabaseManager
from config import config

# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================

app = Flask(__name__)

# Cargar configuración según entorno
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Configuración de logging profesional
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/sistema.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# INYECCIÓN DE DEPENDENCIAS
# ============================================================================

db = DatabaseManager(app.config['DATABASE_PATH'])

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================================================

# Flask-Login para autenticación
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicie sesión para acceder al sistema.'

# Rate Limiter para prevenir ataques
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=app.config['RATELIMIT_STORAGE_URL'],
    default_limits=app.config['RATELIMIT_DEFAULT'].split(';') if app.config['RATELIMIT_ENABLED'] else []
)

# ============================================================================
# MODELO DE USUARIO
# ============================================================================

class Usuario(UserMixin):
    """Modelo de usuario para Flask-Login"""
    def __init__(self, username: str):
        self.id = username
        self.username = username

@login_manager.user_loader
def cargar_usuario(username: str) -> Optional[Usuario]:
    """Callback requerido por Flask-Login"""
    if username in app.config['USUARIOS_VALIDOS']:
        return Usuario(username)
    return None

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def obtener_ip_real() -> str:
    """
    Obtiene la IP real del cliente, incluso detrás de proxies.
    Maneja headers X-Forwarded-For de manera segura.
    """
    if request.headers.get('X-Forwarded-For'):
        # Toma la primera IP (la del cliente original)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or "0.0.0.0"

def validar_modo(modo: str) -> bool:
    """Valida que el modo solicitado sea válido"""
    return modo.upper() in app.config['MODOS_VALIDOS']

def registrar_accion(
    evento: str,
    detalles: str,
    nivel: str = "INFO",
    estado_previo: Optional[str] = None,
    estado_nuevo: Optional[str] = None
) -> None:
    """
    Wrapper para registrar eventos con contexto completo.
    Captura automáticamente IP, usuario y user-agent.
    """
    usuario = current_user.username if current_user.is_authenticated else "anónimo"
    ip = obtener_ip_real()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    db.registrar_evento(
        evento=evento,
        detalles=detalles,
        ip=ip,
        nivel=nivel,
        usuario=usuario,
        estado_previo=estado_previo,
        estado_nuevo=estado_nuevo,
        user_agent=user_agent
    )

# ============================================================================
# DECORADORES PERSONALIZADOS
# ============================================================================

def requiere_confirmacion(f):
    """
    Decorador para endpoints que requieren confirmación explícita.
    Útil para acciones críticas como apagar el sistema.
    """
    @wraps(f)
    def decorador(*args, **kwargs):
        confirmado = request.json.get('confirmado', False) if request.json else False
        if not confirmado and request.json.get('modo') == 'OFF':
            return jsonify({
                "status": "confirmation_required",
                "msg": "Esta acción requiere confirmación explícita.",
                "codigo": "CONFIRM_SHUTDOWN"
            }), 403
        return f(*args, **kwargs)
    return decorador

# ============================================================================
# RUTAS DE AUTENTICACIÓN
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Endpoint de autenticación con rate limiting"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validación de entrada
        if not username or not password:
            registrar_accion("LOGIN_FALLIDO", "Credenciales incompletas", nivel="WARNING")
            return jsonify({"error": "Usuario y contraseña requeridos"}), 400
        
        # Verificación de credenciales
        if username in app.config['USUARIOS_VALIDOS']:
            if app.config['USUARIOS_VALIDOS'][username] == password:
                user = Usuario(username)
                login_user(user)
                session.permanent = True
                
                registrar_accion("LOGIN_EXITOSO", f"Usuario {username} autenticado correctamente")
                logger.info(f"Login exitoso: {username} desde {obtener_ip_real()}")
                
                return jsonify({
                    "status": "success",
                    "msg": f"Bienvenido, {username}",
                    "redirect": url_for('index')
                })
        
        # Credenciales inválidas
        registrar_accion("LOGIN_FALLIDO", f"Intento fallido para usuario: {username}", nivel="WARNING")
        return jsonify({"error": "Credenciales inválidas"}), 401
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/logout')
@login_required
def logout():
    """Cierre de sesión"""
    username = current_user.username
    registrar_accion("LOGOUT", f"Usuario {username} cerró sesión")
    logout_user()
    return redirect(url_for('login'))

# ============================================================================
# RUTAS DE VISTA (Frontend)
# ============================================================================

@app.route('/')
@login_required
def index():
    """Dashboard principal - requiere autenticación"""
    return render_template('dashboard.html', usuario=current_user.username)

# ============================================================================
# API ENDPOINTS (Backend Logic)
# ============================================================================

@app.route('/api/cambiar_modo', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
@requiere_confirmacion
def cambiar_modo():
    """
    Endpoint para cambiar el modo de operación del sistema.
    Implementa validación completa, manejo de errores y auditoría.
    """
    inicio = datetime.now()
    
    try:
        # 1. Validación de entrada
        data = request.get_json()
        if not data or 'modo' not in data:
            return jsonify({
                "status": "error",
                "msg": "Falta el parámetro 'modo' en la solicitud"
            }), 400
        
        nuevo_modo = data['modo'].upper()
        
        # 2. Validar modo
        if not validar_modo(nuevo_modo):
            modos_validos = ', '.join(app.config['MODOS_VALIDOS'])
            return jsonify({
                "status": "error",
                "msg": f"Modo inválido. Modos válidos: {modos_validos}"
            }), 400
        
        # 3. Obtener estado actual
        estado_actual = db.obtener_estado()
        modo_previo = estado_actual.get('modo_actual', 'UNKNOWN')
        
        # 4. Verificar si ya está en ese modo
        if modo_previo == app.config['CONFIGURACIONES_MODOS'][nuevo_modo]['modo_actual']:
            return jsonify({
                "status": "info",
                "msg": f"El sistema ya está en modo {nuevo_modo}",
                "estado": estado_actual
            })
        
        # 5. Aplicar nueva configuración
        nueva_config = app.config['CONFIGURACIONES_MODOS'][nuevo_modo].copy()
        detalles = nueva_config.pop('detalles')
        
        # 6. Actualizar estado en BD (thread-safe)

        # 6. Actualizar estado en BD (thread-safe)
        if not db.actualizar_estado(nueva_config):
            raise Exception("Error al actualizar estado en base de datos")
        
        # 7. Registrar en auditoría
        duracion = (datetime.now() - inicio).total_seconds() * 1000
        registrar_accion(
            evento="CAMBIO_MODO",
            detalles=f"{detalles} (Procesado en {duracion:.2f}ms)",
            estado_previo=modo_previo,
            estado_nuevo=nueva_config['modo_actual']
        )
        
        logger.info(f"Modo cambiado: {modo_previo} → {nueva_config['modo_actual']} por {current_user.username}")
        
        # 8. Respuesta exitosa
        return jsonify({
            "status": "success",
            "estado": nueva_config,
            "msg": detalles,
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        logger.warning(f"Validación fallida en cambiar_modo: {str(e)}")
        return jsonify({"status": "error", "msg": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Error crítico en cambiar_modo: {str(e)}", exc_info=True)
        registrar_accion("ERROR_SISTEMA", f"Fallo al cambiar modo: {str(e)}", nivel="ERROR")
        return jsonify({
            "status": "error",
            "msg": "Error interno del servidor. Contacte al administrador."
        }), 500

@app.route('/api/estado', methods=['GET'])
@login_required
def obtener_estado_actual():
    """Obtiene el estado actual del sistema desde la BD"""
    try:
        estado = db.obtener_estado()
        return jsonify({
            "status": "success",
            "estado": estado,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error al obtener estado: {str(e)}")
        return jsonify({"status": "error", "msg": "Error al obtener estado"}), 500

@app.route('/api/historial', methods=['GET'])
@login_required
def obtener_historial():
    """
    Recupera el historial de eventos con paginación opcional.
    Serealiza los datos para evitar problemas de encoding.
    """
    try:
        limite = request.args.get('limite', default=20, type=int)
        
        # Limitar el máximo de registros por seguridad
        if limite > 100:
            limite = 100
        
        logs = db.obtener_ultimos_logs(limite)
        
        # Serialización robusta
        datos_limpios = [
            {
                "id": row[0],
                "fecha": row[1],
                "nivel": row[2],
                "usuario": row[3] or "Sistema",
                "evento": row[4],
                "detalle": row[5] or "",
                "ip": row[6]
            }
            for row in logs
        ]
        
        return jsonify({
            "status": "success",
            "logs": datos_limpios,
            "total": len(datos_limpios)
        })
        
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        return jsonify({
            "status": "error",
            "msg": "Error al recuperar historial"
        }), 500

# ============================================================================
# MANEJO DE ERRORES GLOBAL
# ============================================================================

@app.errorhandler(404)
def no_encontrado(e):
    """Maneja errores 404"""
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(401)
def no_autorizado(e):
    """Maneja errores 401"""
    return jsonify({"error": "No autorizado. Inicie sesión."}), 401

@app.errorhandler(429)
def limite_excedido(e):
    """Maneja rate limiting"""
    return jsonify({
        "error": "Demasiadas solicitudes. Intente nuevamente más tarde.",
        "retry_after": e.description
    }), 429

@app.errorhandler(500)
def error_interno(e):
    """Maneja errores 500"""
    logger.error(f"Error 500: {str(e)}", exc_info=True)
    return jsonify({"error": "Error interno del servidor"}), 500

# ============================================================================
# RUTAS DE ADMINISTRACIÓN Y ANALÍTICAS
# ============================================================================

@app.route('/admin')
@login_required
def admin_panel():
    """Panel de administración (solo para admin)"""
    if current_user.username != 'admin':
        return redirect(url_for('index'))
    return render_template('admin.html', usuario=current_user.username)

# ---------- CRUD de Usuarios ----------

@app.route('/api/admin/usuarios', methods=['GET'])
@login_required
def obtener_usuarios():
    """Obtiene lista de todos los usuarios"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        usuarios = db.obtener_todos_usuarios()
        return jsonify({"status": "success", "usuarios": usuarios})
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/usuarios', methods=['POST'])
@login_required
def crear_usuario():
    """Crea un nuevo usuario"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        datos = request.get_json()
        username = datos.get('username')
        password = datos.get('password')
        rol = datos.get('rol', 'operador')
        nombre_completo = datos.get('nombre_completo')
        email = datos.get('email')
        
        if not username or not password:
            return jsonify({"error": "Username y password requeridos"}), 400
        
        password_hash = generate_password_hash(password)
        
        if db.crear_usuario(username, password_hash, rol, nombre_completo, email):
            registrar_accion(
                evento="Usuario creado",
                detalles=f"Nuevo usuario: {username} ({rol})",
                nivel="INFO"
            )
            return jsonify({"status": "success", "msg": "Usuario creado correctamente"})
        else:
            return jsonify({"error": "Error al crear usuario"}), 500
            
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/usuarios/<int:user_id>', methods=['PUT'])
@login_required
def actualizar_usuario(user_id):
    """Actualiza datos de un usuario"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        datos = request.get_json()
        
        # Filtrar campos permitidos
        campos_permitidos = ['nombre_completo', 'email', 'rol', 'activo']
        datos_filtrados = {k: v for k, v in datos.items() if k in campos_permitidos}
        
        if db.actualizar_usuario(user_id, datos_filtrados):
            registrar_accion(
                evento="Usuario actualizado",
                detalles=f"ID: {user_id} - Campos: {', '.join(datos_filtrados.keys())}",
                nivel="INFO"
            )
            return jsonify({"status": "success", "msg": "Usuario actualizado"})
        else:
            return jsonify({"error": "Error al actualizar usuario"}), 500
            
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/usuarios/<int:user_id>', methods=['DELETE'])
@login_required
def eliminar_usuario(user_id):
    """Elimina (desactiva) un usuario"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        if db.eliminar_usuario(user_id):
            registrar_accion(
                evento="Usuario eliminado",
                detalles=f"Usuario desactivado ID: {user_id}",
                nivel="WARNING"
            )
            return jsonify({"status": "success", "msg": "Usuario desactivado"})
        else:
            return jsonify({"error": "Error al eliminar usuario"}), 500
            
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- Búsqueda y Gestión de Logs ----------

@app.route('/api/admin/logs/buscar', methods=['POST'])
@login_required
def buscar_logs():
    """Busca logs con filtros avanzados"""
    try:
        filtros = request.get_json()
        limite = filtros.pop('limite', 50)
        
        logs = db.buscar_logs(filtros, limite)
        return jsonify({"status": "success", "logs": logs, "total": len(logs)})
        
    except Exception as e:
        logger.error(f"Error al buscar logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/logs/limpiar', methods=['POST'])
@login_required
def limpiar_logs():
    """Elimina logs antiguos"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        datos = request.get_json()
        dias = datos.get('dias', 30)
        
        eliminados = db.eliminar_logs_antiguos(dias)
        
        registrar_accion(
            evento="Limpieza de logs",
            detalles=f"Eliminados {eliminados} registros anteriores a {dias} días",
            nivel="INFO"
        )
        
        return jsonify({
            "status": "success",
            "msg": f"Se eliminaron {eliminados} registros",
            "eliminados": eliminados
        })
        
    except Exception as e:
        logger.error(f"Error al limpiar logs: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- Analíticas y Estadísticas ----------

@app.route('/api/admin/estadisticas', methods=['GET'])
@login_required
def obtener_estadisticas():
    """Obtiene estadísticas generales del sistema"""
    try:
        stats = db.obtener_estadisticas_generales()
        return jsonify({"status": "success", "estadisticas": stats})
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/analiticas/usuarios', methods=['GET'])
@login_required
def analitica_usuarios():
    """Obtiene actividad por usuario"""
    try:
        limite = request.args.get('limite', default=10, type=int)
        actividad = db.obtener_actividad_por_usuario(limite)
        return jsonify({"status": "success", "actividad": actividad})
        
    except Exception as e:
        logger.error(f"Error en analítica de usuarios: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/analiticas/eventos-diarios', methods=['GET'])
@login_required
def eventos_diarios():
    """Obtiene eventos agrupados por día"""
    try:
        dias = request.args.get('dias', default=7, type=int)
        eventos = db.obtener_eventos_por_dia(dias)
        return jsonify({"status": "success", "eventos": eventos})
        
    except Exception as e:
        logger.error(f"Error en eventos diarios: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/analiticas/timeline-modos', methods=['GET'])
@login_required
def timeline_modos():
    """Obtiene timeline de cambios de modo"""
    try:
        limite = request.args.get('limite', default=20, type=int)
        timeline = db.obtener_cambios_modo_timeline(limite)
        return jsonify({"status": "success", "timeline": timeline})
        
    except Exception as e:
        logger.error(f"Error en timeline: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- Configuraciones ----------

@app.route('/api/admin/configuraciones', methods=['GET'])
@login_required
def obtener_configuraciones():
    """Obtiene configuraciones del sistema"""
    try:
        categoria = request.args.get('categoria')
        configs = db.obtener_configuraciones(categoria)
        return jsonify({"status": "success", "configuraciones": configs})
        
    except Exception as e:
        logger.error(f"Error al obtener configuraciones: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/configuraciones/<clave>', methods=['PUT'])
@login_required
def actualizar_configuracion(clave):
    """Actualiza una configuración"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        datos = request.get_json()
        valor = datos.get('valor')
        
        if db.actualizar_configuracion(clave, valor, current_user.username):
            registrar_accion(
                evento="Configuración actualizada",
                detalles=f"{clave} = {valor}",
                nivel="INFO"
            )
            return jsonify({"status": "success", "msg": "Configuración actualizada"})
        else:
            return jsonify({"error": "Error al actualizar configuración"}), 500
            
    except Exception as e:
        logger.error(f"Error al actualizar configuración: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- Exportación de Datos ----------

@app.route('/api/admin/exportar/logs', methods=['GET'])
@login_required
def exportar_logs():
    """Exporta logs a CSV"""
    try:
        import csv
        from io import StringIO
        
        limite = request.args.get('limite', default=1000, type=int)
        logs = db.obtener_ultimos_logs(limite)
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Fecha', 'Nivel', 'Usuario', 'Evento', 'Detalles', 'IP'])
        
        for log in logs:
            writer.writerow(log)
        
        registrar_accion(
            evento="Exportación de datos",
            detalles=f"Exportados {len(logs)} registros a CSV",
            nivel="INFO"
        )
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
        
    except Exception as e:
        logger.error(f"Error al exportar logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/analiticas/uso-por-modo', methods=['GET'])
@login_required
def obtener_uso_por_modo():
    """Obtiene estadísticas de uso por modo del auditorio"""
    if current_user.username != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    
    try:
        datos = db.obtener_uso_por_modo()
        return jsonify({
            "status": "success",
            "modos": datos
        })
    except Exception as e:
        logger.error(f"Error al obtener uso por modo: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎯 SISTEMA DE AUDIO DISTRIBUIDO - VERSIÓN PROFESIONAL 2.0")
    print("="*70)
    print(f"📦 Entorno: {env.upper()}")
    print(f"🔒 Autenticación: ACTIVADA (Flask-Login)")
    print(f"🛡️  Rate Limiting: {'ACTIVADO' if app.config['RATELIMIT_ENABLED'] else 'DESACTIVADO'}")
    print(f"📊 Base de Datos: {app.config['DATABASE_PATH']}")
    print(f"📝 Logs: logs/sistema.log")
    print("="*70)
    print(f"🌐 Servidor iniciando en http://localhost:5000")
    print(f"👤 Usuarios disponibles: {', '.join(app.config['USUARIOS_VALIDOS'].keys())}")
    print("="*70 + "\n")
    
    # Registrar inicio del sistema
    logger.info("Sistema iniciado correctamente")
    
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',  # Accesible desde la red local
        port=5000
    )
