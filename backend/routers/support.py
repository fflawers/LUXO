from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conectar_db

router = APIRouter()

class TicketCreate(BaseModel):
    id_usuario: int
    detalle_problema: str

class TicketResolve(BaseModel):
    solucion: str

@router.get("/")
def get_tickets():
    """Obtiene todos los tickets de soporte."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.ID_Ticket, t.Fecha_Hora, u.Nombre_Completo, t.Detalle_Problema, t.Respuesta_Soporte, t.Estatus
            FROM tickets_soporte t
            JOIN usuarios u ON t.ID_Usuario = u.ID_Usuario
            ORDER BY t.Fecha_Hora DESC
        """)
        rows = cursor.fetchall()
        return {"status": "ok", "data": rows}
    except Exception as e:
        print("ERROR CARGANDO TICKETS:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/")
def create_ticket(ticket: TicketCreate):
    """Crea un nuevo ticket de soporte desde la UI del usuario."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tickets_soporte (ID_Usuario, Detalle_Problema) VALUES (%s, %s)",
            (ticket.id_usuario, ticket.detalle_problema)
        )
        db.commit()
        return {"status": "ok", "message": "Ticket levantado exitosamente"}
    except Exception as e:
        print("ERROR CREANDO TICKET:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/{ticket_id}/resolve")
def resolve_ticket(ticket_id: int, req: TicketResolve):
    """Marca un ticket como resuelto y le asocia la solución del soporte."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE tickets_soporte 
            SET Estatus = 'Resuelto', Respuesta_Soporte = %s 
            WHERE ID_Ticket = %s
        """, (req.solucion, ticket_id))
        db.commit()
        return {"status": "ok", "message": "Ticket resuelto con éxito."}
    except Exception as e:
        print("ERROR RESOLVER TICKET:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
