from repository import VentanillaRepository

db = VentanillaRepository()
db.inicializar_db()

def handle_listar_todas():
    return {"ventanillas": db.obtener_todas()}, 200

def handle_crear(data):
    etiqueta = data.get('etiqueta')
    if not etiqueta: return {"error": "Falta etiqueta"}, 400
    v_id = db.crear(etiqueta, data.get('descripcion', ''))
    return {"mensaje": "Ventanilla creada", "id": v_id}, 201

def handle_eliminar(v_id):
    if db.desactivar(v_id):
        return {"mensaje": "Ventanilla dada de baja"}, 200
    return {"error": "No encontrada"}, 404

def handle_disponibles():
    return {"disponibles": db.obtener_disponibles()}, 200

def handle_abrir(data):
    v_id, u_id = data.get('ventanilla_id'), data.get('usuario_id')
    if not v_id or not u_id: return {"error": "Faltan datos"}, 400
    try:
        s_id = db.abrir_sesion(v_id, u_id)
        return {"mensaje": "Sesión iniciada", "sesion_id": s_id}, 200
    except Exception as e:
        return {"error": str(e)}, 500

def handle_cerrar(data):
    v_id, u_id = data.get('ventanilla_id'), data.get('usuario_id')
    if db.cerrar_sesion(v_id, u_id):
        return {"mensaje": "Sesión cerrada"}, 200
    return {"error": "No se encontró sesión activa para este cajero"}, 404