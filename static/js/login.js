/**
 * Login Page JavaScript
 * Manejo de autenticación y validación de formulario
 */

// Referencias a elementos del DOM
const form = document.getElementById('loginForm');
const btnLogin = document.getElementById('btnLogin');
const alertBox = document.getElementById('alert');

/**
 * Muestra una alerta al usuario
 * @param {string} mensaje - Mensaje a mostrar
 * @param {string} tipo - Tipo de alerta ('success' o 'error')
 */
function mostrarAlerta(mensaje, tipo) {
    alertBox.textContent = mensaje;
    alertBox.className = `alert alert-${tipo}`;
    alertBox.style.display = 'block';
    
    if (tipo === 'success') {
        setTimeout(() => {
            alertBox.style.display = 'none';
        }, 2000);
    }
}

/**
 * Maneja el envío del formulario de login
 * @param {Event} e - Evento de submit
 */
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    // Deshabilitar botón y mostrar loading
    btnLogin.disabled = true;
    btnLogin.innerHTML = 'Autenticando<span class="loading"></span>';
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            mostrarAlerta(data.msg, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            mostrarAlerta(data.error || 'Error desconocido', 'error');
            btnLogin.disabled = false;
            btnLogin.textContent = 'Iniciar Sesión';
        }
        
    } catch (error) {
        mostrarAlerta('Error de conexión con el servidor', 'error');
        btnLogin.disabled = false;
        btnLogin.textContent = 'Iniciar Sesión';
    }
}

// Event Listeners
form.addEventListener('submit', handleLogin);

// Focus automático en el campo de usuario
document.getElementById('username').focus();
