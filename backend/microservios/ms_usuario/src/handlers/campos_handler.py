from handlers.validacion_handler import ValidacionHandler


class CamposObligatoriosHandler(ValidacionHandler):

    def handle(self, data, pasos_ok):
        nombre   = data.get('nombre')
        email    = data.get('email')
        registro = data.get('registro')
        password = data.get('password')

        if not all([nombre, email, registro, password]):
            return {"error": "Faltan datos obligatorios", "pasos_ok": pasos_ok}, 400

        pasos_ok.append("campos")
        return self._continuar(data, pasos_ok)
