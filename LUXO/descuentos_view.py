import flet as ft
import os
import urllib.parse
import threading
import descuentos_service as ds

def build_descuentos_view(page: ft.Page, store_code="A540", store_name="Tienda A540", user_role="admin", seleccionar_archivo_async=None):
    # Asegurar que exista la tabla en MySQL
    try:
        ds.crear_tabla_descuentos_if_not_exists()
    except Exception as ex_init:
        print("Notice init descuentos table:", ex_init)

    # Estado local de casillas marcadas como "Encontrado" (set de IDs)
    encontrados_set = set()

    # Identificación del perfil (Admin vs Tienda)
    es_admin = str(user_role).strip().lower() in ["admin", "administrativo", "coordinador", "jefe_zonal", "gerente"]
    tienda_activa_code = str(store_code).strip() if store_code else "A540"
    tienda_activa_label = str(store_name).strip() if store_name else f"Tienda {tienda_activa_code}"

    # Campo de tienda exclusivo para perfiles Administrativos / Admin
    txt_tienda_admin = ft.TextField(
        label="🏪 Filtrar por Sucursal (Modo Admin)",
        value=tienda_activa_code,
        hint_text="ej. 9277, 2281, AMERICAS VER",
        width=230,
        dense=True,
        on_change=lambda _: cargar_tabla_descuentos(update_page=True)
    )

    # Filtros Pestaña 1: Pendientes por Ubicar
    dd_filtro_marca_pend = ft.Dropdown(
        label="🏷️ Marca (Pendientes)",
        width=170,
        dense=True,
        options=[ft.dropdown.Option("TODAS", "Todas las Marcas")],
        value="TODAS"
    )
    dd_filtro_marca_pend.on_change = lambda _: cargar_tabla_descuentos(update_page=True)

    dd_filtro_tipo_pend = ft.Dropdown(
        label="🎨 Tipo Descuento",
        width=180,
        dense=True,
        options=[
            ft.dropdown.Option("TODOS", "Todos los Descuentos"),
            ft.dropdown.Option("20%", "🔵 20% OFF"),
            ft.dropdown.Option("30%", "🟢 30% OFF"),
            ft.dropdown.Option("ESTRATEGIA", "🔴 Estrategias 50%")
        ],
        value="TODOS"
    )
    dd_filtro_tipo_pend.on_change = lambda _: cargar_tabla_descuentos(update_page=True)

    # Filtros Pestaña 2: Encontradas
    dd_filtro_marca_enc = ft.Dropdown(
        label="🏷️ Marca (Encontradas)",
        width=170,
        dense=True,
        options=[ft.dropdown.Option("TODAS", "Todas las Marcas")],
        value="TODAS"
    )
    dd_filtro_marca_enc.on_change = lambda _: cargar_tabla_descuentos(update_page=True)

    dd_filtro_tipo_enc = ft.Dropdown(
        label="🎨 Tipo Descuento",
        width=180,
        dense=True,
        options=[
            ft.dropdown.Option("TODOS", "Todos los Descuentos"),
            ft.dropdown.Option("20%", "🔵 20% OFF"),
            ft.dropdown.Option("30%", "🟢 30% OFF"),
            ft.dropdown.Option("ESTRATEGIA", "🔴 Estrategias 50%")
        ],
        value="TODOS"
    )
    dd_filtro_tipo_enc.on_change = lambda _: cargar_tabla_descuentos(update_page=True)

    txt_buscar_upc = ft.TextField(
        label="🔍 Buscar por UPC o Descripción (Búsqueda General)",
        hint_text="Escanea o escribe un UPC...",
        width=300,
        dense=True,
        on_change=lambda _: cargar_tabla_descuentos(update_page=True)
    )

    txt_archivo_path = ft.TextField(
        label="Archivo Excel de Descuentos (.xlsx)",
        hint_text="Haz clic en 'Buscar Archivo' o carga el Excel semanal...",
        expand=True,
        dense=True
    )

    # Barra de Progreso Redondeada y Porcentaje Live
    progress_bar = ft.ProgressBar(width=350, value=0.0, color="#00FFFF", bgcolor="#222233", border_radius=10, visible=False)
    lbl_pct = ft.Text("0%", weight="bold", color="#00FFFF", size=14, visible=False)
    lbl_status_carga = ft.Text("", size=13, weight="bold")

    txt_conteo_badge = ft.Text("🏷️ 0 promociones asignadas", weight="bold", color="#00FFFF", size=14)
    container_tabs_principal = ft.Column(spacing=10)

    def make_google_btn(u_code):
        clean_u = str(u_code).strip()
        search_url = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(clean_u)}"
        return ft.Container(
            content=ft.Text("🌎", size=18),
            url=search_url,
            tooltip=f"Ver foto de {clean_u} en Google Imágenes 🖼️",
            padding=2
        )

    def poblar_opciones_filtros(codigo_t):
        try:
            marcas, _ = ds.obtener_marcas_y_descuentos_disponibles(codigo_t)
            opts_m = [ft.dropdown.Option("TODAS", "Todas las Marcas")]
            for m in marcas:
                if m and str(m).strip():
                    opts_m.append(ft.dropdown.Option(str(m).strip(), str(m).strip()))
            dd_filtro_marca_pend.options = opts_m
            dd_filtro_marca_enc.options = opts_m
        except Exception as ex_f:
            print("Notice poblar_opciones_filtros:", ex_f)

    def cargar_tabla_descuentos(update_page=False):
        c_target = txt_tienda_admin.value.strip() if (es_admin and txt_tienda_admin.value) else tienda_activa_code
        query_search = txt_buscar_upc.value.strip() if txt_buscar_upc.value else ""

        try:
            rows_db = ds.obtener_descuentos_por_tienda(codigo_tienda=c_target if c_target else None, query_search=query_search if query_search else None)
        except Exception as ex_fetch:
            print("Notice fetch descuentos error:", ex_fetch)
            rows_db = []

        total_modelos = len(rows_db)
        total_piezas = sum(int(r.get("stock_tienda", 1) or 1) for r in rows_db)

        # Clasificación en tiempo real entre Pendientes y Encontradas
        list_pendientes_raw = [r for r in rows_db if r["id"] not in encontrados_set]
        list_encontradas_raw = [r for r in rows_db if r["id"] in encontrados_set]

        # Aplicar Filtros Independientes a Pendientes
        sel_m_p = dd_filtro_marca_pend.value
        if sel_m_p and sel_m_p != "TODAS":
            list_pendientes_raw = [r for r in list_pendientes_raw if str(r.get("descripcion", "")).strip().upper() == sel_m_p.upper()]

        sel_t_p = dd_filtro_tipo_pend.value
        if sel_t_p and sel_t_p != "TODOS":
            if sel_t_p == "20%":
                list_pendientes_raw = [r for r in list_pendientes_raw if "20%" in str(r.get("tipo_descuento", "")).upper() or "0.2" in str(r.get("tipo_descuento", ""))]
            elif sel_t_p == "30%":
                list_pendientes_raw = [r for r in list_pendientes_raw if "30%" in str(r.get("tipo_descuento", "")).upper() or "0.3" in str(r.get("tipo_descuento", ""))]
            elif sel_t_p == "ESTRATEGIA":
                list_pendientes_raw = [r for r in list_pendientes_raw if "ESTRATEGIA" in str(r.get("tipo_descuento", "")).upper()]

        # Aplicar Filtros Independientes a Encontradas
        sel_m_e = dd_filtro_marca_enc.value
        if sel_m_e and sel_m_e != "TODAS":
            list_encontradas_raw = [r for r in list_encontradas_raw if str(r.get("descripcion", "")).strip().upper() == sel_m_e.upper()]

        sel_t_e = dd_filtro_tipo_enc.value
        if sel_t_e and sel_t_e != "TODOS":
            if sel_t_e == "20%":
                list_encontradas_raw = [r for r in list_encontradas_raw if "20%" in str(r.get("tipo_descuento", "")).upper() or "0.2" in str(r.get("tipo_descuento", ""))]
            elif sel_t_e == "30%":
                list_encontradas_raw = [r for r in list_encontradas_raw if "30%" in str(r.get("tipo_descuento", "")).upper() or "0.3" in str(r.get("tipo_descuento", ""))]
            elif sel_t_e == "ESTRATEGIA":
                list_encontradas_raw = [r for r in list_encontradas_raw if "ESTRATEGIA" in str(r.get("tipo_descuento", "")).upper()]

        txt_conteo_badge.value = f"📋 Pendientes: {len(list_pendientes_raw)} | ☑️ Ubicados: {len(list_encontradas_raw)} | 📦 Total: {total_piezas:,} pz(s)"

        # --- 1. RENDERIZAR PESTAÑA PENDIENTES (REGLA ESTRICTA MAX 20 FILAS) ---
        rows_pendientes_view = list_pendientes_raw[:20]  # ¡JAMÁS MÁS DE 20 FILAS!
        detail_pendientes = []

        for item in rows_pendientes_view:
            rec_id = item["id"]
            upc_str = str(item.get("upc", "")).strip()
            desc_str = str(item.get("descripcion", "") or "Sin descripción")
            descuento_str = ds.normalizar_tipo_descuento(item.get("tipo_descuento", ""))
            stock_val = item.get("stock_tienda", 1)
            t_nombre_excel = str(item.get("nombre_tienda", "") or item.get("codigo_tienda", "")).strip()

            def make_mark_pend_cb(r_id):
                def _chk_pend(e):
                    if e.control.value:
                        encontrados_set.add(r_id)
                        cargar_tabla_descuentos(update_page=True)
                return _chk_pend

            chk_pend = ft.Checkbox(value=False, tooltip="Marcar como ubicado y enviar a pestaña Encontradas")

            row_cell_upc = ft.DataCell(
                ft.Container(content=ft.Text(upc_str, weight="bold", size=11, selectable=True), width=120)
            )

            d_upper = descuento_str.upper()
            if "20%" in d_upper or d_upper == "0.2":
                lbl_desc_display = "20% OFF"; badge_bg = "#1e3a8a"; badge_border = "#3b82f6"; badge_color = "#93c5fd"
            elif "30%" in d_upper or d_upper == "0.3":
                lbl_desc_display = "30% OFF"; badge_bg = "#065f46"; badge_border = "#10b981"; badge_color = "#6ee7b7"
            elif "ESTRATEGIA" in d_upper:
                lbl_desc_display = descuento_str; badge_bg = "#991b1b"; badge_border = "#ef4444"; badge_color = "#fca5a5"
            else:
                lbl_desc_display = descuento_str; badge_bg = "#854d0e"; badge_border = "#f59e0b"; badge_color = "#fef08a"

            tag_descuento = ft.Container(
                content=ft.Text(lbl_desc_display, weight="bold", color=badge_color, size=10),
                bgcolor=badge_bg, padding=4, border_radius=6, border=ft.Border.all(1, badge_border)
            )

            tag_tienda_excel = ft.Container(
                content=ft.Text(f"🏪 {t_nombre_excel}", weight="bold", color="#00FFFF", size=10),
                bgcolor="#0F172A", padding=4, border_radius=6, border=ft.Border.all(1, "#0284c7")
            )

            d_row = ft.DataRow(
                cells=[
                    ft.DataCell(chk_pend),
                    ft.DataCell(make_google_btn(upc_str)),
                    row_cell_upc,
                    ft.DataCell(ft.Text(desc_str, selectable=True, size=12)),
                    ft.DataCell(tag_descuento),
                    ft.DataCell(tag_tienda_excel),
                    ft.DataCell(ft.Text(f"{stock_val} pz(s)", weight="bold", color="#16a34a", size=12))
                ]
            )
            chk_pend.on_change = make_mark_pend_cb(rec_id)
            detail_pendientes.append(d_row)

        if not detail_pendientes:
            dt_pendientes_ctrl = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#16a34a", size=40),
                    ft.Text("¡Excelente! No hay promociones pendientes.", color="#16a34a", weight="bold", size=14)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20, bgcolor="#141424", border_radius=10
            )
        else:
            dt_pendientes = ft.DataTable(
                column_spacing=12,
                columns=[
                    ft.DataColumn(ft.Text("☑️ Ubicar", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("🌎", weight="bold", size=15)),
                    ft.DataColumn(ft.Text("UPC", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("Descripción / Modelo", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("🏷️ Descuento", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("🏪 Sucursal Excel", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("Stock", weight="bold", color="#00FFFF", size=12))
                ],
                rows=detail_pendientes,
                border=ft.Border.all(1, "#333344"),
                border_radius=8,
                vertical_lines=ft.BorderSide(1, "#222222"),
                horizontal_lines=ft.BorderSide(1, "#222222")
            )
            dt_pendientes_ctrl = ft.Container(
                content=ft.Row([dt_pendientes], scroll=ft.ScrollMode.AUTO),
                bgcolor="#0F0F1A", padding=8, border_radius=10
            )

        # --- 2. RENDERIZAR PESTAÑA ENCONTRADAS (LIGERA HASTA 50 FILAS) ---
        rows_encontradas_view = list_encontradas_raw[:50]
        detail_encontradas = []

        for item in rows_encontradas_view:
            rec_id = item["id"]
            upc_str = str(item.get("upc", "")).strip()
            desc_str = str(item.get("descripcion", "") or "Sin descripción")
            descuento_str = ds.normalizar_tipo_descuento(item.get("tipo_descuento", ""))
            stock_val = item.get("stock_tienda", 1)

            def make_unmark_enc_cb(r_id):
                def _chk_enc(e):
                    if not e.control.value:
                        encontrados_set.discard(r_id)
                        cargar_tabla_descuentos(update_page=True)
                return _chk_enc

            chk_enc = ft.Checkbox(value=True, tooltip="Desmarcar para devolver a Pendientes")

            row_cell_upc = ft.DataCell(
                ft.Container(content=ft.Text(upc_str, weight="bold", size=11, selectable=True), width=120)
            )

            d_row_enc = ft.DataRow(
                color="#1b2e1b",
                cells=[
                    ft.DataCell(chk_enc),
                    row_cell_upc,
                    ft.DataCell(ft.Text(desc_str, selectable=True, size=12)),
                    ft.DataCell(ft.Text(descuento_str, weight="bold", color="#FFD700", size=11)),
                    ft.DataCell(ft.Text(f"{stock_val} pz(s)", weight="bold", color="#16a34a", size=12))
                ]
            )
            chk_enc.on_change = make_unmark_enc_cb(rec_id)
            detail_encontradas.append(d_row_enc)

        if not detail_encontradas:
            dt_encontradas_ctrl = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INBOX, color="#888888", size=38),
                    ft.Text("Aún no has marcado gafas como encontradas.", color="#888888", italic=True, size=14)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20, bgcolor="#141424", border_radius=10
            )
        else:
            dt_encontradas = ft.DataTable(
                column_spacing=12,
                columns=[
                    ft.DataColumn(ft.Text("☑️ Encontrado", weight="bold", color="#16a34a", size=12)),
                    ft.DataColumn(ft.Text("UPC", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("Descripción / Modelo", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("🏷️ Descuento", weight="bold", color="#00FFFF", size=12)),
                    ft.DataColumn(ft.Text("Stock", weight="bold", color="#00FFFF", size=12))
                ],
                rows=detail_encontradas,
                border=ft.Border.all(1, "#16a34a"),
                border_radius=8,
                vertical_lines=ft.BorderSide(1, "#112611"),
                horizontal_lines=ft.BorderSide(1, "#112611")
            )
            dt_encontradas_ctrl = ft.Container(
                content=ft.Row([dt_encontradas], scroll=ft.ScrollMode.AUTO),
                bgcolor="#0A180A", padding=8, border_radius=10
            )

        # Control de Pestañas Independientes Adaptativo Celular
        tab_pendientes_content = ft.Container(
            content=ft.Column([
                ft.Row([dd_filtro_marca_pend, dd_filtro_tipo_pend], spacing=8, wrap=True),
                dt_pendientes_ctrl
            ], spacing=8),
            padding=8
        )

        tab_encontradas_content = ft.Container(
            content=ft.Column([
                ft.Row([dd_filtro_marca_enc, dd_filtro_tipo_enc], spacing=8, wrap=True),
                dt_encontradas_ctrl
            ], spacing=8),
            padding=8
        )

        tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            length=2,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label=f"📋 Pendientes ({len(list_pendientes_raw)}) [Max 20]", icon=ft.Icons.FORMAT_LIST_BULLETED),
                            ft.Tab(label=f"☑️ Ubicadas ({len(list_encontradas_raw)})", icon=ft.Icons.CHECK_BOX)
                        ]
                    ),
                    ft.Container(
                        content=ft.TabBarView(
                            controls=[
                                tab_pendientes_content,
                                tab_encontradas_content
                            ]
                        ),
                        height=580
                    )
                ]
            )
        )

        card_resumen_piezas = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.INVENTORY_2, color="#00FFFF", size=18),
                    ft.Text("Resumen Auditoría:", weight="bold", color="#00FFFF", size=13)
                ], spacing=6),
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"📋 Pendientes: {len(list_pendientes_raw):,}", weight="bold", color="#FFD700", size=12),
                        bgcolor="#2d2206", padding=5, border_radius=6, border=ft.Border.all(1, "#854d0e")
                    ),
                    ft.Container(
                        content=ft.Text(f"☑️ Ubicados: {len(list_encontradas_raw):,}", weight="bold", color="#16a34a", size=12),
                        bgcolor="#052e16", padding=5, border_radius=6, border=ft.Border.all(1, "#16a34a")
                    ),
                    ft.Container(
                        content=ft.Text(f"📦 TOTAL: {total_piezas:,} pz(s)", weight="bold", color="#00FFFF", size=12),
                        bgcolor="#0F172A", padding=5, border_radius=6, border=ft.Border.all(1, "#0284c7")
                    )
                ], spacing=8, wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            bgcolor="#0F172A", padding=10, border_radius=8, border=ft.Border.all(1, "#0284c7")
        )

        container_tabs_principal.controls = [
            tabs_control,
            card_resumen_piezas
        ]

        if update_page:
            try: page.update()
            except Exception: pass

    def procesar_archivo_click(e):
        path = txt_archivo_path.value.strip()
        if not path or not os.path.exists(path):
            try:
                page.snack_bar = ft.SnackBar(ft.Text("⚠️ Por favor selecciona un archivo Excel válido."), open=True)
                page.update()
            except Exception: pass
            return

        btn_procesar.disabled = True
        btn_buscar_archivo.disabled = True
        progress_bar.visible = True
        progress_bar.value = 0.05
        lbl_pct.visible = True
        lbl_pct.value = "5%"
        lbl_status_carga.value = "⏳ Iniciando lectura masiva..."
        lbl_status_carga.color = "#00FFFF"
        try: page.update()
        except Exception: pass

        def _on_progress(pct, status_text):
            progress_bar.visible = True
            progress_bar.value = float(pct) / 100.0
            lbl_pct.visible = True
            lbl_pct.value = f"{pct}%"
            lbl_status_carga.value = status_text
            lbl_status_carga.color = "#00FFFF"
            try:
                page.update()
            except Exception: pass

        def _bg_task():
            ok, msg = ds.procesar_excel_descuentos(path, progress_callback=_on_progress)
            btn_procesar.disabled = False
            btn_buscar_archivo.disabled = False
            progress_bar.visible = False
            lbl_pct.visible = False
            
            if ok:
                lbl_status_carga.value = "✅ ¡Catálogo fragmentado con éxito a todas las sucursales!"
                lbl_status_carga.color = "#16a34a"
                c_target = txt_tienda_admin.value.strip() if (es_admin and txt_tienda_admin.value) else tienda_activa_code
                poblar_opciones_filtros(c_target)
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(msg), open=True, bgcolor="#16a34a")
                    page.update()
                except Exception: pass
                cargar_tabla_descuentos(update_page=True)
            else:
                lbl_status_carga.value = f"❌ Error al procesar: {msg}"
                lbl_status_carga.color = "#dc2626"
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(f"❌ {msg}"), open=True, bgcolor="#dc2626")
                    page.update()
                except Exception: pass

        threading.Thread(target=_bg_task, daemon=True).start()

    def buscar_excel_descuentos_click(e):
        def on_excel_cargado(ruta):
            if ruta:
                txt_archivo_path.value = ruta
                try: page.update()
                except Exception: pass
                procesar_archivo_click(None)

        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Excel Semanal de Descuentos",
                [("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")],
                on_excel_cargado
            )
        else:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                initial_dir = os.path.expanduser('~/Downloads')
                f_selected = filedialog.askopenfilename(
                    title="Seleccionar Excel Semanal de Descuentos",
                    initialdir=initial_dir,
                    filetypes=[("Archivos Excel (*.xlsx)", "*.xlsx"), ("Todos los archivos (*.*)", "*.*")]
                )
                root.destroy()
                if f_selected and os.path.exists(f_selected):
                    txt_archivo_path.value = f_selected
                    try: page.update()
                    except Exception: pass
                    procesar_archivo_click(None)
            except Exception as ex_dialog:
                print("Notice en dialog:", ex_dialog)

    btn_buscar_archivo = ft.ElevatedButton(
        "📁 Buscar Archivo",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=buscar_excel_descuentos_click,
        style=ft.ButtonStyle(color="white", bgcolor="#0284c7")
    )

    btn_procesar = ft.ElevatedButton(
        "🚀 Cargar Catálogo Semanal",
        icon=ft.Icons.CLOUD_UPLOAD,
        on_click=procesar_archivo_click,
        style=ft.ButtonStyle(color="white", bgcolor="#16a34a")
    )

    # Carga inicial de datos y opciones de filtro
    poblar_opciones_filtros(tienda_activa_code)
    cargar_tabla_descuentos(update_page=False)

    # Bloque de Carga (Visibilidad para perfiles administrativos)
    card_carga_admin = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color="#FFD700", size=22),
                ft.Text("Carga Central de Ofertas (Perfil Administrativo)", size=16, weight="bold", color="#FFD700")
            ], spacing=8),
            ft.Text("Sube aquí el Excel semanal. LUXO fragmentará las ofertas y las asignará a cada sucursal en automático.", size=12, color="#aaaaaa"),
            ft.Row([txt_archivo_path, btn_buscar_archivo], spacing=10),
            ft.Row([
                btn_procesar,
                lbl_pct,
                progress_bar,
                lbl_status_carga
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        ], spacing=10),
        padding=15, border=ft.Border.all(1, "#854d0e"), border_radius=10, bgcolor="#1e1809"
    )

    search_bar_controls = [txt_buscar_upc]
    if es_admin:
        search_bar_controls.insert(0, txt_tienda_admin)

    # Vista Principal del Módulo de Descuentos
    return ft.Column([
        ft.Row([
            ft.Text("🏷️ DESCUENTOS Y PROMOCIONES", size=24, color="#00FFFF", weight="bold"),
            ft.Container(
                content=ft.Text(f"🏪 Sucursal Activa: {tienda_activa_label} ({tienda_activa_code})", weight="bold", color="#00FFFF", size=13),
                bgcolor="#0F0F1A", padding=8, border_radius=8, border=ft.Border.all(1, "#00FFFF")
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        ft.Text("Módulo de localización rápida con sistema de cola dinámica y pestaña de ubicados.", color="#aaaaaa", size=13),
        card_carga_admin if es_admin else ft.Container(),
        ft.Divider(height=10, color="#333333"),
        ft.Row(search_bar_controls + [ft.Container(content=txt_conteo_badge, padding=10)], spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        container_tabs_principal
    ], expand=True, spacing=15)


