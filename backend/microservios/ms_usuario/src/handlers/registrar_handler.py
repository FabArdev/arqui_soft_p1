from handlers.validacion_handler import ValidacionHandler


class RegistrarUsuarioHandler(ValidacionHandler):

    def __init__(self, db):
        super().__init__()
        self.db = db

    def handle(self, data, pasos_ok):
        usuario_id = self.db.registrar(
            data.get('nombre'),
            data.get('email'),
            data.get('password'),
            data.get('registro'),
            data.get('telefono', ''),
            1
        )
        if not usuario_id:
            return {"error": "No se pudo crear el usuario", "pasos_ok": pasos_ok}, 400

        pasos_ok.append("registrado")
        return {"mensaje": "Usuario creado", "id": usuario_id, "pasos_ok": pasos_ok}, 201
