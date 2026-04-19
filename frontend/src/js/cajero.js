// ─────────────────────────────────────────────────────────────────────────────
// cajero.js — Flujo completo del cajero
//
// FLUJO:
//   1. initCajero()        → Carga ventanillas disponibles (dashboard.html)
//   2. abrirCaja()         → Abre sesión y redirige a atencion.html
//   3. llamarSiguiente()   → Toma el próximo ticket (ESPERANDO → ATENDIENDO)
//   4. iniciarEscaner()    → Activa cámara para leer QR del estudiante
//   5. validarQR()         → Verifica el QR contra la BD
//   6. completarAtencion() → Cierra el ticket (ATENDIENDO → ATENDIDO)
// ─────────────────────────────────────────────────────────────────────────────

let html5QrCode = null;
let ticketActual = null;

// ──────────────────────────────────────────────────────────
// PASO 1: Cargar ventanillas disponibles en dashboard.html
// ──────────────────────────────────────────────────────────

async function initCajero() {
    const { data, error } = await apiFetch('/ventanilla/disponibles');
    const select = document.getElementById('select-ventanilla');
    if (!select) return;

    if (error || !data || !data.disponibles) {
        select.innerHTML = '<option disabled>Error al cargar ventanillas</option>';
        return;
    }
    if (data.disponibles.length === 0) {
        select.innerHTML = '<option disabled>No hay ventanillas disponibles</option>';
        return;
    }
    select.innerHTML = data.disponibles.map(v =>
        `<option value="${v.id}">${v.etiqueta}</option>`
    ).join('');
}

// ──────────────────────────────────────────────────────────
// PASO 2: Abrir ventanilla
// ──────────────────────────────────────────────────────────

async function abrirCaja() {
    const vId = document.getElementById('select-ventanilla').value;
    const uId = localStorage.getItem('usuario_id');

    if (!vId || !uId) return showToast('Error: no se pudo identificar cajero o ventanilla.', 'error');

    const { data, error } = await apiFetch('/ventanilla/abrir', 'POST', {
        ventanilla_id: parseInt(vId),
        usuario_id: parseInt(uId)
    });

    if (error) return showToast('Error al abrir ventanilla: ' + error, 'error');

    localStorage.setItem('ventanilla_actual', vId);
    window.location.href = 'atencion.html';
}

// ──────────────────────────────────────────────────────────
// PASO 3: Llamar al siguiente estudiante
// ──────────────────────────────────────────────────────────

async function llamarSiguiente() {
    const vId = localStorage.getItem('ventanilla_actual');
    const cId = localStorage.getItem('usuario_id');

    if (!vId || !cId) return showToast('Sesión de cajero no encontrada.', 'error');

    await detenerEscaner();

    // Si había un ticket en ATENDIENDO que nunca fue escaneado, expirarlo primero.
    // Esto ocurre cuando el cajero llama a alguien, esa persona no se presenta,
    // y el cajero presiona "Llamar Siguiente" de nuevo sin haber completado la atención.
    if (ticketActual) {
        await expirarTicketActual();
    }

    setBanner('cargando', 'Llamando al siguiente...');

    const { data, error } = await apiFetch('/fila/llamar_siguiente', 'POST', {
        ventanilla_id: parseInt(vId),
        cajero_id: parseInt(cId)
    });

    if (error) {
        setBanner('espera', 'Listo para atender');
        return showToast('Error: ' + error, 'error');
    }

    if (data.mensaje === 'No hay nadie en la fila') {
        setBanner('espera', 'Fila vacía por ahora');
        setTextoEstudiante('No hay estudiantes en espera.');
        ticketActual = null;
        return;
    }

    ticketActual = data.atendiendo_a;
    setBanner('atendiendo', 'Atendiendo turno');
    setTextoEstudiante(`Turno #${ticketActual.posicion} — Registro: ${ticketActual.registro}`);
    iniciarEscaner();
}

// ──────────────────────────────────────────────────────────
// Expirar ticket no atendido
// ──────────────────────────────────────────────────────────

async function expirarTicketActual() {
    if (!ticketActual) return;

    await apiFetch('/fila/expirar_ticket', 'POST', { ticket_id: ticketActual.id });

    showToast(`Turno #${ticketActual.posicion} expirado. El estudiante deberá sacar un nuevo turno.`, 'error');
    ticketActual = null;
}

// ──────────────────────────────────────────────────────────
// PASO 4: Iniciar escáner de cámara
// ──────────────────────────────────────────────────────────

async function iniciarEscaner() {
    if (!ticketActual) return showToast('Primero llama a un estudiante.', 'error');

    const contenedor = document.getElementById('reader');
    if (!contenedor) return;

    await detenerEscaner();
    contenedor.style.display = 'block';

    html5QrCode = new Html5Qrcode('reader');
    try {
        await html5QrCode.start(
            { facingMode: 'environment' },
            { fps: 10, qrbox: { width: 250, height: 250 } },
            async (codigoLeido) => {
                await detenerEscaner();
                await validarQR(codigoLeido);
            },
            () => {}
        );
    } catch (err) {
        contenedor.style.display = 'none';
        showToast('No se pudo acceder a la cámara. Verifica los permisos.', 'error');
    }
}

// ──────────────────────────────────────────────────────────
// Detener escáner de forma segura
// ──────────────────────────────────────────────────────────

async function detenerEscaner() {
    if (html5QrCode) {
        try {
            if (html5QrCode.getState() === 2) await html5QrCode.stop();
        } catch (_) {}
        html5QrCode = null;
    }
    const contenedor = document.getElementById('reader');
    if (contenedor) contenedor.style.display = 'none';
}

// ──────────────────────────────────────────────────────────
// PASO 5: Validar QR leído
// ──────────────────────────────────────────────────────────

async function validarQR(codigoLeido) {
    const vId = localStorage.getItem('ventanilla_actual');

    const { data, error } = await apiFetch('/fila/validar_qr', 'POST', {
        codigo_qr: codigoLeido,
        ventanilla_id: parseInt(vId)
    });

    if (error) {
        setTextoEstudiante(`❌ QR inválido — Turno #${ticketActual.posicion}`);
        showToast('QR no corresponde a este turno. Escanea de nuevo.', 'error');
        iniciarEscaner();
        return;
    }

    setTextoEstudiante(`✅ Verificado — Registro: ${data.datos.registro}`);
    showToast('Identidad verificada.', 'success');
    await completarAtencion();
}

// ──────────────────────────────────────────────────────────
// PASO 6: Completar atención (estado final)
// ──────────────────────────────────────────────────────────

async function completarAtencion() {
    if (!ticketActual) return;
    await apiFetch('/fila/completar_atencion', 'POST', { ticket_id: ticketActual.id });
    ticketActual = null;
    setBanner('listo', '✅ Atención completada');
    setTextoEstudiante('Listo. Presiona "Llamar Siguiente" para continuar.');
}

// ──────────────────────────────────────────────────────────
// Utilidades visuales
// ──────────────────────────────────────────────────────────

function setTextoEstudiante(texto) {
    const el = document.getElementById('estudiante-actual');
    if (el) el.innerText = texto;
}

function setBanner(estado, texto) {
    const el = document.getElementById('estado-atencion');
    if (!el) return;
    el.textContent = texto;
    el.className = `estado-banner estado-${estado}`;
}

function showToast(mensaje, tipo = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) { console.log('[Toast]', mensaje); return; }
    toast.textContent = mensaje;
    toast.className = `toast toast-${tipo}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3500);
}