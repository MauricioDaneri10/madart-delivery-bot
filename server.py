"""
server.py -- Servidor Webhook de Entrega Automática para Mercado Libre
Madart Studio
"""

import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from meli_client import MeliClient, load_config

meli = MeliClient()

class WebhookHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # 1. ROOT / HEALTH CHECK
        if parsed.path == "/":
            cfg = load_config()
            status = {
                "status": "ONLINE",
                "app": "Madart Studio Delivery Bot",
                "has_token": bool(cfg.get("access_token")),
                "seller_id": cfg.get("seller_id", "No configurado")
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(status, indent=2).encode("utf-8"))

        # 2. OAUTH CALLBACK (/callback?code=TG-...)
        elif parsed.path == "/callback":
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if code:
                redirect_uri = f"http://{self.headers.get('Host')}/callback"
                token_data = meli.exchange_code_for_token(code, redirect_uri)
                if token_data:
                    self._set_headers(200, "text/html; charset=utf-8")
                    html = """
                    <html>
                    <body style='font-family:sans-serif; text-align:center; padding:40px; background:#0B0B0E; color:#FFF;'>
                        <h1 style='color:#00E676;'>✓ ¡Cuenta de Mercado Libre Vinculada con Éxito!</h1>
                        <p>El bot de Madart Studio ya está listo para entregar el pack en automático.</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode("utf-8"))
                    return
            self._set_headers(400)
            self.wfile.write(b'{"error": "No se recibio codigo de autorizacion"}')

        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Not Found"}')

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        # 1. WEBHOOK DE MERCADO LIBRE (/webhook)
        if parsed.path == "/webhook":
            try:
                body = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic = body.get("topic") or body.get("type")
                resource = body.get("resource", "")
                
                print(f"📩 Webhook Recibido: Topic={topic}, Resource={resource}")

                # Si es una orden de compra
                if "orders" in str(resource) or topic in ["orders_v2", "orders"]:
                    order_id = resource.split("/")[-1]
                    print(f"⚡ Procesando nueva venta: Orden #{order_id}")
                    # Procesar en hilo secundario para responder inmediatamente 200 OK a Mercado Libre
                    threading.Thread(target=meli.send_delivery_message, args=(order_id,)).start()

                self._set_headers(200)
                self.wfile.write(b'{"status": "OK"}')
            except Exception as e:
                print("❌ Error procesando webhook:", e)
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Not Found"}')

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"\n🚀 Servidor de Entrega Automática Madart Studio escuchando en puerto {port}...")
    print(f"👉 Local: http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")

if __name__ == "__main__":
    run_server()
