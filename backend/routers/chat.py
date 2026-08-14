from fastapi import APIRouter, Request
from services.chat_service import procesar_chat

router = APIRouter()

@router.post("/ask")
async def ask_chat(request: Request):
    try:
        body = await request.json()
        usuario_id = body.get("usuario_id")
        mensaje = body.get("mensaje", "")
        historial = body.get("historial", [])
        
        if not mensaje:
            return {"status": "error", "message": "Mensaje vacío"}
            
        resultado = procesar_chat(usuario_id, mensaje, historial)
        return {"status": "ok", "data": resultado}
    except Exception as e:
        return {"status": "error", "message": str(e)}
