// ── Mapeo de pasos del backend a IDs del DOM ──────────────────────
const _COR_PASOS    = ['campos', 'email', 'registro_disponible', 'registrado'];
const _COR_CIRCULOS = ['cc-campos', 'cc-email', 'cc-registro', 'cc-crear'];
const _COR_LINEAS   = ['cl-1', 'cl-2', 'cl-3', null];

async function handleRegistro(event) {
    event.preventDefault();

    const datos = {
        nombre:   document.getElementById('nombre').value,
        email:    document.getElementById('email').value,
        registro: parseInt(document.getElementById('registro').value),
        password: document.getElementById('password').value,
        telefono: document.getElementById('telefono').value
    };

    const mensajeError = document.getElementById('mensaje-error');
    mensajeError.style.display = 'none';

    // Mostrar cadena y resetear todos los nodos a "pending"
    const chain = document.getElementById('cor-chain');
    chain.classList.remove('hidden');
    _COR_CIRCULOS.forEach(id => document.getElementById(id).className = 'cor-circle pending');
    ['cl-1','cl-2','cl-3'].forEach(id => document.getElementById(id).className = 'cor-connector');

    const { data, error } = await apiFetch('/usuario/registro', 'POST', datos);
    const pasosOk = (data && data.pasos_ok) ? data.pasos_ok : [];

    // Animar cada nodo de la cadena en secuencia
    for (let i = 0; i < _COR_CIRCULOS.length; i++) {
        await new Promise(r => setTimeout(r, 380));
        const circulo  = document.getElementById(_COR_CIRCULOS[i]);
        const lineaId  = _COR_LINEAS[i];
        const linea    = lineaId ? document.getElementById(lineaId) : null;

        if (pasosOk.includes(_COR_PASOS[i])) {
            circulo.className = 'cor-circle success';
            if (linea) linea.className = 'cor-connector passed';
        } else {
            circulo.className = 'cor-circle error';
            if (linea) linea.className = 'cor-connector failed';
            break;
        }
    }

    if (error) {
        await new Promise(r => setTimeout(r, 200));
        mensajeError.innerText = error;
        mensajeError.style.display = 'block';
    } else {
        await new Promise(r => setTimeout(r, 700));
        alert('¡Registro exitoso! Ahora puedes iniciar sesión.');
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
        localStorage.setItem('nombre',     data.usuario.nombre);
        localStorage.setItem('rol_id',     data.usuario.rol_id);
        localStorage.setItem('registro',   registro);
        window.location.href = 'dashboard.html';
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}
