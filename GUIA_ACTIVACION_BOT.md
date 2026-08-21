# 🤖 GUÍA OFICIAL: BOT DE ENTREGA AUTOMÁTICA MERCADO LIBRE
### MADART STUDIO — LA PREVIA PACK IMPRIMIBLE

Este sistema escucha las ventas de Mercado Libre en tiempo real (Webhooks) y le envía automáticamente al comprador un mensaje por el chat posventa con el link de descarga directa de los archivos, las 24 horas del día.

---

## 📁 Archivos del Bot en tu Carpeta:
`E:\Venta De Juegos Digitales\LaPrevia\bot_mercadolibre\`
* `server.py`: Servidor que recibe las compras en tiempo real.
* `meli_client.py`: Módulo que conecta con la API de Mercado Libre y envía los mensajes.
* `config.json`: Archivo de configuración con tus credenciales y el link de descarga.
* `processed_orders.json`: Registro de ventas para no enviar duplicados.

---

## 🚀 PASO 1: Subir el Pack ZIP a Google Drive
1. En tu carpeta `E:\Venta De Juegos Digitales\LaPrevia\output\` ya tenés creado el archivo comprimido oficial:
   📁 **`PACK_IMPRIMIBLE_LA_PREVIA_MADART_STUDIO.zip`** (contiene los 4 PDFs listos).
2. Subí ese archivo a tu **Google Drive** (o Dropbox/Mega).
3. Hacé clic derecho en el archivo en Drive &rarr; **Compartir** &rarr; cambiar acceso a: **«Cualquier persona con el enlace (Lector)»**.
4. Copiá el enlace de descarga y pegalo en `config.json` en el campo `"download_link"`.

---

## 🔑 PASO 2: Crear tu Aplicación Gratuita en Mercado Libre
1. Ingresá a [developers.mercadolibre.com.ar](https://developers.mercadolibre.com.ar) con tu cuenta de vendedor.
2. Hacé clic en **Mis Aplicaciones** &rarr; **Crear una nueva aplicación**.
3. Completá los datos básicos:
   * **Nombre:** `Madart Delivery Bot`
   * **Descripción corta:** `Bot de entrega automática de productos digitales de Madart Studio`
   * **Redirect URI:** `http://localhost:8080/callback` (o la URL de tu servidor en la nube).
   * **Tópicos de Notificación (Webhooks):** Marcá la casilla **`orders_v2`** y poné en Callback URL: `https://tu-dominio.com/webhook`
4. Al guardar, Mercado Libre te dará:
   * **App ID (Client ID)**
   * **Secret Key (Client Secret)**
5. Pegá esos dos valores en `config.json`.

---

## ⚡ PASO 3: Vincular tu Cuenta y Activar el Bot
1. Abrí una terminal en `E:\Venta De Juegos Digitales\LaPrevia\bot_mercadolibre\`.
2. Ejecutá:
   ```bash
   python server.py
   ```
3. Ingresá a la URL de autorización de Mercado Libre desde tu navegador:
   ```
   https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=TU_APP_ID&redirect_uri=http://localhost:8080/callback
   ```
4. Dale clic a **"Permitir"**.
5. ¡Listo! El servidor guardará tu `access_token` y `refresh_token` automáticamente.

A partir de ese momento, **cada vez que una persona compre tu publicación en Mercado Libre, recibirá el mensaje y los PDFs en menos de 2 segundos**.
