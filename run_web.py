import flet as ft
import uvicorn
import os
import socket
from main import main, configurar_rutas_fastapi

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip_local = obtener_ip_local()
    usar_ssl = os.environ.get("USE_SSL", "false").lower() == "true"
    
    ssl_args = {}
    protocolo = "http"
    if usar_ssl and os.path.exists("cert.pem") and os.path.exists("key.pem"):
        ssl_args = {"ssl_keyfile": "key.pem", "ssl_certfile": "cert.pem"}
        protocolo = "https"

    print("=" * 60)
    print("🚀 INICIANDO SERVIDOR WEB LUXO (Acceso Multidispositivo)")
    print("=" * 60)
    print(f"💻 Acceso PC:      {protocolo}://localhost:8550  ó  {protocolo}://{ip_local}:8550")
    print(f"📱 Acceso Celular: {protocolo}://{ip_local}:8550")
    print("=" * 60)

    os.makedirs("uploads", exist_ok=True)
    
    from fastapi import FastAPI
    app = FastAPI(title="LUXO Web Server")
    configurar_rutas_fastapi(app)

    flet_asgi_app = ft.app(
        target=main, 
        upload_dir="uploads", 
        view=ft.AppView.WEB_BROWSER,
        export_asgi_app=True
    )
    from fastapi.staticfiles import StaticFiles
    os.makedirs("custom_assets/temp_pdfs", exist_ok=True)
    os.makedirs("custom_assets/temp_audio", exist_ok=True)
    app.mount("/temp_pdfs", StaticFiles(directory="custom_assets/temp_pdfs"), name="temp_pdfs")
    app.mount("/temp_audio", StaticFiles(directory="custom_assets/temp_audio"), name="temp_audio")
    app.mount("/custom_assets", StaticFiles(directory="custom_assets"), name="custom_assets")
    app.mount("/", flet_asgi_app)

    puerto = int(os.environ.get("PORT", 8550))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=puerto, 
        ws_ping_interval=3.0, 
        ws_ping_timeout=5.0, 
        timeout_keep_alive=30, 
        **ssl_args
    )

