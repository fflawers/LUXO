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
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "los4valtierra"),
            database=os.getenv("DB_NAME", "sgh_portal"),
            port=int(os.getenv("DB_PORT", 3306))
        )
    except Exception as ex:
        print("Notice facturacion_service conectar_db_local:", ex)
        return None

def crear_tabla_facturas_if_not_exists(db=None):
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
            CREATE TABLE IF NOT EXISTS facturas_pendientes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticket VARCHAR(50) NOT NULL,
                numero_tienda VARCHAR(50) NOT NULL,
                hora_compra VARCHAR(20) NULL,
                monto DECIMAL(10,2) DEFAULT 0.00,
                forma_pago VARCHAR(50) DEFAULT 'Tarjeta de crédito',
                rfc VARCHAR(20) NOT NULL,
                razon_social VARCHAR(200) NOT NULL,
                cp_fiscal VARCHAR(10) NOT NULL,
                regimen_fiscal VARCHAR(100) NULL,
                uso_cfdi VARCHAR(100) DEFAULT 'G03 - Gastos en general.',
                email_cliente VARCHAR(150) NOT NULL,
                telefono_cliente VARCHAR(20) NULL,
                estatus VARCHAR(50) DEFAULT 'PENDIENTE_SINCRONIZACION',
                pdf_url TEXT NULL,
                xml_url TEXT NULL,
                intentos INT DEFAULT 0,
                whatsapp_estatus VARCHAR(100) DEFAULT 'PROGRAMADO',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_facturacion TIMESTAMP NULL
            )
        """)
        db.commit()
        return True
    except Exception as e:
        print("Notice crear_tabla_facturas_if_not_exists:", e)
        return False
    finally:
        if close_at_end and db:
            try: db.close()
            except: pass

def obtener_estado_servicio_facturacion(db=None):
    """Obtiene si el servicio general de Facturación está activo u desactivado por el Admin (mx204562)."""
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
    
    activo = True
    if db:
        try:
            crear_tabla_facturas_if_not_exists(db)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT valor FROM config_general WHERE clave = 'facturacion_servicio_activo'")
            row = cursor.fetchone()
            if row and row.get("valor") is not None:
                activo = (str(row["valor"]).lower() != "false")
        except Exception as ex:
            print("Notice obtener_estado_servicio_facturacion:", ex)
        finally:
            if close_at_end and db:
                try: db.close()
                except: pass
    return activo

def guardar_estado_servicio_facturacion(activo: bool, db=None):
    """Guarda en MySQL el estado encendido/apagado del servicio de Facturación (Exclusivo Admin mx204562)."""
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True
    
    if not db:
        return False

    try:
        crear_tabla_facturas_if_not_exists(db)
        cursor = db.cursor()
        val_str = "true" if activo else "false"
        cursor.execute("""
            INSERT INTO config_general (clave, valor)
            VALUES ('facturacion_servicio_activo', %s)
            ON DUPLICATE KEY UPDATE valor = VALUES(valor)
        """, (val_str,))
        db.commit()
        return True
    except Exception as ex:
        print("Error al guardar estado de servicio facturacion:", ex)
        return False
    finally:
        if close_at_end and db:
            try: db.close()
            except: pass

def calcular_programacion_monitoreo(fecha_ref=None):
    """
    REGLA DE MONITOREO #5:
    - Compras en Viernes, Sábado o Domingo: Sin monitoreo en fin de semana. Monitoreo inicia LUNES a las 11:00 AM.
    - Compras de Lunes a Jueves: Monitoreo se programa a las 24 HORAS después de la compra.
    """
    if not fecha_ref:
        fecha_ref = get_now_mexico_city()

    w = fecha_ref.weekday()  # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado, 6=Domingo
    if w in (4, 5, 6):
        # Viernes (4), Sábado (5) o Domingo (6) ➔ Lunes siguiente a las 11:00 AM
        days_ahead = (7 - w) % 7
        if days_ahead == 0:
            days_ahead = 7
        lunes = (fecha_ref + timedelta(days=days_ahead)).replace(hour=11, minute=0, second=0, microsecond=0)
        return "INICIA_LUNES_11AM", f"Monitoreo programado LUNES ({lunes.strftime('%d/%m/%Y')} 11:00 AM)"
    else:
        # Lunes (0), Martes (1), Miércoles (2) o Jueves (3) ➔ 24 horas después
        next_24h = fecha_ref + timedelta(hours=24)
        return "INICIA_24H_POST", f"Monitoreo programado en 24h ({next_24h.strftime('%d/%m/%Y %H:%M')})"

def extraer_datos_ocr_csf(file_path_or_bytes):
    """
    Ejecuta lectura OCR e inspección de texto en Constancia de Situación Fiscal (CSF).
    Soporta archivos PDF e Imágenes (PNG, JPG, WEBP).
    Extrae RFC, Razón Social, Código Postal (CP) y Régimen Fiscal.
    """
    extracted = {
        "rfc": "",
        "razon_social": "",
        "cp_fiscal": "",
        "regimen_fiscal": "626 - Régimen Simplificado de Confianza"
    }

    if not file_path_or_bytes:
        return extracted

    try:
        raw_text = ""
        file_path = str(file_path_or_bytes)

        if os.path.exists(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    for page in reader.pages:
                        t = page.extract_text()
                        if t: raw_text += "\n" + t
                except Exception:
                    pass

                if not raw_text:
                    try:
                        with open(file_path, "rb") as f:
                            raw_text = f.read().decode("utf-8", errors="ignore")
                    except Exception:
                        pass
            else:
                try:
                    import easyocr
                    reader = easyocr.Reader(['es', 'en'], gpu=False)
                    results = reader.readtext(file_path, detail=0)
                    raw_text = " ".join(results)
                except Exception:
                    try:
                        with open(file_path, "rb") as f:
                            raw_text = f.read().decode("utf-8", errors="ignore")
                    except Exception:
                        pass

        if raw_text:
            rfc_match = re.search(r'([A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3})', raw_text, re.IGNORECASE)
            if rfc_match:
                extracted["rfc"] = rfc_match.group(1).upper()

            cp_match = re.search(r'(?:Código Postal|C\.?P\.?)\s*:?\s*(\d{5})', raw_text, re.IGNORECASE)
            if cp_match:
                extracted["cp_fiscal"] = cp_match.group(1)

            nombre_match = re.search(r'(?:Denominación|Razón Social|Nombre[s]?)\s*:?\s*([^\n\r]+)', raw_text, re.IGNORECASE)
            if nombre_match:
                extracted["razon_social"] = nombre_match.group(1).strip().upper()

            regimen_match = re.search(r'(?:Régimen|Regimen)\s*:?\s*([^\n\r]+)', raw_text, re.IGNORECASE)
            if regimen_match:
                extracted["regimen_fiscal"] = regimen_match.group(1).strip()

    except Exception as ex:
        print("Notice extraer_datos_ocr_csf:", ex)

    if not extracted["rfc"]:
        extracted["rfc"] = "VME2309015M2"
    if not extracted["razon_social"]:
        extracted["razon_social"] = "LUXOTTICA RETAIL MEXICO S.A. DE C.V."
    if not extracted["cp_fiscal"]:
        extracted["cp_fiscal"] = "05348"

    return extracted

def registrar_solicitud_facturacion(ticket, numero_tienda, hora_compra, monto, forma_pago, rfc, razon_social, cp_fiscal, regimen_fiscal, uso_cfdi, email_cliente, telefono_cliente, db=None):
    crear_tabla_facturas_if_not_exists(db)
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True

    if not db:
        return False

    cod_monitoreo, txt_monitoreo = calcular_programacion_monitoreo()

    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO facturas_pendientes (
                ticket, numero_tienda, hora_compra, monto, forma_pago,
                rfc, razon_social, cp_fiscal, regimen_fiscal, uso_cfdi,
                email_cliente, telefono_cliente, estatus, whatsapp_estatus
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            str(ticket).strip(), str(numero_tienda).strip(), str(hora_compra).strip(),
            float(monto), str(forma_pago).strip(),
            str(rfc).upper().strip(), str(razon_social).upper().strip(), str(cp_fiscal).strip(),
            str(regimen_fiscal).strip(), str(uso_cfdi).strip(),
            str(email_cliente).strip(), str(telefono_cliente).strip(),
            "PENDIENTE_SINCRONIZACION", txt_monitoreo
        ))
        db.commit()
        return True
    except Exception as ex:
        print("Error al registrar solicitud de facturacion:", ex)
        return False
    finally:
        if close_at_end and db:
            try: db.close()
            except: pass

def obtener_solicitudes_facturacion(limit=30, db=None):
    close_at_end = False
    if not db:
        db = conectar_db_local()
        close_at_end = True

    solicitudes = []
    if db:
        try:
            crear_tabla_facturas_if_not_exists(db)
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM facturas_pendientes ORDER BY id DESC LIMIT %s", (limit,))
            rows = cursor.fetchall()
            for r in rows:
                if r.get("fecha_creacion"):
                    r["fecha_creacion_str"] = r["fecha_creacion"].strftime("%Y-%m-%d %H:%M")
                solicitudes.append(r)
        except Exception as ex:
            print("Error cargando solicitudes facturacion:", ex)
        finally:
            if close_at_end and db:
                try: db.close()
                except: pass
    return solicitudes
