import http.server
import socketserver
import json
import controller

PORT = 8001

class UsuarioHandler(http.server.BaseHTTPRequestHandler):
    
    def enviar_json(self, respuesta, status):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        
        self.end_headers()
        self.wfile.write(json.dumps(respuesta).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body) if length > 0 else {}

            if self.path == '/registro':
                respuesta, status = controller.handle_registro(data)
            elif self.path == '/login':
                respuesta, status = controller.handle_login(data)
            else:
                respuesta, status = {"error": "Ruta no encontrada"}, 404
            
            self.enviar_json(respuesta, status)

        except Exception as e:
            print(f"Error crítico en do_POST: {e}")
            self.enviar_json({"error": "Error interno del servidor"}, 500)
    
    def do_GET(self):
        if self.path.startswith('/obtener_usuario/'):
            user_id = self.path.split('/')[-1]
            respuesta, status = controller.handle_get_user(user_id)
            self.enviar_json(respuesta, status)
        
        elif self.path == '/obtener_usuarios':
            respuesta, status = controller.handle_get_users()
            self.enviar_json(respuesta, status)
            
        else:
            self.enviar_json({"error": "Ruta GET no encontrada"}, 404)
            
    def do_PATCH(self):
        if self.path.startswith('/usuarios/'):
            user_id = self.path.split('/')[-1]
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length)) if length > 0 else {}
            
            respuesta, status = controller.handle_update_user(user_id, data)
            self.enviar_json(respuesta, status)
        else:
            self.enviar_json({"error": "Ruta PATCH no encontrada"}, 404)
            
    def do_DELETE(self):
        if self.path.startswith('/usuarios/'):
            user_id = self.path.split('/')[-1]
            respuesta, status = controller.handle_delete_user(user_id)
            self.enviar_json(respuesta, status)
        else:
            self.enviar_json({"error": "Ruta DELETE no encontrada"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), UsuarioHandler) as httpd:
        print(f"MS_USUARIO listo en el puerto {PORT}")
        httpd.serve_forever()