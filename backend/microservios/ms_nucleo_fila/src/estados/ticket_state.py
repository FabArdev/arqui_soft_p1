from abc import ABC, abstractmethod


class TicketState(ABC):

    @abstractmethod
    def llamar(self, context, ventanilla_id, cajero_id):
        pass

    @abstractmethod
    def validar_qr(self, context, codigo_qr, ventanilla_id):
        pass

    @abstractmethod
    def completar(self, context):
        pass

    @abstractmethod
    def expirar(self, context):
        pass

    def _invalida(self, operacion):
        estado = self.__class__.__name__.replace("Estado", "").upper()
        return {"error": f"Transición inválida: '{operacion}' no está permitido en estado {estado}"}, 409
