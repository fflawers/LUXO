# -*- coding: utf-8 -*-
"""
COTIZADOR POS INTELIGENTE LUXO / SUNGLASS HUT
Motor matemático (Outlet / Línea / Promos Seleccionadas / Buen Fin / MSI),
importador de precios MIM (StockSummary_Details), lectura solo-SELECT de
descuentos_semanales, cotizaciones guardadas en MySQL y PDF vectorial multipágina.
"""

import os
import re
import json
import uuid
import math
from datetime import datetime, timedelta, timezone

import openpyxl
import mysql.connector
import fitz

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_now_mexico_city():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Mexico_City"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-6)))


def conectar_db():
    try:
        import sys
        main_mod = sys.modules.get("main")
        if main_mod and hasattr(main_mod, "conectar_db"):
            db = main_mod.conectar_db()
            if db and db.is_connected():
                return db
    except Exception:
        pass
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "los4valtierra"),
            database=os.getenv("DB_NAME", "sgh_portal"),
            port=int(os.getenv("DB_PORT", 3306)),
        )
    except Exception as ex:
        print("Notice conectar_db cotizador_service:", ex)
        return None


_TABLAS_COTIZADOR_OK = False


def asegurar_tablas_cotizador(db=None):
    global _TABLAS_COTIZADOR_OK
    if _TABLAS_COTIZADOR_OK and db is None:
        return True
    own_db = False
    if db is None:
        db = conectar_db()
        own_db = True
    if not db:
        return False
    try:
        cur = db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cotizador_catalogo_precios (
                upc VARCHAR(64) PRIMARY KEY,
                marca VARCHAR(120),
                tipo_producto VARCHAR(120),
                descripcion VARCHAR(255),
                precio DECIMAL(12, 2) NOT NULL DEFAULT 0,
                outlet_pct INT NULL DEFAULT NULL,
                actualizado_en DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cotizador_promo_especial (
                id INT PRIMARY KEY,
                config_json LONGTEXT,
                actualizado_en DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cotizador_tienda_config (
                codigo_tienda VARCHAR(100) PRIMARY KEY,
                modo_tienda VARCHAR(20) NOT NULL DEFAULT 'LINEA',
                actualizado_en DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cotizador_cotizaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                folio VARCHAR(50) NOT NULL,
                codigo_tienda VARCHAR(100),
                nombre_tienda VARCHAR(150),
                cliente_nombre VARCHAR(150),
                tipo_tienda VARCHAR(20),
                modo_agrupacion VARCHAR(30),
                total_piezas INT DEFAULT 0,
                total_original DECIMAL(12, 2) DEFAULT 0,
                total_ahorro DECIMAL(12, 2) DEFAULT 0,
                total_final DECIMAL(12, 2) DEFAULT 0,
                msi_meses INT DEFAULT 0,
                items_json LONGTEXT,
                resumen_json LONGTEXT,
                creado_en DATETIME,
                actualizado_en DATETIME,
                INDEX idx_cot_tienda (codigo_tienda),
                INDEX idx_cot_fecha (actualizado_en)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        db.commit()
        cur.close()
        _TABLAS_COTIZADOR_OK = True
        return True
    except Exception as ex:
        print("Error asegurando tablas cotizador:", ex)
        return False
    finally:
        if own_db and db:
            try:
                db.close()
            except Exception:
                pass


def normalizar_upc(val):
    s = str(val or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = re.sub(r"\s+", "", s)
    return s


def _norm_txt_busqueda(val):
    return re.sub(r"[^A-Z0-9]+", " ", str(val or "").upper()).strip()


def _parse_precio(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    s = re.sub(r"[^0-9.]", "", str(val).replace(",", ""))
    try:
        return round(float(s), 2) if s else 0.0
    except Exception:
        return 0.0


# ==============================================================================
# 1. CATÁLOGO DE PRECIOS + IMPORTADOR MIM (EXCLUSIVO ADMIN)
# ==============================================================================

def importar_excel_precios_mim(ruta_excel, progress_callback=None):
    """
    Importa precios de StockSummary_Details (MIM) u hoja equivalente:
    EAN/UPC, Marca de producto, Tipo de producto, Descripción, Precio de venta al cliente final.
    """
    if not ruta_excel or not os.path.exists(ruta_excel):
        return False, "El archivo Excel seleccionado no existe.", 0

    if progress_callback:
        progress_callback(5, "Abriendo archivo Excel de precios...")

    try:
        wb = openpyxl.load_workbook(ruta_excel, data_only=True, read_only=True)
        sheet = wb["StockSummary_Details"] if "StockSummary_Details" in wb.sheetnames else wb.active
    except Exception as ex:
        return False, f"No se pudo abrir el Excel: {ex}", 0

    rows_iter = sheet.iter_rows(values_only=True)
    sample = []
    for _ in range(15):
        try:
            r = next(rows_iter)
            if r:
                sample.append(r)
        except StopIteration:
            break

    if not sample:
        wb.close()
        return False, "El archivo Excel está vacío.", 0

    header_idx = 0
    header_norm = None
    col_upc = col_marca = col_tipo = col_desc = col_precio = col_outlet = -1

    for idx, row in enumerate(sample):
        rn = [str(c or "").strip().lower() for c in row]
        hits = sum(1 for cell in rn if any(k in cell for k in ("upc", "ean", "precio", "marca", "descrip")))
        if hits >= 2:
            header_idx = idx
            header_norm = rn
            break

    if header_norm is None:
        header_norm = [str(c or "").strip().lower() for c in sample[0]]

    for i, col in enumerate(header_norm):
        if col_upc == -1 and ("ean" in col or "upc" in col or "codigo" in col or "código" in col or "barcode" in col):
            col_upc = i
        elif col_marca == -1 and "marca" in col:
            col_marca = i
        elif col_tipo == -1 and "tipo" in col:
            col_tipo = i
        elif col_desc == -1 and ("descrip" in col or "producto" in col or "modelo" in col or "articulo" in col):
            col_desc = i
        elif col_precio == -1 and ("precio" in col or "venta al cliente" in col or "pvp" in col or "price" in col):
            col_precio = i
        elif col_outlet == -1 and ("outlet" in col or "60" in col or "70" in col or "% desc" in col):
            col_outlet = i

    if col_upc == -1:
        col_upc = 2 if len(header_norm) > 2 else 0
    if col_precio == -1:
        col_precio = 5 if len(header_norm) > 5 else (len(header_norm) - 1)

    now_str = get_now_mexico_city().strftime("%Y-%m-%d %H:%M:%S")
    batch_map = {}

    def _ingest_row(r):
        if not r or col_upc >= len(r):
            return
        u = normalizar_upc(r[col_upc])
        if not u or u.lower() in ("none", "ean/upc", "upc"):
            return
        precio = _parse_precio(r[col_precio] if col_precio < len(r) else 0)
        if precio <= 0:
            return
        marca = str(r[col_marca] if 0 <= col_marca < len(r) and r[col_marca] is not None else "").strip()[:120]
        tipo_p = str(r[col_tipo] if 0 <= col_tipo < len(r) and r[col_tipo] is not None else "").strip()[:120]
        desc = str(r[col_desc] if 0 <= col_desc < len(r) and r[col_desc] is not None else "").strip()[:255]
        out_pct = None
        if 0 <= col_outlet < len(r) and r[col_outlet] is not None:
            m_o = re.search(r"(60|70)", str(r[col_outlet]))
            if m_o:
                out_pct = int(m_o.group(1))
        batch_map[u] = (u, marca, tipo_p, desc, precio, out_pct, now_str)

    for r in sample[header_idx + 1:]:
        _ingest_row(r)

    cnt_scan = len(sample)
    for r in rows_iter:
        cnt_scan += 1
        _ingest_row(r)
        if cnt_scan % 3000 == 0 and progress_callback:
            progress_callback(min(55, 10 + int(cnt_scan / 1000)), f"Leyendo Excel: {len(batch_map):,} productos con precio...")

    wb.close()

    registros = list(batch_map.values())
    if not registros:
        return False, "No se encontraron filas con EAN/UPC y Precio válido (> $0).", 0

    db = conectar_db()
    if not db:
        return False, "Sin conexión a la base de datos MySQL.", 0

    try:
        asegurar_tablas_cotizador(db)
        cur = db.cursor()
        chunk = 2500
        tot = len(registros)
        sql = """
            INSERT INTO cotizador_catalogo_precios
                (upc, marca, tipo_producto, descripcion, precio, outlet_pct, actualizado_en)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                marca = IF(VALUES(marca) != '', VALUES(marca), marca),
                tipo_producto = IF(VALUES(tipo_producto) != '', VALUES(tipo_producto), tipo_producto),
                descripcion = IF(VALUES(descripcion) != '', VALUES(descripcion), descripcion),
                precio = VALUES(precio),
                outlet_pct = COALESCE(VALUES(outlet_pct), outlet_pct),
                actualizado_en = VALUES(actualizado_en)
        """
        for i in range(0, tot, chunk):
            cur.executemany(sql, registros[i:i + chunk])
            db.commit()
            if progress_callback:
                pct = 55 + int((min(i + chunk, tot) / tot) * 45)
                progress_callback(pct, f"Guardando catálogo: {min(i + chunk, tot):,} / {tot:,} ({pct}%)...")
        cur.close()
        db.close()
        if progress_callback:
            progress_callback(100, f"✅ Catálogo actualizado con {tot:,} productos.")
        return True, f"Catálogo actualizado correctamente ({tot:,} productos con precio).", tot
    except Exception as ex:
        try:
            db.close()
        except Exception:
            pass
        return False, f"Error guardando catálogo en BD: {ex}", 0


def obtener_conteo_catalogo():
    db = conectar_db()
    if not db:
        return 0
    try:
        asegurar_tablas_cotizador(db)
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM cotizador_catalogo_precios")
        res = cur.fetchone()
        cur.close()
        db.close()
        return int(res[0]) if res else 0
    except Exception:
        try:
            db.close()
        except Exception:
            pass
        return 0


def guardar_precio_manual_upc(upc, marca, descripcion, precio, outlet_pct=None):
    u = normalizar_upc(upc)
    if not u or float(precio or 0) <= 0:
        return False
    db = conectar_db()
    if not db:
        return False
    try:
        asegurar_tablas_cotizador(db)
        cur = db.cursor()
        now_s = get_now_mexico_city().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO cotizador_catalogo_precios
                (upc, marca, tipo_producto, descripcion, precio, outlet_pct, actualizado_en)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                marca = IF(VALUES(marca) != '', VALUES(marca), marca),
                descripcion = IF(VALUES(descripcion) != '', VALUES(descripcion), descripcion),
                precio = VALUES(precio),
                outlet_pct = COALESCE(VALUES(outlet_pct), outlet_pct),
                actualizado_en = VALUES(actualizado_en)
        """, (u, str(marca or "")[:120], "Gafas", str(descripcion or "")[:255], round(float(precio), 2), outlet_pct, now_s))
        db.commit()
        cur.close()
        db.close()
        return True
    except Exception as ex:
        print("Error guardando precio manual UPC:", ex)
        try:
            db.close()
        except Exception:
            pass
        return False


def _interpretar_tipo_descuento_semanal(tipo_str):
    s = str(tipo_str or "").strip().lower()
    if not s:
        return "REGULAR", None
    if "70" in s:
        return "OUTLET_70", None
    if "60" in s:
        return "OUTLET_60", None
    if "estrategia" in s or "50%" in s or "2 o más" in s or "2 o mas" in s:
        return "ROJO_30_50", None
    if "30%" in s or s == "30":
        return "VERDE_30", None
    if "20%" in s or s == "20":
        return "AZUL_20", None
    return "REGULAR", None


def _candidatos_codigo_tienda(store_code, store_name=""):
    cands = []
    try:
        import operacion_tiendas as ot
        alias_dict = ot.MAPEO_CODIGOS_TIENDAS_ALIAS
    except Exception:
        alias_dict = {}

    for raw in (store_code, store_name):
        s = str(raw or "").strip()
        if s:
            if s not in cands:
                cands.append(s)
            digits = "".join(ch for ch in s if ch.isdigit())
            if digits and digits not in cands:
                cands.append(digits)
            if s.upper() in alias_dict:
                al = str(alias_dict[s.upper()]).strip()
                if al not in cands:
                    cands.append(al)
    return cands


def buscar_producto_completo(query_val, store_code="", store_name=""):
    """
    Busca por UPC/EAN exacto o parcial (o marca/modelo).
    Lee en modo solo-SELECT de cotizador_catalogo_precios, catalogo_upcs y descuentos_semanales.
    Retorna lista de coincidencias enriquecidas.
    """
    q_raw = str(query_val or "").strip()
    if not q_raw:
        return []
    q_upc = normalizar_upc(q_raw)

    db = conectar_db()
    if not db:
        return []

    resultados = []
    try:
        asegurar_tablas_cotizador(db)
        cur = db.cursor(dictionary=True)

        # 1. Búsqueda exacta primero en cotizador_catalogo_precios
        cur.execute("SELECT * FROM cotizador_catalogo_precios WHERE upc = %s LIMIT 1", (q_upc,))
        rows_p = cur.fetchall()

        if not rows_p:
            # 2. Buscar parcial en cotizador_catalogo_precios
            cur.execute(
                "SELECT * FROM cotizador_catalogo_precios WHERE upc LIKE %s OR descripcion LIKE %s OR marca LIKE %s LIMIT 12",
                (f"%{q_raw}%", f"%{q_raw}%", f"%{q_raw}%"),
            )
            rows_p = cur.fetchall()

        found_map = {}
        for r in rows_p:
            u = normalizar_upc(r.get("upc"))
            found_map[u] = {
                "upc": u,
                "marca": str(r.get("marca") or "").strip(),
                "tipo_producto": str(r.get("tipo_producto") or "").strip(),
                "descripcion": str(r.get("descripcion") or "").strip(),
                "precio": float(r.get("precio") or 0.0),
                "outlet_pct": r.get("outlet_pct"),
                "tag": f"OUTLET_{r['outlet_pct']}" if r.get("outlet_pct") in (60, 70) else "REGULAR",
                "descuento_origen": "",
            }

        # 3. Completar desde catalogo_upcs (93k+ códigos) si no estuvo en precios o le falta detalle
        if not found_map or (len(q_upc) >= 6 and q_upc.isdigit() and q_upc not in found_map):
            try:
                cur.execute(
                    "SELECT upc, marca, articulo, descripcion_articulo, modelo, color FROM catalogo_upcs WHERE upc = %s LIMIT 1",
                    (q_upc,),
                )
                rows_c = cur.fetchall()
                if not rows_c and not found_map:
                    cur.execute(
                        "SELECT upc, marca, articulo, descripcion_articulo, modelo, color FROM catalogo_upcs "
                        "WHERE upc LIKE %s OR modelo LIKE %s OR descripcion_articulo LIKE %s LIMIT 12",
                        (f"%{q_raw}%", f"%{q_raw}%", f"%{q_raw}%"),
                    )
                    rows_c = cur.fetchall()
                for rc in rows_c:
                    u = normalizar_upc(rc.get("upc"))
                    desc_c = " ".join(p for p in (rc.get("modelo"), rc.get("color"), rc.get("descripcion_articulo")) if p).strip()
                    if u not in found_map:
                        found_map[u] = {
                            "upc": u,
                            "marca": str(rc.get("marca") or "").strip(),
                            "tipo_producto": str(rc.get("articulo") or "").strip(),
                            "descripcion": desc_c[:255],
                            "precio": 0.0,
                            "outlet_pct": None,
                            "tag": "REGULAR",
                            "descuento_origen": "",
                        }
                    else:
                        if not found_map[u]["marca"]:
                            found_map[u]["marca"] = str(rc.get("marca") or "").strip()
                        if not found_map[u]["descripcion"]:
                            found_map[u]["descripcion"] = desc_c[:255]
            except Exception as ex_cu:
                print("Notice lookup catalogo_upcs:", ex_cu)

        # 4. Consultar solo-SELECT descuentos_semanales para esa tienda
        if found_map:
            upcs_list = list(found_map.keys())
            ph_u = ",".join(["%s"] * len(upcs_list))
            cands_t = _candidatos_codigo_tienda(store_code, store_name)
            try:
                if cands_t:
                    conds_t = " OR ".join(["codigo_tienda = %s OR nombre_tienda = %s"] * len(cands_t))
                    params_t = []
                    for ct in cands_t:
                        params_t.extend([ct, ct])
                    cur.execute(
                        f"SELECT upc, tipo_descuento, descripcion FROM descuentos_semanales WHERE upc IN ({ph_u}) AND ({conds_t})",
                        tuple(upcs_list + params_t),
                    )
                else:
                    cur.execute(f"SELECT upc, tipo_descuento, descripcion FROM descuentos_semanales WHERE upc IN ({ph_u})", tuple(upcs_list))
                for rd in cur.fetchall():
                    u_d = normalizar_upc(rd.get("upc"))
                    if u_d in found_map:
                        tag_d, _ = _interpretar_tipo_descuento_semanal(rd.get("tipo_descuento"))
                        if found_map[u_d]["tag"] == "REGULAR":
                            found_map[u_d]["tag"] = tag_d
                            found_map[u_d]["descuento_origen"] = str(rd.get("tipo_descuento") or "")
                        if not found_map[u_d]["descripcion"] and rd.get("descripcion"):
                            found_map[u_d]["descripcion"] = str(rd.get("descripcion"))[:255]
            except Exception as ex_ds:
                print("Notice lookup descuentos_semanales:", ex_ds)

        cur.close()
        db.close()
        resultados = list(found_map.values())
    except Exception as ex:
        print("Error buscar_producto_completo:", ex)
        try:
            db.close()
        except Exception:
            pass
    return resultados


def obtener_descuentos_tienda_readonly(store_code="", store_name="", limit=5000):
    """Lectura segura (solo SELECT) de los descuentos activos de una tienda en descuentos_semanales."""
    db = conectar_db()
    if not db:
        return []
    try:
        cur = db.cursor(dictionary=True)
        cands = _candidatos_codigo_tienda(store_code, store_name)
        if cands:
            conds = " OR ".join(["codigo_tienda = %s OR nombre_tienda = %s"] * len(cands))
            params = []
            for ct in cands:
                params.extend([ct, ct])
            cur.execute(
                f"SELECT codigo_tienda, nombre_tienda, upc, descripcion, tipo_descuento, stock_tienda "
                f"FROM descuentos_semanales WHERE ({conds}) ORDER BY tipo_descuento, upc LIMIT %s",
                tuple(params + [int(limit)]),
            )
        else:
            cur.execute(
                "SELECT codigo_tienda, nombre_tienda, upc, descripcion, tipo_descuento, stock_tienda "
                "FROM descuentos_semanales ORDER BY tipo_descuento, upc LIMIT %s",
                (int(limit),),
            )
        rows = cur.fetchall()
        cur.close()
        db.close()
        return rows
    except Exception as ex:
        print("Notice obtener_descuentos_tienda_readonly:", ex)
        try:
            db.close()
        except Exception:
            pass
        return []


def exportar_descuentos_tienda_excel(store_code="", store_name=""):
    rows = obtener_descuentos_tienda_readonly(store_code, store_name, limit=15000)
    os.makedirs(os.path.join(BASE_PATH, "uploads"), exist_ok=True)
    safe_s = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(store_code or "tienda"))
    fname = f"Descuentos_Activos_{safe_s}_{get_now_mexico_city().strftime('%Y%m%d_%H%M%S')}.xlsx"
    fpath = os.path.join(BASE_PATH, "uploads", fname)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Descuentos"
    ws.append(["Código Tienda", "Nombre Tienda", "UPC", "Descripción", "Tipo Descuento", "Stock"])
    for r in rows:
        ws.append([
            r.get("codigo_tienda", ""),
            r.get("nombre_tienda", ""),
            r.get("upc", ""),
            r.get("descripcion", ""),
            r.get("tipo_descuento", ""),
            r.get("stock_tienda", 0),
        ])
    wb.save(fpath)
    wb.close()
    return fpath, fname, len(rows)


# ==============================================================================
# 2. CONFIGURACIÓN POR TIENDA (LÍNEA / OUTLET) + PROMO ESPECIAL GLOBAL (ADMIN)
# ==============================================================================

DEFAULT_PROMO_ESPECIAL = {
    "activa": False,
    "nombre": "Buen Fin",
    "descuento_pct": 20.0,
    "alcance": "TODAS",
    "tiendas_permitidas": "",
    "exclusiones": "RAY BAN META, OAKLEY META, META",
    "actualizado_por": "",
    "fecha": "",
}


def obtener_promo_especial():
    db = conectar_db()
    if not db:
        return dict(DEFAULT_PROMO_ESPECIAL)
    try:
        asegurar_tablas_cotizador(db)
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT config_json FROM cotizador_promo_especial WHERE id = 1")
        row = cur.fetchone()
        cur.close()
        db.close()
        if row and row.get("config_json"):
            data = json.loads(row["config_json"])
            res = dict(DEFAULT_PROMO_ESPECIAL)
            res.update(data)
            return res
    except Exception as ex:
        print("Notice obtener_promo_especial:", ex)
        try:
            db.close()
        except Exception:
            pass
    return dict(DEFAULT_PROMO_ESPECIAL)


def guardar_promo_especial(cfg_dict):
    db = conectar_db()
    if not db:
        return False
    try:
        asegurar_tablas_cotizador(db)
        clean = dict(DEFAULT_PROMO_ESPECIAL)
        clean.update(cfg_dict or {})
        clean["descuento_pct"] = max(0.0, min(90.0, float(clean.get("descuento_pct") or 0.0)))
        clean["fecha"] = get_now_mexico_city().strftime("%Y-%m-%d %H:%M")
        now_s = get_now_mexico_city().strftime("%Y-%m-%d %H:%M:%S")
        cur = db.cursor()
        cur.execute("""
            INSERT INTO cotizador_promo_especial (id, config_json, actualizado_en)
            VALUES (1, %s, %s)
            ON DUPLICATE KEY UPDATE config_json = VALUES(config_json), actualizado_en = VALUES(actualizado_en)
        """, (json.dumps(clean, ensure_ascii=False), now_s))
        db.commit()
        cur.close()
        db.close()
        return True
    except Exception as ex:
        print("Error guardar_promo_especial:", ex)
        try:
            db.close()
        except Exception:
            pass
        return False


def obtener_modo_tienda(codigo_tienda, nombre_tienda=""):
    c_key = str(codigo_tienda or nombre_tienda or "DEFAULT").strip()
    db = conectar_db()
    if db:
        try:
            asegurar_tablas_cotizador(db)
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT modo_tienda FROM cotizador_tienda_config WHERE codigo_tienda = %s", (c_key,))
            row = cur.fetchone()
            cur.close()
            db.close()
            if row and row.get("modo_tienda") in ("LINEA", "OUTLET"):
                return row["modo_tienda"]
        except Exception:
            try:
                db.close()
            except Exception:
                pass
    if "OUTLET" in str(nombre_tienda or "").upper() or "OUTLET" in c_key.upper():
        return "OUTLET"
    return "LINEA"


def guardar_modo_tienda(codigo_tienda, modo_tienda):
    c_key = str(codigo_tienda or "DEFAULT").strip()
    modo = "OUTLET" if str(modo_tienda).upper() == "OUTLET" else "LINEA"
    db = conectar_db()
    if not db:
        return False
    try:
        asegurar_tablas_cotizador(db)
        now_s = get_now_mexico_city().strftime("%Y-%m-%d %H:%M:%S")
        cur = db.cursor()
        cur.execute("""
            INSERT INTO cotizador_tienda_config (codigo_tienda, modo_tienda, actualizado_en)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE modo_tienda = VALUES(modo_tienda), actualizado_en = VALUES(actualizado_en)
        """, (c_key, modo, now_s))
        db.commit()
        cur.close()
        db.close()
        return True
    except Exception:
        try:
            db.close()
        except Exception:
            pass
        return False


# ==============================================================================
# 3. MOTOR MATEMÁTICO DE PROMOCIONES (OUTLET, LÍNEA, BUEN FIN, MSI)
# ==============================================================================

def _item_excluido_promo_especial(item, promo_cfg):
    raw_exc = str((promo_cfg or {}).get("exclusiones") or "").strip()
    if not raw_exc:
        return False
    haystack = _norm_txt_busqueda(
        f"{item.get('marca', '')} {item.get('descripcion', '')} {item.get('upc', '')} {item.get('tipo_producto', '')}"
    )
    tokens = [p.strip() for p in re.split(r"[,;\n]+", raw_exc) if p.strip()]
    for tk in tokens:
        tk_norm = _norm_txt_busqueda(tk)
        if not tk_norm:
            continue
        words = tk_norm.split()
        if tk_norm in haystack or (len(words) > 1 and all(w in haystack for w in words)):
            return True
    return False


def _promo_especial_aplica_tienda(promo_cfg, tipo_tienda, codigo_tienda, nombre_tienda=""):
    if not promo_cfg or not promo_cfg.get("activa"):
        return False
    pct = float(promo_cfg.get("descuento_pct") or 0.0)
    if pct <= 0:
        return False
    alc = str(promo_cfg.get("alcance") or "TODAS").upper()
    if alc == "TODAS":
        return True
    if alc == "LINEA":
        return str(tipo_tienda).upper() == "LINEA"
    if alc == "OUTLET":
        return str(tipo_tienda).upper() == "OUTLET"
    if alc == "CODIGOS":
        permitidas = {p.strip().upper() for p in re.split(r"[,;\s]+", str(promo_cfg.get("tiendas_permitidas") or "")) if p.strip()}
        cands = {c.upper() for c in _candidatos_codigo_tienda(codigo_tienda, nombre_tienda)}
        return bool(permitidas & cands)
    return False


def calcular_msi(total_final):
    t = round(float(total_final or 0.0), 2)
    plazos = []
    if t >= 3000.0:
        plazos.append(3)
    if t >= 5000.0:
        plazos.append(6)
    if t >= 9000.0:
        plazos.append(9)
    if t >= 11000.0:
        plazos.append(12)

    opciones = []
    for m in plazos:
        mens = round(t / m, 2)
        diario = round(mens / 30.0, 2)
        opciones.append({"meses": m, "mensualidad": mens, "diario": diario})

    faltante_3msi = round(max(0.0, 3000.0 - t), 2) if t < 3000.0 else 0.0
    mejor_opcion = opciones[-1] if opciones else None
    return {
        "elegible": bool(opciones),
        "plazos": plazos,
        "opciones": opciones,
        "mejor_opcion": mejor_opcion,
        "faltante_3msi": faltante_3msi,
    }


def _simular_linea_pareo(items_regs, modo_agrupacion="PAREJAS_DESC"):
    """
    Empareja una lista de índices+precios regulares en LINEA para aplicar 40% al de menor valor.
    Retorna dict {idx: (pct, motivo_str)}
    """
    res = {}
    n = len(items_regs)
    if n < 2:
        for idx, _ in items_regs:
            res[idx] = (0.0, "Precio regular (1 pz)")
        return res

    if modo_agrupacion == "MANUAL":
        grupos = {}
        sin_grupo = []
        for idx, it in items_regs:
            g = str(it.get("manual_group") or "").strip()
            if g:
                grupos.setdefault(g, []).append((idx, float(it["precio"])))
            else:
                sin_grupo.append((idx, float(it["precio"])))
        for g, members in grupos.items():
            members.sort(key=lambda x: x[1], reverse=True)
            for j in range(0, len(members) - 1, 2):
                i_hi, _ = members[j]
                i_lo, _ = members[j + 1]
                res[i_hi] = (0.0, f"Grupo {g} (Base par)")
                res[i_lo] = (40.0, f"40% Grupo {g} (Menor)")
            if len(members) % 2 == 1:
                i_rem, _ = members[-1]
                res[i_rem] = (0.0, f"Grupo {g} (Sin par)")
        for idx, _ in sin_grupo:
            res[idx] = (0.0, "Sin grupo manual")
        return res

    ordered = sorted([(idx, float(it["precio"])) for idx, it in items_regs], key=lambda x: x[1], reverse=True)
    if modo_agrupacion == "EXTREMOS":
        # Modo 1: 1 más cara con 1 más barata
        l, r = 0, len(ordered) - 1
        par_num = 1
        while l < r:
            i_hi, _ = ordered[l]
            i_lo, _ = ordered[r]
            res[i_hi] = (0.0, f"Par #{par_num} (Cara base)")
            res[i_lo] = (40.0, f"40% Par #{par_num} (Menor)")
            l += 1
            r -= 1
            par_num += 1
        if l == r:
            i_mid, _ = ordered[l]
            res[i_mid] = (0.0, "Sin par (impar)")
        return res

    # Modo 2 (PAREJAS_DESC): De mayor a menor agrupando de 2 en 2 (1ª+2ª, 3ª+4ª...)
    par_num = 1
    for j in range(0, len(ordered) - 1, 2):
        i_hi, _ = ordered[j]
        i_lo, _ = ordered[j + 1]
        res[i_hi] = (0.0, f"Par #{par_num} (Cara base)")
        res[i_lo] = (40.0, f"40% Par #{par_num} (Menor)")
        par_num += 1
    if len(ordered) % 2 == 1:
        i_rem, _ = ordered[-1]
        res[i_rem] = (0.0, "Sin par (impar)")
    return res


def calcular_cotizacion(items, tipo_tienda="LINEA", modo_agrupacion="PAREJAS_DESC",
                        preferencia_mixta="AUTO", promo_especial=None,
                        codigo_tienda="", nombre_tienda=""):
    """
    Calcula descuentos pieza por pieza para 1 a 200+ piezas.
    - tipo_tienda: "LINEA" o "OUTLET"
    - modo_agrupacion: "PAREJAS_DESC" (1a+2a), "EXTREMOS" (Cara+Barata), "MANUAL"
    - preferencia_mixta: "AUTO" (elige mayor ahorro), "ROJA_50" (prioriza Roja 50%), "PAR_40" (prioriza 2da al 40%)
    """
    # Expandir si algún item trae cantidad > 1, preservando estructura unitaria para cálculos exactos
    unidades = []
    for raw in (items or []):
        cant = max(1, int(raw.get("cantidad") or 1))
        precio = round(float(raw.get("precio") or 0.0), 2)
        if precio <= 0:
            continue
        for c_i in range(cant):
            unidades.append({
                "uid": raw.get("uid") if cant == 1 else f"{raw.get('uid', uuid.uuid4().hex)}_{c_i}",
                "upc": str(raw.get("upc") or "").strip(),
                "marca": str(raw.get("marca") or "").strip(),
                "tipo_producto": str(raw.get("tipo_producto") or "").strip(),
                "descripcion": str(raw.get("descripcion") or "").strip(),
                "precio": precio,
                "tag": str(raw.get("tag") or "REGULAR").upper(),
                "manual_group": str(raw.get("manual_group") or "").strip(),
            })

    total_pz = len(unidades)
    if total_pz == 0:
        return {
            "total_piezas": 0,
            "total_original": 0.0,
            "total_ahorro": 0.0,
            "total_final": 0.0,
            "ahorro_pct": 0.0,
            "desglose": [],
            "alertas": [],
            "comparativa": None,
            "msi": calcular_msi(0.0),
            "promo_especial_activa": None,
        }

    camp_aplica = _promo_especial_aplica_tienda(promo_especial, tipo_tienda, codigo_tienda, nombre_tienda)
    camp_pct = float(promo_especial.get("descuento_pct") or 0.0) if camp_aplica else 0.0
    camp_nom = str(promo_especial.get("nombre") or "Promo Especial").strip() if camp_aplica else ""

    alertas = []
    comparativa = None
    asignaciones = {}  # idx -> (pct, motivo)

    if str(tipo_tienda).upper() == "OUTLET":
        # ---------------- MODO TIENDAS OUTLET ----------------
        regulares = [(i, u) for i, u in enumerate(unidades) if u["tag"] == "REGULAR"]
        esp_60_70 = [(i, u) for i, u in enumerate(unidades) if u["tag"] in ("OUTLET_60", "OUTLET_70")]
        otras_sel = [(i, u) for i, u in enumerate(unidades) if u["tag"] in ("AZUL_20", "VERDE_30", "ROJO_30_50")]

        n_reg = len(regulares)
        desbloqueo_60_70 = bool(esp_60_70 and n_reg >= 2)

        if esp_60_70 and not desbloqueo_60_70:
            # 1 regular + 1 del 60/70 => NO desbloquea 60/70; se va al tier normal Outlet por pieza
            total_pool = len(regulares) + len(esp_60_70)
            tier_fallback = 30.0 if total_pool == 1 else (40.0 if total_pool == 2 else 50.0)
            for idx, _ in regulares:
                asignaciones[idx] = (tier_fallback, f"Outlet {int(tier_fallback)}% ({total_pool} pz)")
            for idx, u in esp_60_70:
                target_s = 70 if u["tag"] == "OUTLET_70" else 60
                asignaciones[idx] = (tier_fallback, f"Outlet {int(tier_fallback)}% (Faltan reg. p/ {target_s}%)")
            faltan = 2 - n_reg
            alertas.append(f"⚠️ Te falta(n) {faltan} pieza(s) regular(es) para desbloquear el 60%/70% (actualmente en {int(tier_fallback)}%).")
        else:
            if desbloqueo_60_70:
                reg_pct = 50.0
                for idx, _ in regulares:
                    asignaciones[idx] = (reg_pct, "Outlet 50% (Desbloqueó 60/70%)")
                for idx, u in esp_60_70:
                    s_pct = 70.0 if u["tag"] == "OUTLET_70" else 60.0
                    asignaciones[idx] = (s_pct, f"Outlet Especial {int(s_pct)}% DESBLOQUEADO")
            else:
                reg_pct = 30.0 if n_reg == 1 else (40.0 if n_reg == 2 else 50.0)
                for idx, _ in regulares:
                    asignaciones[idx] = (reg_pct, f"Outlet {int(reg_pct)}% ({n_reg} reg.)")

        for idx, u in otras_sel:
            if u["tag"] == "AZUL_20":
                asignaciones[idx] = (20.0, "🔵 Azul 20% Selecc.")
            elif u["tag"] == "VERDE_30":
                asignaciones[idx] = (30.0, "🟢 Verde 30% Selecc.")
            else:
                p_r = 50.0 if total_pz >= 2 else 30.0
                asignaciones[idx] = (p_r, f"🔴 Roja {int(p_r)}%" + (" (2+ pzs)" if total_pz >= 2 else " (1 pz)"))

    else:
        # ---------------- MODO TIENDAS DE LÍNEA ----------------
        def _evaluar_linea(estrategia):
            asig = {}
            if estrategia == "ROJA_50":
                regulares = [(i, u) for i, u in enumerate(unidades) if u["tag"] == "REGULAR"]
                pareo_reg = _simular_linea_pareo(regulares, modo_agrupacion=modo_agrupacion)
                asig.update(pareo_reg)
                for i, u in enumerate(unidades):
                    if u["tag"] == "AZUL_20":
                        asig[i] = (20.0, "🔵 Azul 20% Selecc.")
                    elif u["tag"] == "VERDE_30":
                        asig[i] = (30.0, "🟢 Verde 30% Selecc.")
                    elif u["tag"] == "ROJO_30_50":
                        if total_pz >= 2:
                            asig[i] = (50.0, "🔴 Roja sube a 50% (2+ pzs)")
                        else:
                            asig[i] = (30.0, "🔴 Roja 30% (1 pz)")
                    elif u["tag"] in ("OUTLET_60", "OUTLET_70"):
                        sp = 70.0 if u["tag"] == "OUTLET_70" else 60.0
                        asig[i] = (sp, f"Selecc. {int(sp)}%")
            else:
                # Estrategia PAR_40: trata Roja + Regulares en pareo 2da al 40% sin combinar dos promos en el mismo par
                pool_par = [(i, u) for i, u in enumerate(unidades) if u["tag"] in ("REGULAR", "ROJO_30_50")]
                pareo_p = _simular_linea_pareo(pool_par, modo_agrupacion=modo_agrupacion)
                for idx, (pct, mot) in pareo_p.items():
                    if unidades[idx]["tag"] == "ROJO_30_50" and pct == 0.0 and "impar" in mot.lower():
                        # Si queda suelta (impar sin par), conserva su 30% base
                        asig[idx] = (30.0, "🔴 Roja base 30% (suelta)")
                    else:
                        asig[idx] = (pct, mot)
                for i, u in enumerate(unidades):
                    if u["tag"] == "AZUL_20":
                        asig[i] = (20.0, "🔵 Azul 20% Selecc.")
                    elif u["tag"] == "VERDE_30":
                        asig[i] = (30.0, "🟢 Verde 30% Selecc.")
                    elif u["tag"] in ("OUTLET_60", "OUTLET_70"):
                        sp = 70.0 if u["tag"] == "OUTLET_70" else 60.0
                        asig[i] = (sp, f"Selecc. {int(sp)}%")
            return asig

        has_roja = any(u["tag"] == "ROJO_30_50" for u in unidades)
        asig_roja = _evaluar_linea("ROJA_50")

        if has_roja and total_pz >= 2:
            asig_par = _evaluar_linea("PAR_40")

            def _tot_neto(asig_map):
                t_val = 0.0
                for idx, u in enumerate(unidades):
                    pct_i, _ = asig_map.get(idx, (0.0, ""))
                    if camp_aplica and not _item_excluido_promo_especial(u, promo_especial):
                        pct_i = max(pct_i, camp_pct)
                    t_val += round(u["precio"] * (1.0 - pct_i / 100.0), 2)
                return round(t_val, 2)

            neto_r = _tot_neto(asig_roja)
            neto_p = _tot_neto(asig_par)
            mejor = "ROJA_50" if neto_r <= neto_p else "PAR_40"
            comparativa = {
                "total_roja_50": neto_r,
                "total_par_40": neto_p,
                "ahorro_extra": round(abs(neto_p - neto_r), 2),
                "mejor": mejor,
            }
            if preferencia_mixta == "PAR_40":
                asignaciones = asig_par
            elif preferencia_mixta == "ROJA_50":
                asignaciones = asig_roja
            else:
                asignaciones = asig_roja if mejor == "ROJA_50" else asig_par
        else:
            asignaciones = asig_roja

        # Comparativa Modo 1 (Extremos) vs Modo 2 (Parejas desc) cuando hay 4+ piezas regulares
        regs_cnt = sum(1 for u in unidades if u["tag"] == "REGULAR")
        if regs_cnt >= 4 and modo_agrupacion in ("EXTREMOS", "PAREJAS_DESC"):
            otro_modo = "EXTREMOS" if modo_agrupacion == "PAREJAS_DESC" else "PAREJAS_DESC"
            reg_items = [(i, u) for i, u in enumerate(unidades) if u["tag"] == "REGULAR"]
            p_actual = _simular_linea_pareo(reg_items, modo_agrupacion=modo_agrupacion)
            p_otro = _simular_linea_pareo(reg_items, modo_agrupacion=otro_modo)
            ahorro_act = sum(round(unidades[idx]["precio"] * pct / 100.0, 2) for idx, (pct, _) in p_actual.items())
            ahorro_otr = sum(round(unidades[idx]["precio"] * pct / 100.0, 2) for idx, (pct, _) in p_otro.items())
            if ahorro_otr > ahorro_act + 0.01:
                nom_m = "Modo 2 (De mayor a menor)" if otro_modo == "PAREJAS_DESC" else "Modo 1 (Cara + Barata)"
                alertas.append(f"💡 Con '{nom_m}' el cliente ahorra ${ahorro_otr - ahorro_act:,.2f} extra en las piezas de línea.")

    # Aplicar Promo Especial Global (ej. Buen Fin 20% sin descuento sobre descuento y respetando exclusiones)
    desglose = []
    tot_orig = 0.0
    tot_final = 0.0

    for idx, u in enumerate(unidades):
        pct, motivo = asignaciones.get(idx, (0.0, "Precio regular"))
        excluida_camp = False
        if camp_aplica:
            if _item_excluido_promo_especial(u, promo_especial):
                excluida_camp = True
                if pct == 0.0:
                    motivo = f"Excluida de {camp_nom} (0%)"
            elif camp_pct > pct:
                pct = camp_pct
                motivo = f"🔥 {camp_nom} ({int(camp_pct)}%)"

        p_orig = round(u["precio"], 2)
        desc_mxn = round(p_orig * (pct / 100.0), 2)
        p_neto = round(p_orig - desc_mxn, 2)
        tot_orig += p_orig
        tot_final += p_neto

        desglose.append({
            "num": idx + 1,
            "uid": u["uid"],
            "upc": u["upc"],
            "marca": u["marca"],
            "descripcion": u["descripcion"],
            "precio_original": p_orig,
            "tag": u["tag"],
            "descuento_pct": round(pct, 1),
            "descuento_monto": desc_mxn,
            "precio_final": p_neto,
            "motivo": motivo,
            "excluida_campana": excluida_camp,
            "manual_group": u["manual_group"],
        })

    tot_orig = round(tot_orig, 2)
    tot_final = round(tot_final, 2)
    tot_ahorro = round(tot_orig - tot_final, 2)
    ahorro_pct = round((tot_ahorro / tot_orig) * 100.0, 1) if tot_orig > 0 else 0.0
    msi_info = calcular_msi(tot_final)

    return {
        "total_piezas": total_pz,
        "total_original": tot_orig,
        "total_ahorro": tot_ahorro,
        "total_final": tot_final,
        "ahorro_pct": ahorro_pct,
        "desglose": desglose,
        "alertas": alertas,
        "comparativa": comparativa,
        "msi": msi_info,
        "promo_especial_activa": f"{camp_nom} ({int(camp_pct)}%)" if camp_aplica else None,
    }


# ==============================================================================
# 4. COTIZACIONES GUARDADAS (GUARDAR / LISTAR / EDITAR / BORRAR)
# ==============================================================================

def guardar_cotizacion(codigo_tienda, nombre_tienda, cliente_nombre, tipo_tienda,
                       modo_agrupacion, items_raw, resultado_calc, cotizacion_id=None):
    db = conectar_db()
    if not db:
        return False, None, "Sin conexión a MySQL."
    try:
        asegurar_tablas_cotizador(db)
        now_dt = get_now_mexico_city()
        now_s = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        msi_data = resultado_calc.get("msi") or {}
        mejor_msi = (msi_data.get("mejor_opcion") or {}).get("meses", 0)

        items_json = json.dumps(items_raw or [], ensure_ascii=False)
        resumen_json = json.dumps({
            "ahorro_pct": resultado_calc.get("ahorro_pct", 0.0),
            "msi": msi_data,
            "promo_especial_activa": resultado_calc.get("promo_especial_activa"),
        }, ensure_ascii=False)

        cur = db.cursor()
        if cotizacion_id:
            cur.execute("""
                UPDATE cotizador_cotizaciones
                SET cliente_nombre = %s,
                    tipo_tienda = %s,
                    modo_agrupacion = %s,
                    total_piezas = %s,
                    total_original = %s,
                    total_ahorro = %s,
                    total_final = %s,
                    msi_meses = %s,
                    items_json = %s,
                    resumen_json = %s,
                    actualizado_en = %s
                WHERE id = %s
            """, (
                str(cliente_nombre or "Cliente Mostrador")[:150],
                tipo_tienda,
                modo_agrupacion,
                int(resultado_calc.get("total_piezas", 0)),
                float(resultado_calc.get("total_original", 0.0)),
                float(resultado_calc.get("total_ahorro", 0.0)),
                float(resultado_calc.get("total_final", 0.0)),
                int(mejor_msi),
                items_json,
                resumen_json,
                now_s,
                int(cotizacion_id),
            ))
            db.commit()
            cur.close()
            db.close()
            return True, int(cotizacion_id), "Cotización actualizada correctamente."

        folio = f"COT-{str(codigo_tienda or 'SGH')[:6]}-{now_dt.strftime('%y%m%d-%H%M%S')}"
        cur.execute("""
            INSERT INTO cotizador_cotizaciones (
                folio, codigo_tienda, nombre_tienda, cliente_nombre, tipo_tienda,
                modo_agrupacion, total_piezas, total_original, total_ahorro,
                total_final, msi_meses, items_json, resumen_json, creado_en, actualizado_en
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            folio,
            str(codigo_tienda or "")[:100],
            str(nombre_tienda or "")[:150],
            str(cliente_nombre or "Cliente Mostrador")[:150],
            tipo_tienda,
            modo_agrupacion,
            int(resultado_calc.get("total_piezas", 0)),
            float(resultado_calc.get("total_original", 0.0)),
            float(resultado_calc.get("total_ahorro", 0.0)),
            float(resultado_calc.get("total_final", 0.0)),
            int(mejor_msi),
            items_json,
            resumen_json,
            now_s,
            now_s,
        ))
        new_id = cur.lastrowid
        db.commit()
        cur.close()
        db.close()
        return True, int(new_id), f"Cotización guardada ({folio})."
    except Exception as ex:
        try:
            db.close()
        except Exception:
            pass
        return False, None, f"Error guardando cotización: {ex}"


def listar_cotizaciones(codigo_tienda=None, es_admin=False, limit=100):
    db = conectar_db()
    if not db:
        return []
    try:
        asegurar_tablas_cotizador(db)
        cur = db.cursor(dictionary=True)
        if es_admin or not codigo_tienda:
            cur.execute(
                "SELECT id, folio, codigo_tienda, nombre_tienda, cliente_nombre, tipo_tienda, "
                "modo_agrupacion, total_piezas, total_original, total_ahorro, total_final, "
                "msi_meses, items_json, actualizado_en FROM cotizador_cotizaciones "
                "ORDER BY actualizado_en DESC, id DESC LIMIT %s",
                (int(limit),),
            )
        else:
            cands = _candidatos_codigo_tienda(codigo_tienda)
            ph = ",".join(["%s"] * len(cands))
            cur.execute(
                f"SELECT id, folio, codigo_tienda, nombre_tienda, cliente_nombre, tipo_tienda, "
                f"modo_agrupacion, total_piezas, total_original, total_ahorro, total_final, "
                f"msi_meses, items_json, actualizado_en FROM cotizador_cotizaciones "
                f"WHERE codigo_tienda IN ({ph}) ORDER BY actualizado_en DESC, id DESC LIMIT %s",
                tuple(cands + [int(limit)]),
            )
        rows = cur.fetchall()
        cur.close()
        db.close()
        return rows
    except Exception as ex:
        print("Error listando cotizaciones:", ex)
        try:
            db.close()
        except Exception:
            pass
        return []


def borrar_cotizacion(cotizacion_id):
    db = conectar_db()
    if not db:
        return False
    try:
        cur = db.cursor()
        cur.execute("DELETE FROM cotizador_cotizaciones WHERE id = %s", (int(cotizacion_id),))
        db.commit()
        cur.close()
        db.close()
        return True
    except Exception as ex:
        print("Error borrando cotización:", ex)
        try:
            db.close()
        except Exception:
            pass
        return False


# ==============================================================================
# 5. GENERADOR PDF VECTORIAL MULTIPÁGINA DE COTIZACIÓN (HASTA 200+ PIEZAS)
# ==============================================================================

def generar_pdf_cotizacion(resultado_calc, tienda_label="Sunglass Hut", cliente_nombre="Cliente Mostrador",
                           tipo_tienda="LINEA", folio=None, out_pdf_path=None):
    os.makedirs(os.path.join(BASE_PATH, "uploads"), exist_ok=True)
    now_dt = get_now_mexico_city()
    folio_str = str(folio) if folio not in (None, "") else f"COT-{now_dt.strftime('%y%m%d-%H%M%S')}"
    fname = f"Cotizacion_{re.sub(r'[^a-zA-Z0-9_-]+', '_', folio_str)}.pdf"
    if not out_pdf_path:
        out_pdf_path = os.path.join(BASE_PATH, "uploads", fname)

    doc = fitz.open()
    W, H = 612, 792
    M = 28

    C_NAVY = (0.06, 0.09, 0.16)
    C_CYAN = (0.0, 0.65, 0.78)
    C_DARK = (0.12, 0.15, 0.22)
    C_GRAY = (0.42, 0.46, 0.54)
    C_LIGHT = (0.95, 0.96, 0.98)
    C_GREEN = (0.04, 0.56, 0.36)
    C_GREEN_BG = (0.89, 0.98, 0.93)
    C_WHITE = (1, 1, 1)

    def _draw_page_header(page, page_num, is_first):
        page.draw_rect(fitz.Rect(0, 0, W, 62), color=C_NAVY, fill=C_NAVY)
        page.insert_text((M, 25), "SUNGLASS HUT  |  COTIZACION DE VENTA", fontsize=14, fontname="helv", color=C_WHITE)
        page.insert_text((M, 42), f"Sucursal: {tienda_label} ({tipo_tienda})   |   Cliente: {cliente_nombre}", fontsize=8.5, fontname="helv", color=(0.75, 0.92, 0.98))
        page.insert_text((W - 185, 25), f"Folio: {folio_str}", fontsize=9, fontname="helv", color=(0.4, 0.95, 1.0))
        page.insert_text((W - 185, 42), f"Fecha: {now_dt.strftime('%d/%m/%Y %I:%M %p')}", fontsize=8, fontname="helv", color=C_WHITE)
        if resultado_calc.get("promo_especial_activa"):
            page.insert_text((M, 55), f"Promocion activa: {resultado_calc['promo_especial_activa']}", fontsize=7.5, fontname="helv", color=(0.98, 0.85, 0.35))
        y = 74

        if is_first:
            # Tarjetas KPI resumen arriba en Página 1
            card_w = (W - 2 * M - 18) / 4.0
            cards = [
                ("PIEZAS", f"{resultado_calc['total_piezas']}", C_LIGHT, C_DARK),
                ("PRECIO ORIGINAL", f"${resultado_calc['total_original']:,.2f}", C_LIGHT, C_DARK),
                ("TU AHORRO", f"-${resultado_calc['total_ahorro']:,.2f} ({resultado_calc['ahorro_pct']:.1f}%)", C_GREEN_BG, C_GREEN),
                ("TOTAL A PAGAR", f"${resultado_calc['total_final']:,.2f}", (0.88, 0.96, 1.0), C_CYAN),
            ]
            for i, (lbl, val, bg, fg) in enumerate(cards):
                x0 = M + i * (card_w + 6)
                r = fitz.Rect(x0, y, x0 + card_w, y + 40)
                page.draw_rect(r, color=(0.82, 0.85, 0.90), fill=bg, width=0.6)
                page.insert_text((x0 + 7, y + 14), lbl, fontsize=7, fontname="helv", color=C_GRAY)
                page.insert_text((x0 + 7, y + 31), val, fontsize=10.5, fontname="helv", color=fg)
            y += 50

        # Encabezado de tabla
        cols = [
            (M, 24, "#"),
            (M + 24, 88, "UPC / EAN"),
            (M + 112, 168, "PRODUCTO / MARCA"),
            (M + 280, 118, "PROMO APLICADA"),
            (M + 398, 58, "P. ORIG"),
            (M + 456, 42, "DESC"),
            (M + 498, 58, "FINAL"),
        ]
        page.draw_rect(fitz.Rect(M, y, W - M, y + 18), color=C_DARK, fill=C_DARK)
        for cx, cw, title in cols:
            page.insert_text((cx + 3, y + 12), title, fontsize=7.2, fontname="helv", color=C_WHITE)
        return y + 18, cols

    desglose = resultado_calc.get("desglose") or []
    idx_item = 0
    page_num = 1
    row_h = 16.5

    while idx_item < len(desglose) or page_num == 1:
        p = doc.new_page(width=W, height=H)
        y, cols = _draw_page_header(p, page_num, is_first=(page_num == 1))
        max_y = H - 110 if idx_item + 1 >= len(desglose) else H - 36

        while idx_item < len(desglose) and (y + row_h) <= (H - 36):
            it = desglose[idx_item]
            bg = C_LIGHT if idx_item % 2 == 1 else C_WHITE
            p.draw_rect(fitz.Rect(M, y, W - M, y + row_h), color=(0.86, 0.88, 0.92), fill=bg, width=0.4)

            prod_txt = f"{it.get('marca', '')} {it.get('descripcion', '')}".strip()
            if len(prod_txt) > 34:
                prod_txt = prod_txt[:33] + "."
            mot_txt = re.sub(r"[^\x20-\x7E\xA0-\xFF]", "", str(it.get("motivo") or "")).strip()
            if len(mot_txt) > 25:
                mot_txt = mot_txt[:24] + "."

            p.insert_text((cols[0][0] + 3, y + 11.5), str(it["num"]), fontsize=7, fontname="helv", color=C_DARK)
            p.insert_text((cols[1][0] + 3, y + 11.5), str(it.get("upc") or "")[:16], fontsize=6.8, fontname="helv", color=C_DARK)
            p.insert_text((cols[2][0] + 3, y + 11.5), prod_txt, fontsize=6.8, fontname="helv", color=C_DARK)
            p.insert_text((cols[3][0] + 3, y + 11.5), mot_txt, fontsize=6.5, fontname="helv", color=C_GREEN if it["descuento_pct"] > 0 else C_GRAY)
            p.insert_text((cols[4][0] + 3, y + 11.5), f"${it['precio_original']:,.2f}", fontsize=6.8, fontname="helv", color=C_DARK)
            p.insert_text((cols[5][0] + 3, y + 11.5), f"{int(it['descuento_pct'])}%" if it["descuento_pct"] > 0 else "0%", fontsize=6.8, fontname="helv", color=C_GREEN if it["descuento_pct"] > 0 else C_GRAY)
            p.insert_text((cols[6][0] + 3, y + 11.5), f"${it['precio_final']:,.2f}", fontsize=7, fontname="helv", color=C_DARK)

            y += row_h
            idx_item += 1

        if idx_item >= len(desglose):
            # Bloque final MSI & Mensaje de cierre
            if y > H - 105:
                p.insert_text((M, H - 14), f"Pagina {page_num}  |  LUXO AI System", fontsize=7, fontname="helv", color=C_GRAY)
                page_num += 1
                p = doc.new_page(width=W, height=H)
                p.draw_rect(fitz.Rect(0, 0, W, 38), color=C_NAVY, fill=C_NAVY)
                p.insert_text((M, 24), f"RESUMEN FINAL DE COTIZACION  |  Folio: {folio_str}", fontsize=11, fontname="helv", color=C_WHITE)
                y = 54

            y += 10
            box_r = fitz.Rect(M, y, W - M, y + 78)
            p.draw_rect(box_r, color=C_CYAN, fill=C_GREEN_BG, width=1.0)
            p.insert_text(
                (M + 10, y + 17),
                f"Precio original: ${resultado_calc['total_original']:,.2f}   |   Total con descuento: ${resultado_calc['total_final']:,.2f}   |   Te ahorras: ${resultado_calc['total_ahorro']:,.2f}",
                fontsize=9.2, fontname="helv", color=C_DARK,
            )
            msi = resultado_calc.get("msi") or {}
            if msi.get("elegible"):
                op_txts = [f"{o['meses']} MSI: ${o['mensualidad']:,.2f}/mes" for o in msi["opciones"]]
                p.insert_text((M + 10, y + 36), "Meses Sin Intereses (tarjetas participantes):  " + "   |   ".join(op_txts), fontsize=8, fontname="helv", color=C_GREEN)
                mejor = msi["mejor_opcion"]
                p.insert_text(
                    (M + 10, y + 54),
                    f"Llevatelo desde ${mejor['mensualidad']:,.2f} al mes ({mejor['meses']} MSI) - menos de ${mejor['diario']:,.2f} al dia (mas barato que un cafe!).",
                    fontsize=8.5, fontname="helv", color=C_NAVY,
                )
            else:
                falt = msi.get("faltante_3msi", 0.0)
                p.insert_text((M + 10, y + 38), f"Pago de contado. (Agrega ${falt:,.2f} para desbloquear 3 Meses Sin Intereses desde $3,000).", fontsize=8.2, fontname="helv", color=C_GRAY)
            p.insert_text((M + 10, y + 70), "Cotizacion informativa sujeta a disponibilidad y vigencia de promociones en caja.", fontsize=6.8, fontname="helv", color=C_GRAY)

        p.insert_text((M, H - 14), f"Pagina {page_num}  |  LUXO AI System  |  {tienda_label}", fontsize=7, fontname="helv", color=C_GRAY)
        page_num += 1

    doc.save(out_pdf_path)
    doc.close()
    return out_pdf_path, os.path.basename(out_pdf_path)
