from abc import ABC, abstractmethod


class ValidacionHandler(ABC):

    def __init__(self):
        self._siguiente = None

    def set_next(self, handler):
        self._siguiente = handler
        return handler

    @abstractmethod
    def handle(self, data, pasos_ok):
        pass

    def _continuar(self, data, pasos_ok):
        if self._siguiente:
            return self._siguiente.handle(data, pasos_ok)
        return {"pasos_ok": pasos_ok}, 201
