from repository import FilaRepository
from ticket_context import TicketContext

db = FilaRepository()
db.inicializar_db()


def handle_tomar_ticket(data):
    est_id   = data.get('estudiante_id')
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
    tiempo  = delante * 2.5

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

    siguiente = db.obtener_siguiente_esperando()
    if not siguiente:
        return {"mensaje": "No hay nadie en la fila"}, 200

    context   = TicketContext(siguiente, db)
    resultado = context.llamar(v_id, c_id)

    if isinstance(resultado, tuple):
        return resultado
    if not resultado:
        return {"mensaje": "No hay nadie en la fila"}, 200

    return {"atendiendo_a": resultado}, 200


def handle_validar_qr(data):
    qr_leido = data.get('codigo_qr')
    v_id     = data.get('ventanilla_id')

    if not qr_leido or not v_id:
        return {"error": "Faltan datos: codigo_qr y ventanilla_id"}, 400

    ticket = db.obtener_ticket_atendiendo_ventanilla(v_id)
    if not ticket:
        return {"error": "No hay ticket en atención para esta ventanilla"}, 400

    context   = TicketContext(ticket, db)
    resultado = context.validar_qr(qr_leido, v_id)

    if isinstance(resultado, tuple):
        return resultado
    if resultado:
        return {"mensaje": "Validación exitosa", "datos": resultado}, 200
    return {"error": "Código QR no válido o no corresponde a esta ventanilla"}, 400


def handle_expirar(data):
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        return {"error": "Falta ticket_id"}, 400

    ticket = db.obtener_ticket_por_id(ticket_id)
    if not ticket:
        return {"error": "Ticket no encontrado"}, 404

    context   = TicketContext(ticket, db)
    resultado = context.expirar()

    if isinstance(resultado, tuple):
        return resultado
    if resultado:
        return {"mensaje": "Ticket expirado. El estudiante deberá sacar un nuevo turno."}, 200
    return {"error": "Ticket no encontrado o no estaba en estado ATENDIENDO"}, 404


def handle_completar(data):
    ticket_id = data.get('ticket_id')
    if not ticket_id:
        return {"error": "Falta ticket_id"}, 400

    ticket = db.obtener_ticket_por_id(ticket_id)
    if not ticket:
        return {"error": "Ticket no encontrado"}, 404

    context   = TicketContext(ticket, db)
    resultado = context.completar()

    if isinstance(resultado, tuple):
        return resultado
    if resultado:
        return {"mensaje": "Atención completada exitosamente"}, 200
    return {"error": "Ticket no encontrado o ya fue completado"}, 404
