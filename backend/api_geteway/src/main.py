import http.server
import socketserver
import json
import urllib.request
import urllib.error

PORT = 8000

MICROSERVICIOS = {
    "/usuario":    "http://ms_usuario:8001",
    "/fila":       "http://ms_nucleo_fila:8002",
    "/ventanilla": "http://ms_ventanilla:8003"
}

# ─────────────────────────────────────────────────────────────────────────────
# RBAC por rol_id:
#   1 = estudiante  (acceso mínimo)
#   2 = cajero      (gestión de fila y ventanillas)
#   3 = admin       (acceso total)
#
# Estrategia: lista de rutas permitidas por rol (whitelist).
# Es más seguro que una blacklist: lo que no está explícitamente permitido,
# queda denegado para ese rol.
# ─────────────────────────────────────────────────────────────────────────────

RUTAS_PERMITIDAS = {
    # rol_id 1 - Estudiante: solo puede operar sobre su propio ticket
    1: [
        "/usuario/registro",
        "/usuario/login",
        "/fila/tomar_ticket",
        "/fila/estado/",     
    ],
    # rol_id 2 - Cajero: gestiona la fila y su ventanilla
    2: [
        "/usuario/login",
        "/ventanilla/disponibles",
        "/ventanilla/abrir",
        "/ventanilla/cerrar",
        "/fila/llamar_siguiente",
        "/fila/validar_qr",
        "/fila/completar_atencion",
        "/fila/expirar_ticket",
        "/fila/estado/",
    ],
    # rol_id 3 - Admin: acceso total (no se filtra)
    3: None
}


def rol_puede_acceder(rol_id, path):
    """
    Devuelve True si el rol tiene permiso para la ruta indicada.
    El admin (rol 3) siempre puede. Los demás usan prefijos whitelist.
    """
    if rol_id == 3:
        return True

    rutas = RUTAS_PERMITIDAS.get(rol_id, [])
    if rutas is None:
        return True 

    # Verificar si la ruta comienza con alguno de los prefijos permitidos
    return any(path.startswith(ruta) for ruta in rutas)


class GatewayHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[GATEWAY] {self.command} {self.path}")

    def enviar_json(self, respuesta, status):
        body = json.dumps(respuesta).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        # CORS: permite llamadas desde el frontend en cualquier origen
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Rol-Id')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.enviar_json({}, 200)

    def proxy_request(self, method):
        # ── 1. Parsear prefijo y ruta interna ─────────────────────────────
        path_sin_query = self.path.split('?')[0]
        query_string   = self.path[len(path_sin_query):] 

        partes = path_sin_query.split('/')
        if len(partes) < 2:
            return self.enviar_json({"error": "Ruta inválida"}, 400)

        prefijo  = "/" + partes[1]
        ruta_ms  = "/" + "/".join(partes[2:]) + query_string

        if prefijo not in MICROSERVICIOS:
            return self.enviar_json({"error": f"Microservicio '{prefijo}' no encontrado"}, 404)

        # ── 2. Verificar RBAC ────────────────────────────────────────────
        try:
            rol_id = int(self.headers.get('X-Rol-Id', '1'))
        except ValueError:
            rol_id = 1

        ruta_completa = prefijo + "/" + "/".join(partes[2:])
        if not rol_puede_acceder(rol_id, ruta_completa):
            return self.enviar_json(
                {"error": "No tienes permisos para esta acción"},
                403
            )

        # ── 3. Leer body de forma robusta ────────────────────────────────
        body = None
        raw_length = self.headers.get('Content-Length')
        if raw_length:
            try:
                content_length = int(raw_length)
                if content_length > 0:
                    body = self.rfile.read(content_length)
                    if body and self.headers.get('Content-Type', '').startswith('application/json'):
                        try:
                            json.loads(body.decode('utf-8'))
                        except json.JSONDecodeError:
                            return self.enviar_json({"error": "El cuerpo de la petición no es JSON válido"}, 400)
            except ValueError:
                return self.enviar_json({"error": "Content-Length inválido"}, 400)

        # ── 4. Hacer proxy al microservicio destino ──────────────────────
        target_url = f"{MICROSERVICIOS[prefijo]}{ruta_ms}"

        try:
            req = urllib.request.Request(target_url, data=body, method=method)
            req.add_header('Content-Type', 'application/json')
            if body:
                req.add_header('Content-Length', str(len(body)))

            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                self.enviar_json(res_body, response.status)

        except urllib.error.HTTPError as e:
            # El microservicio respondió con un código de error HTTP
            try:
                error_body = json.loads(e.read().decode('utf-8'))
            except Exception:
                error_body = {"error": f"Error en el microservicio destino (HTTP {e.code})"}
            self.enviar_json(error_body, e.code)

        except urllib.error.URLError as e:
            # No se pudo conectar al microservicio (down, red, etc.)
            print(f"[GATEWAY] URLError hacia {target_url}: {e.reason}")
            self.enviar_json(
                {"error": f"No se pudo contactar al microservicio. ¿Está levantado?"},
                503
            )

        except Exception as e:
            print(f"[GATEWAY] Error inesperado: {e}")
            self.enviar_json({"error": "Error interno del Gateway"}, 500)

    def do_GET(self):    self.proxy_request("GET")
    def do_POST(self):   self.proxy_request("POST")
    def do_PATCH(self):  self.proxy_request("PATCH")
    def do_DELETE(self): self.proxy_request("DELETE")


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), GatewayHandler) as httpd:
        print(f"[GATEWAY] API Gateway corriendo en el puerto {PORT}")
        httpd.serve_forever()