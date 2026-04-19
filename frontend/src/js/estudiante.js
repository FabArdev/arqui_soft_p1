let intervalEstado = null;

async function initEstudiante() {
    actualizarEstadoTicket();
    if (intervalEstado) clearInterval(intervalEstado);
    intervalEstado = setInterval(actualizarEstadoTicket, 10000);
}

async function pedirTicket() {
    const estId = localStorage.getItem('usuario_id');
    const registro = localStorage.getItem('registro');

    const { data, error } = await apiFetch('/fila/tomar_ticket', 'POST', {
        estudiante_id: parseInt(estId),
        registro: parseInt(registro)
    });

    // CORREGIDO: reemplazados los alert() nativos por showToast()
    if (error) return showToast(error, 'error');

    showToast('¡Ticket obtenido con éxito!', 'success');
    actualizarEstadoTicket();
}

async function actualizarEstadoTicket() {
    const estId = localStorage.getItem('usuario_id');

    // CORREGIDO: guard para evitar GET /fila/estado/null
    if (!estId) return;

    const { data, error } = await apiFetch(`/fila/estado/${estId}`);
    const container = document.getElementById('info-ticket');
    if (!container) return;

    // Sin ticket activo: mostrar botón para sacar uno
    if (error || data.mensaje === 'Sin tickets activos') {
        container.innerHTML = `
            <p class="text-muted-custom" style="margin-bottom:1rem;">No tienes turnos pendientes.</p>
            <button class="btn-main btn-success" onclick="pedirTicket()">Sacar Ticket</button>`;
        return;
    }

    const t = data.ticket;

    // ── ESTADO EXPIRADO ──────────────────────────────────────────────────────
    // El cajero llamó al estudiante pero no se presentó a tiempo.
    // El QR fue invalidado. Debe sacar un nuevo turno.
    if (t.estado === 'EXPIRADO') {
        // Detener el polling: ya no hay nada que actualizar para este ticket
        if (intervalEstado) {
            clearInterval(intervalEstado);
            intervalEstado = null;
        }
        container.innerHTML = `
            <div class="text-center">
                <div class="estado-banner estado-expirado" style="margin-bottom:1rem;">
                    ⚠ Tu turno fue cancelado
                </div>
                <p style="margin-bottom:0.5rem;">Fuiste llamado a la ventanilla pero no te presentaste a tiempo.</p>
                <p class="text-muted-custom" style="margin-bottom:1.5rem;">Tu QR ya no es válido. Debes sacar un nuevo turno.</p>
                <button class="btn-main btn-success" onclick="pedirTicket()">Sacar Nuevo Ticket</button>
            </div>`;
        return;
    }
    // ────────────────────────────────────────────────────────────────────────

    // Badge de color según estado
    const badgeClass = t.estado === 'ATENDIENDO' ? 'badge-active' : 'badge-waiting';

    container.innerHTML = `
        <div class="text-center">
            <h3 style="margin-bottom:0.5rem;">Tu Posición: #${t.posicion}</h3>
            <p class="badge ${badgeClass}" style="margin-bottom:1rem;">${t.estado}</p>
            <p>Personas delante: <strong>${data.personas_delante}</strong></p>
            <p>Tiempo estimado: <strong>${data.tiempo_estimado}</strong></p>
            <div id="qrcode" style="margin-top:1rem; display:flex; justify-content:center;"></div>
            ${t.estado === 'ATENDIENDO'
                ? '<p style="color:var(--danger-color);font-weight:600;font-size:1.1rem;margin-top:1rem;">¡DIRÍGETE A LA VENTANILLA AHORA!</p>'
                : ''}
        </div>`;

    // Generar imagen QR solo si el código existe (ATENDIENDO con QR válido o ESPERANDO)
    if (t.codigo_qr) {
        new QRCode(document.getElementById('qrcode'), {
            text: t.codigo_qr,
            width: 140,
            height: 140
        });
    }
}

function showToast(mensaje, tipo = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) { console.log('[Toast]', mensaje); return; }
    toast.textContent = mensaje;
    toast.className = `toast toast-${tipo}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3500);
}