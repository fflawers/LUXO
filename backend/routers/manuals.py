from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conectar_db
# Import rebuild_rag_cache to update RAG
from services.chat_service import rebuild_rag_cache

router = APIRouter()

class ManualCreate(BaseModel):
    nombre_archivo: str
    titulo: str
    version: str = "1.0"
    texto_extraido: str
    categoria: str = "General"
    archivo_base64: str = "" # Opcional para enviar binario

@router.get("/")
def get_manuals():
    """Obtiene la lista de manuales registrados."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT ID_Manual, Nombre_Archivo, Titulo, Version, Abierto FROM manuales ORDER BY Nombre_Archivo")
        rows = cursor.fetchall()
        return {"status": "ok", "data": rows}
    except Exception as e:
        print("ERROR CARGANDO MANUALES:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/")
def create_manual(req: ManualCreate):
    """Guarda un nuevo manual en la base de datos."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        import base64
        pdf_binario = base64.b64decode(req.archivo_base64) if req.archivo_base64 else None
        
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO manuales (Nombre_Archivo, Titulo, Version, Texto_Extraido, Contenido_Texto, Archivo_PDF, Categoria, Abierto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        """, (req.nombre_archivo, req.titulo, req.version, req.texto_extraido, req.texto_extraido, pdf_binario, req.categoria))
        db.commit()
        inserted_id = cursor.lastrowid
        
        rebuild_rag_cache()
        
        return {"status": "ok", "message": "Manual guardado correctamente", "id_manual": inserted_id}
    except Exception as e:
        print("ERROR GUARDANDO MANUAL:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.delete("/{id_manual}")
def delete_manual(id_manual: int):
    """Elimina un manual y sus historiales."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM pendientes_actualizacion 
            WHERE ID_Conversacion IN (
                SELECT ID_Conversacion FROM historial_conversaciones WHERE ID_Manual = %s
            )
        """, (id_manual,))
        cursor.execute("DELETE FROM historial_conversaciones WHERE ID_Manual = %s", (id_manual,))
        cursor.execute("DELETE FROM manuales WHERE ID_Manual = %s", (id_manual,))
        db.commit()
        
        # Invalidate internal cache
        rebuild_rag_cache()
        
        return {"status": "ok", "message": "Manual eliminado con éxito."}
    except Exception as e:
        print("ERROR ELIMINANDO MANUAL:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
