"""
meli_client.py -- Cliente Oficial de la API de Mercado Libre
Maneja Autenticación OAuth 2.0, Refresco de Tokens y Envío de Mensajes Posventa.
Madart Studio
"""

import os
import json
import time
import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
PROCESSED_PATH = os.path.join(os.path.dirname(__file__), "processed_orders.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_processed_orders():
    if os.path.exists(PROCESSED_PATH):
        with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def mark_order_processed(order_id):
    processed = load_processed_orders()
    processed.add(str(order_id))
    with open(PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, indent=2)

class MeliClient:
    API_BASE = "https://api.mercadolibre.com"

    def __init__(self):
        self.config = load_config()

    def exchange_code_for_token(self, code, redirect_uri):
        """Intercambia el código de autorización por access_token y refresh_token."""
        url = f"{self.API_BASE}/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.config["app_id"],
            "client_secret": self.config["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri
        }
        res = requests.post(url, data=payload)
        data = res.json()
        if "access_token" in data:
            self.config["access_token"] = data["access_token"]
            self.config["refresh_token"] = data["refresh_token"]
            self.config["seller_id"] = str(data["user_id"])
            save_config(self.config)
            print("✓ Tokens guardados exitosamente en config.json")
            return data
        else:
            print("❌ Error al obtener token:", data)
            return None

    def refresh_access_token(self):
        """Refresca el access_token usando el refresh_token."""
        url = f"{self.API_BASE}/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.config["app_id"],
            "client_secret": self.config["client_secret"],
            "refresh_token": self.config["refresh_token"]
        }
        res = requests.post(url, data=payload)
        data = res.json()
        if "access_token" in data:
            self.config["access_token"] = data["access_token"]
            self.config["refresh_token"] = data["refresh_token"]
            save_config(self.config)
            print("✓ Access Token refrescado exitosamente")
            return data["access_token"]
        else:
            print("❌ Error al refrescar token:", data)
            return None

    def get_order_details(self, order_id):
        """Consulta los datos de una orden específica."""
        headers = {"Authorization": f"Bearer {self.config['access_token']}"}
        res = requests.get(f"{self.API_BASE}/orders/{order_id}", headers=headers)
        
        if res.status_code == 401: # Token expirado
            new_token = self.refresh_access_token()
            if new_token:
                headers = {"Authorization": f"Bearer {new_token}"}
                res = requests.get(f"{self.API_BASE}/orders/{order_id}", headers=headers)

        if res.status_code == 200:
            return res.json()
        return None

    def send_delivery_message(self, order_id):
        """Envía el mensaje automático posventa con el link de descarga."""
        if str(order_id) in load_processed_orders():
            print(f"⚠️ La orden {order_id} ya fue entregada previamente. Omitiendo.")
            return True

        order = self.get_order_details(order_id)
        if not order:
            print(f"❌ No se pudo obtener la orden {order_id}")
            return False

        # Verificar que el pago esté aprobado
        status = order.get("status")
        if status != "paid":
            print(f"⏳ La orden {order_id} aún no está pagada (Estado: {status}).")
            return False

        buyer_id = order["buyer"]["id"]
        buyer_name = order["buyer"].get("nickname", "Jugador")
        seller_id = self.config["seller_id"] or str(order["seller"]["id"])
        pack_id = order.get("pack_id") or order_id

        # Armar mensaje
        mensaje = self.config["mensaje_template"].format(
            comprador=buyer_name,
            link=self.config["download_link"]
        )

        # Enviar vía API de mensajería posventa
        url = f"{self.API_BASE}/messages/packs/{pack_id}/sellers/{seller_id}?tag=post_sale"
        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": {"user_id": int(seller_id)},
            "to": [{"user_id": int(buyer_id), "resource": "orders", "resource_id": int(order_id)}],
            "text": mensaje
        }

        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code in [200, 201]:
            print(f"🎉 ¡MENSAJE ENVIADO CON ÉXITO A {buyer_name} (Orden {order_id})!")
            mark_order_processed(order_id)
            return True
        else:
            print(f"❌ Error al enviar mensaje: {res.status_code} - {res.text}")
            return False
