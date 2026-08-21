"""
main.py -- Servidor Maestro de Entrega Automática Multi-Producto
MADART STUDIO -- The Digital Gaming Company
"""

import os
import json
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Madart Studio Delivery Cloud", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DIR_PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DIR_PATH, "config.json")
CATALOG_PATH = os.path.join(DIR_PATH, "catalogo.json")
PROCESSED_PATH = os.path.join(DIR_PATH, "processed_orders.json")

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_product_by_order(order_data):
    """Busca el producto correspondiente en el catálogo según item_id o título."""
    catalog = load_json(CATALOG_PATH, {"productos": {}})
    order_items = order_data.get("order_items", [])
    
    for item in order_items:
        title = item.get("item", {}).get("title", "").lower()
        item_id = item.get("item", {}).get("id", "")
        
        # Buscar por ID o por palabras clave
        for p_key, p_val in catalog.get("productos", {}).items():
            if p_val.get("item_id_ml") and p_val.get("item_id_ml") == item_id:
                return p_val
            for kw in p_val.get("keywords", []):
                if kw in title:
                    return p_val

    # Fallback al primer producto
    prods = list(catalog.get("productos", {}).values())
    return prods[0] if prods else None

def process_and_deliver(order_id: str):
    config = load_json(CONFIG_PATH, {})
    processed = set(load_json(PROCESSED_PATH, []))

    if str(order_id) in processed:
        print(f"⚠️ La orden {order_id} ya fue procesada anteriormente.")
        return

    # Consultar Orden
    headers = {"Authorization": f"Bearer {config.get('access_token', '')}"}
    res = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=headers)
    
    if res.status_code == 401: # Refrescar Token
        refresh_url = "https://api.mercadolibre.com/oauth/token"
        rf_payload = {
            "grant_type": "refresh_token",
            "client_id": config.get("app_id"),
            "client_secret": config.get("client_secret"),
            "refresh_token": config.get("refresh_token")
        }
        rf_res = requests.post(refresh_url, data=rf_payload).json()
        if "access_token" in rf_res:
            config["access_token"] = rf_res["access_token"]
            config["refresh_token"] = rf_res["refresh_token"]
            save_json(CONFIG_PATH, config)
            headers = {"Authorization": f"Bearer {config['access_token']}"}
            res = requests.get(f"https://api.mercadolibre.com/orders/{order_id}", headers=headers)

    if res.status_code != 200:
        print(f"❌ Error al consultar orden {order_id}: {res.status_code}")
        return

    order = res.json()
    if order.get("status") != "paid":
        print(f"⏳ La orden {order_id} aún no está pagada (Estado: {order.get('status')}).")
        return

    product = get_product_by_order(order)
    if not product:
        print(f"❌ No se encontró producto asociado para la orden {order_id}")
        return

    buyer_id = order["buyer"]["id"]
    buyer_name = order["buyer"].get("nickname", "Jugador")
    seller_id = config.get("seller_id") or str(order["seller"]["id"])
    pack_id = order.get("pack_id") or order_id

    mensaje = product["mensaje"].format(
        comprador=buyer_name,
        link=product["download_link"]
    )

    url = f"https://api.mercadolibre.com/messages/packs/{pack_id}/sellers/{seller_id}?tag=post_sale"
    msg_headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": {"user_id": int(seller_id)},
        "to": [{"user_id": int(buyer_id), "resource": "orders", "resource_id": int(order_id)}],
        "text": mensaje
    }

    send_res = requests.post(url, headers=msg_headers, json=payload)
    if send_res.status_code in [200, 201]:
        print(f"🎉 ¡ENTREGA AUTOMÁTICA COMPLETADA! Producto: {product['nombre']} -> Comprador: {buyer_name}")
        processed.add(str(order_id))
        save_json(PROCESSED_PATH, list(processed))
    else:
        print(f"❌ Error enviando mensaje posventa: {send_res.status_code} - {send_res.text}")

@app.get("/", response_class=HTMLResponse)
def index():
    config = load_json(CONFIG_PATH, {})
    catalog = load_json(CATALOG_PATH, {"productos": {}})
    processed = load_json(PROCESSED_PATH, [])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MADART STUDIO -- Delivery Hub</title>
        <style>
            body {{ background: #0B0B0E; color: #FFF; font-family: -apple-system, sans-serif; padding: 40px; text-align: center; }}
            .card {{ background: #14141B; border: 1px solid #282835; border-radius: 12px; max-width: 650px; margin: 0 auto; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            h1 {{ color: #C9182B; font-family: serif; letter-spacing: 2px; }}
            .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: bold; background: #00E676; color: #000; }}
            .stat {{ display: flex; justify-content: space-around; margin: 25px 0; border-top: 1px solid #282835; border-bottom: 1px solid #282835; padding: 15px 0; }}
            .stat-num {{ font-size: 24px; font-weight: bold; color: #D4AF37; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>MADART STUDIO</h1>
            <p style="color:#AAA;">Servidor en la Nube de Entrega Automática 24/7</p>
            <div class="badge">● SISTEMA ONLINE</div>
            <div class="stat">
                <div><div class="stat-num">{len(catalog.get('productos', {}))}</div><div>Productos Activos</div></div>
                <div><div class="stat-num">{len(processed)}</div><div>Entregas Realizadas</div></div>
                <div><div class="stat-num">{'CONECTADO' if config.get('access_token') else 'PENDIENTE'}</div><div>Mercado Libre</div></div>
            </div>
            <p style="font-size:12px; color:#666;">Webhook URL: /webhook | Auth Callback: /callback</p>
        </div>
    </body>
    </html>
    """
    return html

@app.get("/callback")
def oauth_callback(code: str = None):
    if not code:
        return JSONResponse({"error": "No se recibio codigo"}, status_code=400)
    
    config = load_json(CONFIG_PATH, {})
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": config["app_id"],
        "client_secret": config["client_secret"],
        "code": code,
        "redirect_uri": config.get("redirect_uri", "")
    }
    res = requests.post(url, data=payload).json()
    if "access_token" in res:
        config["access_token"] = res["access_token"]
        config["refresh_token"] = res["refresh_token"]
        config["seller_id"] = str(res["user_id"])
        save_json(CONFIG_PATH, config)
        return HTMLResponse("<h1 style='color:green; text-align:center; margin-top:50px;'>✓ ¡Cuenta de Mercado Libre Vinculada con Éxito a Madart Studio!</h1>")
    return JSONResponse({"error": "Error al canjear token", "details": res}, status_code=400)

@app.post("/webhook")
async def webhook(request: Request, bg_tasks: BackgroundTasks):
    try:
        body = await request.json()
        topic = body.get("topic") or body.get("type")
        resource = body.get("resource", "")

        if "orders" in str(resource) or topic in ["orders_v2", "orders"]:
            order_id = resource.split("/")[-1]
            print(f"⚡ Nueva compra detectada: Orden #{order_id}")
            bg_tasks.add_task(process_and_deliver, order_id)

        return {"status": "OK"}
    except Exception as e:
        print("Error en webhook:", e)
        return JSONResponse({"error": str(e)}, status_code=500)
