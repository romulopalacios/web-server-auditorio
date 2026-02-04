# 🎯 Sistema de Control de Auditorio

Sistema web profesional para la gestión integral de equipos de audio en auditorios universitarios con control en tiempo real, auditoría completa y panel administrativo.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Características Principales

✅ **Control en Tiempo Real**: Cambio de modos de operación (CONFERENCIA, CINE, STANDBY, OFF)  
✅ **Auditoría Completa**: Trazabilidad de todas las acciones con timestamp, usuario e IP  
✅ **Panel Administrativo**: CRUD completo de usuarios, búsqueda avanzada de logs  
✅ **Seguridad**: Autenticación, autorización por roles, rate limiting, protección CSRF  
✅ **Arquitectura MVC**: Separación de responsabilidades y código mantenible  
✅ **Sistema de Roles**: ADMIN, OPERADOR, INVITADO con permisos diferenciados

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd web-server
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tu configuración
```

5. **Inicializar la base de datos**
```bash
python -c "from modulos.gestor_datos import GestorDatos; GestorDatos('database/auditorio.db').inicializar_base_datos()"
```

6. **Ejecutar la aplicación**
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

### Credenciales por Defecto

- **Usuario Admin**: `admin` / Contraseña: `admin123`
- **Usuario Operador**: `operador` / Contraseña: `operador123`
- **Usuario Invitado**: `invitado` / Contraseña: `invitado123`

⚠️ **IMPORTANTE**: Cambiar las contraseñas por defecto en producción.

## 📁 Estructura del Proyecto

```
web-server/
├── app.py                      # Aplicación principal Flask
├── config.py                   # Configuración centralizada
├── requirements.txt            # Dependencias del proyecto
├── .env.example               # Plantilla de variables de entorno
├── modulos/
│   ├── __init__.py
│   └── gestor_datos.py        # Capa de acceso a datos
├── templates/                 # Plantillas HTML
│   ├── login.html
│   ├── dashboard.html
│   └── admin.html
├── static/                    # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── images/
├── database/                  # Base de datos (no versionada)
├── docs/                      # Documentación
└── scripts/                   # Scripts de utilidad
```

## 🛠️ Stack Tecnológico

### Backend
- **Flask 3.0**: Framework web minimalista y flexible
- **SQLite 3**: Base de datos embebida
- **Werkzeug**: Utilidades WSGI y gestión de sesiones

### Frontend
- **HTML5 + CSS3**: Estructura y diseño responsive
- **JavaScript (Vanilla)**: Interactividad sin dependencias
- **Font Awesome**: Iconografía profesional

### Herramientas de Desarrollo
- **pytest**: Testing automatizado
- **logging**: Sistema de logs robusto

## 🔐 Seguridad

- **Autenticación basada en sesiones** con Flask-Session
- **Hash de contraseñas** con Werkzeug
- **Validación de entrada** en formularios
- **Protección contra SQL Injection** con consultas parametrizadas
- **Rate limiting** para prevenir ataques de fuerza bruta
- **Control de acceso basado en roles** (RBAC)

## 📊 Base de Datos

### Tablas Principales

- **usuarios**: Gestión de usuarios y autenticación
- **estados_sistema**: Registro histórico de estados del auditorio
- **logs_auditoria**: Auditoría completa de acciones

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con cobertura
pytest --cov=modulos --cov-report=html

# Ejecutar tests específicos
pytest test_sistema.py -v
```

## 📈 Roadmap

- [ ] API REST con autenticación JWT
- [ ] Integración con hardware real (Raspberry Pi)
- [ ] Dashboard con gráficos en tiempo real
- [ ] Notificaciones push
- [ ] Modo multi-auditorio
- [ ] App móvil (React Native)

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

⭐ Si este proyecto te fue útil, considera darle una estrella
