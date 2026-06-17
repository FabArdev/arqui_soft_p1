from estados.ticket_state import TicketState


class EstadoAtendiendo(TicketState):

    def llamar(self, context, ventanilla_id, cajero_id):
        return self._invalida("llamar")

    def validar_qr(self, context, codigo_qr, ventanilla_id):
        return context.db.validar_ticket_qr(codigo_qr, ventanilla_id)

    def completar(self, context):
        ok = context.db.completar_atencion(context.ticket_id)
        if ok:
            context.transicionar("ATENDIDO")
        return ok

    def expirar(self, context):
        ok = context.db.expirar_ticket(context.ticket_id)
        if ok:
            context.transicionar("EXPIRADO")
        return ok
