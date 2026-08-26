import os
import json
import re
import mysql.connector
from datetime import datetime, timedelta, timezone

def get_now_mexico_city():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Mexico_City"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-6)))

def conectar_db_local():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="los4valtierra",
            database="sgh_portal"
        )
    except Exception as ex:
        print("Notice fedex_service conectar_db_local:", ex)
        return None

def crear_tabla_fedex_if_not_exists(db=None):
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
    if not db:
        return False

    try:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_general (
                clave VARCHAR(100) PRIMARY KEY,
                valor TEXT NOT NULL,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fedex_envios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                folio_rastreo VARCHAR(50) NOT NULL UNIQUE,
                tienda_origen VARCHAR(100) NOT NULL,
                tienda_destino VARCHAR(100) NOT NULL,
                peso_kg DECIMAL(6,2) DEFAULT 1.00,
                largo_cm INT DEFAULT 20,
                ancho_cm INT DEFAULT 15,
                alto_cm INT DEFAULT 10,
                valor_declarado DECIMAL(10,2) DEFAULT 4500.00,
                fecha_recoleccion DATE NULL,
                horario_recoleccion VARCHAR(50) DEFAULT '11:00 - 19:00',
                folio_recoleccion VARCHAR(50) NULL,
                estatus VARCHAR(50) DEFAULT 'EN_TRANSITO',
                pdf_url TEXT NULL,
                modo VARCHAR(20) DEFAULT 'SANDBOX',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
        return True
    except Exception as e:
        print("Notice crear_tabla_fedex_if_not_exists:", e)
        return False
    finally:
        if close_at_end and db:
            try: db.close()
            except: pass

def obtener_config_fedex(db=None):
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
    
    config = {
        "account_number": "",
        "api_key": "",
        "secret_key": "",
        "meter_number": "",
        "modo_produccion": False,
        "servicio_activo": True
    }
    
    if db:
        try:
            crear_tabla_fedex_if_not_exists(db)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT clave, valor FROM config_general WHERE clave LIKE 'fedex_%'")
            rows = cursor.fetchall()
            for r in rows:
                k = r["clave"].replace("fedex_", "")
                v = r["valor"]
                if k == "modo_produccion":
                    config["modo_produccion"] = (str(v).lower() == "true")
                elif k == "servicio_activo":
                    config["servicio_activo"] = (str(v).lower() != "false")
                elif k in config:
                    config[k] = v
        except Exception as ex:
            print("Notice obtener_config_fedex:", ex)
        finally:
            if close_at_end and db:
                try: db.close()
                except: pass
    return config

def guardar_config_fedex(account_number, api_key, secret_key, meter_number, modo_produccion=False, servicio_activo=True, db=None):
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
        
    if not db:
        return False
        
    try:
        crear_tabla_fedex_if_not_exists(db)
        cursor = db.cursor()
        data = {
            "fedex_account_number": str(account_number).strip(),
            "fedex_api_key": str(api_key).strip(),
            "fedex_secret_key": str(secret_key).strip(),
            "fedex_meter_number": str(meter_number).strip(),
            "fedex_modo_produccion": "true" if modo_produccion else "false",
            "fedex_servicio_activo": "true" if servicio_activo else "false"
        }
        for k, v in data.items():
            cursor.execute("""
                INSERT INTO config_general (clave, valor)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE valor = %s
            """, (k, v, v))
        db.commit()
        return True
    except Exception as ex:
        print("Error al guardar config_fedex:", ex)
        return False
    finally:
        if close_at_end and db:
            try: db.close()
            except: pass

def obtener_datos_tienda(nombre_tienda, db=None):
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
        
    tienda_info = {
        "nombre": nombre_tienda,
        "direccion": "Av. Principal #100",
        "colonia": "Centro",
        "ciudad": "Ciudad de México",
        "estado": "CDMX",
        "cp": "01000",
        "telefono": "5555555555",
        "email": "sucursal@sunglasshut.com"
    }
    
    if db:
        try:
            cursor = db.cursor(dictionary=True)
            t_clean = str(nombre_tienda).replace("📍", "").strip()
            cursor.execute("""
                SELECT * FROM tiendas 
                WHERE TRIM(nombre_tienda) LIKE CONCAT('%%', %s, '%%') 
                   OR TRIM(numero_tienda) LIKE CONCAT('%%', %s, '%%')
                LIMIT 1
            """, (t_clean, t_clean))
            row = cursor.fetchone()
            if row:
                tienda_info["nombre"] = row.get("nombre_tienda", nombre_tienda)
                tienda_info["direccion"] = row.get("direccion", tienda_info["direccion"])
                tienda_info["colonia"] = row.get("colonia", tienda_info["colonia"])
                tienda_info["ciudad"] = row.get("ciudad", tienda_info["ciudad"])
                tienda_info["estado"] = row.get("estado", tienda_info["estado"])
                tienda_info["cp"] = str(row.get("cp", tienda_info["cp"]))
                tienda_info["telefono"] = str(row.get("telefono", tienda_info["telefono"]))
                tienda_info["email"] = row.get("email", f"sgh_{t_clean}@luxottica.com")
        except Exception as ex:
            print("Notice obtener_datos_tienda:", ex)
        finally:
            if close_at_end and db:
                try: db.close()
                except: pass
                
    return tienda_info

def generar_guia_fedex(origen, destino, peso_kg=1.0, largo_cm=20, ancho_cm=15, alto_cm=10, valor_declarado=4500.0, fecha_recoleccion=None, db=None):
    crear_tabla_fedex_if_not_exists(db)
    cfg = obtener_config_fedex(db)
    
    if not cfg.get("servicio_activo", True):
        return {
            "status": "disabled",
            "error": "El servicio de envíos FedEx ha sido deshabilitado temporalmente por la Dirección Corporativa (Política de Ahorro)."
        }
    
    now_dt = get_now_mexico_city()
    if not fecha_recoleccion:
        fecha_recoleccion = (now_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        
    datos_origen = obtener_datos_tienda(origen, db)
    datos_destino = obtener_datos_tienda(destino, db)
    
    import random
    folio_rastreo = f"78{random.randint(1000000000, 9999999999)}"
    folio_recoleccion = f"PR-{random.randint(100000, 999999)}"
    
    pdf_url = f"https://www.fedex.com/fedextrack/?trknbr={folio_rastreo}"
    modo = "PRODUCCION" if cfg.get("modo_produccion") else "SANDBOX_SIMULADOR"
    
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
        
    if db:
        try:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO fedex_envios (
                    folio_rastreo, tienda_origen, tienda_destino, peso_kg, 
                    largo_cm, ancho_cm, alto_cm, valor_declarado, 
                    fecha_recoleccion, horario_recoleccion, folio_recoleccion, 
                    estatus, pdf_url, modo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                folio_rastreo, origen, destino, peso_kg, 
                largo_cm, ancho_cm, alto_cm, valor_declarado, 
                fecha_recoleccion, "11:00 - 19:00", folio_recoleccion, 
                "EN_RUTA_DE_RECOLECCION", pdf_url, modo
            ))
            db.commit()
        except Exception as ex:
            print("Error registrando guia en DB:", ex)
        finally:
            if close_at_end and db:
                try: db.close()
                except: pass
                
    return {
        "status": "success",
        "folio_rastreo": folio_rastreo,
        "folio_recoleccion": folio_recoleccion,
        "origen": datos_origen,
        "destino": datos_destino,
        "peso_kg": peso_kg,
        "dimensiones": f"{largo_cm}x{ancho_cm}x{alto_cm} cm",
        "horario_recoleccion": "11:00 - 19:00 hrs",
        "fecha_recoleccion": fecha_recoleccion,
        "servicio": "FedEx Nacional Económico (Terrestre)",
        "pdf_url": pdf_url,
        "modo": modo
    }

def solicitar_solo_recoleccion_fedex(tienda_origen, paquetes=1, fecha_recoleccion=None, db=None):
    crear_tabla_fedex_if_not_exists(db)
    now_dt = get_now_mexico_city()
    if not fecha_recoleccion:
        fecha_recoleccion = (now_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        
    import random
    folio_recoleccion = f"PR-{random.randint(100000, 999999)}"
    datos_origen = obtener_datos_tienda(tienda_origen, db)
    
    return {
        "status": "success",
        "folio_recoleccion": folio_recoleccion,
        "tienda_origen": datos_origen,
        "paquetes": paquetes,
        "fecha_recoleccion": fecha_recoleccion,
        "horario_recoleccion": "11:00 - 19:00 hrs"
    }

def obtener_historial_envios_fedex(limit=20, db=None):
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
        
    envios = []
    if db:
        try:
            crear_tabla_fedex_if_not_exists(db)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM fedex_envios ORDER BY id DESC LIMIT %s", (limit,))
            rows = cursor.fetchall()
            for r in rows:
                if r.get("fecha_creacion"):
                    r["fecha_creacion_str"] = r["fecha_creacion"].strftime("%Y-%m-%d %H:%M")
                envios.append(r)
        except Exception as ex:
            print("Error cargando historial fedex:", ex)
        finally:
            if close_at_end and db:
                try: db.close()
                except: pass
    return envios
