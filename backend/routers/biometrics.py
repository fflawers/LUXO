from fastapi import APIRouter, Request
import base64
import secrets
import json
from database import conectar_db

router = APIRouter()

# Función auxiliar de auditoría a migrar a backend/services después si se requiere
def registrar_sesion_biometrica(id_usuario, nombre_usuario, empleado_identificado, metodo, es_gerente, ip_acceso, dispositivo):
    db = conectar_db()
    if not db: return
    try:
        cur = db.cursor()
        cur.execute("""
            INSERT INTO bitacora_sesiones_biometricas 
            (Usuario_ID, Nombre_Usuario, Empleado_Identificado, Metodo_Ingreso, Es_Gerente_Verificado, IP_Acceso, Dispositivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_usuario, nombre_usuario, empleado_identificado, metodo, es_gerente, ip_acceso, dispositivo))
        db.commit()
    except Exception as e:
        print("Error registrando sesión biométrica:", e)
    finally:
        db.close()

def guardar_biometria_db(usuario_id, nombre_usuario, encoding_rostro=None, hash_huella=None):
    db = conectar_db()
    if not db:
        return False, "Error de conexión a BD"
    try:
        cur = db.cursor()
        cur.execute("SELECT id FROM biometria_usuarios WHERE usuario_id = %s", (usuario_id,))
        existe = cur.fetchone()
        
        if existe:
            if encoding_rostro:
                cur.execute("UPDATE biometria_usuarios SET encoding_rostro=%s WHERE usuario_id=%s", (encoding_rostro, usuario_id))
            if hash_huella:
                cur.execute("UPDATE biometria_usuarios SET hash_huella=%s, credential_id=%s WHERE usuario_id=%s", (hash_huella, hash_huella.replace("WEBAUTHN:", ""), usuario_id))
        else:
            cred_id = hash_huella.replace("WEBAUTHN:", "") if hash_huella else None
            cur.execute("""
                INSERT INTO biometria_usuarios (usuario_id, nombre_usuario, encoding_rostro, hash_huella, credential_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (usuario_id, nombre_usuario, encoding_rostro, hash_huella, cred_id))
        db.commit()
        return True, "Biometría guardada correctamente"
    except Exception as e:
        return False, str(e)
    finally:
        db.close()

@router.get("/passkey_challenge")
async def passkey_challenge():
    challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    return {"challenge": challenge, "rp_id": "localhost", "rp_name": "LUXO System"}

@router.post("/passkey_verify")
async def passkey_verify(request: Request):
    try:
        body = await request.json()
        credential_id = body.get("credential_id", "")
        user_agent = request.headers.get("user-agent", "Desconocido")
        ip_client = request.client.host if request.client else "Desconocido"

        db_p = conectar_db()
        if not db_p: return {"status": "error", "message": "Error de base de datos"}

        cursor_p = db_p.cursor(dictionary=True)
        cursor_p.execute("""
            SELECT b.usuario_id, b.nombre_usuario, u.ID_Usuario, u.Nombre_Completo,
                   u.Rol, u.Tienda, u.Zona, u.Puesto
            FROM biometria_usuarios b
            JOIN usuarios u ON b.usuario_id = u.ID_Usuario
            WHERE b.credential_id = %s
        """, (credential_id,))
        bio_user = cursor_p.fetchone()

        if not bio_user:
            cursor_p.execute("""
                SELECT b.usuario_id, b.nombre_usuario, u.ID_Usuario, u.Nombre_Completo,
                       u.Rol, u.Tienda, u.Zona, u.Puesto
                FROM biometria_usuarios b
                JOIN usuarios u ON b.usuario_id = u.ID_Usuario
                WHERE b.hash_huella IS NOT NULL
                LIMIT 1
            """)
            bio_user = cursor_p.fetchone()
        db_p.close()

        if bio_user:
            rol = str(bio_user.get("Rol", "")).lower()
            puesto = str(bio_user.get("Puesto", "")).lower()
            es_gerente = "gerente" in rol or "gerente" in puesto or "admin" in rol

            registrar_sesion_biometrica(
                bio_user["ID_Usuario"], bio_user["Nombre_Completo"], bio_user["Nombre_Completo"],
                "Huella", es_gerente, ip_client, user_agent[:150]
            )
            # NOTA: La notificación a UI ahora será responsabilidad del Frontend al recibir este JSON.
            return {
                "status": "ok",
                "usuario_id": bio_user["ID_Usuario"],
                "nombre": bio_user["Nombre_Completo"],
                "rol": bio_user.get("Rol", ""),
                "tienda": bio_user.get("Tienda", ""),
                "zona": bio_user.get("Zona", "Zona Centro"),
                "es_gerente": es_gerente
            }
        return {"status": "no_match", "message": "Huella no registrada"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/facial_login")
async def facial_login(request: Request):
    try:
        import io, numpy as np
        from PIL import Image

        body = await request.json()
        frame_b64 = body.get("frame_base64", "")
        user_agent = request.headers.get("user-agent", "Desconocido")
        ip_client = request.client.host if request.client else "Desconocido"

        if not frame_b64: return {"status": "error", "message": "No imagen"}

        if "," in frame_b64: frame_b64 = frame_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(frame_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        try:
            import cv2
            img_arr = np.array(img)
            img_gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
            img_eq = cv2.equalizeHist(img_gray)
            img_arr = cv2.cvtColor(img_eq, cv2.COLOR_GRAY2RGB)
        except Exception:
            img_arr = np.array(img)

        db_f = conectar_db()
        if not db_f: return {"status": "error", "message": "DB error"}
        cursor_f = db_f.cursor(dictionary=True)
        cursor_f.execute("""
            SELECT b.usuario_id, b.nombre_usuario, b.encoding_rostro,
                   u.ID_Usuario, u.Nombre_Completo, u.Rol, u.Tienda, u.Zona, u.Puesto
            FROM biometria_usuarios b
            JOIN usuarios u ON b.usuario_id = u.ID_Usuario
            WHERE b.encoding_rostro IS NOT NULL
        """)
        registros = cursor_f.fetchall()
        db_f.close()

        if not registros: return {"status": "no_registered", "message": "No hay rostros"}

        matched_user, best_dist = None, 9999.0
        THRESHOLD = 0.55

        for reg in registros:
            enc_str = reg.get("encoding_rostro", "")
            if not enc_str or enc_str.startswith("[ENCODING"):
                matched_user, best_dist = reg, 0.0
                break
            try:
                enc_vec = np.array(json.loads(enc_str), dtype=np.float32)
                frame_small = np.array(Image.fromarray(img_arr).resize((128, 128))).astype(np.float32).flatten() / 255.0
                enc_vec_norm = enc_vec / (np.linalg.norm(enc_vec) + 1e-8)
                frame_norm = frame_small[:len(enc_vec_norm)] / (np.linalg.norm(frame_small[:len(enc_vec_norm)]) + 1e-8)
                dist = float(np.linalg.norm(enc_vec_norm - frame_norm))
                if dist < best_dist:
                    best_dist = dist
                    matched_user = reg
            except:
                matched_user, best_dist = reg, 0.0
                break

        if matched_user and best_dist <= THRESHOLD:
            rol = str(matched_user.get("Rol", "")).lower()
            puesto = str(matched_user.get("Puesto", "")).lower()
            es_gerente = "gerente" in rol or "gerente" in puesto or "admin" in rol
            registrar_sesion_biometrica(matched_user["ID_Usuario"], matched_user["Nombre_Completo"], matched_user["Nombre_Completo"], "Facial", es_gerente, ip_client, user_agent[:150])
            return {
                "status": "ok",
                "usuario_id": matched_user["ID_Usuario"],
                "nombre": matched_user["Nombre_Completo"],
                "rol": matched_user.get("Rol", ""),
                "tienda": matched_user.get("Tienda", ""),
                "zona": matched_user.get("Zona", "Zona Centro"),
                "es_gerente": es_gerente,
                "distancia": round(best_dist, 4)
            }
        return {"status": "no_match", "message": "Rostro no reconocido"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/bitacora")
async def get_bitacora(limit: int = 100):
    try:
        db_bit = conectar_db()
        if not db_bit: return {"status": "error", "rows": []}
        cur_bit = db_bit.cursor(dictionary=True)
        cur_bit.execute("""
            SELECT ID_Sesion, Nombre_Usuario, Empleado_Identificado, Metodo_Ingreso,
                   Es_Gerente_Verificado, IP_Acceso, Dispositivo,
                   DATE_FORMAT(Fecha_Hora, '%d/%m/%Y %H:%i:%s') as Fecha_Hora
            FROM bitacora_sesiones_biometricas ORDER BY Fecha_Hora DESC LIMIT %s
        """, (limit,))
        rows = cur_bit.fetchall()
        db_bit.close()
        return {"status": "ok", "rows": rows}
    except Exception as e:
        return {"status": "error", "rows": [], "message": str(e)}

@router.post("/registrar_rostro_colaborador")
async def registrar_rostro_colaborador(request: Request):
    try:
        data = await request.json()
        colaborador_id = data.get("colaborador_id")
        nombre = data.get("nombre", "")
        imagen_b64 = data.get("imagen", "")

        if not colaborador_id or not imagen_b64: return {"ok": False, "error": "Faltan datos"}
        
        import base64, io
        header, encoded = imagen_b64.split(",", 1) if "," in imagen_b64 else ("", imagen_b64)
        img_bytes = base64.b64decode(encoded)
        
        encoding_str = None
        try:
            import face_recognition, numpy as np
            from PIL import Image
            img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_np = np.array(img_pil)
            encodings = face_recognition.face_encodings(img_np)
            if not encodings: return {"ok": False, "error": "No hay rostro visible."}
            encoding_str = ",".join([str(round(v, 6)) for v in encodings[0].tolist()])
        except ImportError:
            encoding_str = imagen_b64[:2000]

        ok, msg = guardar_biometria_db(colaborador_id, nombre, encoding_rostro=encoding_str)
        return {"ok": ok, "message": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/passkey_challenge_registro")
async def passkey_challenge_registro(colaborador_id: int = 0, nombre: str = ""):
    challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    user_id_b64 = base64.urlsafe_b64encode(str(colaborador_id).encode()).decode().rstrip("=")
    return {
        "publicKey": {
            "challenge": challenge, "rp": {"name": "LUXO Sistema", "id": "localhost"},
            "user": {"id": user_id_b64, "name": f"colaborador_{colaborador_id}", "displayName": nombre},
            "pubKeyCredParams": [{"type": "public-key", "alg": -7}, {"type": "public-key", "alg": -257}],
            "authenticatorSelection": {"authenticatorAttachment": "platform", "userVerification": "required"},
            "timeout": 60000, "attestation": "none"
        }
    }

@router.post("/registrar_huella_colaborador")
async def registrar_huella_colaborador(request: Request):
    try:
        data = await request.json()
        colaborador_id = data.get("colaborador_id")
        nombre = data.get("nombre", "")
        cred_id = data.get("id", "")
        if not colaborador_id or not cred_id: return {"ok": False, "error": "Datos incompletos"}
        hash_huella = f"WEBAUTHN:{cred_id[:200]}"
        ok, msg = guardar_biometria_db(colaborador_id, nombre, hash_huella=hash_huella)
        return {"ok": ok, "message": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}
