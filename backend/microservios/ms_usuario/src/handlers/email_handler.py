import re
from handlers.validacion_handler import ValidacionHandler


class FormatoEmailHandler(ValidacionHandler):
    _PATRON = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def handle(self, data, pasos_ok):
        if not self._PATRON.match(data.get('email', '')):
            return {"error": "Formato de email inválido", "pasos_ok": pasos_ok}, 400

        pasos_ok.append("email")
        return self._continuar(data, pasos_ok)
