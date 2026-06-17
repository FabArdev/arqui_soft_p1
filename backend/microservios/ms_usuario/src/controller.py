from repository import UsuarioRepository
from handlers.campos_handler import CamposObligatoriosHandler
from handlers.email_handler import FormatoEmailHandler
from handlers.registro_unico_handler import RegistroUnicoHandler
from handlers.registrar_handler import RegistrarUsuarioHandler

db_manager = UsuarioRepository()
db_manager.inicializar_db()


def handle_registro(data):
    try:
        h1 = CamposObligatoriosHandler()
        h2 = FormatoEmailHandler()
        h3 = RegistroUnicoHandler(db_manager)
        h4 = RegistrarUsuarioHandler(db_manager)

        h1.set_next(h2).set_next(h3).set_next(h4)

        return h1.handle(data, [])
    except Exception as e:
        return {"error": str(e), "pasos_ok": []}, 500


def handle_login(data):
    registro = data.get("registro")
    password = data.get("password")

    if not registro or not password:
        return {"error": "Registro o contraseña faltante"}, 400

    usuario = db_manager.verificar_credenciales(registro, password)

    if usuario:
        return {"message": "Login exitoso", "usuario": usuario}, 200
    else:
        return {"error": "Registro o contraseña incorrecta (o usuario inactivo)"}, 401


def handle_get_user(user_id):
    usuario = db_manager.obtener_usuario_por_id(user_id)

    if usuario:
        return {"usuario": usuario}, 200
    else:
        return {"error": "Usuario no encontrado"}, 404


def handle_get_users():
    usuarios = db_manager.obtener_usuarios()

    if usuarios:
        return {"usuarios": usuarios}, 200
    else:
        return {"usuarios": []}, 200


def handle_update_user(user_id, data):
    campos_permitidos = ["nombre", "email", "telefono", "rol_id", "password", "activo"]
    datos_a_actualizar = {k: v for k, v in data.items() if k in campos_permitidos}

    if not datos_a_actualizar:
        return {"error": "No se proporcionaron campos válidos para actualizar"}, 400

    exito = db_manager.actualizar_usuario(user_id, datos_a_actualizar)
    if exito:
        return {"mensaje": "Usuario actualizado correctamente"}, 200
    return {"error": "Usuario no encontrado o error en DB"}, 404


def handle_delete_user(user_id):
    exito = db_manager.desactivar_usuario(user_id)
    if exito:
        return {"mensaje": "Usuario desactivado correctamente (Baja lógica)"}, 200
    return {"error": "No se pudo encontrar al usuario para desactivar"}, 404
