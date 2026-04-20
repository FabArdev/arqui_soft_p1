from repository import FilaRepository

db = FilaRepository()
db.inicializar_db()


def handle_tomar_ticket(data):
    est_id = data.get('estudiante_id')
    registro = data.get('registro')

    if not est_id or not registro:
        return {"error": "Faltan datos: se requiere estudiante_id y registro"}, 400

    existente = db.obtener_ticket_activo_estudiante(est_id)
    if existente:
        return {"error": "Ya tienes un ticket en curso", "ticket": existente}, 400

    ticket = db.crear_ticket(est_id, registro)
    return {"mensaje": "Ticket generado", "ticket": ticket}, 201


def handle_ver_estado(est_id):
    ticket = db.obtener_ticket_activo_estudiante(est_id)

    if not ticket:
        return {"mensaje": "Sin tickets activos"}, 200

    delante = db.contar_delante(ticket['posicion'])
    tiempo = delante * 2.5 

    return {
        "ticket": ticket,
        "personas_delante": delante,
        "tiempo_estimado": f"{tiempo:.1f} min"
    }, 200


def handle_llamar(data):
    v_id = data.get('ventanilla_id')
    c_id = data.get('cajero_id')

    if not v_id or not c_id:
        return {"error": "Faltan IDs de atención: ventanilla_id y cajero_id"}, 400

    siguiente = db.llamar_siguiente(v_id, c_id)
    if not siguiente:
        return {"mensaje": "No hay nadie en la fila"}, 200

    return {"atendiendo_a": siguiente}, 200


def handle_validar_qr(data):
    """
    Valida que el QR escaneado por el cajero corresponda al ticket
    actualmente en estado ATENDIENDO para esa ventanilla.
    ANTES: Esta función existía en el controller pero nunca era invocada
    porque faltaba la ruta en main.py. Ahora está conectada.
    """
    qr_leido = data.get('codigo_qr')
    v_id = data.get('ventanilla_id')

    if not qr_leido or not v_id:
        return {"error": "Faltan datos: codigo_qr y ventanilla_id"}, 400

    resultado = db.validar_ticket_qr(qr_leido, v_id)
    if resultado:
        return {"mensaje": "Validación exitosa", "datos": resultado}, 200

    return {"error": "Código QR no válido o no corresponde a esta ventanilla"}, 400


def handle_expirar(data):
    """
    Expira un ticket que fue llamado pero cuyo dueño no se presentó.
    Borra el QR para que el estudiante deba sacar uno nuevo.
    """
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        return {"error": "Falta ticket_id"}, 400

    ok = db.expirar_ticket(ticket_id)
    if ok:
        return {"mensaje": "Ticket expirado. El estudiante deberá sacar un nuevo turno."}, 200
    return {"error": "Ticket no encontrado o no estaba en estado ATENDIENDO"}, 404


def handle_completar(data):
    """
    Marca un ticket como ATENDIDO (estado final).
    NUEVO: Sin este paso, los tickets quedaban bloqueados en ATENDIENDO
    indefinidamente, impidiendo que el estudiante pudiera tomar un nuevo
    ticket en el futuro.
    """
    ticket_id = data.get('ticket_id')

    if not ticket_id:
        return {"error": "Falta ticket_id"}, 400

    ok = db.completar_atencion(ticket_id)
    if ok:
        return {"mensaje": "Atención completada exitosamente"}, 200

    return {"error": "Ticket no encontrado o ya fue completado"}, 404