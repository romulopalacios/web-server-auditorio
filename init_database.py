"""
Script de Inicialización y Gestión de Base de Datos
Permite crear, verificar y resetear la base de datos del sistema
"""
import sys
import os
import argparse
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from modulos.gestor_datos import DatabaseManager
from werkzeug.security import generate_password_hash

def crear_base_datos(db_path: str = "database/auditorio.db"):
    """Crea la base de datos con la estructura completa"""
    print(f"📦 Creando base de datos en: {db_path}")
    
    try:
        db = DatabaseManager(db_path)
        print("✅ Base de datos creada exitosamente")
        
        # Mostrar información
        health = db.health_check()
        print(f"\n📊 Información de la base de datos:")
        print(f"   - Estado: {health['status']}")
        print(f"   - Integridad: {health['integrity']}")
        print(f"   - Tamaño: {health['db_size_mb']} MB")
        print(f"   - Tablas: {health['num_tables']}")
        print(f"   - Logs registrados: {health['total_logs']}")
        
        return True
    except Exception as e:
        print(f"❌ Error al crear base de datos: {e}")
        return False

def verificar_base_datos(db_path: str = "database/auditorio.db"):
    """Verifica el estado de la base de datos"""
    print(f"🔍 Verificando base de datos: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ La base de datos no existe")
        return False
    
    try:
        db = DatabaseManager(db_path)
        health = db.health_check()
        
        print(f"\n📊 Estado de la Base de Datos:")
        print(f"   ✅ Estado: {health['status']}")
        print(f"   ✅ Integridad: {health['integrity']}")
        print(f"   📁 Tamaño: {health['db_size_mb']} MB ({health['db_size_bytes']} bytes)")
        print(f"   📋 Tablas: {health['num_tables']}")
        print(f"   📝 Total de logs: {health['total_logs']}")
        
        # Verificar usuarios
        usuarios = db.obtener_todos_usuarios()
        print(f"\n👥 Usuarios registrados: {len(usuarios)}")
        for usuario in usuarios:
            estado = "🟢 Activo" if usuario['activo'] else "🔴 Inactivo"
            print(f"   {estado} - {usuario['username']} ({usuario['rol']})")
        
        # Verificar estado del sistema
        estado_sistema = db.obtener_estado()
        print(f"\n⚙️  Estado del sistema:")
        for clave, valor in estado_sistema.items():
            print(f"   - {clave}: {valor}")
        
        # Últimos logs
        logs = db.obtener_ultimos_logs(limite=5)
        print(f"\n📜 Últimos 5 eventos:")
        for log in logs:
            print(f"   - [{log[2]}] {log[1]} - {log[4]} por {log[3] or 'sistema'}")
        
        return True
    except Exception as e:
        print(f"❌ Error al verificar base de datos: {e}")
        return False

def resetear_base_datos(db_path: str = "database/auditorio.db"):
    """Elimina y recrea la base de datos"""
    print(f"⚠️  ADVERTENCIA: Esto eliminará todos los datos existentes")
    
    respuesta = input("¿Está seguro de continuar? (escriba 'SI' para confirmar): ")
    if respuesta != 'SI':
        print("❌ Operación cancelada")
        return False
    
    try:
        # Eliminar archivo si existe
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️  Base de datos anterior eliminada")
        
        # Crear nueva
        return crear_base_datos(db_path)
    except Exception as e:
        print(f"❌ Error al resetear base de datos: {e}")
        return False

def agregar_usuario(db_path: str, username: str, password: str, rol: str, 
                   nombre: str = None, email: str = None):
    """Agrega un nuevo usuario a la base de datos"""
    print(f"👤 Agregando usuario: {username}")
    
    try:
        db = DatabaseManager(db_path)
        password_hash = generate_password_hash(password)
        
        result = db.crear_usuario(
            username=username,
            password_hash=password_hash,
            rol=rol,
            nombre_completo=nombre,
            email=email
        )
        
        if result:
            print(f"✅ Usuario '{username}' creado exitosamente")
            return True
        else:
            print(f"❌ Error al crear usuario (puede que ya exista)")
            return False
    except Exception as e:
        print(f"❌ Error al agregar usuario: {e}")
        return False

def generar_datos_prueba(db_path: str = "database/auditorio.db"):
    """Genera datos de prueba para desarrollo"""
    print("🧪 Generando datos de prueba...")
    
    try:
        db = DatabaseManager(db_path)
        
        # Registrar eventos de prueba
        eventos = [
            ('LOGIN', 'Login exitoso', 'INFO', 'admin'),
            ('CAMBIO_MODO', 'Cambio a modo CONFERENCIA', 'INFO', 'admin'),
            ('CAMBIO_MODO', 'Cambio a modo CINE', 'INFO', 'operador'),
            ('ERROR', 'Error simulado para pruebas', 'ERROR', 'operador'),
            ('LOGOUT', 'Logout exitoso', 'INFO', 'admin'),
        ]
        
        for evento, detalle, nivel, usuario in eventos:
            db.registrar_evento(
                evento=evento,
                detalles=detalle,
                ip='127.0.0.1',
                nivel=nivel,
                usuario=usuario,
                user_agent='Script de prueba'
            )
        
        print(f"✅ {len(eventos)} eventos de prueba registrados")
        
        # Actualizar estado del sistema
        db.actualizar_estado({
            'modo_actual': 'STANDBY',
            'carga_cpu': '15%',
            'latencia': '5ms',
            'sistema_activo': 'true'
        })
        
        print("✅ Estado del sistema inicializado")
        return True
    except Exception as e:
        print(f"❌ Error al generar datos de prueba: {e}")
        return False

def exportar_estadisticas(db_path: str = "database/auditorio.db"):
    """Exporta estadísticas del sistema a un archivo"""
    print("📊 Exportando estadísticas...")
    
    try:
        db = DatabaseManager(db_path)
        stats = db.obtener_estadisticas_generales()
        
        filename = f"estadisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("ESTADÍSTICAS DEL SISTEMA DE CONTROL DE AUDITORIO\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Total de eventos registrados: {stats.get('total_eventos', 0)}\n")
            f.write(f"Usuarios activos: {stats.get('usuarios_activos', 0)}\n")
            f.write(f"Cambios de modo hoy: {stats.get('cambios_hoy', 0)}\n\n")
            
            f.write("Eventos por nivel:\n")
            for nivel, cantidad in stats.get('eventos_nivel', {}).items():
                f.write(f"  - {nivel}: {cantidad}\n")
            
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"✅ Estadísticas exportadas a: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error al exportar estadísticas: {e}")
        return False

def main():
    """Función principal con interfaz CLI"""
    parser = argparse.ArgumentParser(
        description='Gestión de Base de Datos - Sistema de Control de Auditorio'
    )
    
    parser.add_argument('comando', 
                       choices=['crear', 'verificar', 'resetear', 'usuario', 'prueba', 'stats'],
                       help='Comando a ejecutar')
    
    parser.add_argument('--db', default='database/auditorio.db',
                       help='Ruta a la base de datos (default: database/auditorio.db)')
    
    # Argumentos para crear usuario
    parser.add_argument('--username', help='Nombre de usuario')
    parser.add_argument('--password', help='Contraseña del usuario')
    parser.add_argument('--rol', choices=['admin', 'operador'], help='Rol del usuario')
    parser.add_argument('--nombre', help='Nombre completo del usuario')
    parser.add_argument('--email', help='Email del usuario')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🗄️  GESTOR DE BASE DE DATOS - Sistema de Control de Auditorio")
    print("=" * 70 + "\n")
    
    if args.comando == 'crear':
        crear_base_datos(args.db)
    
    elif args.comando == 'verificar':
        verificar_base_datos(args.db)
    
    elif args.comando == 'resetear':
        resetear_base_datos(args.db)
    
    elif args.comando == 'usuario':
        if not all([args.username, args.password, args.rol]):
            print("❌ Error: Se requieren --username, --password y --rol")
            return 1
        agregar_usuario(args.db, args.username, args.password, args.rol, 
                       args.nombre, args.email)
    
    elif args.comando == 'prueba':
        generar_datos_prueba(args.db)
    
    elif args.comando == 'stats':
        exportar_estadisticas(args.db)
    
    print("\n" + "=" * 70 + "\n")
    return 0

if __name__ == '__main__':
    sys.exit(main())
