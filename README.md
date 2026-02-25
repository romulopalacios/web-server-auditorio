# Sistema de Control de Auditorio

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

Sistema profesional de gestión y monitoreo en tiempo real para auditorios empresariales. Desarrollado con arquitectura MVC y patrones de diseño empresariales.

## 🎯 Características Principales

- **Control en Tiempo Real**: Gestión de modos de operación (Conferencia, Cine, Standby, OFF)
- **Dashboard Interactivo**: Visualización de métricas con actualización automática
- **Sistema de Autenticación**: Control de acceso con roles (Admin/Operador)
- **Monitoreo de Estado**: Seguimiento de CPU, latencia y configuración de equipos
- **Registro de Actividad**: Auditoría completa de operaciones del sistema
- **Panel de Administración**: Gestión de usuarios y configuraciones
- **Rate Limiting**: Protección contra ataques de fuerza bruta
- **Logging Avanzado**: Registro detallado para debugging y auditoría

## 🏗️ Arquitectura

- **Patrón MVC**: Separación clara de responsabilidades
- **Repository Pattern**: Abstracción de acceso a datos
- **Security Layer**: Capa de seguridad con Flask-Login y Flask-Limiter
- **SQLite**: Base de datos embebida para máximo rendimiento
- **Frontend Responsivo**: Interfaz adaptable a cualquier dispositivo

## 📋 Requisitos del Sistema

- **Python** 3.10 o superior
- **Sistema Operativo**: Windows, Linux o macOS
- **RAM**: Mínimo 512 MB
- **Espacio en Disco**: 50 MB

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/sistema-control-auditorio.git
cd sistema-control-auditorio
```

### 2. Crear entorno virtual

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Inicializar base de datos

```bash
python init_database.py
```

### 5. Configurar variables de entorno (Opcional)

Copiar `.env.example` a `.env` y ajustar según necesidades:

```bash
cp .env.example .env
```

Variables disponibles:
- `FLASK_ENV`: `development` o `production`
- `SECRET_KEY`: Clave secreta para sesiones (cambiar en producción)

## ▶️ Ejecución

### Modo desarrollo

```bash
python app.py
```

El servidor estará disponible en: `http://localhost:5000`

### Modo producción

```bash
export FLASK_ENV=production  # Linux/macOS
# o
$env:FLASK_ENV="production"  # Windows PowerShell

python app.py
```

## 👤 Credenciales por Defecto

| Usuario   | Contraseña | Rol       |
|-----------|------------|-----------|
| admin     | admin123   | Administrador |
| operador  | oper456    | Operador  |

> ⚠️ **Importante**: Cambiar estas credenciales en producción editando `config.py`

## 📁 Estructura del Proyecto

```
sistema-control-auditorio/
├── app.py                      # Aplicación principal Flask
├── config.py                   # Configuraciones por entorno
├── init_database.py            # Script de inicialización de BD
├── requirements.txt            # Dependencias Python
├── .env.example               # Template de variables de entorno
├── .gitignore                 # Archivos excluidos de Git
│
├── database/
│   └── auditorio.db           # Base de datos SQLite
│
├── logs/
│   └── sistema.log            # Logs de la aplicación
│
├── modulos/
│   ├── __init__.py
│   └── gestor_datos.py        # Capa de acceso a datos
│
├── static/
│   ├── css/                   # Estilos
│   │   ├── admin.css
│   │   ├── dashboard.css
│   │   └── login.css
│   ├── js/                    # JavaScript
│   │   ├── admin.js
│   │   ├── dashboard.js
│   │   └── login.js
│   └── images/                # Recursos gráficos
│
└── templates/                 # Plantillas HTML
    ├── login.html
    ├── dashboard.html
    └── admin.html
```

## 🔒 Seguridad

- **Hashing de Contraseñas**: Werkzeug PBKDF2
- **Protección CSRF**: Tokens de sesión
- **Rate Limiting**: Límite de peticiones por IP
- **Session Management**: Expiración automática (2 horas)
- **Logging de Seguridad**: Registro de intentos de acceso

## 🛠️ Configuración Avanzada

### Cambiar Puerto

Editar `app.py` línea final:

```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### Ajustar Rate Limits

Editar `config.py`:

```python
RATELIMIT_DEFAULT = "100 per day;20 per hour"
```

### Agregar Nuevos Usuarios

Editar `config.py`:

```python
USUARIOS_VALIDOS = {
    "admin": "nueva_contraseña_segura",
    "usuario2": "otra_contraseña"
}
```

## 📊 Modos de Operación

| Modo         | Descripción                           | Uso de CPU | Latencia |
|--------------|---------------------------------------|------------|----------|
| CONFERENCIA  | Optimizado para voz y presentaciones  | 45%        | 12ms     |
| CINE         | Procesamiento 3D y Atmos              | 88%        | 24ms     |
| STANDBY      | Modo de espera con bajo consumo       | 5%         | 8ms      |
| OFF          | Sistema apagado                       | 0%         | N/A      |

## 🔧 Troubleshooting

### Error: "Port already in use"

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:5000 | xargs kill -9
```

### Error: "Database locked"

Cerrar todas las instancias de la aplicación y reiniciar.

### No aparecen los logs

Verificar que la carpeta `logs/` existe y tiene permisos de escritura.

## 📝 API Endpoints

| Endpoint              | Método | Autenticación | Descripción                    |
|-----------------------|--------|---------------|--------------------------------|
| `/`                   | GET    | Sí            | Dashboard principal            |
| `/login`              | GET/POST | No          | Inicio de sesión               |
| `/logout`             | POST   | Sí            | Cerrar sesión                  |
| `/admin`              | GET    | Sí (Admin)    | Panel de administración        |
| `/api/estado`         | GET    | Sí            | Estado actual del sistema      |
| `/api/cambiar-modo`   | POST   | Sí            | Cambiar modo de operación      |
| `/api/registro`       | GET    | Sí            | Historial de cambios           |
| `/api/usuarios`       | GET    | Sí (Admin)    | Lista de usuarios              |
| `/health`             | GET    | No            | Health check para monitoreo    |

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autores

- **Romul** - Autor Principal
- **Gudiño Anthony** - Co-Autor

## 📞 Soporte

Para reportar bugs o solicitar nuevas funcionalidades, por favor abre un issue en GitHub.

---

**Version 2.0 Professional Edition** - Sistema de Control de Auditorio © 2026
