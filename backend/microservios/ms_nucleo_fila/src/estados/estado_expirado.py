from estados.ticket_state import TicketState


class EstadoExpirado(TicketState):

    def llamar(self, context, ventanilla_id, cajero_id):
        return self._invalida("llamar")

    def validar_qr(self, context, codigo_qr, ventanilla_id):
        return self._invalida("validar_qr")

    def completar(self, context):
        return self._invalida("completar")

    def expirar(self, context):
        return self._invalida("expirar")
