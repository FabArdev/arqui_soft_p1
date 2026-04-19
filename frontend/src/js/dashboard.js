document.addEventListener('DOMContentLoaded', () => {
    // 1. Verificar si hay sesión
    checkAuth();

    // 2. Recuperar datos del usuario
    const nombre = localStorage.getItem('nombre');
    const rolId = parseInt(localStorage.getItem('rol_id'));

    // 3. Personalizar Bienvenida
    document.getElementById('welcome-name').innerText = `Hola, ${nombre}`;

    // 4. Mostrar vista según el Rol
    renderizarVista(rolId);
});

function renderizarVista(rolId) {
    document.getElementById('vista-estudiante').classList.add('hidden');
    document.getElementById('vista-cajero').classList.add('hidden');
    document.getElementById('vista-admin').classList.add('hidden');

    switch (rolId) {
        case 1:
            document.getElementById('vista-estudiante').classList.remove('hidden');
            initEstudiante(); 
            break;
        case 2: 
            document.getElementById('vista-cajero').classList.remove('hidden');
            initCajero();
            break;
        case 3: 
            document.getElementById('vista-admin').classList.remove('hidden');
            initAdmin(); 
            break;
        default:
            console.error("Rol no reconocido");
            logout();
            break;
    }
}