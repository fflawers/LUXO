import flet as ft
import os
import glob
import zipfile
import urllib.parse
from datetime import datetime

import mysql.connector

PANAMERICANO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "panamericano")

def conectar_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "los4valtierra"),
            database=os.getenv("DB_NAME", "sgh_portal"),
            port=int(os.getenv("DB_PORT", 3306))
        )
    except Exception as e:
        print("Notice conectar_db en panamericano_view:", e)
        return None

def crear_tablas_panamericano_if_not_exists():
    db = conectar_db()
    if not db:
        return False
    try:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fichas_panamericano (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo_tienda VARCHAR(50),
                nombre_tienda VARCHAR(100),
                nombre_archivo VARCHAR(255) NOT NULL UNIQUE,
                ruta_archivo VARCHAR(255) DEFAULT '',
                tamano_bytes BIGINT DEFAULT 0,
                contenido_blob LONGBLOB,
                fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
                subido_por VARCHAR(100)
            )
        """)
        try:
            cursor.execute("SHOW COLUMNS FROM fichas_panamericano")
            cols_res = cursor.fetchall()
            cols = [r[0] if isinstance(r, (tuple, list)) else r.get("Field") for r in cols_res]
            if "contenido_blob" not in cols:
                cursor.execute("ALTER TABLE fichas_panamericano ADD COLUMN contenido_blob LONGBLOB")
        except Exception: pass
        db.commit()
        db.close()
        return True
    except Exception as ex:
        print("Notice crear_tablas_panamericano_if_not_exists:", ex)
        return False

def asegurar_directorio():
    os.makedirs(PANAMERICANO_DIR, exist_ok=True)
    crear_tablas_panamericano_if_not_exists()

def guardar_ficha_en_db(filename, file_path, subido_por="admin"):
    try:
        if not os.path.exists(file_path):
            return
        f_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f_in:
            blob_data = f_in.read()

        db = conectar_db()
        if db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM fichas_panamericano WHERE nombre_archivo = %s", (filename,))
            cursor.execute("""
                INSERT INTO fichas_panamericano 
                (codigo_tienda, nombre_archivo, ruta_archivo, tamano_bytes, contenido_blob, subido_por)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (filename[:20], filename, file_path, f_size, blob_data, subido_por))
            db.commit()
            db.close()
    except Exception as ex_g:
        print("Error guardando ficha en DB:", ex_g)

def obtener_archivos_panamericano():
    asegurar_directorio()
    archivos = []
    # 1. Intentar leer desde la Base de Datos MySQL (persistente en la Nube)
    try:
        db = conectar_db()
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre_archivo, tamano_bytes, fecha_subida FROM fichas_panamericano ORDER BY nombre_archivo ASC")
            rows = cursor.fetchall()
            db.close()
            for r in rows:
                f_name = r["nombre_archivo"]
                ext = os.path.splitext(f_name)[1].lower()
                mtime = r["fecha_subida"].timestamp() if r.get("fecha_subida") else 0
                archivos.append({
                    "id": r["id"],
                    "nombre": f_name,
                    "path": os.path.join(PANAMERICANO_DIR, f_name),
                    "mtime": mtime,
                    "size": r["tamano_bytes"] or 0,
                    "ext": ext
                })
            if archivos:
                return archivos
    except Exception as ex_db:
        print("Notice obtener_archivos_panamericano db:", ex_db)

    # 2. Fallback a archivos en disco local
    try:
        if os.path.exists(PANAMERICANO_DIR):
            for f in os.listdir(PANAMERICANO_DIR):
                f_path = os.path.join(PANAMERICANO_DIR, f)
                if os.path.isfile(f_path) and not f.startswith("~$") and not f.startswith("."):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in [".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".xls", ".doc", ".docx"]:
                        mtime = os.path.getmtime(f_path)
                        f_size = os.path.getsize(f_path)
                        archivos.append({
                            "nombre": f,
                            "path": f_path,
                            "mtime": mtime,
                            "size": f_size,
                            "ext": ext
                        })
            archivos.sort(key=lambda x: x["nombre"].lower())
    except Exception as ex:
        print("Notice obtener_archivos_panamericano disk:", ex)
    return archivos

def procesar_zip_panamericano(zip_path):
    asegurar_directorio()
    extraidos = 0
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                if not member.is_dir():
                    filename = os.path.basename(member.filename)
                    if filename and not filename.startswith("~$") and not filename.startswith("."):
                        target_path = os.path.join(PANAMERICANO_DIR, filename)
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())
                        guardar_ficha_en_db(filename, target_path)
                        extraidos += 1
    except Exception as ex:
        print("Error al extraer ZIP Panamericano:", ex)
        raise ex
    return extraidos

def build_panamericano_view(page: ft.Page, user_info=None, seleccionar_archivo_async=None):
    asegurar_directorio()
    if user_info is None:
        user_info = {}

    st_code = str(user_info.get("tienda") or "").strip()
    u_role = "admin" if (user_info.get("rol") == "admin" or str(user_info.get("puesto","")).lower() == "admin") else "tienda"

    # Input de Búsqueda
    txt_buscar = ft.TextField(
        hint_text="🔍 Buscar Ficha Panamericano por Número o Nombre de Tienda (ej. A540, 540, Vallejo)...",
        value=st_code if u_role != "admin" else "",
        dense=True,
        border_color="#00FFFF",
        focused_border_color="#D8B4FE",
        color="white",
        width=320
    )

    container_fichas = ft.Column(spacing=10, expand=True)

    def render_fichas(update_page=True):
        archivos = obtener_archivos_panamericano()
        query = (txt_buscar.value or "").strip().lower()

        filtered = []
        for a in archivos:
            nom_lower = a["nombre"].lower()
            if not query or query in nom_lower:
                filtered.append(a)

        if not filtered:
            if query:
                container_fichas.controls = [
                    ft.Container(
                        content=ft.Text(f"⚠️ No se encontró ninguna Ficha Panamericano para: '{txt_buscar.value}'.", color="#aaaaaa", italic=True),
                        padding=15
                    )
                ]
            else:
                container_fichas.controls = [
                    ft.Container(
                        content=ft.Text("📦 No hay Fichas Panamericano cargadas aún. Usa los botones para subir PDFs o un ZIP masivo.", color="#aaaaaa", italic=True),
                        padding=15
                    )
                ]
            if update_page:
                try: page.update()
                except Exception: pass
            return

        items = []
        for a in filtered:
            f_nom = a["nombre"]
            f_size_kb = f"{a['size'] / 1024:.1f} KB" if a['size'] < 1024*1024 else f"{a['size'] / (1024*1024):.2f} MB"
            f_fecha = datetime.fromtimestamp(a["mtime"]).strftime("%d/%m/%Y %H:%M")
            f_encoded = urllib.parse.quote(f_nom)
            url_dl = f"/dl?file={f_encoded}&original={f_encoded}"
            url_view = f"/dl?file={f_encoded}&original={f_encoded}&inline=1"

            # Resaltar si coincide con la tienda activa
            es_mi_tienda = bool(st_code and st_code.lower() in f_nom.lower())
            border_col = "#00FFFF" if es_mi_tienda else "#333344"
            bg_col = "#0f172a" if es_mi_tienda else "#141424"

            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PICTURE_AS_PDF if a["ext"] == ".pdf" else ft.Icons.INSERT_DRIVE_FILE, color="#00FFFF" if es_mi_tienda else "#6E48AA", size=26),
                            ft.Column([
                                ft.Row([
                                    ft.Text(f_nom, weight="bold", size=14, color="white"),
                                    ft.Container(
                                        content=ft.Text("Mi Tienda ⭐", color="black", weight="bold", size=10),
                                        bgcolor="#00FFFF", padding=ft.padding.Padding(6,2,6,2), border_radius=4, visible=es_mi_tienda
                                    )
                                ], spacing=6, wrap=True),
                                ft.Text(f"📅 Modificado: {f_fecha} | 📁 Tamaño: {f_size_kb}", size=11, color="#888888")
                            ], expand=True)
                        ], spacing=8, wrap=True),
                        ft.Row([
                            ft.ElevatedButton(
                                "👁️ Ver Ficha",
                                icon=ft.Icons.VISIBILITY,
                                url=url_view,
                                style=ft.ButtonStyle(color="white", bgcolor="#2563eb")
                            ),
                            ft.ElevatedButton(
                                "📥 Descargar",
                                icon=ft.Icons.DOWNLOAD,
                                url=url_dl,
                                style=ft.ButtonStyle(color="white", bgcolor="#16a34a")
                            )
                        ], spacing=8, wrap=True, alignment=ft.MainAxisAlignment.END)
                    ], spacing=10),
                    padding=12,
                    border=ft.Border.all(1.5 if es_mi_tienda else 1, border_col),
                    border_radius=10,
                    bgcolor=bg_col
                )
            )

        container_fichas.controls = items
        if update_page:
            try: page.update()
            except Exception: pass

    txt_buscar.on_change = lambda e: render_fichas(update_page=True)

    # Handlers para subir PDF individual o ZIP masivo
    def on_subir_pdf_cargado(ruta):
        if not ruta or not os.path.exists(ruta):
            return
        f_name = os.path.basename(ruta)
        target = os.path.join(PANAMERICANO_DIR, f_name)
        if os.path.abspath(ruta) != os.path.abspath(target):
            import shutil
            shutil.copy2(ruta, target)
        guardar_ficha_en_db(f_name, target)
        page.snack_bar = ft.SnackBar(ft.Text(f"✅ Ficha Panamericano '{f_name}' subida correctamente."), open=True)
        render_fichas(update_page=True)

    def on_subir_zip_cargado(ruta):
        if not ruta or not os.path.exists(ruta):
            return
        try:
            cant = procesar_zip_panamericano(ruta)
            page.snack_bar = ft.SnackBar(ft.Text(f"🎉 Extraídas {cant} Fichas Panamericano correctamente desde el ZIP."), open=True)
            render_fichas(update_page=True)
        except Exception as ex_z:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error al procesar el archivo ZIP: {ex_z}"), open=True)
            try: page.update()
            except Exception: pass

    def subir_pdf_click(e):
        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Ficha Panamericano (PDF)",
                [("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
                on_subir_pdf_cargado
            )
        else:
            try:
                from ciclicos_view import seleccionar_archivo_nativo
                p = seleccionar_archivo_nativo("Seleccionar Ficha Panamericano (PDF)")
                if p: on_subir_pdf_cargado(p)
            except Exception as ex:
                print("Notice subir pdf panamericano:", ex)

    def subir_zip_click(e):
        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Archivo ZIP Masivo de Fichas (218 tiendas)",
                [("Archivos ZIP", "*.zip")],
                on_subir_zip_cargado
            )
        else:
            try:
                from ciclicos_view import seleccionar_archivo_nativo
                p = seleccionar_archivo_nativo("Seleccionar Archivo ZIP Masivo")
                if p: on_subir_zip_cargado(p)
            except Exception as ex:
                print("Notice subir zip panamericano:", ex)

    btn_subir_pdf = ft.ElevatedButton(
        "📄 Subir Ficha PDF",
        icon=ft.Icons.UPLOAD_FILE,
        style=ft.ButtonStyle(color="white", bgcolor="#0284c7"),
        on_click=subir_pdf_click
    )

    btn_subir_zip = ft.ElevatedButton(
        "📦 Subir ZIP Masivo",
        icon=ft.Icons.FOLDER_ZIP,
        style=ft.ButtonStyle(color="white", bgcolor="#9D50BB"),
        on_click=subir_zip_click
    )

    btn_refresh = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Actualizar Lista",
        on_click=lambda _: render_fichas(update_page=True)
    )

    # Render inicial sin invocar page.update() durante construccion de vista
    render_fichas(update_page=False)

    return ft.Column([
        ft.Row([
            ft.Text("🚚 FICHAS PANAMERICANO POR TIENDA", size=20, color="#00FFFF", weight="bold"),
            btn_refresh
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        ft.Text("Repositorio dedicado para consultar y descargar la Ficha de Panamericano correspondiente a cada sucursal.", color="#aaaaaa", size=13),
        ft.Divider(height=10, color="#333333"),
        ft.Row([
            txt_buscar,
            btn_subir_pdf,
            btn_subir_zip
        ], spacing=10, wrap=True),
        ft.Divider(height=10, color="transparent"),
        container_fichas
    ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=12)
