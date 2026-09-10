import flet as ft
import os
import openpyxl
import threading
from optics_engine import analizar_tecnologia_optica

def build_catalogo_upc_view(page: ft.Page, user_info=None, conectar_db_fn=None, seleccionar_archivo_async=None):
    """
    Vista de Gestión y Consulta del Catálogo de Inventario UPC (+93,600 Registros).
    Optimizada para rendimiento máximo, 0 lag y respuesta instantánea.
    """
    if user_info is None:
        user_info = {}
    
    is_admin = bool(user_info.get("rol") and str(user_info.get("rol")).strip().lower() in ("admin", "administrador")) or str(user_info.get("usuario", "")).lower() == "admin"
    
    total_codigos_txt = ft.Text("93,661 códigos registrados en MySQL", color="#00FFFF", weight="bold", size=18)
    estado_carga_txt = ft.Text("", color="#7CFC00", size=13, weight="bold")
    progreso_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, color="#00FFFF", visible=False)
    
    # Campo de búsqueda en vivo
    search_input = ft.TextField(
        label="🔍 Buscar por UPC, Modelo o Marca...",
        hint_text="Ej. 8056266264597, RW4011, OO9406, Ray-Ban...",
        border_color="#9D50BB",
        color="white",
        focused_border_color="#00FFFF",
        text_size=14,
        expand=True
    )
    
    search_results_col = ft.Column(spacing=10)

    def refrescar_conteo():
        try:
            if conectar_db_fn:
                db = conectar_db_fn()
                if db:
                    cur = db.cursor()
                    cur.execute("SELECT COUNT(*) FROM catalogo_upcs")
                    res = cur.fetchone()
                    count = res[0] if res else 93661
                    total_codigos_txt.value = f"{count:,} códigos registrados en MySQL"
                    db.close()
                    try: page.update()
                    except: pass
        except Exception as ex:
            print("Error contando UPCs:", ex)

    def renderizar_tarjeta_producto(r):
        marca = str(r.get('marca') or 'Luxottica').strip()
        modelo = str(r.get('modelo') or '').strip()
        color = str(r.get('color') or '').strip()
        desc = str(r.get('descripcion_articulo') or '').strip()
        upc = str(r.get('upc') or '').strip()
        
        info_opt = analizar_tecnologia_optica(marca, modelo, color, desc, upc=upc)
        
        if info_opt.get("es_oftalmico"):
            badge_polar_txt = "👓 OFTÁLMICO"
            badge_polar_bg = "#0C4A6E"
            badge_polar_color = "#38BDF8"
        elif info_opt.get("es_polarizado"):
            badge_polar_txt = "✨ POLARIZADO"
            badge_polar_bg = "#004D40"
            badge_polar_color = "#00FFFF"
        else:
            badge_polar_txt = "☀️ SOLAR UV400"
            badge_polar_bg = "#1A1A3A"
            badge_polar_color = "#D8B4FE"

        if info_opt.get("es_graduable", True):
            badge_grad_txt = "👓 GRADUABLE: SÍ"
            badge_grad_bg = "#064E3B"
            badge_grad_color = "#10B981"
        else:
            badge_grad_txt = "🚫 NO GRADUABLE"
            badge_grad_bg = "#450A0A"
            badge_grad_color = "#F87171"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.QR_CODE_2, color="#00FFFF", size=18),
                        ft.Text(f"{info_opt['marca']} {info_opt['modelo']} {info_opt['color_codigo']}", color="white", weight="bold", size=14),
                    ], spacing=6),
                    ft.Container(
                        content=ft.Text(f"UPC: {upc}", color="#00FFFF", size=11, weight="bold"),
                        bgcolor="#0A2540",
                        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                        border_radius=5,
                        border=ft.Border.all(1, "#00FFFF44")
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Divider(height=1, color="#333355"),

                ft.Row([
                    ft.Container(
                        content=ft.Text(info_opt["coleccion_ano"], color="#FFD700", size=11, weight="bold"),
                        bgcolor="#332B00",
                        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                        border_radius=5,
                    ),
                    ft.Container(
                        content=ft.Text(badge_polar_txt, color=badge_polar_color, size=11, weight="bold"),
                        bgcolor=badge_polar_bg,
                        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                        border_radius=5,
                        border=ft.Border.all(1, f"{badge_polar_color}44")
                    ),
                    ft.Container(
                        content=ft.Text(badge_grad_txt, color=badge_grad_color, size=11, weight="bold"),
                        bgcolor=badge_grad_bg,
                        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                        border_radius=5,
                        border=ft.Border.all(1, f"{badge_grad_color}44")
                    ),
                ], spacing=6),

                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("🧬 Mica:", color="#00FFFF", weight="bold", size=12),
                            ft.Text(info_opt['tecnologia_mica'], color="white", size=12, selectable=True),
                        ], spacing=6),
                        ft.Row([
                            ft.Text("👓 RX Graduable:", color=badge_grad_color, weight="bold", size=12),
                            ft.Text(info_opt.get('graduacion_detalle', 'Compatible con graduación'), color="white", size=12, selectable=True),
                        ], spacing=6),
                        ft.Row([
                            ft.Text("🎯 Uso Ideal:", color="#D8B4FE", weight="bold", size=12),
                            ft.Text(info_opt['uso_ideal'], color="#DDDDDD", size=12, selectable=True),
                        ], spacing=6),
                        ft.Row([
                            ft.Text("🔬 Specs:", color="#7CFC00", weight="bold", size=12),
                            ft.Text(f"{info_opt['nanometros']}  •  VLT: {info_opt['vlt_porcentaje']}", color="#DDDDDD", size=12, selectable=True),
                        ], spacing=6),
                        ft.Row([
                            ft.Text("💬 Story (20s):", color="#FF9900", weight="bold", size=12),
                            ft.Text(f'"{info_opt["storytelling"]}"', color="#FFFFFF", italic=True, size=12, selectable=True),
                        ], spacing=6),
                    ], spacing=4),
                    bgcolor="#121222",
                    padding=8,
                    border_radius=6
                ),

                ft.Row([
                    ft.ElevatedButton(
                        "🌐 Ver Fotos en Google",
                        icon=ft.Icons.TRAVEL_EXPLORE,
                        url=info_opt['google_img_url'],
                        bgcolor="#0A3C60",
                        color="#00FFFF",
                        height=32,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6),
                            side=ft.BorderSide(1, "#00FFFF")
                        )
                    ),
                    ft.Text(f"Ref: {desc}", color="#8888AA", size=10, italic=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment="center")
            ], spacing=6),
            bgcolor="#18182A",
            padding=12,
            border_radius=10,
            border=ft.Border.all(1, "#2A2A44"),
        )

    def ejecutar_busqueda(e=None):
        query = search_input.value.strip()
        if not query:
            search_results_col.controls.clear()
            search_results_col.controls.append(
                ft.Text("💡 Escribe un código UPC (ej. 8056266264597) o un modelo (ej. RW4011) para buscar.", color="#8888AA", italic=True)
            )
            try: page.update()
            except: pass
            return
            
        search_results_col.controls.clear()
        search_results_col.controls.append(
            ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2, color="#00FFFF"), ft.Text(f"Buscando '{query}'...", color="#00FFFF", size=12)], spacing=8)
        )
        try: page.update()
        except: pass

        try:
            if conectar_db_fn:
                db = conectar_db_fn()
                if db:
                    cur = db.cursor(dictionary=True)
                    q_num = "".join(filter(str.isdigit, query))
                    
                    if len(q_num) >= 6:
                        cur.execute("""
                            SELECT * FROM catalogo_upcs 
                            WHERE upc = %s OR upc LIKE %s
                            LIMIT 20
                        """, (q_num, f"{q_num}%"))
                    else:
                        cur.execute("""
                            SELECT * FROM catalogo_upcs 
                            WHERE modelo = %s OR modelo LIKE %s OR marca = %s
                            LIMIT 20
                        """, (query, f"{query}%", query))
                    
                    rows = cur.fetchall()
                    db.close()

                    search_results_col.controls.clear()
                    if not rows:
                        search_results_col.controls.append(
                            ft.Container(
                                content=ft.Text(f"No se encontraron coincidencias para '{query}' en el catálogo.", color="#FFA500", size=12, italic=True),
                                padding=8
                            )
                        )
                    else:
                        search_results_col.controls.append(
                            ft.Text(f"✅ Se encontraron {len(rows)} resultados para '{query}':", color="#7CFC00", weight="bold", size=12)
                        )
                        for r in rows:
                            search_results_col.controls.append(renderizar_tarjeta_producto(r))
        except Exception as ex:
            print("Error buscando:", ex)
            search_results_col.controls.clear()
            search_results_col.controls.append(ft.Text(f"Error en consulta: {ex}", color="red"))
        
        try: page.update()
        except: pass

    search_input.on_submit = ejecutar_busqueda
    btn_buscar = ft.ElevatedButton("Buscar 🔍", on_click=ejecutar_busqueda, bgcolor="#6E48AA", color="white")

    # MÓDULO DE ACTUALIZACIÓN DE EXCEL PARA ADMINISTRADORES
    def procesar_archivo_excel(ruta_archivo):
        progreso_ring.visible = True
        estado_carga_txt.value = "Leyendo archivo Excel... Por favor espera."
        estado_carga_txt.color = "#00FFFF"
        try: page.update()
        except: pass

        def thread_import():
            try:
                db = conectar_db_fn()
                if not db:
                    estado_carga_txt.value = "Error al conectar con la base de datos."
                    estado_carga_txt.color = "red"
                    progreso_ring.visible = False
                    try: page.update()
                    except: pass
                    return

                cursor = db.cursor()
                wb = openpyxl.load_workbook(ruta_archivo, read_only=True, data_only=True)
                sheet = wb["Base"] if "Base" in wb.sheetnames else wb[wb.sheetnames[0]]

                cursor.execute("TRUNCATE TABLE catalogo_upcs;")
                db.commit()

                batch = []
                total = 0
                insert_query = """
                    INSERT INTO catalogo_upcs (
                        upc, marca, articulo, descripcion_articulo, modelo, color, site, short_name, region, zona
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                for i, row in enumerate(sheet.iter_rows(values_only=True)):
                    if i == 0: continue
                    upc_raw = str(row[0] or "").strip() if len(row) > 0 and row[0] is not None else ""
                    if not upc_raw: continue
                    if "." in upc_raw and upc_raw.replace(".", "").isdigit():
                        upc_raw = upc_raw.split(".")[0]
                    
                    marca = str(row[1] or "").strip() if len(row) > 1 and row[1] is not None else ""
                    articulo = str(row[2] or "").strip() if len(row) > 2 and row[2] is not None else ""
                    desc_art = str(row[5] or "").strip() if len(row) > 5 and row[5] is not None else ""
                    modelo = str(row[6] or "").strip() if len(row) > 6 and row[6] is not None else ""
                    color = str(row[7] or "").strip() if len(row) > 7 and row[7] is not None else ""
                    site = str(row[9] or "").strip() if len(row) > 9 and row[9] is not None else ""
                    short_name = str(row[10] or "").strip() if len(row) > 10 and row[10] is not None else ""
                    region = str(row[11] or "").strip() if len(row) > 11 and row[11] is not None else ""
                    zona = str(row[12] or "").strip() if len(row) > 12 and row[12] is not None else ""

                    batch.append((upc_raw, marca, articulo, desc_art, modelo, color, site, short_name, region, zona))
                    if len(batch) >= 5000:
                        cursor.executemany(insert_query, batch)
                        db.commit()
                        total += len(batch)
                        estado_carga_txt.value = f"Insertando códigos: {total:,} en MySQL..."
                        try: page.update()
                        except: pass
                        batch = []

                if batch:
                    cursor.executemany(insert_query, batch)
                    db.commit()
                    total += len(batch)

                wb.close()
                cursor.close()
                db.close()

                progreso_ring.visible = False
                estado_carga_txt.value = f"✅ ¡Catálogo actualizado con éxito! {total:,} códigos registrados."
                estado_carga_txt.color = "#7CFC00"
                refrescar_conteo()
                try: page.update()
                except: pass
            except Exception as ex_imp:
                print("Error importando Excel:", ex_imp)
                progreso_ring.visible = False
                estado_carga_txt.value = f"Error al procesar Excel: {ex_imp}"
                estado_carga_txt.color = "red"
                try: page.update()
                except: pass

        threading.Thread(target=thread_import, daemon=True).start()

    def on_subir_excel_click(e):
        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Base de Datos Excel (.xlsx)",
                [("Archivos Excel", "*.xlsx;*.xls"), ("Todos los archivos", "*.*")],
                procesar_archivo_excel
            )
        else:
            try:
                from tkinter import Tk, filedialog
                root = Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                f_path = filedialog.askopenfilename(
                    title="Seleccionar Base de Datos Excel (.xlsx)",
                    filetypes=[("Archivos Excel", "*.xlsx;*.xls"), ("Todos los archivos", "*.*")]
                )
                root.destroy()
                if f_path:
                    procesar_archivo_excel(f_path)
            except Exception as ex_f:
                print("Error abriendo diálogo de archivo:", ex_f)

    btn_subir_excel = ft.ElevatedButton(
        "Subir Nuevo Excel de Inventario (.xlsx) 📑",
        icon=ft.Icons.UPLOAD_FILE_ROUNDED,
        bgcolor="#1f6f43",
        color="white",
        on_click=on_subir_excel_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    admin_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color="#FFD700", size=20),
                ft.Text("PANEL DE ADMINISTRACIÓN: ACTUALIZAR CATÁLOGO EXCEL", color="#FFD700", weight="bold", size=13),
            ], spacing=8),
            ft.Text("Sube el archivo Excel de inventario más reciente para actualizar automáticamente la base de datos de MySQL en 1 clic.", color="#cccccc", size=11),
            ft.Row([btn_subir_excel, progreso_ring, estado_carga_txt], spacing=10, vertical_alignment="center", wrap=True)
        ], spacing=8),
        bgcolor="#221e10",
        padding=12,
        border_radius=8,
        border=ft.Border.all(1, "#FFD70055"),
        visible=is_admin
    )

    search_results_col.controls.append(
        ft.Text("💡 Escribe un código UPC (ej. 8056266264597) o un modelo (ej. RW4011) en el buscador para consultar.", color="#8888AA", size=12, italic=True)
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, color="#00FFFF", size=24),
                ft.Text("Catálogo e Inventario Óptico de UPCs 🕶️", size=20, color="#D8B4FE", weight="bold"),
            ], spacing=8),
            ft.Text("Consulta instantánea de más de 93,660 gafas con tecnologías de mica, nanómetros, año de colección, uso ideal y fotos oficiales.", color="#aaaaaa", size=11),
            ft.Divider(height=5, color="#333333"),
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("ESTADO DE LA BASE DE DATOS:", color="#aaaaaa", size=10),
                        total_codigos_txt
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.ElevatedButton("Refrescar 🔄", on_click=lambda e: refrescar_conteo(), bgcolor="#2A1B4E", color="white")
                ], vertical_alignment="center"),
                bgcolor="#141424",
                padding=10,
                border_radius=8,
                border=ft.Border.all(1, "#2A1B4E")
            ),
            admin_panel,
            ft.Row([search_input, btn_buscar], spacing=8),
            search_results_col
        ], scroll=ft.ScrollMode.AUTO, spacing=12),
        padding=16,
        expand=True
    )
