from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conectar_db

router = APIRouter()

class SuggestionCreate(BaseModel):
    id_usuario: int
    sugerencia: str

@router.get("/")
def get_suggestions():
    """Obtiene todas las sugerencias registradas."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor(dictionary=True)
        # Ensure table exists first, mimicking original logic, though should be in migration script
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sugerencias_luxo (
                ID_Sugerencia INT AUTO_INCREMENT PRIMARY KEY,
                ID_Usuario INT NOT NULL,
                Fecha_Hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                Sugerencia TEXT NOT NULL,
                FOREIGN KEY (ID_Usuario) REFERENCES usuarios(ID_Usuario) ON DELETE CASCADE
            )
        """)
        db.commit()
        
        cursor.execute("""
            SELECT s.Fecha_Hora, u.Nombre_Completo, s.Sugerencia 
            FROM sugerencias_luxo s
            JOIN usuarios u ON s.ID_Usuario = u.ID_Usuario
            ORDER BY s.Fecha_Hora DESC
        """)
        rows = cursor.fetchall()
        return {"status": "ok", "data": rows}
    except Exception as e:
        print("ERROR CARGANDO SUGERENCIAS:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/")
def create_suggestion(sug: SuggestionCreate):
    """Crea una nueva sugerencia desde la UI del usuario."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO sugerencias_luxo (ID_Usuario, Sugerencia) VALUES (%s, %s)",
            (sug.id_usuario, sug.sugerencia)
        )
        db.commit()
        return {"status": "ok", "message": "Sugerencia enviada exitosamente"}
    except Exception as e:
        print("ERROR CREANDO SUGERENCIA:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
