import os, openpyxl, datetime, mysql.connector

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
excel_path = os.path.join(os.path.expanduser("~"), "Downloads", "Tiendas Sunglass Hut 2026 Q2.xlsx")

def conectar_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="los4valtierra",
            database="sgh_portal"
        )
    except Exception as ex:
        print("Error conectando a MySQL:", ex)
        return None

def ejecutar_importacion():
    if not os.path.exists(excel_path):
        print(f"❌ Archivo Excel no encontrado en {excel_path}")
        return

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active

    db = conectar_db()
    if not db:
        print("❌ No se pudo conectar a la base de datos MySQL")
        return

    cur = db.cursor(dictionary=True)

    # 1. Obtener mapeo de tiendas a Zonas desde MySQL
    cur.execute("""
        SELECT LOWER(TRIM(t.nombre_tienda)) as n_tienda, z.nombre_zona
        FROM tiendas t
        JOIN regiones r ON t.region_id = r.id
        JOIN zonas z ON r.zona_id = z.id
    """)
    zone_map = {row["n_tienda"]: row["nombre_zona"] for row in cur.fetchall()}

    # 2. Obtener usuarios/tiendas que ya existen en usuarios
    cur.execute("SELECT LOWER(TRIM(Usuario)) as u, LOWER(TRIM(Tienda)) as t FROM usuarios")
    existing_users = set()
    existing_stores = set()
    for row in cur.fetchall():
        if row.get("u"): existing_users.add(row["u"])
        if row.get("t"): existing_stores.add(row["t"])

    n_creados = 0
    n_omitidos_amarillo = 0
    n_omitidos_existentes = 0

    for row_idx in range(2, ws.max_row + 1):
        c_num = ws.cell(row=row_idx, column=1).value
        c_nom = ws.cell(row=row_idx, column=2).value
        if c_num is None or c_nom is None: continue

        num_str = str(c_num).strip()
        nom_str = str(c_nom).strip()

        # Checar relleno amarillo en Excel
        fill = ws.cell(row=row_idx, column=1).fill
        is_yellow = False
        if fill:
            for color_obj in [fill.start_color, fill.fgColor]:
                if color_obj and color_obj.rgb:
                    rgb_str = str(color_obj.rgb)
                    if any(y in rgb_str for y in ['FFFF00', 'FFF200', 'E6E600']):
                        is_yellow = True
                        break

        usuario_key = f"sgh{num_str.lower()}"
        tienda_lower = nom_str.lower()

        if is_yellow:
            n_omitidos_amarillo += 1
            print(f"🟡 OMITIDO (Marcado en Amarillo): {num_str} - {nom_str}")
            continue

        if usuario_key in existing_users or tienda_lower in existing_stores:
            n_omitidos_existentes += 1
            print(f"⏩ OMITIDO (Ya existe en usuarios DB): {num_str} - {nom_str}")
            continue

        # Obtener Zona oficial
        zona_oficial = zone_map.get(tienda_lower, "ZONA CENTRO")

        nombre_completo = f"Tienda {nom_str} ({num_str})"
        contrasena = "sgh12345"
        rol = "Gerente"
        segmento = "SGH"
        puesto = "Gerente de Tienda"
        fecha_now = datetime.datetime.now()

        cur.execute("""
            INSERT INTO usuarios 
            (Usuario, Contrasena, Nombre_Completo, Rol, Fecha_Creacion, Tienda, Segmento, Zona, Puesto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (usuario_key, contrasena, nombre_completo, rol, fecha_now, nom_str, segmento, zona_oficial, puesto))

        n_creados += 1
        existing_users.add(usuario_key)
        existing_stores.add(tienda_lower)
        print(f"✅ CREADO NUEVO USUARIO [{n_creados}]: {usuario_key} | {nom_str} | {zona_oficial}")

    db.commit()
    db.close()

    print("\n==================================================")
    print(f"🎉 IMPORTACIÓN FINALIZADA CON ÉXITO:")
    print(f"   - Usuarios Nuevos Creados: {n_creados}")
    print(f"   - Tiendas Omitidas por Amarillo: {n_omitidos_amarillo}")
    print(f"   - Tiendas Omitidas por DB Existente: {n_omitidos_existentes}")
    print("==================================================")

if __name__ == "__main__":
    ejecutar_importacion()
