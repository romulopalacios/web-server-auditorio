"""
Configuración Centralizada del Sistema
Arquitectura: Separación de Configuraciones por Entorno
"""
import os
from datetime import timedelta

class Config:
    """Configuración Base"""
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production-2026'
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Base de datos
    DATABASE_PATH = "database/auditorio.db"
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/sistema.log"
    
    # Credenciales de ejemplo
    USUARIOS_VALIDOS = {
        "admin": "admin123",  
        "operador": "oper456"
    }
    
    # Modos válidos del sistema
    MODOS_VALIDOS = ["CONFERENCIA", "CINE", "OFF", "STANDBY"]
    
    # Configuraciones de hardware simulado
    CONFIGURACIONES_MODOS = {
        "CONFERENCIA": {
            "modo_actual": "CONFERENCIA",
            "carga_cpu": "45%",
            "latencia": "12ms",
            "detalles": "Perfil Vocal Activado. Filtro HPF: ON. Compresor: 3:1 @ -20dB."
        },
        "CINE": {
            "modo_actual": "CINE 3D",
            "carga_cpu": "88%",
            "latencia": "24ms",
            "detalles": "Algoritmo Pseudo-3D Activado. Subwoofers: +6dB. Atmos Processing: ON."
        },
        "OFF": {
            "modo_actual": "OFF",
            "carga_cpu": "2%",
            "latencia": "0ms",
            "detalles": "Sistema Silenciado (MUTE ALL). Amplificadores en Standby."
        },
        "STANDBY": {
            "modo_actual": "STANDBY",
            "carga_cpu": "5%",
            "latencia": "0ms",
            "detalles": "Sistema en espera. Procesamiento mínimo activo."
        }
    }

class DevelopmentConfig(Config):
    """Configuración para Desarrollo"""
    DEBUG = True
    RATELIMIT_ENABLED = False  # Desactivar rate limiting en desarrollo

class ProductionConfig(Config):
    """Configuración para Producción"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Requiere HTTPS
    RATELIMIT_ENABLED = True

# Selección automática de configuración
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
