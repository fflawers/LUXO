from fastapi import APIRouter, Request
from database import conectar_db
import bcrypt

router = APIRouter()

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, stored_password: str) -> bool:
    if not stored_password: return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8'))
    except ValueError:
        return plain_password == stored_password

@router.post("/login")
async def login(request: Request):
    try:
        body = await request.json()
        user = body.get("user")
        password = body.get("password")
        
        if not user or not password:
            return {"status": "error", "message": "Faltan credenciales"}
            
        db = conectar_db()
        if not db:
            return {"status": "error", "message": "Error Base de Datos"}
            
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT ID_Usuario, Nombre_Completo, Rol, Tienda, Zona, Contrasena
            FROM usuarios WHERE Usuario = %s
        """, (user,))
        res = cursor.fetchone()
        
        if res and verify_password(password, res.get("Contrasena", "")):
            stored_pass = str(res.get("Contrasena") or "")
            if not (stored_pass.startswith("$2b$") or stored_pass.startswith("$2a$")):
                try:
                    new_hash = hash_password(password)
                    cursor.execute("UPDATE usuarios SET Contrasena = %s WHERE ID_Usuario = %s", (new_hash, res["ID_Usuario"]))
                    db.commit()
                except Exception as e:
                    print("Error actualizando hash:", e)

            u_id = res["ID_Usuario"]
            nombre = res["Nombre_Completo"]
            rol = str(res["Rol"]).lower()
            es_gerente = "admin" in rol or "gerente" in rol
            
            ip_client = request.client.host if request.client else "Desconocido"
            user_agent = request.headers.get("user-agent", "Desconocido")
            
            # Log session asynchronously or inline
            try:
                import requests as req
                city = "Localhost"
                country = "Local / Desarrollo"
                if ip_client not in ("127.0.0.1", "::1", "localhost", "Desconocido"):
                    try:
                        resp_ip = req.get(f"http://ip-api.com/json/{ip_client}", timeout=2)
                        if resp_ip.status_code == 200:
                            data_ip = resp_ip.json()
                            if data_ip.get("status") == "success":
                                city = data_ip.get("city", "Desconocido")
                                country = data_ip.get("country", "Desconocido")
                    except: pass
                
                cursor.execute(
                    "INSERT INTO sesiones (ID_Usuario, Direccion_IP, Ubicacion_Ciudad, Ubicacion_Pais) VALUES (%s, %s, %s, %s)",
                    (u_id, ip_client, city, country)
                )
                cursor.execute("""
                    INSERT INTO bitacora_sesiones_biometricas
                        (ID_Usuario, Nombre_Usuario, Empleado_Identificado, Metodo_Ingreso, Es_Gerente_Verificado, IP_Acceso, Dispositivo)
                    VALUES (%s, %s, %s, 'Contrasena', %s, %s, %s)
                """, (u_id, nombre, nombre, es_gerente, ip_client, user_agent[:150]))
                db.commit()
            except Exception as e_log:
                print("Error registrando log de sesión:", e_log)

            db.close()
            return {
                "status": "ok",
                "usuario_id": res["ID_Usuario"],
                "usuario": user,
                "nombre": res["Nombre_Completo"],
                "rol": res["Rol"],
                "tienda": res.get("Tienda"),
                "zona": res.get("Zona")
            }
        
        db.close()
        return {"status": "error", "message": "Credenciales inválidas"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
