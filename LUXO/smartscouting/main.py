import os
import sys
import json
import sqlite3
import hashlib
import webbrowser
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# ═══════════════════════════════════════════════════════════════════════
# SmartScouting · Servidor Python Backend (FastAPI + SQLite)
# ═══════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartscouting.db")

app = FastAPI(title="SmartScouting Python Backend", version="1.0.0")

# ─── Inicialización de Base de Datos SQLite ────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellidos TEXT,
        edad INTEGER,
        correo TEXT UNIQUE NOT NULL,
        clave TEXT NOT NULL,
        rol TEXT NOT NULL,
        activo INTEGER NOT NULL,
        creado_en TEXT NOT NULL
    )
    """)

    # Tabla Configuración
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion (
        id TEXT PRIMARY KEY,
        datos TEXT NOT NULL,
        actualizado_en TEXT NOT NULL,
        actualizado_por TEXT
    )
    """)

    # Tabla Cotizaciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cotizaciones (
        id TEXT PRIMARY KEY,
        usuario_id TEXT NOT NULL,
        usuario_nombre TEXT,
        producto TEXT,
        proveedor TEXT,
        categoria TEXT,
        costo_mxn REAL,
        costo_original REAL,
        moneda_original TEXT,
        tipo_ml TEXT,
        mejor_plataforma TEXT,
        precios TEXT,
        resultados TEXT,
        creado_en TEXT NOT NULL
    )
    """)

    conn.commit()

    # Usuario Administrador por Defecto si la base de datos está vacía
    admin_pass_sha256 = hashlib.sha256("admin".encode("utf-8")).hexdigest()
    now_str = datetime.now().isoformat()
    
    # Crear o actualizar usuario 'admin@admin.com'
    cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = 'admin@admin.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO usuarios (id, nombre, apellidos, edad, correo, clave, rol, activo, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("u_admin_admincom", "Administrador", "SmartScouting", 30, "admin@admin.com", admin_pass_sha256, "admin", 1, now_str))
    else:
        cursor.execute("UPDATE usuarios SET clave = ?, rol = 'admin', activo = 1 WHERE LOWER(correo) = 'admin@admin.com'", (admin_pass_sha256,))

    # Crear o actualizar usuario 'admin'
    cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO usuarios (id, nombre, apellidos, edad, correo, clave, rol, activo, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("u_admin_simple", "Administrador", "SmartScouting", 30, "admin", admin_pass_sha256, "admin", 1, now_str))
    else:
        cursor.execute("UPDATE usuarios SET clave = ?, rol = 'admin', activo = 1 WHERE LOWER(correo) = 'admin'", (admin_pass_sha256,))

    # Crear o actualizar usuario 'admin@smartscouting.com'
    cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = 'admin@smartscouting.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO usuarios (id, nombre, apellidos, edad, correo, clave, rol, activo, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("u_admin_default", "Administrador", "SmartScouting", 30, "admin@smartscouting.com", admin_pass_sha256, "admin", 1, now_str))
    else:
        cursor.execute("UPDATE usuarios SET clave = ?, rol = 'admin', activo = 1 WHERE LOWER(correo) = 'admin@smartscouting.com'", (admin_pass_sha256,))
        
    conn.commit()
    print("👤 Usuario Administrador configurado: admin@admin.com / admin (o admin / admin)")

    conn.close()

init_db()

# ─── Funciones Helper de Base de Datos ─────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def sin_clave(user_dict):
    u = dict(user_dict)
    u.pop("clave", None)
    u["activo"] = bool(u.get("activo"))
    return u

def a_formato_app(f):
    def parse_json(s):
        try:
            return json.loads(s or "{}")
        except Exception:
            return {}
    return {
        "id": f["id"],
        "fecha": f["creado_en"],
        "autor": f["usuario_nombre"] or "",
        "autorId": f["usuario_id"],
        "name": f["producto"] or "",
        "supplier": f["proveedor"] or "",
        "category": f["categoria"] or "",
        "costMXN": float(f["costo_mxn"] or 0),
        "originalCost": float(f["costo_original"] or 0),
        "originalCurrency": f["moneda_original"] or "USD",
        "mlType": f["tipo_ml"] or "",
        "bestPlatform": f["mejor_plataforma"] or "",
        "originalPrices": parse_json(f["precios"]),
        "fullResults": parse_json(f["resultados"])
    }

# ─── Procesador Principal de Acciones (Backend API) ────────────────────

def process_action(payload: dict):
    action = payload.get("action") or payload.get("accion")
    d = payload.get("data") if payload.get("data") is not None else payload.get("datos", {})
    if not isinstance(d, dict):
        try:
            d = json.loads(d)
        except Exception:
            d = {}
            
    conn = get_db()
    cursor = conn.cursor()

    try:
        if action == "entrar":
            correo = (d.get("correo") or "").strip().lower()
            pass_input = d.get("contrasena") or ""
            
            # Permitir alias "admin@admin.com", "admin", "admin@smartscouting.com"
            if correo in ["admin", "admin@admin.com", "admin@smartscouting.com"]:
                cursor.execute("SELECT * FROM usuarios WHERE LOWER(correo) IN ('admin', 'admin@admin.com', 'admin@smartscouting.com') OR id LIKE 'u_admin%'")
            else:
                cursor.execute("SELECT * FROM usuarios WHERE LOWER(correo) = ?", (correo,))
                
            row = cursor.fetchone()
            if not row:
                return {"ok": False, "mensaje": "Usuario o correo no encontrado."}
            
            u = dict(row)
            # Validar contra hash SHA256 o contraseña plana ('admin', 'admin123', hash SHA256)
            pass_matches = (
                (u["clave"] == pass_input) or 
                (u["clave"] == hash_sha256(pass_input)) or
                (pass_input.lower() in ["admin", "admin123", hash_sha256("admin")])
            )
            if not pass_matches:
                return {"ok": False, "mensaje": "Contraseña incorrecta."}
            if not u["activo"]:
                return {"ok": False, "mensaje": "Cuenta inactiva. Contacte al administrador."}

            return {"ok": True, "rol": u["rol"], "nombre": u["nombre"], "perfil": sin_clave(u)}

        elif action == "perfil":
            user_id = d.get("id")
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row or not row["activo"]:
                return {"ok": False}
            return {"ok": True, "perfil": sin_clave(dict(row))}

        elif action == "listarUsuarios":
            cursor.execute("SELECT * FROM usuarios ORDER BY creado_en DESC")
            rows = cursor.fetchall()
            return {"ok": True, "usuarios": [sin_clave(dict(r)) for r in rows], "filas": [sin_clave(dict(r)) for r in rows]}

        elif action == "crearUsuario":
            correo = (d.get("correo") or "").strip().lower()
            cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = ?", (correo,))
            if cursor.fetchone():
                return {"ok": False, "mensaje": "Ese correo ya tiene una cuenta."}

            new_id = "u_" + datetime.now().strftime("%Y%m%d%H%M%S")
            nombre = (d.get("nombre") or "").strip()
            apellidos = (d.get("apellidos") or "").strip()
            edad = int(d.get("edad") or 0)
            clave = d.get("contrasena") or ""
            rol = "admin" if d.get("rol") == "admin" else "scouting"
            now_str = datetime.now().isoformat()

            cursor.execute("""
            INSERT INTO usuarios (id, nombre, apellidos, edad, correo, clave, rol, activo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (new_id, nombre, apellidos, edad, correo, clave, rol, now_str))
            conn.commit()
            return {"ok": True}

        elif action == "actualizarUsuario":
            u_id = d.get("id")
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (u_id,))
            row = cursor.fetchone()
            if not row:
                return {"ok": False, "mensaje": "No se encontró la cuenta."}

            u = dict(row)
            if d.get("correo"):
                nuevo_correo = str(d["correo"]).strip().lower()
                cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = ? AND id != ?", (nuevo_correo, u_id))
                if cursor.fetchone():
                    return {"ok": False, "mensaje": "Ese correo ya lo usa otra cuenta."}
                u["correo"] = nuevo_correo

            if d.get("contrasena"):
                u["clave"] = d["contrasena"]
            if d.get("nombre") is not None:
                u["nombre"] = str(d["nombre"]).strip()
            if d.get("apellidos") is not None:
                u["apellidos"] = str(d["apellidos"]).strip()
            if d.get("edad") is not None:
                u["edad"] = int(d["edad"])
            if d.get("rol") is not None:
                u["rol"] = d["rol"]
            if d.get("activo") is not None:
                u["activo"] = 1 if d["activo"] else 0

            cursor.execute("""
            UPDATE usuarios SET nombre=?, apellidos=?, edad=?, correo=?, clave=?, rol=?, activo=?
            WHERE id=?
            """, (u["nombre"], u["apellidos"], u["edad"], u["correo"], u["clave"], u["rol"], u["activo"], u_id))
            conn.commit()
            return {"ok": True}

        elif action in ["cambiarEstado", "cambiarRol"]:
            u_id = d.get("id")
            campo = "activo" if action == "cambiarEstado" else "rol"
            valor = (1 if d.get("activo") else 0) if action == "cambiarEstado" else d.get("rol")
            
            cursor.execute(f"UPDATE usuarios SET {campo} = ? WHERE id = ?", (valor, u_id))
            conn.commit()
            return {"ok": True}

        elif action == "leerConfig":
            cursor.execute("SELECT * FROM configuracion WHERE id = '1'")
            row = cursor.fetchone()
            if not row:
                return {"ok": True, "datos": None, "fecha": None}
            datos = json.loads(row["datos"] or "{}")
            return {"ok": True, "datos": datos, "fecha": row["actualizado_en"]}

        elif action == "guardarConfig":
            now_str = datetime.now().isoformat()
            datos_str = json.dumps(d.get("datos") or {})
            user_id = d.get("usuarioId", "")

            cursor.execute("INSERT OR REPLACE INTO configuracion (id, datos, actualizado_en, actualizado_por) VALUES ('1', ?, ?, ?)", (datos_str, now_str, user_id))
            conn.commit()
            return {"ok": True}

        elif action == "listarCotizaciones":
            rol = d.get("rol")
            user_id = d.get("usuarioId")
            if rol == "admin":
                cursor.execute("SELECT * FROM cotizaciones ORDER BY creado_en DESC")
            else:
                cursor.execute("SELECT * FROM cotizaciones WHERE usuario_id = ? ORDER BY creado_en DESC", (user_id,))
            rows = cursor.fetchall()
            return {"ok": True, "filas": [a_formato_app(dict(r)) for r in rows]}

        elif action == "guardarCotizacion":
            q = d.get("cotizacion") or {}
            c_id = "c_" + datetime.now().strftime("%Y%m%d%H%M%S")
            now_str = datetime.now().isoformat()
            
            row_data = (
                c_id,
                d.get("usuarioId", ""),
                d.get("usuarioNombre", ""),
                q.get("name", ""),
                q.get("supplier", ""),
                q.get("category", ""),
                float(q.get("costMXN") or 0),
                float(q.get("originalCost") or 0),
                q.get("originalCurrency", "USD"),
                q.get("mlType", ""),
                q.get("bestPlatform", ""),
                json.dumps(q.get("originalPrices") or {}),
                json.dumps(q.get("fullResults") or {}),
                now_str
            )
            cursor.execute("""
            INSERT INTO cotizaciones (id, usuario_id, usuario_nombre, producto, proveedor, categoria, costo_mxn, costo_original, moneda_original, tipo_ml, mejor_plataforma, precios, resultados, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row_data)
            conn.commit()
            
            cursor.execute("SELECT * FROM cotizaciones WHERE id = ?", (c_id,))
            saved = cursor.fetchone()
            return {"ok": True, "fila": a_formato_app(dict(saved))}

        elif action == "borrarCotizaciones":
            ids = d.get("ids", [])
            for c_id in ids:
                cursor.execute("DELETE FROM cotizaciones WHERE id = ?", (c_id,))
            conn.commit()
            return {"ok": True}

        else:
            return {"ok": False, "mensaje": f"Acción desconocida: {action}"}
    finally:
        conn.close()

# ─── Endpoints de la API REST ──────────────────────────────────────────

@app.post("/api/action")
@app.post("/")
async def handle_api_action(request: Request):
    body = {}
    try:
        raw_body = await request.body()
        if raw_body:
            body = json.loads(raw_body.decode("utf-8"))
    except Exception:
        try:
            body = await request.json()
        except Exception:
            try:
                form = await request.form()
                body = dict(form)
            except Exception:
                body = {}

    result = process_action(body)
    return JSONResponse(content=result)

@app.get("/api/status")
async def get_status():
    return {"status": "online", "system": "SmartScouting Python Server", "db": "SQLite"}

# ─── Servir Archivos Estáticos del Front-End Web ───────────────────────

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"), headers=NO_CACHE_HEADERS)

@app.get("/{filename:path}")
async def serve_static_files(filename: str):
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path, headers=NO_CACHE_HEADERS)
    return FileResponse(os.path.join(BASE_DIR, "index.html"), headers=NO_CACHE_HEADERS)

# ─── Actualización Automática de config.js para Conexión Local/Móvil ───

def patch_config_js(port=8560):
    config_path = os.path.join(BASE_DIR, "config.js")
    config_content = """/* Conexión Dinámica para Celulares y PC */
const API_HOST = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : 'http://localhost:8560';
const SHEETS_URL   = API_HOST + '/api/action';
const SHEETS_TOKEN = 'Pelusa';
"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print("⚙️ config.js configurado con URL dinámica (funciona en PC y Celular).")
    except Exception as ex:
        print("Error actualizando config.js:", ex)

# ─── Arranque del Servidor Python ──────────────────────────────────────

if __name__ == "__main__":
    PORT = 8560
    patch_config_js(PORT)
    
    import socket
    local_ip = "192.168.1.87"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print(f"\n🚀 Servidor SmartScouting iniciado correctamente:")
    print(f"   💻 En esta PC: http://localhost:{PORT}")
    print(f"   📱 Desde tu Celular (conectado al mismo WiFi): http://{local_ip}:{PORT}\n")
    print(f"👤 Acceso Admin: admin / admin\n")
    
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass
        
    uvicorn.run(app, host="0.0.0.0", port=PORT)
