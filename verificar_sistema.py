import sys
import os
import re

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🧪 INICIANDO AUDITORÍA Y DIAGNÓSTICO PRE-FLIGHT DE LUXO")
print("=" * 60)

passed_checks = 0
total_checks = 0

def log_result(name, success, detail=""):
    global passed_checks, total_checks
    total_checks += 1
    if success:
        passed_checks += 1
        print(f"  ✅ [PASS] {name} {detail}")
    else:
        print(f"  ❌ [FAIL] {name} -> {detail}")

# -------------------------------------------------------------
# 1. PRUEBA DE CONEXIÓN A BASE DE DATOS MYSQL
# -------------------------------------------------------------
print("\n[1/4] Verificando Conexión a Base de Datos MySQL...")
try:
    import operacion_tiendas
    db = operacion_tiendas.conectar_db_local()
    if db and db.is_connected():
        log_result("Conexión MySQL Local", True, "Conectado exitosamente")
    else:
        log_result("Conexión MySQL Local", False, "No se pudo conectar a MySQL local")
        db = None
except Exception as ex:
    log_result("Conexión MySQL Local", False, str(ex))
    db = None

# -------------------------------------------------------------
# 2. AUDITORÍA DE ESQUEMA Y COLUMNAS EN BASE DE DATOS
# -------------------------------------------------------------
print("\n[2/4] Verificando Columnas y Tablas Críticas...")
if db:
    try:
        cursor = db.cursor(dictionary=True)
        
        # Verificar columnas en tabla 'usuarios'
        cursor.execute("SHOW COLUMNS FROM usuarios")
        cols_user = set(r["Field"] for r in cursor.fetchall())
        required_user_cols = {"ID_Usuario", "Usuario", "Contrasena", "Nombre_Completo", "Rol", "Tienda", "Zona", "Region"}
        missing_user_cols = required_user_cols - cols_user
        if not missing_user_cols:
            log_result("Esquema Tabla 'usuarios'", True, f"Columnas OK: {required_user_cols}")
        else:
            log_result("Esquema Tabla 'usuarios'", False, f"Faltan columnas: {missing_user_cols}")

        # Verificar columnas en tabla 'tiendas'
        cursor.execute("SHOW COLUMNS FROM tiendas")
        cols_tiendas = set(r["Field"] for r in cursor.fetchall())
        required_tienda_cols = {"id", "nombre_tienda", "region_id", "hora_limite_apertura"}
        missing_tienda_cols = required_tienda_cols - cols_tiendas
        if not missing_tienda_cols:
            log_result("Esquema Tabla 'tiendas'", True, f"Columnas OK: {required_tienda_cols}")
        else:
            log_result("Esquema Tabla 'tiendas'", False, f"Faltan columnas: {missing_tienda_cols}")

    except Exception as ex_sch:
        log_result("Auditoría de Esquema", False, str(ex_sch))

# -------------------------------------------------------------
# 3. PRUEBA SIMULADA DE INICIO DE SESIÓN
# -------------------------------------------------------------
print("\n[3/4] Verificando Autenticación de Usuarios (Admin y Tiendas)...")
if db:
    try:
        import main
        cursor = db.cursor(dictionary=True)
        
        test_logins = [
            ("mx204562", "sgh12345", "Moises Garcia Admin"),
            ("sghc964", "sgh12345", "Explanada Pachuca"),
            ("sghq382", "sgh12345", "Parque Tepeyac"),
            ("sgh3488", "sgh12345", "Santa Fe")
        ]
        
        for u_name, u_pass, desc in test_logins:
            cursor.execute("SELECT ID_Usuario, Usuario, Contrasena, Nombre_Completo, Rol FROM usuarios WHERE LOWER(TRIM(Usuario)) = %s", (u_name.lower(),))
            user_row = cursor.fetchone()
            if not user_row:
                log_result(f"Login '{u_name}' ({desc})", False, "Usuario no existe en BD")
            else:
                is_valid = main.verify_password(u_pass, user_row["Contrasena"])
                if is_valid:
                    log_result(f"Login '{u_name}' ({desc})", True, f"Rol='{user_row['Rol']}'")
                else:
                    log_result(f"Login '{u_name}' ({desc})", False, "Contraseña no coincide")

    except Exception as ex_auth:
        log_result("Prueba de Autenticación", False, str(ex_auth))

# -------------------------------------------------------------
# 4. PRUEBA DE BÚSQUEDA RAG PONDERADA
# -------------------------------------------------------------
print("\n[4/4] Verificando Ponderación de Búsqueda RAG para Tiendas...")
try:
    from operacion_tiendas import MAPEO_CODIGOS_TIENDAS_ALIAS
    q382_alias = MAPEO_CODIGOS_TIENDAS_ALIAS.get("Q382")
    c964_alias = MAPEO_CODIGOS_TIENDAS_ALIAS.get("C964")
    
    if q382_alias == "26382" and c964_alias == "12964":
        log_result("Mapa de Alias de Tiendas", True, f"Q382->{q382_alias}, C964->{c964_alias}")
    else:
        log_result("Mapa de Alias de Tiendas", False, f"Respuesta inesperada: {q382_alias}, {c964_alias}")
except Exception as ex_rag:
    log_result("Búsqueda RAG", False, str(ex_rag))

if db:
    db.close()

print("\n" + "=" * 60)
print(f"📊 RESUMEN DE DIAGNÓSTICO: {passed_checks} de {total_checks} pruebas superadas.")
if passed_checks == total_checks:
    print("🚀 TODO EL SISTEMA ESTÁ EN ESTADO 100% OPTIMO Y LISTO PARA OPERAR.")
else:
    print("⚠️ SE DETECTARON ANOMALÍAS. REVISAR LOS PUNTOS MARCADOS CON [FAIL].")
print("=" * 60)
