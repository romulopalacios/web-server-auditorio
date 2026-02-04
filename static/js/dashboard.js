/**
 * Dashboard JavaScript
 * Sistema de Control de Auditorio
 * Manejo de estado, notificaciones y comunicación con API
 */

// Variable global para el botón actual en el modal
let btnActual = null;

/**
 * Inicialización al cargar la página
 */
window.addEventListener('DOMContentLoaded', () => {
    cargarEstadoActual();
    cargarLogs();
    
    // Actualizar logs cada 10 segundos
    setInterval(cargarLogs, 10000);
});

/**
 * Muestra una notificación temporal al usuario
 * @param {string} mensaje - Mensaje a mostrar
 * @param {string} tipo - Tipo de notificación ('success', 'error', 'info')
 */
function mostrarNotificacion(mensaje, tipo = 'info') {
    // Remover notificación anterior si existe
    const notifAnterior = document.querySelector('.notificacion');
    if (notifAnterior) {
        notifAnterior.remove();
    }
    
    const notif = document.createElement('div');
    notif.className = `notificacion ${tipo}`;
    notif.textContent = mensaje;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}

/**
 * Carga el estado actual del sistema desde el servidor
 */
async function cargarEstadoActual() {
    try {
        const res = await fetch('/api/estado');
        if (!res.ok) throw new Error('Error al obtener estado');
        
        const data = await res.json();
        if (data.status === 'success') {
            actualizarUI(data.estado);
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error al cargar estado del sistema', 'error');
    }
}

/**
 * Actualiza la interfaz con el estado del sistema
 * @param {Object} estado - Estado actual del sistema
 */
function actualizarUI(estado) {
    document.getElementById('modo-val').textContent = estado.modo_actual;
    document.getElementById('cpu-val').textContent = estado.carga_cpu;
    document.getElementById('latencia-val').textContent = estado.latencia;
    
    // Actualizar estilo según estado
    const kpiEstado = document.getElementById('kpi-estado');
    kpiEstado.className = 'kpi';
    
    if (estado.modo_actual === 'OFF') {
        kpiEstado.classList.add('status-off');
    } else if (estado.modo_actual === 'STANDBY') {
        kpiEstado.classList.add('status-standby');
    } else {
        kpiEstado.classList.add('status-on');
    }
}

/**
 * Envía un comando para cambiar el modo del sistema
 * @param {string} modo - Modo a activar ('CONFERENCIA', 'CINE', 'OFF')
 * @param {HTMLElement} btn - Botón que activó el comando
 */
async function enviarComando(modo, btn) {
    // Deshabilitar botón y mostrar loading
    btn.disabled = true;
    const textoOriginal = btn.innerHTML;
    btn.innerHTML = btn.innerHTML + '<span class="spinner"></span>';
    
    try {
        const res = await fetch('/api/cambiar_modo', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ modo: modo })
        });
        
        const data = await res.json();
        
        if (res.status === 429) {
            mostrarNotificacion('Demasiadas solicitudes. Espere un momento.', 'error');
        } else if (data.status === 'success') {
            actualizarUI(data.estado);
            mostrarNotificacion(data.msg, 'success');
            cargarLogs();
        } else if (data.status === 'info') {
            mostrarNotificacion(data.msg, 'info');
        } else {
            mostrarNotificacion(data.msg, 'error');
        }
        
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error de conexión con el servidor', 'error');
    } finally {
        // Restaurar botón
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

/**
 * Muestra el modal de confirmación para apagar el sistema
 * @param {HTMLElement} btn - Botón de apagar
 */
function confirmarApagado(btn) {
    btnActual = btn;
    document.getElementById('modal-confirm').style.display = 'block';
}

/**
 * Cierra el modal de confirmación
 */
function cerrarModal() {
    document.getElementById('modal-confirm').style.display = 'none';
    btnActual = null;
}

/**
 * Confirma y ejecuta el apagado del sistema
 */
async function confirmarApagadoFinal() {
    // Verificar que hay un botón antes de cerrar el modal
    if (!btnActual) {
        cerrarModal();
        return;
    }
    
    // Cerrar modal y guardar referencia al botón antes de que se pierda
    const btn = btnActual;
    cerrarModal();
    
    btn.disabled = true;
    const textoOriginal = btn.innerHTML;
    btn.innerHTML = textoOriginal + '<span class="spinner"></span>';
    
    try {
        const res = await fetch('/api/cambiar_modo', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ modo: 'OFF', confirmado: true })
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            actualizarUI(data.estado);
            mostrarNotificacion('Sistema apagado correctamente', 'success');
            cargarLogs();
        } else {
            mostrarNotificacion(data.msg, 'error');
        }
        
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error de conexión', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

/**
 * Carga el historial de logs desde el servidor
 */
async function cargarLogs() {
    try {
        const res = await fetch('/api/historial?limite=15');
        if (!res.ok) throw new Error('Error al cargar logs');
        
        const data = await res.json();
        if (data.status !== 'success') return;
        
        const caja = document.getElementById('log-box');
        caja.innerHTML = '';
        
        data.logs.forEach(log => {
            const nivel = log.nivel || 'INFO';
            caja.innerHTML += `
                <div class="log-row ${nivel}">
                    [${log.fecha}] [${nivel}] ${log.usuario}: ${log.evento} - ${log.detalle}
                </div>
            `;
        });
        
        // Mantener scroll arriba para ver siempre el evento más reciente
        caja.scrollTop = 0;
        
    } catch (error) {
        console.error('Error al cargar logs:', error);
    }
}

/**
 * Cerrar modal al hacer clic fuera de él
 */
window.onclick = function(event) {
    const modal = document.getElementById('modal-confirm');
    if (event.target == modal) {
        cerrarModal();
    }
}
