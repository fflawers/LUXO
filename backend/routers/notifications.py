from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conectar_db

router = APIRouter()

class NotificationBase(BaseModel):
    usuario_id: int
    titulo: str
    mensaje: str
    tipo: str = "general"

@router.get("/{user_id}")
def get_notifications(user_id: int):
    """Retorna la lista de notificaciones recientes para un usuario (máximo 15)."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT ID_Notificacion, Titulo, Mensaje, Fecha_Hora, Leida, Tipo FROM notificaciones WHERE ID_Usuario = %s ORDER BY ID_Notificacion DESC LIMIT 15",
            (user_id,)
        )
        rows = cursor.fetchall()
        return {"status": "ok", "data": rows}
    except Exception as e:
        print("ERROR CARGANDO NOTIFICACIONES:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/{user_id}/unread")
def get_unread_count(user_id: int):
    """Retorna el conteo de notificaciones no leídas para un usuario."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM notificaciones WHERE ID_Usuario = %s AND Leida = 0",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        return {"status": "ok", "count": count}
    except Exception as e:
        print("ERROR OBTENIENDO SIN LEER:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/{user_id}/read-all")
def mark_all_as_read(user_id: int):
    """Marca todas las notificaciones de un usuario como leídas."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE notificaciones SET Leida = 1 WHERE ID_Usuario = %s AND Leida = 0",
            (user_id,)
        )
        db.commit()
        return {"status": "ok", "message": "Notificaciones marcadas como leídas"}
    except Exception as e:
        print("ERROR MARCANDO LEIDAS:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/")
def create_notification(noti: NotificationBase):
    """Inserta una nueva notificación."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO notificaciones (ID_Usuario, Titulo, Mensaje, Tipo) VALUES (%s, %s, %s, %s)",
            (noti.usuario_id, noti.titulo, noti.mensaje, noti.tipo)
        )
        db.commit()
        return {"status": "ok", "message": "Notificación creada"}
    except Exception as e:
        print("ERROR CREANDO NOTIFICACION:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/role/{rol}")
def create_notification_role(noti: NotificationBase, rol: str):
    """Crea una notificación para todos los usuarios con un rol determinado."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Rol = %s", (rol,))
        users = cursor.fetchall()
        for u in users:
            cursor.execute(
                "INSERT INTO notificaciones (ID_Usuario, Titulo, Mensaje, Tipo) VALUES (%s, %s, %s, %s)",
                (u[0], noti.titulo, noti.mensaje, noti.tipo)
            )
        db.commit()
        return {"status": "ok", "message": f"Notificaciones enviadas al rol {rol}"}
    except Exception as e:
        print("ERROR CREANDO NOTIFICACION ROL:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/zone/{zona}")
def create_notification_zone(noti: NotificationBase, zona: str):
    """Crea una notificación para todos los gerentes de una zona en específico."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Rol = 'Gerente' AND (Zona = %s OR %s = 'Todas')", (zona, zona))
        users = cursor.fetchall()
        for u in users:
            cursor.execute(
                "INSERT INTO notificaciones (ID_Usuario, Titulo, Mensaje, Tipo) VALUES (%s, %s, %s, %s)",
                (u[0], noti.titulo, noti.mensaje, noti.tipo)
            )
        db.commit()
        return {"status": "ok", "message": f"Notificaciones enviadas a la zona {zona}"}
    except Exception as e:
        print("ERROR CREANDO NOTIFICACION ZONA:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
