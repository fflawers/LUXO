import os
import openpyxl
import re
import urllib.parse
import mysql.connector

def _normalizar_texto(val):
    if val is None:
        return ""
    return str(val).strip().lower()

def conectar_db():
    try:
        import main
        db = main.conectar_db()
        if db and db.is_connected():
            return db
    except Exception: pass
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "los4valtierra"),
            database=os.getenv("DB_NAME", "sgh_portal"),
            port=int(os.getenv("DB_PORT", 3306))
        )
    except Exception as e:
        print("Error al conectar a DB en descuentos_service:", e)
        return None

def crear_tabla_descuentos_if_not_exists():
    db = conectar_db()
    if not db:
        print("Error: No se pudo conectar a DB para crear tabla descuentos_semanales.")
        return False
    try:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS descuentos_semanales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo_tienda VARCHAR(100) NOT NULL,
                nombre_tienda VARCHAR(150),
                upc VARCHAR(50) NOT NULL,
                descripcion VARCHAR(255),
                tipo_descuento VARCHAR(100),
                stock_tienda INT DEFAULT 1,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tienda (codigo_tienda),
                INDEX idx_upc (upc)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        db.commit()
        db.close()
        return True
    except Exception as e:
        print("Error creando tabla descuentos_semanales:", e)
        if db: db.close()
        return False

def normalizar_tipo_descuento(val):
    if val is None: return "OFERTA"
    s = str(val).strip()
    if not s or s.lower() == "none": return "OFERTA"
    
    try:
        f = float(s)
        if 0.0 < f < 1.0:
            pct = int(round(f * 100))
            return f"{pct}% OFF"
    except Exception:
        pass

    if s == "0.2": return "20% OFF"
    if s == "0.3": return "30% OFF"
    if s == "0.5": return "50% OFF"
    
    return s

def procesar_excel_descuentos(ruta_excel, progress_callback=None):
    """
    Procesa el Excel semanal de descuentos notificando progreso live en porcentaje (0% a 100%).
    """
    if not os.path.exists(ruta_excel):
        return False, "El archivo de Excel no existe."

    crear_tabla_descuentos_if_not_exists()

    if progress_callback:
        progress_callback(6, "Abriendo y decodificando Excel semanal...")

    try:
        wb = openpyxl.load_workbook(ruta_excel, data_only=True, read_only=True)
        sheet = wb.active
    except Exception as ex:
        return False, f"Error al abrir Excel: {ex}"

    rows_iter = sheet.iter_rows(values_only=True)
    
    # Leer las primeras 15 filas para detectar la estructura de columnas
    header_sample = []
    for _ in range(15):
        try:
            r = next(rows_iter)
            if r: header_sample.append(r)
        except StopIteration:
            break

    if not header_sample:
        wb.close()
        return False, "El archivo Excel está vacío."

    # 1. Encontrar la fila de encabezados (revisar primeras 10 filas)
    header_idx = 0
    header_row = None
    
    kw_tienda = ["sap store", "tiendas", "tienda", "sucursal", "store", "cod_tienda", "n_tienda", "nombre_tienda", "id_tienda", "cod tienda"]
    kw_upc = ["upc #", "upc", "ean", "codigo", "codigo_barras", "sku", "barcode", "material", "articulo", "cod_articulo"]
    kw_desc = ["merch group desc", "descripcion", "descripcion gafa", "modelo", "estilo", "marca", "producto", "detalle"]
    kw_descuento = ["flash", "descuento", "tipo_descuento", "% descuento", "promo", "oferta", "descto", "porcentaje", "pct", "estrategia"]
    kw_stock = ["piez", "piezas", "cantidad", "stock", "cant", "existencia", "qty", "unidades", "pz"]

    for idx, r in enumerate(header_sample[:10]):
        if not r: continue
        r_norm = [_normalizar_texto(cell) for cell in r]
        matches = 0
        for cell in r_norm:
            if any(k in cell for k in kw_tienda + kw_upc + kw_desc + kw_descuento + kw_stock):
                matches += 1
        if matches >= 2:
            header_idx = idx
            header_row = r_norm
            break

    if header_row is None:
        header_idx = 0
        header_row = [_normalizar_texto(cell) for cell in header_sample[0]]

    # Mapas de índice de columna
    col_tienda = -1
    col_nombre_tienda = -1
    col_upc = -1
    col_desc = -1
    col_descuento = -1
    col_stock = -1

    for c_idx, val in enumerate(header_row):
        if not val: continue
        if "sap store" in val or ("store" in val and col_tienda == -1):
            col_tienda = c_idx
        elif "tiendas" in val or "nombre_tienda" in val:
            col_nombre_tienda = c_idx
        elif col_tienda == -1 and any(k in val for k in kw_tienda):
            col_tienda = c_idx
        elif col_upc == -1 and any(k in val for k in kw_upc):
            col_upc = c_idx
        elif col_desc == -1 and any(k in val for k in kw_desc):
            col_desc = c_idx
        elif col_descuento == -1 and any(k in val for k in kw_descuento):
            col_descuento = c_idx
        elif col_stock == -1 and any(k in val for k in kw_stock):
            col_stock = c_idx

    if col_upc == -1:
        col_upc = 6 if len(header_row) > 6 else 0
    if col_tienda == -1:
        col_tienda = 1 if len(header_row) > 1 else 0

    # Extraer registros con porcentaje de avance continuo en streaming
    registros_to_insert = []
    row_count = 0

    # Procesar filas restantes de la muestra inicial que eran datos
    for r in header_sample[header_idx + 1:]:
        row_count += 1
        upc_val = str(r[col_upc]).strip() if col_upc < len(r) and r[col_upc] is not None else ""
        if not upc_val or upc_val.lower() == "none": continue
        if upc_val.endswith(".0"): upc_val = upc_val[:-2]

        tienda_val = str(r[col_tienda]).strip() if col_tienda >= 0 and col_tienda < len(r) and r[col_tienda] is not None else "GENERAL"
        if tienda_val.endswith(".0"): tienda_val = tienda_val[:-2]

        nombre_tienda_val = str(r[col_nombre_tienda]).strip() if col_nombre_tienda >= 0 and col_nombre_tienda < len(r) and r[col_nombre_tienda] is not None else tienda_val
        if nombre_tienda_val.endswith(".0"): nombre_tienda_val = nombre_tienda_val[:-2]

        desc_val = str(r[col_desc]).strip() if col_desc >= 0 and col_desc < len(r) and r[col_desc] is not None else "Sin descripción"
        raw_descuento = r[col_descuento] if col_descuento >= 0 and col_descuento < len(r) else "OFERTA"
        descuento_val = normalizar_tipo_descuento(raw_descuento)

        stock_val = 1
        if col_stock >= 0 and col_stock < len(r) and r[col_stock] is not None:
            try: stock_val = int(float(r[col_stock]))
            except Exception: stock_val = 1

        registros_to_insert.append((tienda_val, nombre_tienda_val, upc_val, desc_val, descuento_val, stock_val))

    # Procesar el resto del archivo mediante streaming (sin colapsar la RAM)
    for r in rows_iter:
        row_count += 1
        if row_count % 2000 == 0 and progress_callback:
            # Estimar progreso aproximado sobre ~50k filas
            pct = min(60, 10 + int((row_count / 50000.0) * 50))
            progress_callback(pct, f"Procesando Excel streaming: {row_count:,} filas ({pct}%)...")

        if not r: continue
        upc_val = str(r[col_upc]).strip() if col_upc < len(r) and r[col_upc] is not None else ""
        if not upc_val or upc_val.lower() == "none": continue
        if upc_val.endswith(".0"): upc_val = upc_val[:-2]

        tienda_val = str(r[col_tienda]).strip() if col_tienda >= 0 and col_tienda < len(r) and r[col_tienda] is not None else "GENERAL"
        if tienda_val.endswith(".0"): tienda_val = tienda_val[:-2]

        nombre_tienda_val = str(r[col_nombre_tienda]).strip() if col_nombre_tienda >= 0 and col_nombre_tienda < len(r) and r[col_nombre_tienda] is not None else tienda_val
        if nombre_tienda_val.endswith(".0"): nombre_tienda_val = nombre_tienda_val[:-2]

        desc_val = str(r[col_desc]).strip() if col_desc >= 0 and col_desc < len(r) and r[col_desc] is not None else "Sin descripción"
        raw_descuento = r[col_descuento] if col_descuento >= 0 and col_descuento < len(r) else "OFERTA"
        descuento_val = normalizar_tipo_descuento(raw_descuento)

        stock_val = 1
        if col_stock >= 0 and col_stock < len(r) and r[col_stock] is not None:
            try: stock_val = int(float(r[col_stock]))
            except Exception: stock_val = 1

        registros_to_insert.append((tienda_val, nombre_tienda_val, upc_val, desc_val, descuento_val, stock_val))

    wb.close()

    if not registros_to_insert:
        return False, "No se encontraron filas válidas en el Excel."

    # Guardar en base de datos MySQL (reemplazar catálogo semanal)
    db = conectar_db()
    if not db:
        return False, "Error de conexión a la base de datos."

    try:
        cursor = db.cursor()
        cursor.execute("TRUNCATE TABLE descuentos_semanales;")
        
        # Inserción en lotes con barra de porcentaje (60% a 100%)
        total_ins = len(registros_to_insert)
        chunk_size = 5000
        for i in range(0, total_ins, chunk_size):
            chunk = registros_to_insert[i:i + chunk_size]
            cursor.executemany("""
                INSERT INTO descuentos_semanales (
                    codigo_tienda, nombre_tienda, upc, descripcion, tipo_descuento, stock_tienda
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, chunk)
            db.commit()
            
            curr = min(i + chunk_size, total_ins)
            if progress_callback:
                pct = 60 + int((curr / total_ins) * 40)
                progress_callback(pct, f"Guardando en Base de Datos: {curr:,} de {total_ins:,} ofertas ({pct}%)...")

        db.close()
        if progress_callback:
            progress_callback(100, "¡Catálogo procesado y distribuido a las sucursales!")

        return True, f"✅ Se cargaron exitosamente {total_ins:,} ofertas fragmentadas a las sucursales."
    except Exception as ex_db:
        print("Error insertando descuentos en DB:", ex_db)
        if db: db.close()
        return False, f"Error al guardar registros en base de datos: {ex_db}"

def obtener_todos_descuentos():
    """
    Carga los descuentos existentes de la base de datos.
    """
    crear_tabla_descuentos_if_not_exists()
    db = conectar_db()
    if not db:
        return []
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM descuentos_semanales ORDER BY id ASC LIMIT 2000")
        rows = cursor.fetchall()
        db.close()
        return rows
    except Exception as e:
        print("Error obteniendo todos los descuentos:", e)
        if db: db.close()
        return []

def obtener_descuentos_por_tienda(codigo_tienda=None, query_search=None):
    """
    Retorna la lista de descuentos para una tienda específica de entre los 49,000+ registros.
    """
    crear_tabla_descuentos_if_not_exists()
    db = conectar_db()
    if not db:
        return []
    try:
        cursor = db.cursor(dictionary=True)
        conditions = []
        params = []

        if codigo_tienda and str(codigo_tienda).strip() and str(codigo_tienda).strip().upper() != "TODAS":
            c_clean = str(codigo_tienda).strip()
            digits_only = "".join(filter(str.isdigit, c_clean))
            if digits_only:
                conditions.append("(codigo_tienda = %s OR nombre_tienda = %s OR codigo_tienda = %s)")
                params.extend([digits_only, c_clean, c_clean])
            else:
                conditions.append("(codigo_tienda = %s OR nombre_tienda = %s OR nombre_tienda LIKE %s)")
                params.extend([c_clean, c_clean, f"%{c_clean}%"])

        if query_search and str(query_search).strip():
            q_clean = str(query_search).strip()
            conditions.append("(upc LIKE %s OR descripcion LIKE %s OR tipo_descuento LIKE %s)")
            params.extend([f"%{q_clean}%", f"%{q_clean}%", f"%{q_clean}%"])

        where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"SELECT * FROM descuentos_semanales {where_sql} ORDER BY id ASC LIMIT 500"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        db.close()
        return rows
    except Exception as e:
        print("Error obteniendo descuentos por tienda:", e)
        if db: db.close()
        return []

def obtener_marcas_y_descuentos_disponibles(codigo_tienda=None):
    """
    Obtiene las marcas y tipos de descuento únicos para poblar los filtros estilo Excel.
    """
    db = conectar_db()
    if not db:
        return [], []
    try:
        cursor = db.cursor(dictionary=True)
        where_clause = ""
        params = []
        if codigo_tienda and str(codigo_tienda).strip() and str(codigo_tienda).upper() != "TODAS":
            c_clean = str(codigo_tienda).strip()
            where_clause = "WHERE codigo_tienda = %s OR nombre_tienda = %s"
            params = [c_clean, c_clean]
        
        cursor.execute(f"SELECT DISTINCT descripcion FROM descuentos_semanales {where_clause} ORDER BY descripcion ASC", tuple(params))
        marcas = [r["descripcion"] for r in cursor.fetchall() if r["descripcion"]]

        cursor.execute(f"SELECT DISTINCT tipo_descuento FROM descuentos_semanales {where_clause} ORDER BY tipo_descuento ASC", tuple(params))
        tipos = [r["tipo_descuento"] for r in cursor.fetchall() if r["tipo_descuento"]]

        db.close()
        return marcas, tipos
    except Exception as e:
        print("Error obteniendo marcas y tipos:", e)
        if db: db.close()
        return [], []
