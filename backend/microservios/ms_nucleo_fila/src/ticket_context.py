from estados.estado_esperando import EstadoEsperando
from estados.estado_atendiendo import EstadoAtendiendo
from estados.estado_atendido import EstadoAtendido
from estados.estado_expirado import EstadoExpirado

_ESTADOS = {
    "ESPERANDO":  EstadoEsperando,
    "ATENDIENDO": EstadoAtendiendo,
    "ATENDIDO":   EstadoAtendido,
    "EXPIRADO":   EstadoExpirado,
}


class TicketContext:

    def __init__(self, ticket_data, db):
        self.ticket_id = ticket_data["id"]
        self.db        = db
        self._state    = _ESTADOS[ticket_data["estado"]]()

    def transicionar(self, nuevo_estado):
        self._state = _ESTADOS[nuevo_estado]()

    def estado_nombre(self):
        return self._state.__class__.__name__

    def llamar(self, ventanilla_id, cajero_id):
        return self._state.llamar(self, ventanilla_id, cajero_id)

    def validar_qr(self, codigo_qr, ventanilla_id):
        return self._state.validar_qr(self, codigo_qr, ventanilla_id)

    def completar(self):
        return self._state.completar(self)

    def expirar(self):
        return self._state.expirar(self)
