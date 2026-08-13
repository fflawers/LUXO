from fastapi import APIRouter, Request
from services.ai_service import auditar_foto_con_gemini, procesar_ticket_con_gemini
import base64

router = APIRouter()

@router.post("/auditar_foto")
async def auditar_foto(request: Request):
    try:
        data = await request.json()
        guia_b64 = data.get("guia_b64")
        tienda_b64 = data.get("tienda_b64")
        instrucciones = data.get("instrucciones", "")
        
        if not guia_b64 or not tienda_b64:
            return {"status": "error", "message": "Faltan imágenes en base64"}
            
        guia_bytes = base64.b64decode(guia_b64)
        tienda_bytes = base64.b64decode(tienda_b64)
        
        resultado = auditar_foto_con_gemini(guia_bytes, tienda_bytes, instrucciones)
        return {"status": "ok", "resultado": resultado}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/procesar_ticket")
async def procesar_ticket(request: Request):
    try:
        data = await request.json()
        ticket_b64 = data.get("ticket_b64")
        
        if not ticket_b64:
            return {"status": "error", "message": "Falta imagen de ticket"}
            
        ticket_bytes = base64.b64decode(ticket_b64)
        resultado, error = procesar_ticket_con_gemini(ticket_bytes)
        
        if error:
            return {"status": "error", "message": error}
        return {"status": "ok", "resultado": resultado}
    except Exception as e:
        return {"status": "error", "message": str(e)}
