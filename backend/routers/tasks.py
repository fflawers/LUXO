from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import conectar_db

router = APIRouter()

class TaskBase(BaseModel):
    categoria: int
    descripcion: str

class ToggleTask(BaseModel):
    id_usuario: int
    id_plantilla: int
    fecha: str

@router.get("/{categoria}/{usuario_id}/{fecha}")
def get_tasks(categoria: int, usuario_id: int, fecha: str):
    """Obtiene las tareas de un checklist (categoria) y marca las que el usuario ya completó en la fecha indicada."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor(dictionary=True)
        # 1. Obtener todas las plantillas (tareas) de la categoría
        cursor.execute("SELECT ID_Plantilla, Descripcion FROM plantillas_checklist WHERE Categoria = %s ORDER BY ID_Plantilla ASC", (categoria,))
        plantillas = cursor.fetchall()
        
        # 2. Obtener los IDs de plantillas que el usuario completó en esta fecha
        cursor.execute("SELECT ID_Plantilla FROM registro_checklist WHERE ID_Usuario = %s AND Fecha = %s", (usuario_id, fecha))
        completadas = {row["ID_Plantilla"] for row in cursor.fetchall()}
        
        # 3. Combinar para indicar el estado "Completado" (bool)
        resultado = []
        for p in plantillas:
            resultado.append({
                "ID_Plantilla": p["ID_Plantilla"],
                "Descripcion": p["Descripcion"],
                "Completado": p["ID_Plantilla"] in completadas
            })
            
        return {"status": "ok", "data": resultado}
    except Exception as e:
        print("ERROR OBTENIENDO CHECKLIST:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/toggle")
def toggle_task(req: ToggleTask):
    """Alterna el estado de una tarea (marcar/desmarcar) en una fecha específica para un usuario."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        # Verificar si ya está completada
        cursor.execute(
            "SELECT ID_Registro FROM registro_checklist WHERE ID_Usuario = %s AND ID_Plantilla = %s AND Fecha = %s",
            (req.id_usuario, req.id_plantilla, req.fecha)
        )
        existe = cursor.fetchone()
        
        if existe:
            # Desmarcar (Eliminar)
            cursor.execute(
                "DELETE FROM registro_checklist WHERE ID_Registro = %s",
                (existe[0],)
            )
            accion = "desmarcada"
        else:
            # Marcar (Insertar)
            import datetime
            fecha_hora = datetime.datetime.now()
            cursor.execute(
                "INSERT INTO registro_checklist (ID_Usuario, ID_Plantilla, Completado, Fecha, Fecha_Hora) VALUES (%s, %s, %s, %s, %s)",
                (req.id_usuario, req.id_plantilla, 1, req.fecha, fecha_hora)
            )
            accion = "marcada"
            
        db.commit()
        return {"status": "ok", "accion": accion}
    except Exception as e:
        print("ERROR TOGGLE TAREA:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/admin/{categoria}")
def get_tasks_admin(categoria: int):
    """Lista tareas para el panel de administrador."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT ID_Plantilla, Descripcion FROM plantillas_checklist WHERE Categoria = %s ORDER BY ID_Plantilla DESC", (categoria,))
        rows = cursor.fetchall()
        return {"status": "ok", "data": rows}
    except Exception as e:
        print("ERROR OBTENIENDO TAREAS ADMIN:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/admin")
def add_task(req: TaskBase):
    """Crea una nueva tarea (plantilla)."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute("INSERT INTO plantillas_checklist (Categoria, Descripcion) VALUES (%s, %s)", (req.categoria, req.descripcion))
        db.commit()
        return {"status": "ok", "message": "Tarea agregada correctamente"}
    except Exception as e:
        print("ERROR AGREGANDO TAREA ADMIN:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.delete("/admin/{id_plantilla}")
def delete_task(id_plantilla: int):
    """Elimina una tarea y sus registros completados."""
    db = conectar_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM registro_checklist WHERE ID_Plantilla = %s", (id_plantilla,))
        cursor.execute("DELETE FROM plantillas_checklist WHERE ID_Plantilla = %s", (id_plantilla,))
        db.commit()
        return {"status": "ok", "message": "Tarea eliminada correctamente"}
    except Exception as e:
        print("ERROR ELIMINANDO TAREA ADMIN:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
