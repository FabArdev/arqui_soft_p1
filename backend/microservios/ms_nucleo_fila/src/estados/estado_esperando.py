from estados.ticket_state import TicketState


class EstadoEsperando(TicketState):

    def llamar(self, context, ventanilla_id, cajero_id):
        resultado = context.db.transicionar_a_atendiendo(context.ticket_id, ventanilla_id, cajero_id)
        if resultado:
            context.transicionar("ATENDIENDO")
        return resultado

    def validar_qr(self, context, codigo_qr, ventanilla_id):
        return self._invalida("validar_qr")

    def completar(self, context):
        return self._invalida("completar")

    def expirar(self, context):
        return self._invalida("expirar")
