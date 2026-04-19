async function handleRegistro(event) {
    event.preventDefault();
    const nombre = document.getElementById('nombre').value;
    const email = document.getElementById('email').value;
    const registro = document.getElementById('registro').value;
    const password = document.getElementById('password').value;
    const mensajeError = document.getElementById('mensaje-error');
    const datos = { nombre, email, registro: parseInt(registro), password, rol_id: 1 };

    const { data, error } = await apiFetch('/usuario/registro', 'POST', datos);

    if (error) {
        mensajeError.innerText = error;
        mensajeError.style.display = 'block';
    } else {
        alert("Registro exitoso. Ahora puedes iniciar sesión.");
        window.location.href = 'login.html';
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const registro = document.getElementById('registro').value;
    const password = document.getElementById('password').value;
    const mensajeError = document.getElementById('mensaje-error');

    const { data, error } = await apiFetch('/usuario/login', 'POST', { 
        registro: parseInt(registro), 
        password 
    });

    if (error) {
        mensajeError.innerText = error;
        mensajeError.style.display = 'block';
    } else {
        localStorage.setItem('usuario_id', data.usuario.id);
        localStorage.setItem('nombre', data.usuario.nombre);
        localStorage.setItem('rol_id', data.usuario.rol_id);
        localStorage.setItem('registro', registro);
        window.location.href = 'dashboard.html';
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}