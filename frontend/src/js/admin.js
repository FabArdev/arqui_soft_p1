// ─────────────────────────────────────────────────────────────────────────────
// admin.js — Panel de administración
//
// CORRECCIONES:
//   - cargarVentanillas() estaba en initAdmin() pero no implementada
//   - crearVentanilla() no existía (el botón en dashboard.html la llama)
//   - eliminarUsuario() no estaba implementada (el botón existía pero no la función)
//   - Los alert() se reemplazan por showToast() para mejor UX
// ─────────────────────────────────────────────────────────────────────────────

async function initAdmin() {
    await cargarUsuarios();
    await cargarVentanillas();
}

// ──────────────────────────────────────────────────────────
// USUARIOS
// ──────────────────────────────────────────────────────────

async function cargarUsuarios() {
    const { data, error } = await apiFetch('/usuario/obtener_usuarios');
    const tbody = document.getElementById('tabla-usuarios-body');

    if (error || !data || !data.usuarios) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted-custom">Error al cargar usuarios.</td></tr>`;
        return;
    }

    if (data.usuarios.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted-custom">No hay usuarios registrados.</td></tr>`;
        return;
    }

    const ROLES = { 1: 'Estudiante', 2: 'Cajero', 3: 'Admin' };

    tbody.innerHTML = data.usuarios.map(u => `
        <tr>
            <td>${u.registro}</td>
            <td>${u.nombre}</td>
            <td>
                <span class="badge ${u.rol_id === 3 ? 'badge-admin' : u.rol_id === 2 ? 'badge-active' : 'badge-waiting'}">
                    ${ROLES[u.rol_id] || 'Desconocido'}
                </span>
            </td>
            <td>
                ${u.rol_id !== 2 && u.rol_id !== 3 ? `
                <button class="btn-main btn-sm" style="width:auto"
                        onclick="ascenderCajero(${u.id})">
                    Hacer Cajero
                </button>` : ''}
                ${u.rol_id !== 3 ? `
                <button class="btn-main btn-danger btn-sm" style="width:auto; margin-left: 4px;"
                        onclick="eliminarUsuario(${u.id}, '${u.nombre}')">
                    Dar de Baja
                </button>` : ''}
            </td>
        </tr>
    `).join('');
}

async function ascenderCajero(id) {
    const { error } = await apiFetch(`/usuario/usuarios/${id}`, 'PATCH', { rol_id: 2 });
    if (error) return showToast('Error al cambiar rol: ' + error, 'error');
    showToast('Usuario ascendido a Cajero.', 'success');
    cargarUsuarios();
}

async function eliminarUsuario(id, nombre) {
    // ANTES: esta función no existía, el botón tiraba error en consola
    if (!confirm(`¿Seguro que deseas dar de baja a "${nombre}"? Esta acción es irreversible.`)) return;

    const { error } = await apiFetch(`/usuario/usuarios/${id}`, 'DELETE');
    if (error) return showToast('Error al dar de baja: ' + error, 'error');
    showToast(`Usuario "${nombre}" dado de baja.`, 'success');
    cargarUsuarios();
}

// ──────────────────────────────────────────────────────────
// VENTANILLAS
// ──────────────────────────────────────────────────────────

async function cargarVentanillas() {
    // ANTES: esta función era llamada en initAdmin() pero nunca estaba implementada
    const { data, error } = await apiFetch('/ventanilla/listar');
    const tbody = document.getElementById('tabla-ventanillas-body');

    if (!tbody) return; // No está en esta página

    if (error || !data || !data.ventanillas) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted-custom">Error al cargar ventanillas.</td></tr>`;
        return;
    }

    if (data.ventanillas.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted-custom">No hay ventanillas creadas.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.ventanillas.map(v => `
        <tr>
            <td>${v.id}</td>
            <td><strong>${v.etiqueta}</strong></td>
            <td>${v.descripcion || '—'}</td>
            <td>
                <button class="btn-main btn-danger btn-sm" style="width:auto"
                        onclick="eliminarVentanilla(${v.id}, '${v.etiqueta}')">
                    Dar de Baja
                </button>
            </td>
        </tr>
    `).join('');
}

async function crearVentanilla() {
    // ANTES: esta función no existía. El botón "+ Nueva" del dashboard la llama.
    const input = document.getElementById('nueva-ventanilla-etiqueta');
    const etiqueta = input ? input.value.trim() : '';

    if (!etiqueta) return showToast('Escribe una etiqueta para la ventanilla.', 'error');

    const { data, error } = await apiFetch('/ventanilla/crear', 'POST', { etiqueta });
    if (error) return showToast('Error al crear ventanilla: ' + error, 'error');

    showToast(`Ventanilla "${etiqueta}" creada.`, 'success');
    if (input) input.value = '';
    cargarVentanillas();
}

async function eliminarVentanilla(id, etiqueta) {
    if (!confirm(`¿Dar de baja la ventanilla "${etiqueta}"?`)) return;

    const { error } = await apiFetch(`/ventanilla/eliminar/${id}`, 'DELETE');
    if (error) return showToast('Error al eliminar: ' + error, 'error');

    showToast(`Ventanilla "${etiqueta}" dada de baja.`, 'success');
    cargarVentanillas();
}

// ──────────────────────────────────────────────────────────
// UTILIDAD: Toast (reemplaza los alert() del navegador)
// ──────────────────────────────────────────────────────────

function showToast(mensaje, tipo = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return; // Si no existe el elemento, usar alert como fallback
    toast.textContent = mensaje;
    toast.className = `toast toast-${tipo}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3500);
}