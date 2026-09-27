import flet as ft
import os
import glob
import json
import base64
import threading
import shutil
import cv2
import calendar
from datetime import datetime, timedelta
import disa_engine

DISA_UPLOADS_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "disa_cortes")
DISA_STATUS_FILE = os.path.join(DISA_UPLOADS_BASE, "disa_status.json")

MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
DIAS_SEMANA_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

def load_disa_status_dict():
    try:
        if os.path.exists(DISA_STATUS_FILE):
            with open(DISA_STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_disa_status_dict(data):
    try:
        with open(DISA_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as ex:
        print("Error saving disa status dict:", ex)

def get_day_record(store_id, date_str):
    data = load_disa_status_dict()
    key = f"{store_id}_{date_str}"
    return data.get(key, {})

def get_day_status(store_id, date_str):
    data = load_disa_status_dict()
    key = f"{store_id}_{date_str}"
    if key in data and data[key].get("status"):
        return data[key].get("status")
    target_dir = os.path.join(DISA_UPLOADS_BASE, date_str, f"Tienda_{store_id}")
    if os.path.exists(target_dir):
        files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if len(files) > 0:
            has_notas = any(f.startswith("12_Notas_Manuales") for f in files)
            if has_notas:
                return "ENVIADO"
            return "ENVIADO"
    return ""

def set_day_status(store_id, date_str, status_val, total_docs=0, note="", observacion=""):
    data = load_disa_status_dict()
    key = f"{store_id}_{date_str}"
    if key not in data:
        data[key] = {}
    data[key].update({
        "status": status_val,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_docs": total_docs,
        "store_id": store_id,
        "date": date_str,
        "note": note
    })
    if observacion:
        data[key]["observacion"] = observacion
    save_disa_status_dict(data)

def save_day_aclaracion(store_id, date_str, aclaracion_text):
    data = load_disa_status_dict()
    key = f"{store_id}_{date_str}"
    if key not in data:
        data[key] = {
            "status": "AMARILLO",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_docs": 0,
            "store_id": store_id,
            "date": date_str
        }
    data[key]["aclaracion"] = aclaracion_text
    data[key]["aclaracion_fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_disa_status_dict(data)

def get_store_observations(store_id):
    data = load_disa_status_dict()
    res = []
    # Collect any records with observations, status AMARILLO, or aclaraciones
    for k, v in data.items():
        if v.get("store_id") == store_id or k.startswith(f"{store_id}_"):
            d = v.get("date", k.replace(f"{store_id}_", ""))
            obs = v.get("observacion") or v.get("note") or ""
            aclar = v.get("aclaracion") or ""
            st = v.get("status") or ""
            # If has observation or is amarillo or has aclaracion
            if obs or st == "AMARILLO" or aclar:
                res.append({
                    "date": d,
                    "status": st,
                    "observacion": obs if obs else "⚠️ Faltante / Observación pendiente en el corte de caja.",
                    "aclaracion": aclar,
                    "aclaracion_fecha": v.get("aclaracion_fecha", ""),
                    "total_docs": v.get("total_docs", 0)
                })
    res = sorted(res, key=lambda x: x["date"], reverse=True)
    return res

TIENDAS_MOCK = [
    "3502 - Interlomas 1",
    "3503 - Santa Fe",
    "3504 - Perisur",
    "3505 - Antara",
    "3506 - Plaza Satélite",
    "3507 - Mitikah",
    "3508 - Oasis Coyoacán",
    "3509 - Paseo Acoxpa",
    "3510 - Parque Delta",
    "3511 - Galerías Insurgentes"
]

# Exact 13 categories from official DiSA App
DISA_SECTIONS = [
    {
        "id": "01_Informe_Diario_Ventas",
        "title": "INFORME DIARIO DE VENTAS",
        "subtitle": "Captura 1 fotografía mínimo.",
        "obligatorio": True
    },
    {
        "id": "02_Informe_Reconciliacion",
        "title": "INFORME DE RECONCILIACIÓN",
        "subtitle": "Captura 1 fotografía mínimo.",
        "obligatorio": True
    },
    {
        "id": "03_Vouchers",
        "title": "VOUCHERS",
        "subtitle": "Captura los vouchers necesarios.",
        "obligatorio": False
    },
    {
        "id": "04_Ticket_Cierre_Dia",
        "title": "TICKET DE CIERRE DE DÍA",
        "subtitle": "Captura 1 fotografía (Obligatoria).",
        "obligatorio": True
    },
    {
        "id": "05_Fichas_Deposito",
        "title": "FICHAS DE DEPÓSITO",
        "subtitle": "Captura 1 fotografía máximo (Si aplica el caso).",
        "obligatorio": False
    },
    {
        "id": "06_Tira_Casa_Cambio",
        "title": "TIRA DE CASA DE CAMBIO",
        "subtitle": "Captura 1 fotografía máximo (Si aplica el caso).",
        "obligatorio": False
    },
    {
        "id": "07_Cierre_Terminal",
        "title": "CIERRE DE TERMINAL",
        "subtitle": "Captura 1 fotografía máximo (Obligatoria).",
        "obligatorio": True
    },
    {
        "id": "08_Credito_Tienda",
        "title": "CRÉDITO DE TIENDA",
        "subtitle": "Captura las fotografías necesarias.",
        "obligatorio": False
    },
    {
        "id": "09_Gift_Card",
        "title": "GIFT CARD",
        "subtitle": "Captura las fotografías necesarias.",
        "obligatorio": False
    },
    {
        "id": "10_Gafa_Aniversario",
        "title": "GAFA ANIVERSARIO",
        "subtitle": "Captura 1 fotografía formato y 1 de ticket (Si aplica el caso).",
        "obligatorio": False
    },
    {
        "id": "11_Deposito_Panamericano_Banco",
        "title": "DEPÓSITO PANAMERICANO/BANCO",
        "subtitle": "Captura 1 fotografía máximo (Requerido si hubo venta en efectivo).",
        "obligatorio": False
    },
    {
        "id": "12_Notas_Manuales",
        "title": "NOTAS MANUALES",
        "subtitle": "Captura las fotografías necesarias (Ampara operación sin sistema en tienda; valida corte en verde).",
        "obligatorio": False
    },
    {
        "id": "13_Ticket_Venta",
        "title": "TICKETS DE VENTAS",
        "subtitle": "Captura las fotografías necesarias. Recuerda que cada ticket debe de ir firmado por el cliente y con su sello correspondiente, ya que es una copia exacta de la que se le da al cliente.",
        "obligatorio": False
    }
]

def build_disa_view(page: ft.Page, user_info=None, seleccionar_archivo_async=None):
    os.makedirs(DISA_UPLOADS_BASE, exist_ok=True)
    if user_info is None:
        user_info = {}
        
    u_role = str(user_info.get("rol") or user_info.get("puesto") or "").lower().strip()
    es_admin = (u_role == "admin" or user_info.get("rol") == "admin")
    
    user_store = "3502"
    st_raw = str(user_info.get("codigo_tienda") or user_info.get("tienda") or "3502").strip()
    st_digits = "".join(filter(str.isdigit, st_raw))
    if st_digits:
        user_store = st_digits
        
    # Match default store name
    matched_store = f"{user_store} - Tienda {user_store}"
    for t in TIENDAS_MOCK:
        if t.startswith(user_store):
            matched_store = t
            break

    current_date = [datetime.now().strftime("%Y-%m-%d")]
    date_btn_text = ft.Text(current_date[0], size=14, weight=ft.FontWeight.BOLD, color="white")
    
    status_text = ft.Text("Listo para procesar cortes DiSA.", size=12, color="#00FFFF")
    progress_bar = ft.ProgressBar(visible=False, color="#00FFFF")
    
    sections_column = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO)
    
    # Store selector: Dropdown for admin, Fixed text for store employee
    if es_admin:
        dd_tienda = ft.Dropdown(
            label="Tienda / Sucursal (Admin)",
            value=matched_store,
            options=[ft.dropdown.Option(t) for t in TIENDAS_MOCK],
            width=240,
            dense=True,
            border_color="#00FFFF",
            color="white"
        )
    else:
        dd_tienda = None
        
    def get_current_store_code():
        if es_admin and dd_tienda and dd_tienda.value:
            return dd_tienda.value.split(" - ")[0].strip()
        return user_store

    # --- Built-in Full Screen HD Modal Image Viewer with 2D Scroll & Download ---
    zoom_level = [1.0]
    base_w = 880
    base_h = 520

    dlg_img = ft.Image(
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAA",
        fit="contain",
        width=base_w,
        height=base_h
    )
    zoom_label = ft.Text("100%", size=12, color="#00FFFF", weight=ft.FontWeight.BOLD)
    dlg_title = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="white", expand=True)
    dlg_prev_btn = ft.ElevatedButton("◀ Anterior", style=ft.ButtonStyle(bgcolor="#008080", color="white"))
    dlg_next_btn = ft.ElevatedButton("Siguiente ▶", style=ft.ButtonStyle(bgcolor="#008080", color="white"))
    current_modal_data = {"title": "", "files": [], "idx": 0}

    pos_x = [0.0]
    pos_y = [0.0]

    def on_pan_update_img(e: ft.DragUpdateEvent):
        pos_x[0] += e.delta_x
        pos_y[0] += e.delta_y
        img_positioned.left = pos_x[0]
        img_positioned.top = pos_y[0]
        try: page.update()
        except Exception: pass

    img_gesture = ft.GestureDetector(
        content=dlg_img,
        on_pan_update=on_pan_update_img,
        mouse_cursor=ft.MouseCursor.MOVE
    )

    img_positioned = ft.Container(
        content=img_gesture,
        left=0,
        top=0,
        width=base_w,
        height=base_h
    )

    viewport_stack = ft.Stack(
        controls=[img_positioned],
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        width=920,
        height=550
    )

    def apply_zoom():
        z = zoom_level[0]
        zoom_label.value = f"{int(z * 100)}%"
        w = int(base_w * z)
        h = int(base_h * z)
        dlg_img.width = w
        dlg_img.height = h
        img_positioned.width = w
        img_positioned.height = h
        try: page.update()
        except Exception: pass

    def zoom_in(e=None):
        if zoom_level[0] < 5.0:
            zoom_level[0] = round(zoom_level[0] + 0.35, 2)
            apply_zoom()

    def zoom_out(e=None):
        if zoom_level[0] > 0.5:
            zoom_level[0] = round(zoom_level[0] - 0.35, 2)
            apply_zoom()

    def zoom_reset(e=None):
        zoom_level[0] = 1.0
        pos_x[0] = 0.0
        pos_y[0] = 0.0
        img_positioned.left = 0
        img_positioned.top = 0
        apply_zoom()

    def descargar_foto_actual(e=None):
        files = current_modal_data["files"]
        idx = current_modal_data["idx"]
        if files and idx < len(files):
            fp = files[idx]
            try:
                rel_path = os.path.relpath(fp, os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")).replace("\\", "/")
                download_url = f"/uploads/{rel_path}"
                page.launch_url(download_url)
            except Exception as ex:
                print("Error downloading disa image:", ex)

    def close_modal(e=None):
        disa_modal.open = False
        zoom_reset()
        try: page.update()
        except Exception: pass

    def delete_modal_file(e=None):
        files = current_modal_data["files"]
        idx = current_modal_data["idx"]
        if files and idx < len(files):
            fp = files[idx]
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception as ex:
                print("Error deleting disa file:", ex)
        close_modal()
        render_disa_categories()

    def rotate_current_img(clockwise=True):
        files = current_modal_data["files"]
        idx = current_modal_data["idx"]
        if files and idx < len(files):
            fp = files[idx]
            try:
                im = cv2.imread(fp)
                if im is not None:
                    code = cv2.ROTATE_90_CLOCKWISE if clockwise else cv2.ROTATE_90_COUNTERCLOCKWISE
                    im_rot = cv2.rotate(im, code)
                    cv2.imwrite(fp, im_rot, [cv2.IMWRITE_JPEG_QUALITY, 98])
                    update_modal_content()
                    render_disa_categories()
            except Exception as ex:
                print("Error rotating img:", ex)

    def update_modal_content():
        files = current_modal_data["files"]
        idx = current_modal_data["idx"]
        total = len(files)
        if not files or idx >= total:
            close_modal()
            return
            
        fp = files[idx]
        dlg_title.value = f"{current_modal_data['title']} ({idx + 1}/{total})"
        dlg_prev_btn.visible = (total > 1 and idx > 0)
        dlg_next_btn.visible = (total > 1 and idx < total - 1)
        
        try:
            with open(fp, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
                dlg_img.src = f"data:image/jpeg;base64,{b64_str}"
                dlg_img.src_base64 = b64_str
        except Exception as ex:
            print("Error loading disa img base64:", ex)
            
        try: page.update()
        except Exception: pass

    def prev_modal_img(e):
        if current_modal_data["idx"] > 0:
            current_modal_data["idx"] -= 1
            zoom_reset()
            update_modal_content()

    def next_modal_img(e):
        if current_modal_data["idx"] < len(current_modal_data["files"]) - 1:
            current_modal_data["idx"] += 1
            zoom_reset()
            update_modal_content()

    dlg_prev_btn.on_click = prev_modal_img
    dlg_next_btn.on_click = next_modal_img

    disa_modal = ft.AlertDialog(
        modal=True,
        bgcolor="#10121e",
        title=ft.Row([
            ft.Icon(ft.Icons.DOCUMENT_SCANNER_ROUNDED, color="#00FFFF", size=26),
            dlg_title,
            ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_CIRCLE_DOWN_ROUNDED,
                    tooltip="📥 Descargar Imagen Completa (Alta Resolución)",
                    icon_color="#00FF7F",
                    icon_size=28,
                    on_click=descargar_foto_actual
                ),
                ft.VerticalDivider(width=1, color="#334155"),
                ft.IconButton(ft.Icons.ZOOM_OUT_ROUNDED, tooltip="Alejar Zoom (-)", icon_color="#94a3b8", on_click=zoom_out),
                zoom_label,
                ft.IconButton(ft.Icons.ZOOM_IN_ROUNDED, tooltip="Acercar Zoom (+)", icon_color="#00FFFF", on_click=zoom_in),
                ft.IconButton(ft.Icons.RESTORE_ROUNDED, tooltip="Restablecer (100%)", icon_color="#94a3b8", on_click=zoom_reset),
                ft.VerticalDivider(width=1, color="#334155"),
                ft.IconButton(ft.Icons.ROTATE_LEFT_ROUNDED, tooltip="Rotar Izquierda (↺)", icon_color="#00FFFF", on_click=lambda _: rotate_current_img(False)),
                ft.IconButton(ft.Icons.ROTATE_RIGHT_ROUNDED, tooltip="Rotar Derecha (↻)", icon_color="#00FFFF", on_click=lambda _: rotate_current_img(True)),
                ft.IconButton(ft.Icons.CLOSE, icon_color="white", on_click=close_modal)
            ], spacing=4)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        content=ft.Container(
            content=ft.Column([
                ft.Container(
                    content=viewport_stack,
                    height=550,
                    width=920,
                    bgcolor="#080911",
                    border_radius=8,
                    padding=4
                ),
                ft.Row([
                    dlg_prev_btn,
                    ft.Text("🖐️ Haz clic y arrastra con el ratón en cualquier dirección (2D) para mover la imagen | Usa (+ / -) para Zoom", size=11, color="#64748b"),
                    dlg_next_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], tight=True, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=940,
            height=630,
            padding=5
        ),
        actions=[
            ft.TextButton("🗑️ Eliminar Documento", on_click=delete_modal_file, style=ft.ButtonStyle(color="#FF4500")),
            ft.ElevatedButton("Cerrar", on_click=close_modal, style=ft.ButtonStyle(bgcolor="#334155", color="white"))
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    page.overlay.append(disa_modal)

    def show_image_viewer(title, filepaths, start_idx=0):
        if not filepaths:
            return
        current_modal_data["title"] = title
        current_modal_data["files"] = list(filepaths)
        current_modal_data["idx"] = max(0, min(start_idx, len(filepaths) - 1))
        update_modal_content()
        disa_modal.open = True
        try: page.update()
        except Exception: pass

    def delete_single_file(fp):
        try:
            if os.path.exists(fp):
                os.remove(fp)
        except Exception as ex:
            print("Error deleting single disa file:", ex)
        render_disa_categories()

    def trigger_upload(categoria_id=None, categoria_nombre="Corte"):
        def _cb(p):
            on_foto_cargada(p, categoria_id)

        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                f"Capturar {categoria_nombre}",
                [("Imágenes", "*.jpg;*.jpeg;*.png;*.webp"), ("Todos los archivos", "*.*")],
                _cb
            )
        else:
            try:
                from ciclicos_view import seleccionar_archivo_nativo
                p = seleccionar_archivo_nativo(f"Capturar {categoria_nombre}")
                if p: _cb(p)
            except Exception as ex:
                print("Notice capturar foto disa:", ex)

    def render_disa_categories():
        st_code = get_current_store_code()
        date_str = current_date[0]
        target_dir = os.path.join(DISA_UPLOADS_BASE, date_str, f"Tienda_{st_code}")
        
        archivos_existentes = glob.glob(os.path.join(target_dir, "*.jpg")) if os.path.exists(target_dir) else []
        
        # Map existing files to section IDs
        files_by_section = {}
        for fpath in archivos_existentes:
            fname = os.path.basename(fpath)
            for sec in DISA_SECTIONS:
                sec_id = sec["id"]
                if fname.startswith(sec_id) or (sec_id == "13_Ticket_Venta" and "ticket_venta" in fname.lower()):
                    if sec_id not in files_by_section:
                        files_by_section[sec_id] = []
                    files_by_section[sec_id].append(fpath)
                    break

        section_blocks = []
        for sec in DISA_SECTIONS:
            sec_id = sec["id"]
            sec_title = sec["title"]
            sec_sub = sec["subtitle"]
            sec_files = sorted(files_by_section.get(sec_id, []))
            
            has_files = len(sec_files) > 0
            
            # Category Header Bar matching Tablet Design
            header_row = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(sec_title, size=15, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(sec_sub, size=12, color="#94a3b8")
                    ], spacing=2),
                    ft.Container(
                        content=ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, color="white", size=24),
                        padding=8,
                        bgcolor="#00B4D8",
                        border_radius=8,
                        ink=True,
                        tooltip=f"Capturar foto para {sec_title}",
                        on_click=lambda e, sid=sec_id, stitle=sec_title: trigger_upload(sid, stitle)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=12,
                bgcolor="#161829",
                border_radius=8
            )

            # Thumbnails Row/Grid under the header (Matching Tablet Design)
            if has_files:
                thumb_controls = []
                for f_idx, fp in enumerate(sec_files):
                    # Load base64 for thumbnail
                    try:
                        with open(fp, "rb") as f_thumb:
                            b64_thumb = base64.b64encode(f_thumb.read()).decode("utf-8")
                            thumb_src = f"data:image/jpeg;base64,{b64_thumb}"
                    except Exception:
                        thumb_src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAA"

                    thumb_card = ft.Stack([
                        # Image Clickable Area
                        ft.Container(
                            content=ft.Image(
                                src=thumb_src,
                                width=115,
                                height=135,
                                fit="cover",
                                border_radius=8
                            ),
                            border=ft.Border.all(1.5, "#00FFFF"),
                            border_radius=8,
                            ink=True,
                            tooltip="Clic para ver en pantalla completa",
                            on_click=lambda e, stitle=sec_title, sfiles=sec_files, sidx=f_idx: show_image_viewer(stitle, sfiles, sidx)
                        ),
                        # Floating Close/Delete Badge in Top-Right
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=14,
                                icon_color="white",
                                bgcolor="#e11d48",
                                tooltip="Eliminar esta foto",
                                on_click=lambda e, del_fp=fp: delete_single_file(del_fp)
                            ),
                            top=-6,
                            right=-6,
                            width=28,
                            height=28
                        )
                    ], width=125, height=145)
                    thumb_controls.append(thumb_card)

                thumbnails_container = ft.Container(
                    content=ft.Row(
                        thumb_controls,
                        wrap=True,
                        spacing=12,
                        run_spacing=12
                    ),
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor="#0d0e1a",
                    border_radius=8
                )
                
                cat_container = ft.Column([
                    header_row,
                    thumbnails_container
                ], spacing=4)
            else:
                cat_container = ft.Column([
                    header_row
                ], spacing=0)

            section_blocks.append(cat_container)
            
        sections_column.controls = section_blocks
        try: page.update()
        except Exception: pass

    if es_admin and dd_tienda:
        dd_tienda.on_change = lambda e: render_disa_categories()

    # Custom Spanish Smart Calendar with Traffic Light Semáforo
    cal_year = [datetime.now().year]
    cal_month = [datetime.now().month]
    cal_title_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="white")
    cal_store_text = ft.Text("", size=12, color="#00FFFF")
    cal_grid_column = ft.Column(spacing=6, alignment=ft.MainAxisAlignment.CENTER)

    def render_calendar_grid():
        y = cal_year[0]
        m = cal_month[0]
        cal_title_text.value = f"{MESES_ES[m]} {y}"
        cal_store_text.value = f"Sucursal: {get_current_store_code()}"
        
        st_code = get_current_store_code()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Day of week header row (Spanish)
        header_cells = [
            ft.Container(
                content=ft.Text(day_name, size=11, weight=ft.FontWeight.BOLD, color="#94a3b8"),
                width=44,
                height=26,
                alignment=ft.Alignment(0, 0)
            ) for day_name in DIAS_SEMANA_ES
        ]
        week_rows = [ft.Row(header_cells, spacing=6, alignment=ft.MainAxisAlignment.CENTER)]
        
        weeks = calendar.monthcalendar(y, m)
        for w in weeks:
            day_cells = []
            for d in w:
                if d == 0:
                    day_cells.append(ft.Container(width=44, height=44, bgcolor="transparent"))
                else:
                    d_str = f"{y:04d}-{m:02d}-{d:02d}"
                    st = get_day_status(st_code, d_str)
                    
                    is_active = (d_str == current_date[0])
                    is_today = (d_str == today_str)
                    
                    if st in ("ENVIADO", "FUERA_DE_OPERACION"):
                        bg_color = "#00C853"  # Green (Submitted / Manual Notes)
                        text_color = "white"
                        badge_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=12, color="white")
                        tip = f"✅ Corte Enviado ({d_str})" if st == "ENVIADO" else f"🟡 Fuera de Operación ({d_str})"
                    elif st in ("AMARILLO", "OBSERVACION"):
                        bg_color = "#F59E0B"  # Yellow (Pending Panamericano / Observation)
                        text_color = "white"
                        badge_icon = ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, size=12, color="white")
                        tip = f"⚠️ Corte con Observación / Faltante ({d_str})"
                    elif d_str < today_str:
                        bg_color = "#D32F2F"  # Red (Past day pending / not submitted)
                        text_color = "white"
                        badge_icon = ft.Icon(ft.Icons.WARNING_ROUNDED, size=12, color="white")
                        tip = f"❌ Corte Pendiente / No Enviado ({d_str})"
                    elif is_today:
                        bg_color = "#1E293B"  # Today in progress
                        text_color = "#00FFFF"
                        badge_icon = ft.Icon(ft.Icons.SCHEDULE, size=12, color="#00FFFF")
                        tip = f"📅 Hoy ({d_str}) - En Curso"
                    else:
                        bg_color = "#141424"  # Future
                        text_color = "#64748b"
                        badge_icon = None
                        tip = f"⏳ Día Futuro ({d_str})"
                        
                    border_style = ft.Border.all(2, "#00FFFF") if is_active else (
                        ft.Border.all(1.5, "#38bdf8") if is_today else ft.Border.all(1, "#262638")
                    )
                    
                    cell_content = ft.Column([
                        ft.Text(str(d), size=12, weight=ft.FontWeight.BOLD, color=text_color),
                        badge_icon if badge_icon else ft.Container(height=4)
                    ], spacing=1, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    
                    def make_day_click(selected_d):
                        def handler(e):
                            current_date[0] = selected_d
                            date_btn_text.value = selected_d
                            calendar_modal.open = False
                            render_disa_categories()
                            try: page.update()
                            except Exception: pass
                        return handler
                        
                    day_cells.append(
                        ft.Container(
                            content=cell_content,
                            width=44,
                            height=44,
                            bgcolor=bg_color,
                            border=border_style,
                            border_radius=8,
                            alignment=ft.Alignment(0, 0),
                            tooltip=tip,
                            ink=True,
                            on_click=make_day_click(d_str)
                        )
                    )
            week_rows.append(ft.Row(day_cells, spacing=6, alignment=ft.MainAxisAlignment.CENTER))
            
        cal_grid_column.controls = week_rows
        try: page.update()
        except Exception: pass

    def cambiar_cal_mes(delta):
        m = cal_month[0] + delta
        y = cal_year[0]
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        cal_month[0] = m
        cal_year[0] = y
        render_calendar_grid()

    def ir_a_hoy(e=None):
        now = datetime.now()
        cal_year[0] = now.year
        cal_month[0] = now.month
        current_date[0] = now.strftime("%Y-%m-%d")
        date_btn_text.value = current_date[0]
        calendar_modal.open = False
        render_disa_categories()
        try: page.update()
        except Exception: pass

    def cerrar_calendario(e=None):
        calendar_modal.open = False
        try: page.update()
        except Exception: pass

    calendar_modal = ft.AlertDialog(
        modal=True,
        bgcolor="#10121e",
        title=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_ROUNDED, icon_color="#00FFFF", icon_size=18, on_click=lambda _: cambiar_cal_mes(-1)),
            ft.Column([
                cal_title_text,
                cal_store_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            ft.IconButton(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, icon_color="#00FFFF", icon_size=18, on_click=lambda _: cambiar_cal_mes(1))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        content=ft.Container(
            content=ft.Column([
                cal_grid_column,
                ft.Divider(height=1, color="#262638"),
                ft.Row([
                    ft.Row([ft.Container(width=10, height=10, bgcolor="#00C853", border_radius=5), ft.Text("Enviado", size=10, color="#94a3b8")], spacing=3),
                    ft.Row([ft.Container(width=10, height=10, bgcolor="#F59E0B", border_radius=5), ft.Text("Observación", size=10, color="#94a3b8")], spacing=3),
                    ft.Row([ft.Container(width=10, height=10, bgcolor="#D32F2F", border_radius=5), ft.Text("Pendiente", size=10, color="#94a3b8")], spacing=3),
                    ft.Row([ft.Container(width=10, height=10, bgcolor="#1E293B", border=ft.Border.all(1, "#00FFFF"), border_radius=5), ft.Text("Hoy/Activo", size=10, color="#94a3b8")], spacing=3),
                    ft.Row([ft.Container(width=10, height=10, bgcolor="#141424", border_radius=5), ft.Text("Futuro", size=10, color="#94a3b8")], spacing=3)
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ], spacing=10, tight=True),
            width=400,
            padding=10
        ),
        actions=[
            ft.TextButton("📅 Ir a Hoy", on_click=ir_a_hoy, style=ft.ButtonStyle(color="#00FFFF")),
            ft.ElevatedButton("Cerrar", on_click=cerrar_calendario, style=ft.ButtonStyle(bgcolor="#334155", color="white"))
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    page.overlay.append(calendar_modal)

    # Interactive Date Selection Dialog & Day Navigation
    def cambiar_dia(delta_dias):
        try:
            curr_dt = datetime.strptime(current_date[0], "%Y-%m-%d")
            new_dt = curr_dt + timedelta(days=delta_dias)
            current_date[0] = new_dt.strftime("%Y-%m-%d")
            date_btn_text.value = current_date[0]
            try: date_btn_text.update()
            except Exception: pass
            render_disa_categories()
        except Exception as ex:
            print("Error cambiando dia:", ex)

    def abrir_calendario(e):
        try:
            curr_dt = datetime.strptime(current_date[0], "%Y-%m-%d")
            cal_year[0] = curr_dt.year
            cal_month[0] = curr_dt.month
        except Exception:
            pass
        render_calendar_grid()
        calendar_modal.open = True
        try: page.update()
        except Exception: pass

    def on_foto_cargada(ruta, categoria_especifica=None):
        if not ruta or not os.path.exists(ruta):
            return
            
        st_code = get_current_store_code()
        date_str = current_date[0]
        
        def _worker():
            try:
                progress_bar.visible = True
                status_text.value = "⏳ Procesando imagen con Visión Artificial en Alta Resolución..."
                status_text.color = "#FFD700"
                try: page.update()
                except Exception: pass
                
                if categoria_especifica:
                    target_dir = os.path.join(DISA_UPLOADS_BASE, date_str, f"Tienda_{st_code}")
                    os.makedirs(target_dir, exist_ok=True)
                    existing = glob.glob(os.path.join(target_dir, f"{categoria_especifica}_*.jpg"))
                    next_num = len(existing) + 1
                    out_path = os.path.join(target_dir, f"{categoria_especifica}_{next_num:02d}.jpg")
                    
                    img = cv2.imread(ruta)
                    if img is not None:
                        enhanced = disa_engine.enhance_doc(img)
                        cv2.imwrite(out_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 98])
                    else:
                        shutil.copyfile(ruta, out_path)
                    total_docs = 1
                else:
                    res = disa_engine.process_corte_image(
                        image_path=ruta,
                        store_id=st_code,
                        date_str=date_str
                    )
                    total_docs = res.get("total_documents", 0) if res.get("success") else 0
                        
                progress_bar.visible = False
                status_text.value = f"✅ ¡Listo! Se procesaron {total_docs} documento(s) ({date_str})."
                status_text.color = "#00FF7F"
                render_disa_categories()
                try: page.update()
                except Exception: pass
            except Exception as ex_proc:
                print("Error en worker disa:", ex_proc)
                progress_bar.visible = False
                status_text.value = f"❌ Error al procesar: {ex_proc}"
                status_text.color = "#FF4500"
                try: page.update()
                except Exception: pass

        threading.Thread(target=_worker, daemon=True).start()

    # Top Store and Date Header matching DiSA App layout
    store_badge = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.STORE, size=18, color="#00FFFF"),
            ft.Text(f"Tienda: {matched_store.upper()}", size=13, weight=ft.FontWeight.BOLD, color="white")
        ], spacing=6),
        padding=8,
        bgcolor="#141424",
        border_radius=8,
        border=ft.Border.all(1, "#333344")
    )

    date_picker_container = ft.Container(
        content=ft.Row([
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_ROUNDED,
                icon_size=16,
                icon_color="#00FFFF",
                tooltip="Día Anterior",
                on_click=lambda _: cambiar_dia(-1)
            ),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=18, color="#00FFFF"),
                    ft.Text("FECHA: ", size=12, weight=ft.FontWeight.BOLD, color="#8899aa"),
                    date_btn_text
                ], spacing=5),
                style=ft.ButtonStyle(
                    bgcolor="#16162a",
                    color="white"
                ),
                on_click=abrir_calendario
            ),
            ft.IconButton(
                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                icon_size=16,
                icon_color="#00FFFF",
                tooltip="Día Siguiente",
                on_click=lambda _: cambiar_dia(1)
            )
        ], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(4, 0, 4, 0)
    )

    header_bar = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.DOCUMENT_SCANNER_ROUNDED, color="#00FFFF", size=28),
                ft.Column([
                    ft.Text("DiSA - Digital Sales Audit", size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Auditoría Inteligente de Cortes", size=11, color="#8899aa")
                ], spacing=2)
            ], spacing=8),
            ft.Row([
                dd_tienda if (es_admin and dd_tienda) else store_badge,
                date_picker_container,
                ft.ElevatedButton(
                    "📸 Capturar Corte (1 Foto)",
                    icon=ft.Icons.UPLOAD_FILE,
                    style=ft.ButtonStyle(
                        bgcolor="#008B8B",
                        color="white"
                    ),
                    on_click=lambda _: trigger_upload(None, "Corte Completo (1 Foto)")
                )
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=12,
        bgcolor="#0f0f1c",
        border_radius=10,
        border=ft.Border.all(1, "#222233")
    )

    # Actions: ENVIAR DOCUMENTOS and FUERA DE OPERACION
    def enviar_documentos_corte(e):
        st_code = get_current_store_code()
        date_str = current_date[0]
        target_dir = os.path.join(DISA_UPLOADS_BASE, date_str, f"Tienda_{st_code}")
        existing_files = glob.glob(os.path.join(target_dir, "*.jpg")) if os.path.exists(target_dir) else []
        
        if len(existing_files) == 0:
            status_text.value = f"⚠️ Debes subir al menos 1 fotografía antes de enviar el corte de {date_str}."
            status_text.color = "#FFD700"
            try:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"⚠️ Debes subir al menos 1 documento antes de enviar el corte ({date_str})."),
                    bgcolor="#B45309"
                )
                page.snack_bar.open = True
            except Exception: pass
            try: page.update()
            except Exception: pass
            return
            
        # Check if contains manual notes (contingency without system) -> Automatically Green
        has_notas_manuales = any("12_Notas_Manuales" in os.path.basename(f) for f in existing_files)
        has_panamericano = any("11_Deposito_Panamericano_Banco" in os.path.basename(f) or "05_Fichas_Deposito" in os.path.basename(f) for f in existing_files)
        
        if has_notas_manuales:
            set_day_status(st_code, date_str, "ENVIADO", total_docs=len(existing_files), note="Amparado con Notas Manuales por contingencia en tienda")
            status_text.value = f"✅ ¡Corte enviado con Notas Manuales (Tienda sin sistema)! Registrado en VERDE."
            status_text.color = "#00FF7F"
            try:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ ¡Corte de {date_str} enviado exitosamente (Notas Manuales en Verde)!"),
                    bgcolor="#00C853"
                )
                page.snack_bar.open = True
            except Exception: pass
        else:
            set_day_status(st_code, date_str, "ENVIADO", total_docs=len(existing_files))
            status_text.value = f"✅ ¡Corte enviado exitosamente ({len(existing_files)} documentos)! Registrado en VERDE en el calendario."
            status_text.color = "#00FF7F"
            try:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ ¡Corte de {date_str} enviado con éxito ({len(existing_files)} docs)!"),
                    bgcolor="#00C853"
                )
                page.snack_bar.open = True
            except Exception: pass
            
        render_disa_categories()
        try: page.update()
        except Exception: pass

    def marcar_fuera_operacion(e):
        st_code = get_current_store_code()
        date_str = current_date[0]
        
        def confirmar_fuera_op(ev):
            fuera_modal.open = False
            set_day_status(st_code, date_str, "FUERA_DE_OPERACION", total_docs=0, note="Marcado por usuario")
            status_text.value = f"🟡 Sucursal {st_code} marcada como FUERA DE OPERACIÓN para el {date_str}."
            status_text.color = "#00FF7F"
            try:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"🟡 {date_str}: Sucursal registrada como Fuera de Operación."),
                    bgcolor="#008080"
                )
                page.snack_bar.open = True
            except Exception: pass
            render_disa_categories()
            try: page.update()
            except Exception: pass

        fuera_modal = ft.AlertDialog(
            modal=True,
            bgcolor="#10121e",
            title=ft.Row([
                ft.Icon(ft.Icons.STORE_MALL_DIRECTORY_OUTLINED, color="#FFD700"),
                ft.Text("Fuera de Operación", size=16, weight=ft.FontWeight.BOLD, color="white")
            ], spacing=6),
            content=ft.Text(
                f"¿Confirmas que la sucursal {st_code} estuvo cerrada o fuera de operación el día {date_str}?",
                size=13,
                color="#cbd5e1"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(fuera_modal, "open", False) or page.update()),
                ft.ElevatedButton("Confirmar", style=ft.ButtonStyle(bgcolor="#00C853", color="white"), on_click=confirmar_fuera_op)
            ]
        )
        page.overlay.append(fuera_modal)
        fuera_modal.open = True
        try: page.update()
        except Exception: pass

    # Bottom action buttons matching official DiSA app
    bottom_buttons = ft.Row([
        ft.ElevatedButton(
            "FUERA DE OPERACIÓN",
            style=ft.ButtonStyle(
                bgcolor="#334155",
                color="white"
            ),
            on_click=marcar_fuera_operacion
        ),
        ft.ElevatedButton(
            "ENVIAR DOCUMENTOS",
            style=ft.ButtonStyle(
                bgcolor="#00A896",
                color="white"
            ),
            on_click=enviar_documentos_corte
        )
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)

    # --- PESTAÑA 2: OBSERVACIONES Y ACLARACIONES PARA CONTABILIDAD ---
    active_tab_index = [0]
    observations_column = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)

    def render_observations_panel():
        st_code = get_current_store_code()
        obs_list = get_store_observations(st_code)
        
        cards = []
        if not obs_list:
            cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#00C853", size=48),
                        ft.Text("¡Excelente! No hay observaciones pendientes para esta sucursal.", size=14, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Todos los cortes enviados están al día y completos.", size=12, color="#94a3b8")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=30,
                    alignment=ft.Alignment(0, 0),
                    bgcolor="#10121e",
                    border_radius=10,
                    border=ft.Border.all(1, "#222233")
                )
            )
        else:
            for item in obs_list:
                d = item["date"]
                obs_text = item["observacion"]
                aclar_text = item.get("aclaracion", "")
                aclar_fecha = item.get("aclaracion_fecha", "")
                
                tf_reply = ft.TextField(
                    value=aclar_text,
                    label="Aclaración / Justificación de la Tienda para Contabilidad",
                    hint_text="Escribe aquí tu aclaración (Ej: Se marcó efectivo por error en caja, el cliente pagó con tarjeta; voucher anexo en su casilla).",
                    multiline=True,
                    min_lines=2,
                    max_lines=4,
                    border_color="#00FFFF",
                    color="white",
                    text_size=13
                )
                
                aclar_status_text = ft.Text(
                    f"✅ Aclaración registrada el {aclar_fecha} (Enviada a Contabilidad)" if aclar_text else "⏳ Pendiente de aclaración por la sucursal",
                    size=11,
                    color="#00FF7F" if aclar_text else "#FFD700",
                    italic=True
                )
                
                def make_save_aclaracion(date_item, tf_ctrl, status_ctrl):
                    def handler(e):
                        val = tf_ctrl.value.strip() if tf_ctrl.value else ""
                        if not val:
                            try:
                                page.snack_bar = ft.SnackBar(ft.Text("⚠️ Por favor escribe tu aclaración antes de guardar."), bgcolor="#B45309")
                                page.snack_bar.open = True
                                page.update()
                            except Exception: pass
                            return
                        save_day_aclaracion(st_code, date_item, val)
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        status_ctrl.value = f"✅ Aclaración registrada el {now_str} (Enviada a Contabilidad)"
                        status_ctrl.color = "#00FF7F"
                        try:
                            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Aclaración para el {date_item} guardada exitosamente."), bgcolor="#00C853")
                            page.snack_bar.open = True
                            page.update()
                        except Exception: pass
                    return handler

                def make_go_to_day(date_item):
                    def handler(e):
                        current_date[0] = date_item
                        date_btn_text.value = date_item
                        switch_to_tab(0)
                        render_disa_categories()
                    return handler

                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.CALENDAR_MONTH, color="#10121e", size=16),
                                    ft.Text(d, size=13, weight=ft.FontWeight.BOLD, color="#10121e")
                                ], spacing=4),
                                bgcolor="#F59E0B",
                                padding=ft.Padding(8, 4, 8, 4),
                                border_radius=6
                            ),
                            ft.Text(f"Sucursal {st_code}", size=13, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Container(expand=True),
                            ft.TextButton("📂 Ver Documentos de este Día", icon=ft.Icons.OPEN_IN_NEW, style=ft.ButtonStyle(color="#00FFFF"), on_click=make_go_to_day(d))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.REPORT_PROBLEM_ROUNDED, color="#F59E0B", size=20),
                                ft.Text(obs_text, size=13, color="#fbbf24", expand=True)
                            ], spacing=8),
                            bgcolor="#1c1917",
                            padding=10,
                            border_radius=6,
                            border=ft.Border.all(1, "#78350f")
                        ),
                        tf_reply,
                        ft.Row([
                            aclar_status_text,
                            ft.ElevatedButton(
                                "Guardar Aclaración",
                                icon=ft.Icons.SAVE,
                                style=ft.ButtonStyle(bgcolor="#008080", color="white"),
                                on_click=make_save_aclaracion(d, tf_reply, aclar_status_text)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ], spacing=10),
                    bgcolor="#10121e",
                    padding=14,
                    border_radius=10,
                    border=ft.Border.all(1, "#334155")
                )
                cards.append(card)
                
        observations_column.controls = cards
        try: page.update()
        except Exception: pass

    # View layout containers for tabs
    view_cortes = ft.Column([
        ft.Row([status_text], alignment=ft.MainAxisAlignment.START),
        progress_bar,
        ft.Divider(height=1, color="#222233"),
        sections_column,
        ft.Divider(height=1, color="#222233"),
        bottom_buttons
    ], spacing=10)

    view_obs = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FACT_CHECK_ROUNDED, color="#00FFFF", size=22),
                ft.Text("Bandeja de Observaciones y Aclaraciones para Contabilidad", size=15, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.REFRESH, tooltip="Actualizar Observaciones", icon_color="#00FFFF", on_click=lambda _: render_observations_panel())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            bgcolor="#0f0f1c",
            border_radius=8,
            border=ft.Border.all(1, "#222233")
        ),
        observations_column
    ], spacing=12)

    content_area = ft.Container(content=view_cortes, expand=True)

    tab_cortes_btn = ft.ElevatedButton(
        "📷 CORTES Y DOCUMENTOS",
        icon=ft.Icons.RECEIPT_LONG,
        style=ft.ButtonStyle(bgcolor="#008080", color="white"),
        on_click=lambda _: switch_to_tab(0)
    )
    tab_obs_btn = ft.ElevatedButton(
        "💬 OBSERVACIONES Y AUDITORÍA",
        icon=ft.Icons.FACT_CHECK_ROUNDED,
        style=ft.ButtonStyle(bgcolor="#16162a", color="#94a3b8"),
        on_click=lambda _: switch_to_tab(1)
    )

    def switch_to_tab(idx):
        active_tab_index[0] = idx
        if idx == 0:
            tab_cortes_btn.style.bgcolor = "#008080"
            tab_cortes_btn.style.color = "white"
            tab_obs_btn.style.bgcolor = "#16162a"
            tab_obs_btn.style.color = "#94a3b8"
            content_area.content = view_cortes
        else:
            tab_cortes_btn.style.bgcolor = "#16162a"
            tab_cortes_btn.style.color = "#94a3b8"
            tab_obs_btn.style.bgcolor = "#008080"
            tab_obs_btn.style.color = "white"
            render_observations_panel()
            content_area.content = view_obs
        try: page.update()
        except Exception: pass

    tab_bar = ft.Container(
        content=ft.Row([
            tab_cortes_btn,
            tab_obs_btn
        ], spacing=10),
        padding=ft.Padding(0, 4, 0, 4)
    )

    # Initial load
    render_disa_categories()

    return ft.Container(
        content=ft.Column([
            header_bar,
            tab_bar,
            content_area
        ], spacing=10, scroll=ft.ScrollMode.AUTO),
        expand=True,
        padding=10
    )
