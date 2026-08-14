import flet as ft
import os
import re
import json
import time
import threading
import datetime
import requests
import base64
import math
import asyncio
import csv
import subprocess
import tempfile
import shutil
import random
import calendar
import flet_video as fv
from frontend.components.ui import EmojiIconButton, EmojiDropdown

def _build_weekly_view(
    BASE_PATH,
    Tk,
    b_i,
    btn_subtab_resumen,
    cnt,
    conectar_db,
    es_admin,
    file_path,
    file_picker_weekly,
    filedialog,
    glob,
    icon_name,
    label,
    mostrar_snack,
    n_reg,
    page,
    procesar_excel_weekly,
    s_corta,
    seleccionar_archivo_async,
    tab_cnt,
    tiendas_set,
    user_info
):
    tiendas_opts = []
    semanas_opts = []
    
    try:
        db = conectar_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT DISTINCT tienda FROM weekly_metricas ORDER BY tienda ASC")
            tiendas_opts = [r[0] for r in cursor.fetchall()]
            cursor.execute("SELECT semana_corta FROM weekly_metricas GROUP BY semana_corta ORDER BY MAX(id) DESC")
            semanas_opts = [r[0] for r in cursor.fetchall()]
            db.close()
    except Exception as ex:
        print("Error cargando opciones weekly:", ex)
    
    user_tienda = user_info.get("tienda", "")
    default_tienda = None
    if user_tienda and tiendas_opts:
        for t_opt in tiendas_opts:
            if user_tienda.lower() in t_opt.lower() or t_opt.lower() in user_tienda.lower():
                default_tienda = t_opt
                break
    if not default_tienda and tiendas_opts:
        default_tienda = tiendas_opts[0]
    
    default_semana = semanas_opts[0] if semanas_opts else None
    
    is_mobile_w = (page.width < 800) if (page and page.width) else False
    w_tienda_dd = 180 if is_mobile_w else 320
    w_semana_dd = 120 if is_mobile_w else 180
    w_buscar_tf = 110 if is_mobile_w else 180
    
    txt_buscar_tienda = ft.TextField(
        label="🔍 Nº Tienda",
        hint_text="Ej: 3502...",
        width=w_buscar_tf,
        border_color="#9D50BB",
        color="white",
        text_size=11 if is_mobile_w else 13,
        height=36 if is_mobile_w else 40
    )
    
    dd_tiendas = ft.Dropdown(
        label="🏬 Tienda",
        value=default_tienda,
        options=[ft.dropdown.Option(t_opt) for t_opt in tiendas_opts],
        width=w_tienda_dd,
        border_color="#9D50BB",
        color="white",
        text_size=11 if is_mobile_w else 13
    )
    
    dd_semanas = ft.Dropdown(
        label="📅 Semana",
        value=default_semana,
        options=[ft.dropdown.Option(s_opt) for s_opt in semanas_opts],
        width=w_semana_dd,
        border_color="#9D50BB",
        color="white",
        text_size=11 if is_mobile_w else 13
    )
    
    def ejecutar_busqueda(e=None):
        q = (txt_buscar_tienda.value or "").strip().lower()
        if not q:
            dd_tiendas.options = [ft.dropdown.Option(t_o) for t_o in tiendas_opts]
            if tiendas_opts:
                dd_tiendas.value = default_tienda or tiendas_opts[0]
        else:
            coincidencias = [t_o for t_o in tiendas_opts if q in t_o.lower()]
            if coincidencias:
                dd_tiendas.options = [ft.dropdown.Option(t_o) for t_o in coincidencias]
                dd_tiendas.value = coincidencias[0]
                mostrar_snack(f"✅ Cargada tienda: {coincidencias[0]}", color="green")
            else:
                mostrar_snack(f"⚠️ No se encontró la tienda con: '{txt_buscar_tienda.value}'", color="orange")
        render_table()
    
    txt_buscar_tienda.on_submit = ejecutar_busqueda
    txt_buscar_tienda.on_change = ejecutar_busqueda
    
    btn_consultar_tienda = ft.ElevatedButton(
        "🔍 Buscar" if is_mobile_w else "🔄 Consultar",
        icon=ft.Icons.SEARCH,
        bgcolor="#0284c7",
        color="white",
        height=36 if is_mobile_w else 40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.Padding(8, 0, 8, 0) if is_mobile_w else None
        ),
        on_click=ejecutar_busqueda
    )
    
    table_container = ft.Column(spacing=15, expand=True)
    
    def render_table(e=None):
        sel_t = dd_tiendas.value
        sel_s = dd_semanas.value
    
        if not sel_t or not sel_s:
            table_container.controls = [
                ft.Container(
                    content=ft.Text("⚠️ No hay datos cargados en el sistema. El Administrador debe subir el archivo Weekly Excel.", color="orange", size=14),
                    padding=20,
                    bgcolor="#1e1b4b",
                    border_radius=8
                )
            ]
            try: page.update()
            except Exception: pass
            return
    
        metrics_data = []
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT periodo, ventas, meta, pct_meta, comp 
                    FROM weekly_metricas 
                    WHERE tienda = %s AND semana_corta = %s
                    ORDER BY FIELD(periodo, 'SEMANA ANTERIOR', 'MTD', 'QTD', 'YTD')
                """, (sel_t, sel_s))
                metrics_data = cursor.fetchall()
                db.close()
        except Exception as ex:
            print("Error leyendo métricas weekly:", ex)
    
        if not metrics_data:
            table_container.controls = [
                ft.Container(
                    content=ft.Text(f"No hay métricas registradas para {sel_t} en {sel_s}.", color="white", size=14),
                    padding=20,
                    bgcolor="#1e1b4b",
                    border_radius=8
                )
            ]
            try: page.update()
            except Exception: pass
            return
    
        data_rows = []
        for m in metrics_data:
            p = m["periodo"]
            if is_mobile_w and "SEMANA ANTERIOR" in p.upper():
                p_display = "SEMANA
ANTERIOR"
            else:
                p_display = p
    
            v = f"${m['ventas']:,.2f}"
            target = f"${m['meta']:,.2f}"
            
            pm_val = float(m["pct_meta"] or 0)
            pm_str = f"{pm_val:.1f}%"
            # Regla % Meta: >= 91% es Verde (#7CFC00), menor a 91% es Rojo (#FF4500)
            pm_color = "#7CFC00" if pm_val >= 91.0 else "#FF4500"
    
            comp_val = float(m["comp"] or 0)
            comp_str = f"{comp_val:.1f}%"
            comp_color = "#7CFC00" if comp_val >= 0 else "#FF4500"
    
            cell_font_size = 10.0 if is_mobile_w else 13.0
            pad_val = ft.padding.Padding(3, 2, 3, 2) if is_mobile_w else 5
    
            data_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p_display, weight="bold", color="#D8B4FE", size=cell_font_size)),
                        ft.DataCell(ft.Text(v, color="#00FFFF", weight="bold", size=cell_font_size)),
                        ft.DataCell(ft.Text(target, color="#ffffff", size=cell_font_size)),
                        ft.DataCell(ft.Container(content=ft.Text(pm_str, color=pm_color, weight="bold", size=cell_font_size), bgcolor="#222233", padding=pad_val, border_radius=5)),
                        ft.DataCell(ft.Container(content=ft.Text(comp_str, color=comp_color, weight="bold", size=cell_font_size), bgcolor="#222233", padding=pad_val, border_radius=5)),
                    ]
                )
            )
    
        hdr_font_size = 10.0 if is_mobile_w else 13.0
        table_widget = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Métrica", weight="bold", color="#D8B4FE", size=hdr_font_size)),
                ft.DataColumn(ft.Text("💲 Ventas", weight="bold", color="#00FFFF", size=hdr_font_size)),
                ft.DataColumn(ft.Text("📑 Meta", weight="bold", color="#7CFC00", size=hdr_font_size)),
                ft.DataColumn(ft.Text("📈 % Meta", weight="bold", color="#FFD700", size=hdr_font_size)),
                ft.DataColumn(ft.Text("📊 Comp", weight="bold", color="#D8B4FE", size=hdr_font_size)),
            ],
            rows=data_rows,
            border=ft.Border.all(1, "#333344"),
            border_radius=8 if is_mobile_w else 10,
            column_spacing=6 if is_mobile_w else 24,
            horizontal_margin=6 if is_mobile_w else 16,
            heading_row_height=32 if is_mobile_w else 56,
            data_row_min_height=32 if is_mobile_w else 48,
            heading_row_color="#1e1b4b",
            data_row_color="#141424"
        )
    
        table_container.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"📍 {sel_t}", size=13 if is_mobile_w else 18, weight="bold", color="#00FFFF"),
                        ft.Container(content=ft.Text(sel_s, color="white", weight="bold", size=10 if is_mobile_w else 12), bgcolor="#9D50BB", padding=ft.padding.Padding(5, 2, 5, 2) if is_mobile_w else ft.padding.Padding(8, 4, 8, 4), border_radius=6)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=8 if is_mobile_w else 10, color="#333344"),
                    ft.Row([table_widget], scroll=ft.ScrollMode.AUTO)
                ]),
                bgcolor="#181828",
                padding=8 if is_mobile_w else 15,
                border_radius=10 if is_mobile_w else 12,
                border=ft.Border.all(1, "#9D50BB")
            )
        ]
        try: page.update()
        except Exception: pass
    
    def on_dd_change(e=None):
        render_table()
        try: page.update()
        except Exception: pass
    
    dd_tiendas.on_change = on_dd_change
    dd_semanas.on_change = on_dd_change
    
    lbl_upload_status = ft.Text("", size=13, color="#00FFFF")
    
    def recargar_dropdowns():
        t_opts, s_opts = [], []
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute("SELECT DISTINCT tienda FROM weekly_metricas ORDER BY tienda ASC")
                t_opts = [r[0] for r in cursor.fetchall()]
                cursor.execute("SELECT semana_corta FROM weekly_metricas GROUP BY semana_corta ORDER BY MAX(id) DESC")
                s_opts = [r[0] for r in cursor.fetchall()]
                db.close()
        except Exception as ex_opts:
            print("Error recargando opciones:", ex_opts)
        dd_tiendas.options = [ft.dropdown.Option(t_o) for t_o in t_opts]
        dd_semanas.options = [ft.dropdown.Option(s_o) for s_o in s_opts]
        if s_opts and (not dd_semanas.value or dd_semanas.value not in s_opts):
            dd_semanas.value = s_opts[0]
        if t_opts and (not dd_tiendas.value or dd_tiendas.value not in t_opts):
            dd_tiendas.value = t_opts[0]
        try: page.update()
        except Exception: pass
    
    def procesar_y_notificar(file_path, f_name):
        lbl_upload_status.value = f"⏳ Procesando '{f_name}'..."
        lbl_upload_status.color = "#FFD700"
        page.update()
    
        try:
            n_t, n_r = procesar_excel_weekly(file_path)
            lbl_upload_status.value = f"✅ ¡Éxito! Se actualizaron {n_t} tiendas ({n_r} registros) desde '{f_name}'."
            lbl_upload_status.color = "#7CFC00"
            mostrar_snack("✅ Excel Weekly procesado y cargado correctamente.", color="green")
            recargar_dropdowns()
            render_table()
        except Exception as ex:
            print("Error procesando Excel Weekly:", ex)
            lbl_upload_status.value = f"❌ Error al procesar: {ex}"
            lbl_upload_status.color = "#FF4500"
            mostrar_snack(f"Error procesando Excel: {ex}", color="red")
        page.update()
    
    def on_file_result(e):
        if not e.files or len(e.files) == 0:
            lbl_upload_status.value = "⚠️ No se seleccionó ningún archivo o la selección fue cancelada."
            lbl_upload_status.color = "#FFD700"
            page.update()
            return
        f_item = e.files[0]
        f_name = f_item.name
    
        if f_item.path:
            txt_ruta_excel.value = f_item.path
            procesar_y_notificar(f_item.path, f_name)
        else:
            lbl_upload_status.value = f"⏳ Subiendo '{f_name}' desde el navegador..."
            lbl_upload_status.color = "#FFD700"
            page.update()
            try:
                upload_url = page.get_upload_url(f_name, 600)
                file_picker_weekly.upload([ft.FilePickerUploadFile(f_name, upload_url=upload_url)])
            except Exception as ex_up:
                print("Error iniciando upload web:", ex_up)
                lbl_upload_status.value = f"❌ Error iniciando subida: {ex_up}"
                lbl_upload_status.color = "#FF4500"
                page.update()
    
    def on_upload_progress(e):
        if getattr(e, "progress", 0) == 1.0 or getattr(e, "status", "") == "uploaded":
            f_name = e.file_name
            f_path = os.path.join(BASE_PATH, "uploads", f_name)
            procesar_y_notificar(f_path, f_name)
    
    def buscar_excel_weekly_reciente():
        import glob
        dirs = [os.path.expanduser('~/Downloads'), os.path.expanduser('~/Documents'), os.path.expanduser('~/Desktop')]
        for d in dirs:
            matches = glob.glob(os.path.join(d, '*Weekly*.xlsx')) + glob.glob(os.path.join(d, '*weekly*.xlsx'))
            if matches:
                matches.sort(key=os.path.getmtime, reverse=True)
                return matches[0]
        return ""
    
    def abrir_dialogo_archivo_nativo():
        try:
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            initial_dir = os.path.expanduser('~/Downloads')
            if not os.path.exists(initial_dir):
                initial_dir = os.path.expanduser('~/Documents')
            f_selected = filedialog.askopenfilename(
                title="Selecciona el archivo Weekly Flash Sales Excel",
                initialdir=initial_dir,
                filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
            )
            root.destroy()
            if f_selected and os.path.exists(f_selected):
                return f_selected
        except Exception as ex_tk:
            print("Error en dialogo Tkinter nativo:", ex_tk)
    
        try:
            import subprocess
            ps_cmd = '''
            [System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null
            $f = New-Object System.Windows.Forms.OpenFileDialog
            $f.InitialDirectory = [System.IO.Path]::Combine($env:USERPROFILE, 'Downloads')
            $f.Filter = "Archivos Excel (*.xlsx)|*.xlsx|Todos los archivos (*.*)|*.*"
            $f.Title = "Selecciona el reporte Excel Weekly"
            $f.ShowHelp = $true
            $f.TopMost = $true
            if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Output $f.FileName
            }
            '''
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120
            )
            selected = proc.stdout.strip()
            if selected and os.path.exists(selected):
                return selected
        except Exception as ex_ps:
            print("Error en PowerShell dialog:", ex_ps)
    
        return ""
    
    auto_detected_path = buscar_excel_weekly_reciente()
    
    txt_ruta_excel = ft.TextField(
        label="📁 Ruta de archivo Excel",
        value=auto_detected_path if auto_detected_path else r"C:\Users\MOISES\Downloads\Weekly Flash Sales Semana 029 Día 07(4).xlsx",
        hint_text=r"Ej: C:\Users\MOISES\Downloads\Weekly...",
        width=240 if is_mobile_w else 650,
        border_color="#00FFFF",
        color="white",
        text_size=11 if is_mobile_w else 12
    )
    
    def resolver_ruta_excel(p):
        if not p:
            return ""
        p_clean = p.strip('"').strip("'")
        if os.path.isabs(p_clean) and os.path.exists(p_clean):
            return p_clean
        rutas_posibles = [
            p_clean,
            os.path.join(BASE_PATH, "uploads", os.path.basename(p_clean)),
            os.path.expanduser(os.path.join("~/Downloads", os.path.basename(p_clean))),
            os.path.expanduser(os.path.join("~/Documents", os.path.basename(p_clean))),
            os.path.expanduser(os.path.join("~/Desktop", os.path.basename(p_clean))),
        ]
        for r in rutas_posibles:
            if os.path.exists(r):
                return r
        return p_clean
    
    def cargar_desde_ruta(e):
        ruta = txt_ruta_excel.value or ""
        ruta_res = resolver_ruta_excel(ruta)
        if not ruta_res or not os.path.exists(ruta_res):
            lbl_upload_status.value = f"❌ Archivo no encontrado en la ruta: '{ruta}'"
            lbl_upload_status.color = "#FF4500"
            mostrar_snack(f"Ruta inválida o archivo no existe: '{ruta}'", color="red")
            page.update()
            return
        procesar_y_notificar(ruta_res, os.path.basename(ruta_res))
    
    btn_cargar_ruta = ft.ElevatedButton(
        "⚡ Cargar y Procesar Excel",
        icon=ft.Icons.PLAY_ARROW,
        bgcolor="#7CFC00",
        color="black",
        height=36 if is_mobile_w else 40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.Padding(8, 0, 8, 0) if is_mobile_w else None
        ),
        on_click=cargar_desde_ruta
    )
    
    def abrir_dialogo_subida(e):
        seleccionar_archivo_async(
            "Seleccionar reporte Excel Weekly",
            [("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")],
            lambda ruta: procesar_y_notificar(ruta, os.path.basename(ruta))
        )
    
    btn_upload = ft.ElevatedButton(
        "📤 Cargar Archivo Excel (Weekly)",
        icon=ft.Icons.UPLOAD_FILE,
        bgcolor="#7c3aed",
        color="white",
        height=36 if is_mobile_w else 40,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.Padding(8, 0, 8, 0) if is_mobile_w else None
        ),
        on_click=abrir_dialogo_subida
    )
    
    weekly_reports_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def cargar_reportes_weekly():
        weekly_reports_list.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT semana_corta, COUNT(DISTINCT tienda) as total_tiendas, COUNT(*) as total_registros
                    FROM weekly_metricas
                    GROUP BY semana_corta
                    ORDER BY MAX(id) DESC
                """)
                reportes = cursor.fetchall()
                db.close()
    
                if not reportes:
                    weekly_reports_list.controls.append(ft.Text("No hay reportes weekly cargados en la BD.", color="#aaaaaa", size=12))
                else:
                    for rep in reportes:
                        sem = rep["semana_corta"]
                        n_t = rep["total_tiendas"]
                        n_r = rep["total_registros"]
    
                        def borrar_weekly_click(e, s_corta=sem):
                            def on_confirmar_weekly(ev):
                                try:
                                    db_del = conectar_db()
                                    if db_del:
                                        cursor_del = db_del.cursor()
                                        cursor_del.execute("DELETE FROM weekly_metricas WHERE semana_corta = %s", (s_corta,))
                                        db_del.commit()
                                        db_del.close()
                                        mostrar_snack(f"Reporte Weekly '{s_corta}' eliminado.")
                                        recargar_dropdowns()
                                        cargar_reportes_weekly()
                                        render_table()
                                        page.pop_dialog()
                                        page.update()
                                except Exception as ex_w:
                                    print("ERROR BORRAR WEEKLY:", ex_w)
                                    mostrar_snack("Error al borrar reporte weekly.", color="red")
    
                            def on_cancelar_weekly(ev):
                                page.pop_dialog()
    
                            dialog_confirm_w = ft.AlertDialog(
                                title=ft.Text("Confirmar Borrado de Reporte Weekly", color="#FF4500", weight="bold"),
                                content=ft.Text(f"¿Seguro que deseas borrar el reporte completo de la '{s_corta}' ({n_t} tiendas)?"),
                                actions=[
                                    ft.TextButton("Cancelar", on_click=on_cancelar_weekly),
                                    ft.ElevatedButton("Sí, Borrar", on_click=on_confirmar_weekly, bgcolor="#FF4500", color="white")
                                ],
                                actions_alignment="end",
                                bgcolor="#0F0F1A"
                            )
                            page.show_dialog(dialog_confirm_w)
    
                        def ver_reporte_weekly_click(e, s_corta=sem):
                            dd_semanas.value = s_corta
                            try:
                                if 'btn_subtab_resumen' in locals() and btn_subtab_resumen and hasattr(btn_subtab_resumen, "on_click"):
                                    btn_subtab_resumen.on_click(None)
                            except Exception: pass
                            render_table()
                            mostrar_snack(f"📊 Visualizando Reporte {s_corta}", color="cyan")
    
                        weekly_reports_list.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.BAR_CHART, color="#00FFFF", size=18 if is_mobile_w else 22),
                                    ft.Column([
                                        ft.Text(f"Reporte {sem}", color="white", weight="bold", size=12 if is_mobile_w else 14),
                                        ft.Text(f"{n_t} tiendas cargadas ({n_r} métricas)", color="#aaaaaa", size=10 if is_mobile_w else 11)
                                    ], spacing=2, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.VISIBILITY_ROUNDED,
                                        icon_color="#00FFFF",
                                        tooltip="👁️ Visualizar métricas de esta semana",
                                        icon_size=18 if is_mobile_w else 22,
                                        on_click=ver_reporte_weekly_click
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_FOREVER,
                                        icon_color="#FF4500",
                                        tooltip="Eliminar reporte de esta semana",
                                        icon_size=18 if is_mobile_w else 22,
                                        on_click=borrar_weekly_click
                                    )
                                ], alignment="spaceBetween", vertical_alignment="center"),
                                bgcolor="#1e1b4b",
                                padding=8 if is_mobile_w else 10,
                                border_radius=8,
                                border=ft.Border.all(1, "#333344")
                            )
                        )
        except Exception as ex:
            print("ERROR LISTA WEEKLY:", ex)
            weekly_reports_list.controls.append(ft.Text("Error al cargar la lista de reportes weekly.", color="red"))
    
        try: page.update()
        except Exception: pass
    
    cargar_reportes_weekly()
    
    def procesar_y_notificar(file_path, f_name):
        lbl_upload_status.value = f"⏳ Procesando '{f_name}'..."
        lbl_upload_status.color = "#FFD700"
        page.update()
        mostrar_snack(f"Extrayendo tiendas y métricas de '{f_name}'...", color="#D8B4FE")
        
        def worker():
            try:
                n_reg, sem, tiendas_set = procesar_excel_weekly(file_path)
                lbl_upload_status.value = f"✅ Éxito: {n_reg} registros insertados de {len(tiendas_set)} tiendas para {sem}."
                lbl_upload_status.color = "#7CFC00"
                mostrar_snack(f"✅ Excel Weekly cargado con éxito ({sem}).", color="green")
                cargar_reportes_weekly()
                render_table()
            except Exception as ex:
                print("Error procesando Excel Weekly:", ex)
                lbl_upload_status.value = f"❌ Error al procesar: {ex}"
                lbl_upload_status.color = "#FF4500"
                mostrar_snack(f"Error procesando Excel: {ex}", color="red")
            page.update()
    
        import threading
        threading.Thread(target=worker, daemon=True).start()
    
    btn_actualizar_listas = ft.IconButton(
        icon=ft.Icons.REFRESH_ROUNDED,
        icon_color="#00FFFF",
        tooltip="🔄 Actualizar Semanas y Tiendas",
        on_click=lambda e: (recargar_dropdowns(), render_table(), mostrar_snack("🔄 Lista de semanas y tiendas actualizada", color="cyan"))
    )
    
    tab_resumen = ft.Column([
        ft.Row([txt_buscar_tienda, btn_consultar_tienda, dd_tiendas, dd_semanas, btn_actualizar_listas], wrap=True, spacing=6 if is_mobile_w else 8, vertical_alignment="center"),
        ft.Divider(height=8 if is_mobile_w else 10, color="#333333"),
        table_container
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    
    render_table()
    
    if es_admin():
        tab_admin = ft.Column([
            ft.Row([
                ft.Text("Reportes Semanales de Sunglass Hut", size=14 if is_mobile_w else 18, color="white", weight="bold"),
                btn_upload
            ], alignment="spaceBetween", vertical_alignment="center", wrap=True),
            ft.Divider(height=10, color="transparent"),
            weekly_reports_list,
            ft.Divider(height=15, color="#333344"),
            ft.Text("⚡ Cargar desde Ruta / Carpeta de Descargas", size=12 if is_mobile_w else 13, weight="bold", color="#00FFFF"),
            ft.Row([txt_ruta_excel, btn_cargar_ruta], wrap=True, spacing=6 if is_mobile_w else 10),
            ft.Container(height=5),
            lbl_upload_status
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
        tab_defs_w = [
            ("📊 Resumen Weekly", ft.Icons.BAR_CHART, tab_resumen),
            ("📤 Cargar Excel (Admin)", ft.Icons.UPLOAD_FILE, tab_admin)
        ]
        curr_w_idx = 0
        content_w_box = ft.Container(content=tab_defs_w[curr_w_idx][2], expand=True)
        tab_w_buttons = []
        for idx, (label, icon_name, tab_cnt) in enumerate(tab_defs_w):
            def make_w_click(i, cnt):
                def click(e):
                    content_w_box.content = cnt
                    for b_i, btn_c in enumerate(tab_w_buttons):
                        is_active = (b_i == i)
                        btn_c.bgcolor = "#7c3aed" if is_active else "#1e1e1e"
                        btn_c.border = ft.Border.all(1, "#9D50BB" if is_active else "#333333")
                    try: page.update()
                    except Exception: pass
                return click
    
            is_sel = (idx == curr_w_idx)
            btn_c = ft.Container(
                content=ft.Row([
                    ft.Icon(icon_name, size=15, color="#00FFFF" if is_sel else "#aaaaaa"),
                    ft.Text(label, size=12, weight="bold", color="white" if is_sel else "#aaaaaa")
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#7c3aed" if is_sel else "#1e1e1e",
                padding=ft.padding.Padding(12, 8, 12, 8),
                border_radius=8,
                border=ft.Border.all(1, "#9D50BB" if is_sel else "#333333"),
                on_click=make_w_click(idx, tab_cnt),
                ink=True
            )
            tab_w_buttons.append(btn_c)
    
        tab_w_bar_row = ft.Row(tab_w_buttons, scroll=ft.ScrollMode.AUTO, spacing=8)
        main_content = ft.Column([
            tab_w_bar_row,
            ft.Container(height=5),
            content_w_box
        ], expand=True)
    else:
        main_content = tab_resumen
    
    return ft.Column([
        ft.Row([
            ft.Text("📅 MÓDULO WEEKLY", size=22 if is_mobile_w else 24, color="#D8B4FE", weight="bold")
        ]),
        ft.Text("Consulta rápida de métricas semanales por tienda (Ventas, Target, % Target y Comparativo).", color="#aaaaaa", size=12 if is_mobile_w else 13),
        ft.Divider(height=12, color="#333333"),
        main_content
    ], expand=True)