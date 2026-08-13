from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
import os
import re
import urllib.parse as _up

router = APIRouter()

# En el backend, definimos dónde se guardan los assets y descargas
BASE_PATH = os.path.abspath(os.path.dirname(__file__))
ASSETS_PATH = os.path.join(BASE_PATH, "..", "..", "custom_assets") # Ajustar según donde vivan realmente

@router.get("/dl")
async def download_file_route(file: str = "", original: str = ""):
    safe = os.path.basename(_up.unquote(file))
    if not safe:
        return Response(content="Archivo no especificado", status_code=400)

    filepath = os.path.join(ASSETS_PATH, "temp_pdfs", safe)
    
    # Aquí iría la lógica de obtener_pdf_assets si no existe
    # if not os.path.exists(filepath):
    #    ...
    
    if not os.path.exists(filepath):
        return Response(content="Archivo no encontrado", status_code=404)

    display_name = _up.unquote(original) if original else safe
    ext = os.path.splitext(safe)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp",
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo",
    }
    media_type = mime_map.get(ext, "application/octet-stream")
    safe_ascii_name = display_name.encode('ascii', 'ignore').decode('ascii') or "descarga"
    encoded_name = _up.quote(display_name)
    return FileResponse(
        path=filepath,
        filename=display_name,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii_name}"; filename*=UTF-8\'\'{encoded_name}',
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("/api/download_enfoque_pdf/{day}")
async def download_enfoque_pdf_route(day: str):
    # Pendiente: Mover lógica de enfoque_diario_generar_pdf
    return {"error": "Endpoint migrado al backend, pendiente de separar dependencias de UI"}

@router.get("/api/download_excel/{day}")
async def download_excel_route(day: str):
    # Pendiente: Mover lógica de enfoque_diario_generar_excel
    return {"error": "Endpoint migrado al backend, pendiente de separar dependencias de UI"}

@router.get("/print_enfoque/{day}")
async def print_enfoque_route(day: str):
    # Pendiente: HTML template de enfoque
    return {"error": "Endpoint migrado al backend, pendiente de HTML template"}
