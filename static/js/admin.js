/**
 * Admin Panel JavaScript
 * Gestión completa del sistema: CRUD, Analíticas, Configuración
 */

// ==================== VARIABLES GLOBALES ====================
let chartUsuarios = null;
let chartEventos = null;

// ==================== INICIALIZACIÓN ====================
window.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
    cargarUsuarios();
});

// ==================== NAVEGACIÓN DE TABS ====================
function cambiarTab(tabName) {
    // Ocultar todos los tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Desactivar todos los botones
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Activar el tab seleccionado
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
    
    // Cargar datos según el tab
    switch(tabName) {
        case 'usuarios':
            cargarUsuarios();
            break;
        case 'logs':
            // Ya se carga con los filtros
            break;
        case 'analiticas':
            cargarAnaliticas();
            break;
        case 'config':
            cargarConfiguraciones();
            break;
    }
}

// ==================== ESTADÍSTICAS GENERALES ====================
async function cargarEstadisticas() {
    try {
        const res = await fetch('/api/admin/estadisticas');
        const data = await res.json();
        
        if (data.status === 'success') {
            const stats = data.estadisticas;
            
            document.getElementById('total-logs').textContent = stats.total_logs || 0;
            document.getElementById('usuarios-activos').textContent = stats.usuarios_activos || 0;
            document.getElementById('cambios-hoy').textContent = stats.cambios_hoy || 0;
            
            const errores = stats.eventos_nivel?.ERROR || 0;
            document.getElementById('errores-total').textContent = errores;
        }
    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// ==================== GESTIÓN DE USUARIOS ====================
async function cargarUsuarios() {
    try {
        const res = await fetch('/api/admin/usuarios');
        const data = await res.json();
        
        if (data.status === 'success') {
            const tbody = document.getElementById('tabla-usuarios');
            tbody.innerHTML = '';
            
            if (data.usuarios.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="loading">No hay usuarios registrados</td></tr>';
                return;
            }
            
            data.usuarios.forEach(user => {
                const estadoBadge = user.activo ? 
                    '<span class="badge badge-activo">Activo</span>' : 
                    '<span class="badge badge-inactivo">Inactivo</span>';
                
                const rolBadge = user.rol === 'admin' ?
                    '<span class="badge badge-admin">Admin</span>' :
                    '<span class="badge badge-operador">Operador</span>';
                
                const ultimoAcceso = user.ultimo_acceso || 'Nunca';
                
                tbody.innerHTML += `
                    <tr>
                        <td>${user.id}</td>
                        <td><strong>${user.username}</strong></td>
                        <td>${user.nombre_completo || '-'}</td>
                        <td>${user.email || '-'}</td>
                        <td>${rolBadge}</td>
                        <td>${estadoBadge}</td>
                        <td>${ultimoAcceso}</td>
                        <td>
                            <div class="action-btns">
                                <button class="btn-icon btn-edit" onclick="editarUsuario(${user.id})">Editar</button>
                                <button class="btn-icon btn-delete" onclick="confirmarEliminarUsuario(${user.id})">Eliminar</button>
                            </div>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (error) {
        console.error('Error al cargar usuarios:', error);
    }
}

function mostrarModalUsuario(userId = null) {
    document.getElementById('modal-usuario').style.display = 'block';
    
    if (userId) {
        document.getElementById('modal-usuario-titulo').textContent = 'Editar Usuario';
        document.getElementById('usuario-id').value = userId;
        // Aquí cargarías los datos del usuario
    } else {
        document.getElementById('modal-usuario-titulo').textContent = 'Nuevo Usuario';
        document.getElementById('form-usuario').reset();
        document.getElementById('usuario-id').value = '';
    }
}

function cerrarModalUsuario() {
    document.getElementById('modal-usuario').style.display = 'none';
    document.getElementById('form-usuario').reset();
}

async function guardarUsuario(event) {
    event.preventDefault();
    
    const userId = document.getElementById('usuario-id').value;
    const datos = {
        username: document.getElementById('usuario-username').value,
        password: document.getElementById('usuario-password').value,
        nombre_completo: document.getElementById('usuario-nombre').value,
        email: document.getElementById('usuario-email').value,
        rol: document.getElementById('usuario-rol').value
    };
    
    try {
        const res = await fetch('/api/admin/usuarios', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(datos)
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            alert('Usuario guardado correctamente');
            cerrarModalUsuario();
            cargarUsuarios();
            cargarEstadisticas();
        } else {
            alert('Error: ' + (data.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error al guardar usuario:', error);
        alert('Error de conexión');
    }
}

async function confirmarEliminarUsuario(userId) {
    if (!confirm('¿Está seguro que desea desactivar este usuario?')) {
        return;
    }
    
    try {
        const res = await fetch(`/api/admin/usuarios/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            alert('Usuario desactivado correctamente');
            cargarUsuarios();
            cargarEstadisticas();
        } else {
            alert('Error: ' + (data.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error al eliminar usuario:', error);
        alert('Error de conexión');
    }
}

// ==================== GESTIÓN DE LOGS ====================
async function buscarLogs() {
    const filtros = {
        usuario: document.getElementById('filtro-usuario').value,
        nivel: document.getElementById('filtro-nivel').value,
        fecha_desde: document.getElementById('filtro-fecha-desde').value,
        fecha_hasta: document.getElementById('filtro-fecha-hasta').value,
        limite: 100
    };
    
    try {
        const res = await fetch('/api/admin/logs/buscar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(filtros)
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            const tbody = document.getElementById('tabla-logs');
            tbody.innerHTML = '';
            
            if (data.logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="loading">No se encontraron registros</td></tr>';
                return;
            }
            
            data.logs.forEach(log => {
                const nivelClass = log.nivel || 'INFO';
                tbody.innerHTML += `
                    <tr>
                        <td>${log.fecha}</td>
                        <td><span class="badge badge-${nivelClass.toLowerCase()}">${log.nivel}</span></td>
                        <td>${log.usuario || 'Sistema'}</td>
                        <td><strong>${log.evento}</strong></td>
                        <td>${log.detalles || '-'}</td>
                        <td>${log.origen_ip || '-'}</td>
                    </tr>
                `;
            });
        }
    } catch (error) {
        console.error('Error al buscar logs:', error);
        alert('Error al buscar logs');
    }
}

function mostrarModalLimpiarLogs() {
    document.getElementById('modal-limpiar-logs').style.display = 'block';
}

function cerrarModalLimpiarLogs() {
    document.getElementById('modal-limpiar-logs').style.display = 'none';
}

async function ejecutarLimpiezaLogs() {
    const dias = document.getElementById('dias-mantener').value;
    
    if (!confirm(`Se eliminarán todos los logs anteriores a ${dias} días. ¿Continuar?`)) {
        return;
    }
    
    try {
        const res = await fetch('/api/admin/logs/limpiar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ dias: parseInt(dias) })
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            alert(`Limpieza completada. ${data.eliminados} registros eliminados`);
            cerrarModalLimpiarLogs();
            cargarEstadisticas();
        } else {
            alert('Error: ' + (data.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error al limpiar logs:', error);
        alert('Error de conexión');
    }
}

async function exportarLogs() {
    try {
        window.location.href = '/api/admin/exportar/logs?limite=1000';
    } catch (error) {
        console.error('Error al exportar:', error);
        alert('Error al exportar logs');
    }
}

// ==================== ANALÍTICAS ====================
async function cargarAnaliticas() {
    await cargarChartUsuarios();
    await cargarChartEventos();
    await cargarTimelineModos();
}

async function cargarChartUsuarios() {
    try {
        const res = await fetch('/api/admin/analiticas/usuarios?limite=5');
        const data = await res.json();
        
        if (data.status === 'success') {
            const ctx = document.getElementById('canvas-usuarios');
            
            if (chartUsuarios) {
                chartUsuarios.destroy();
            }
            
            chartUsuarios = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.actividad.map(u => u.usuario),
                    datasets: [{
                        label: 'Acciones',
                        data: data.actividad.map(u => u.total_acciones),
                        backgroundColor: '#2d8659',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error al cargar chart usuarios:', error);
    }
}

async function cargarChartEventos() {
    try {
        const res = await fetch('/api/admin/analiticas/uso-por-modo');
        const data = await res.json();
        
        if (data.status === 'success') {
            const ctx = document.getElementById('canvas-eventos');
            
            if (chartEventos) {
                chartEventos.destroy();
            }
            
            // Colores para cada modo
            const coloresBase = {
                'STANDBY': '#95a5a6',
                'CINE': '#9b59b6',
                'CONFERENCIA': '#3498db',
                'VIDEOCONFERENCIA': '#1abc9c',
                'GRABACION': '#e74c3c',
                'OFF': '#34495e'
            };
            
            const modos = data.modos.map(m => m.modo);
            const usos = data.modos.map(m => m.total_usos);
            const colores = modos.map(modo => coloresBase[modo] || '#2d8659');
            
            chartEventos = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: modos,
                    datasets: [{
                        label: 'Veces Utilizado',
                        data: usos,
                        backgroundColor: colores,
                        borderColor: colores.map(c => c),
                        borderWidth: 2,
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                afterLabel: function(context) {
                                    const modo = data.modos[context.dataIndex];
                                    return `Usuarios: ${modo.usuarios_distintos}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error al cargar chart eventos:', error);
    }
}

async function cargarTimelineModos() {
    try {
        const res = await fetch('/api/admin/analiticas/timeline-modos?limite=20');
        const data = await res.json();
        
        if (data.status === 'success') {
            const container = document.getElementById('timeline-modos');
            container.innerHTML = '';
            
            if (data.timeline.length === 0) {
                container.innerHTML = '<p class="loading">No hay cambios registrados</p>';
                return;
            }
            
            data.timeline.forEach(item => {
                container.innerHTML += `
                    <div class="timeline-item">
                        <div class="timeline-date">${item.fecha}</div>
                        <div class="timeline-content">
                            <strong>${item.usuario}</strong> cambió de 
                            <strong>${item.estado_previo || 'N/A'}</strong> a 
                            <strong>${item.estado_nuevo || 'N/A'}</strong>
                            ${item.detalles ? `<br><small>${item.detalles}</small>` : ''}
                        </div>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error('Error al cargar timeline:', error);
    }
}

// ==================== CONFIGURACIONES ====================
async function cargarConfiguraciones() {
    try {
        const res = await fetch('/api/admin/configuraciones');
        const data = await res.json();
        
        if (data.status === 'success') {
            const grid = document.getElementById('config-grid');
            grid.innerHTML = '';
            
            data.configuraciones.forEach(config => {
                grid.innerHTML += `
                    <div class="config-item">
                        <h4>${config.clave}</h4>
                        <p>${config.descripcion || 'Sin descripción'}</p>
                        <input type="${config.tipo === 'integer' ? 'number' : 'text'}" 
                               id="config-${config.id}" 
                               value="${config.valor}">
                        <button class="btn-primary" onclick="actualizarConfig('${config.clave}', 'config-${config.id}')">
                            Guardar
                        </button>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error('Error al cargar configuraciones:', error);
    }
}

async function actualizarConfig(clave, inputId) {
    const valor = document.getElementById(inputId).value;
    
    try {
        const res = await fetch(`/api/admin/configuraciones/${clave}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ valor })
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            alert('Configuración actualizada correctamente');
        } else {
            alert('Error: ' + (data.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error al actualizar configuración:', error);
        alert('Error de conexión');
    }
}

// ==================== CERRAR MODAL AL HACER CLIC FUERA ====================
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
}
