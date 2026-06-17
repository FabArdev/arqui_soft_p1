from handlers.validacion_handler import ValidacionHandler


class RegistroUnicoHandler(ValidacionHandler):

    def __init__(self, db):
        super().__init__()
        self.db = db

    def handle(self, data, pasos_ok):
        if self.db.existe_registro(data.get('registro')):
            return {"error": "El número de registro ya está en uso", "pasos_ok": pasos_ok}, 400

        pasos_ok.append("registro_disponible")
        return self._continuar(data, pasos_ok)
