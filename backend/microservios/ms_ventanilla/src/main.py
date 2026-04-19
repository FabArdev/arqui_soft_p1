import http.server, socketserver, json, controller

PORT = 8003

class VentanillaHandler(http.server.BaseHTTPRequestHandler):
    def enviar_json(self, respuesta, status):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode())

    def do_GET(self):
        if self.path == '/listar':
            res, s = controller.handle_listar_todas()
        elif self.path == '/disponibles':
            res, s = controller.handle_disponibles()
        else: res, s = {"error": "No encontrado"}, 404
        self.enviar_json(res, s)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length > 0 else {}
        
        if self.path == '/crear': res, s = controller.handle_crear(data)
        elif self.path == '/abrir': res, s = controller.handle_abrir(data)
        elif self.path == '/cerrar': res, s = controller.handle_cerrar(data)
        else: res, s = {"error": "No encontrado"}, 404
        self.enviar_json(res, s)

    def do_DELETE(self):
        if self.path.startswith('/eliminar/'):
            v_id = self.path.split('/')[-1]
            res, s = controller.handle_eliminar(v_id)
            self.enviar_json(res, s)

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), VentanillaHandler) as httpd:
        print(f"MS_VENTANILLA en puerto {PORT}")
        httpd.serve_forever()