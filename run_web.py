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
    from fastapi.staticfiles import StaticFiles
    app = FastAPI(title="LUXO Web Server")
    
    @app.middleware("http")
    async def add_no_cache_headers(request, call_next):
        response = await call_next(request)
        path = request.url.path
        if (path.endswith(".js") or path.endswith(".html") or path == "" or path == "/") and not path.endswith(".mp4") and not path.endswith(".mp3"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    configurar_rutas_fastapi(app)
    try:
        import traductor_view
        traductor_view.registrar_rutas_fastapi_traductor(app)
    except Exception as e_tr:
        print("Notice traductor startup routes:", e_tr)

    flet_asgi_app = ft.app(
        target=main, 
        assets_dir="custom_assets",
        upload_dir="uploads", 
        view=ft.AppView.WEB_BROWSER,
        web_renderer=ft.WebRenderer.CANVAS_KIT,
        export_asgi_app=True
    )
    os.makedirs("custom_assets/temp_pdfs", exist_ok=True)
    os.makedirs("custom_assets/temp_audio", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    app.mount("/temp_pdfs", StaticFiles(directory="custom_assets/temp_pdfs"), name="temp_pdfs")
    app.mount("/temp_audio", StaticFiles(directory="custom_assets/temp_audio"), name="temp_audio")
    app.mount("/custom_assets", StaticFiles(directory="custom_assets"), name="custom_assets")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    app.mount("/", flet_asgi_app)

    puerto = int(os.environ.get("PORT", 8550))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=puerto, 
        ws_ping_interval=None, 
        ws_ping_timeout=None, 
        timeout_keep_alive=300, 
        **ssl_args
    )

