import http.server, socketserver, json, controller

PORT = 8002

class FilaHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Silenciar logs de acceso por defecto para mayor claridad
        print(f"[MS_FILA] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

    def enviar_json(self, respuesta, status):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode())

    def leer_body(self):
        """
        Lee el body de forma robusta.
        Si Content-Length está presente, lee exactamente esos bytes.
        Si no está, intenta leer lo que quede disponible (no bloquea).
        """
        try:
            length = self.headers.get('Content-Length')
            if length:
                raw = self.rfile.read(int(length))
            else:
                raw = b''
            return json.loads(raw) if raw else {}
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[MS_FILA] Error al leer body: {e}")
            return {}

    def do_POST(self):
        try:
            data = self.leer_body()

            if self.path == '/tomar_ticket':
                res, s = controller.handle_tomar_ticket(data)

            elif self.path == '/llamar_siguiente':
                res, s = controller.handle_llamar(data)

            elif self.path == '/validar_qr':
                res, s = controller.handle_validar_qr(data)

            elif self.path == '/completar_atencion':
                res, s = controller.handle_completar(data)

            elif self.path == '/expirar_ticket':
                res, s = controller.handle_expirar(data)

            else:
                res, s = {"error": "Ruta POST no encontrada"}, 404

            self.enviar_json(res, s)

        except Exception as e:
            print(f"[MS_FILA] Error crítico en do_POST: {e}")
            self.enviar_json({"error": "Error interno del servidor"}, 500)

    def do_GET(self):
        try:
            if self.path.startswith('/estado/'):
                est_id = self.path.split('/')[-1]
                if not est_id.isdigit():
                    self.enviar_json({"error": "ID de estudiante inválido"}, 400)
                    return
                res, s = controller.handle_ver_estado(est_id)
                self.enviar_json(res, s)
            else:
                self.enviar_json({"error": "Ruta GET no encontrada"}, 404)

        except Exception as e:
            print(f"[MS_FILA] Error crítico en do_GET: {e}")
            self.enviar_json({"error": "Error interno del servidor"}, 500)

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FilaHandler) as httpd:
        print(f"[MS_FILA] Servidor corriendo en puerto {PORT}")
        httpd.serve_forever()