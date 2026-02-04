"""
Tests Unitarios para el Sistema de Control de Auditorio
Cobertura: Autenticación, Endpoints, Base de Datos
Ejecutar con: pytest test_sistema.py -v
"""

import pytest
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from modulos.gestor_datos import DatabaseManager
import tempfile

@pytest.fixture
def client():
    """Crea un cliente de prueba para la aplicación"""
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = ':memory:'  # BD en memoria para tests
    app.config['RATELIMIT_ENABLED'] = False  # Desactivar rate limiting en tests
    
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_client(client):
    """Cliente autenticado para pruebas"""
    with client.session_transaction() as session:
        session['_user_id'] = 'admin'
    return client

# ============================================================================
# TESTS DE AUTENTICACIÓN
# ============================================================================

def test_login_exitoso(client):
    """Test: Login con credenciales válidas"""
    response = client.post('/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'admin' in data['msg']

def test_login_credenciales_invalidas(client):
    """Test: Login con credenciales incorrectas"""
    response = client.post('/login',
        json={'username': 'admin', 'password': 'incorrecta'},
        content_type='application/json'
    )
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data

def test_login_sin_datos(client):
    """Test: Login sin enviar datos"""
    response = client.post('/login',
        json={},
        content_type='application/json'
    )
    assert response.status_code == 400

def test_acceso_sin_autenticacion(client):
    """Test: Intentar acceder al dashboard sin login"""
    response = client.get('/')
    assert response.status_code == 302  # Redirección al login

# ============================================================================
# TESTS DE API - CAMBIO DE MODO
# ============================================================================

def test_cambiar_modo_conferencia(authenticated_client):
    """Test: Cambiar a modo CONFERENCIA"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={'modo': 'CONFERENCIA'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['estado']['modo_actual'] == 'CONFERENCIA'

def test_cambiar_modo_cine(authenticated_client):
    """Test: Cambiar a modo CINE"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={'modo': 'CINE'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['estado']['modo_actual'] == 'CINE 3D'

def test_cambiar_modo_apagado_sin_confirmacion(authenticated_client):
    """Test: Intentar apagar sin confirmación"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={'modo': 'OFF'},
        content_type='application/json'
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data['status'] == 'confirmation_required'

def test_cambiar_modo_apagado_con_confirmacion(authenticated_client):
    """Test: Apagar sistema con confirmación"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={'modo': 'OFF', 'confirmado': True},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['estado']['modo_actual'] == 'OFF'

def test_cambiar_modo_invalido(authenticated_client):
    """Test: Intentar usar un modo no válido"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={'modo': 'MODO_INEXISTENTE'},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'

def test_cambiar_modo_sin_parametro(authenticated_client):
    """Test: Request sin parámetro 'modo'"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={},
        content_type='application/json'
    )
    assert response.status_code == 400

# ============================================================================
# TESTS DE API - ESTADO Y LOGS
# ============================================================================

def test_obtener_estado(authenticated_client):
    """Test: Obtener estado actual del sistema"""
    response = authenticated_client.get('/api/estado')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'estado' in data
    assert 'modo_actual' in data['estado']

def test_obtener_historial(authenticated_client):
    """Test: Obtener historial de logs"""
    response = authenticated_client.get('/api/historial')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'logs' in data
    assert isinstance(data['logs'], list)

def test_obtener_historial_con_limite(authenticated_client):
    """Test: Historial con límite personalizado"""
    response = authenticated_client.get('/api/historial?limite=5')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['logs']) <= 5

def test_obtener_estadisticas(authenticated_client):
    """Test: Obtener estadísticas del sistema"""
    response = authenticated_client.get('/api/estadisticas')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'estadisticas' in data

# ============================================================================
# TESTS DE BASE DE DATOS
# ============================================================================

def test_database_inicializacion():
    """Test: Inicialización correcta de la BD"""
    db_test = DatabaseManager(':memory:')
    estado = db_test.obtener_estado()
    assert 'modo_actual' in estado
    assert estado['modo_actual'] == 'STANDBY'

def test_database_actualizar_estado():
    """Test: Actualización de estado en BD"""
    db_test = DatabaseManager(':memory:')
    nuevo_estado = {
        'modo_actual': 'CONFERENCIA',
        'carga_cpu': '45%',
        'latencia': '12ms'
    }
    result = db_test.actualizar_estado(nuevo_estado)
    assert result == True
    
    estado = db_test.obtener_estado()
    assert estado['modo_actual'] == 'CONFERENCIA'

def test_database_registrar_evento():
    """Test: Registro de eventos en auditoría"""
    db_test = DatabaseManager(':memory:')
    result = db_test.registrar_evento(
        evento='TEST',
        detalles='Evento de prueba',
        ip='127.0.0.1',
        usuario='test_user'
    )
    assert result == True
    
    logs = db_test.obtener_ultimos_logs(limite=1)
    assert len(logs) > 0
    assert logs[0][4] == 'TEST'  # Campo 'evento'

def test_database_obtener_estadisticas():
    """Test: Obtención de estadísticas"""
    db_test = DatabaseManager(':memory:')
    
    # Insertar algunos logs
    db_test.registrar_evento('TEST1', 'Detalle 1', '127.0.0.1', nivel='INFO')
    db_test.registrar_evento('TEST2', 'Detalle 2', '127.0.0.1', nivel='WARNING')
    
    stats = db_test.obtener_estadisticas()
    assert 'total_eventos' in stats
    assert stats['total_eventos'] >= 2

# ============================================================================
# TESTS DE SEGURIDAD
# ============================================================================

def test_sql_injection_prevention(authenticated_client):
    """Test: Protección contra SQL Injection"""
    response = authenticated_client.post('/api/cambiar_modo',
        json={'modo': "CINE'; DROP TABLE logs_auditoria; --"},
        content_type='application/json'
    )
    # Debe rechazar el modo inválido sin ejecutar SQL malicioso
    assert response.status_code == 400

def test_xss_prevention(authenticated_client):
    """Test: Headers de seguridad básicos"""
    response = authenticated_client.get('/api/estado')
    # Verificar que la respuesta es JSON (no HTML ejecutable)
    assert response.content_type == 'application/json'

# ============================================================================
# EJECUCIÓN DE TESTS
# ============================================================================

if __name__ == '__main__':
    print("="*70)
    print("🧪 EJECUTANDO SUITE DE TESTS")
    print("="*70)
    pytest.main([__file__, '-v', '--tb=short'])
