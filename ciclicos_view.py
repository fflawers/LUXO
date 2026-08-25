import flet as ft
import os
import glob
import ciclicos_service as cs

def seleccionar_archivo_nativo(titulo="Seleccionar archivo Excel"):
    """
    Abre la ventana nativa del Explorador de Archivos de Windows (TopMost) usando PowerShell / Windows.Forms.
    """
    try:
        import subprocess
        ps_cmd = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $f = New-Object System.Windows.Forms.OpenFileDialog
        $f.InitialDirectory = [System.IO.Path]::Combine($env:USERPROFILE, 'Downloads')
        $f.Filter = "Archivos Excel (*.xlsx)|*.xlsx|Todos los archivos (*.*)|*.*"
        $f.Title = "{titulo}"
        $f.TopMost = $true
        $result = $f.ShowDialog()
        if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
            Write-Output $f.FileName
        }}
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
        print("Notice en PowerShell dialog:", ex_ps)

    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        initial_dir = os.path.expanduser('~/Downloads')
        if not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser('~/Desktop')
        f_selected = filedialog.askopenfilename(
            title=titulo,
            initialdir=initial_dir,
            filetypes=[("Archivos Excel (*.xlsx)", "*.xlsx"), ("Todos los archivos (*.*)", "*.*")]
        )
        root.destroy()
        if f_selected and os.path.exists(f_selected):
            return f_selected
    except Exception as ex_tk:
        print("Notice en Tkinter dialog:", ex_tk)

    return ""

def buscar_excel_reciente(patron="*.xlsx"):
    try:
        downloads_dir = os.path.expanduser('~/Downloads')
        if os.path.exists(downloads_dir):
            matches = [m for m in glob.glob(os.path.join(downloads_dir, patron)) if not os.path.basename(m).startswith('~$')]
            if matches:
                top_matches = matches[:20]
                top_matches.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
                return top_matches[0]
    except Exception:
        pass
    return ""

def build_ciclicos_view(page: ft.Page, store_code="A540", store_name="Tienda A540", user_role="admin", seleccionar_archivo_async=None):
    # Asegurar que existan las tablas en MySQL y purgar historial mayor a 6 meses
    try:
        cs.crear_tablas_ciclicos_if_not_exists()
    except Exception as ex_db:
        print("Notice db ciclicos init:", ex_db)

    # Estado local de la vista
    resultado_conciliacion = {"value": None}

    # Auto-detectar archivos recientes en Downloads como sugerencia inicial
    auto_escaneo = buscar_excel_reciente("*Libro*.xlsx") or buscar_excel_reciente("*escaneo*.xlsx")
    auto_sap = buscar_excel_reciente("*StockSummary*.xlsx") or buscar_excel_reciente("*SAP*.xlsx")

    # Campos de Texto para Rutas de Archivos
    txt_escaneo_path = ft.TextField(
        label="1. Archivo de Escaneo Físico (.xlsx)",
        value=auto_escaneo,
        hint_text="Haz clic en 'Buscar Archivo' o pega la ruta de tu Excel...",
        expand=True,
        dense=True
    )

    txt_sap_path = ft.TextField(
        label="2. Archivo de Inventario SAP (.xlsx)",
        value=auto_sap,
        hint_text="Haz clic en 'Buscar Archivo' o pega la ruta de tu reporte SAP...",
        expand=True,
        dense=True
    )

    # Funciones de búsqueda usando la MISMA función seleccionar_archivo_async de Gestión de Manuales
    def buscar_escaneo_click(e):
        def on_escaneo_cargado(ruta):
            if ruta:
                txt_escaneo_path.value = ruta
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(f"📄 Escaneo Físico cargado: {os.path.basename(ruta)}"), open=True)
                    page.update()
                except Exception: pass

        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Excel de Escaneo Físico",
                [("Excel files", "*.xlsx *.xls"), ("Todos los archivos", "*.*")],
                on_escaneo_cargado
            )
        else:
            path = seleccionar_archivo_nativo("Seleccionar Excel de Escaneo Físico")
            if path:
                txt_escaneo_path.value = path
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(f"📄 Escaneo Físico cargado: {os.path.basename(path)}"), open=True)
                    page.update()
                except Exception: pass

    def buscar_sap_click(e):
        def on_sap_cargado(ruta):
            if ruta:
                txt_sap_path.value = ruta
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(f"📄 Inventario SAP cargado: {os.path.basename(ruta)}"), open=True)
                    page.update()
                except Exception: pass

        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Excel de Inventario SAP",
                [("Excel files", "*.xlsx *.xls"), ("Todos los archivos", "*.*")],
                on_sap_cargado
            )
        else:
            path = seleccionar_archivo_nativo("Seleccionar Excel de Inventario SAP")
            if path:
                txt_sap_path.value = path
                try:
                    page.snack_bar = ft.SnackBar(ft.Text(f"📄 Inventario SAP cargado: {os.path.basename(path)}"), open=True)
                    page.update()
                except Exception: pass

    btn_buscar_escaneo = ft.ElevatedButton(
        "📁 Buscar Archivo",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=buscar_escaneo_click,
        style=ft.ButtonStyle(color="white", bgcolor="#0284c7")
    )

    btn_buscar_sap = ft.ElevatedButton(
        "📁 Buscar Archivo",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=buscar_sap_click,
        style=ft.ButtonStyle(color="white", bgcolor="#0284c7")
    )

    # Campos de Entrada Adicionales
    txt_marca = ft.TextField(
        label="Marca o Familia (ej. Ray-Ban, Oakley)",
        hint_text="Ray-Ban",
        width=300,
        dense=True
    )
    
    txt_comentarios = ft.TextField(
        label="Comentarios / Observaciones del Cíclico",
        hint_text="Ej. Faltantes en vitrina principal, mercancía en ajuste...",
        multiline=True,
        min_lines=2,
        max_lines=3,
        expand=True
    )

    # Contenedores para Mostrar Resultados en la Misma Página
    container_resumen = ft.Row(wrap=True, spacing=15)
    container_tablas = ft.Column(spacing=20, expand=True)

    def conciliar_click(e):
        path_esc = (txt_escaneo_path.value or "").strip().strip('"').strip("'")
        path_sap = (txt_sap_path.value or "").strip().strip('"').strip("'")

        # Auto-reparar si se seleccionó un archivo temporal de Excel (~$)
        for p_var, field_ref in [(path_esc, txt_escaneo_path), (path_sap, txt_sap_path)]:
            base_n = os.path.basename(p_var)
            if base_n.startswith('~$'):
                real_n = base_n.replace('~$', '')
                real_p = os.path.join(os.path.dirname(p_var), real_n)
                if os.path.exists(real_p):
                    field_ref.value = real_p
                    
        path_esc = (txt_escaneo_path.value or "").strip().strip('"').strip("'")
        path_sap = (txt_sap_path.value or "").strip().strip('"').strip("'")

        if not path_esc or not os.path.exists(path_esc):
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Por favor selecciona o pega una ruta válida para el archivo de Escaneo Físico."), open=True)
            try: page.update()
            except Exception: pass
            return
        if not path_sap or not os.path.exists(path_sap):
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Por favor selecciona o pega una ruta válida para el archivo de Inventario SAP."), open=True)
            try: page.update()
            except Exception: pass
            return

        try:
            res = cs.procesar_conciliacion_ciclico(path_esc, path_sap)
            resultado_conciliacion["value"] = res
            
            # REGLA EXPLICITA 1: Varianza 0% es VERDE (#16a34a), cualquier otro número (>0%) es ROJO (#dc2626)
            s = res["summary"]
            var_pct = s["varianza_pct"]
            color_var = "#16a34a" if var_pct == 0.0 else "#dc2626"

            card_var = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Varianza Global", size=13, weight="bold", color="#888888"),
                        ft.Text(f"{var_pct}%", size=28, weight="bold", color=color_var),
                        ft.Text(f"Piezas SAP: {s['total_sap_pzas']} | Escaneo: {s['total_escaneo_pzas']}", size=11, color="#888888")
                    ], horizontal_alignment="center"),
                    padding=15, width=220
                )
            )

            card_falta_esc = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Falta en tu Escaneo", size=13, weight="bold", color="#dc2626"),
                        ft.Text(str(s["total_falta_escaneo"]), size=28, weight="bold", color="#dc2626"),
                        ft.Text("Códigos en SAP no escaneados", size=11, color="#888888")
                    ], horizontal_alignment="center"),
                    padding=15, width=220
                )
            )

            card_falta_sap = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("No está en SAP", size=13, weight="bold", color="#2563eb"),
                        ft.Text(str(s["total_falta_sap"]), size=28, weight="bold", color="#2563eb"),
                        ft.Text("Escaneados no hallados en SAP", size=11, color="#888888")
                    ], horizontal_alignment="center"),
                    padding=15, width=220
                )
            )

            card_neg = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Stock Negativo SAP", size=13, weight="bold", color="#ea580c"),
                        ft.Text(str(s["total_negativos"]), size=28, weight="bold", color="#ea580c"),
                        ft.Text("Piezas en negativo", size=11, color="#888888")
                    ], horizontal_alignment="center"),
                    padding=15, width=220
                )
            )

            container_resumen.controls = [card_var, card_falta_esc, card_falta_sap, card_neg]

            # Construir Tablas de Alertas en la MISMISIMA página
            tables_list = []

            # 1. Tabla Falta en Escaneo
            if res["falta_en_escaneo"]:
                rows = []
                for item in res["falta_en_escaneo"]:
                    rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(item["upc"], weight="bold")),
                        ft.DataCell(ft.Text(item["descripcion"])),
                        ft.DataCell(ft.Text(str(item["cant_sap"]), color="#2563eb")),
                        ft.DataCell(ft.Text(str(item["cant_escaneo"]), color="#888888")),
                        ft.DataCell(ft.Text(item["mensaje"], color="#dc2626"))
                    ]))
                dt = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("UPC")),
                        ft.DataColumn(ft.Text("Descripción Gafa")),
                        ft.DataColumn(ft.Text("SAP")),
                        ft.DataColumn(ft.Text("Escaneo")),
                        ft.DataColumn(ft.Text("Alerta / Diagnóstico"))
                    ],
                    rows=rows
                )
                tables_list.append(ft.Column([
                    ft.Text("🔴 Códigos que no están en tu escaneo (Faltantes)", size=16, weight="bold", color="#dc2626"),
                    ft.Container(content=dt, border=ft.Border.all(1, "#fca5a5"), border_radius=8, padding=5)
                ]))

            # 2. Tabla Falta en SAP
            if res["falta_en_sap"]:
                rows = []
                for item in res["falta_en_sap"]:
                    rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(item["upc"], weight="bold")),
                        ft.DataCell(ft.Text(item["descripcion"])),
                        ft.DataCell(ft.Text(str(item["cant_sap"]), color="#888888")),
                        ft.DataCell(ft.Text(str(item["cant_escaneo"]), color="#16a34a")),
                        ft.DataCell(ft.Text(item["mensaje"], color="#2563eb"))
                    ]))
                dt = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("UPC")),
                        ft.DataColumn(ft.Text("Descripción Gafa")),
                        ft.DataColumn(ft.Text("SAP")),
                        ft.DataColumn(ft.Text("Escaneo")),
                        ft.DataColumn(ft.Text("Alerta / Diagnóstico"))
                    ],
                    rows=rows
                )
                tables_list.append(ft.Column([
                    ft.Text("🔵 Códigos escaneados que no están en tu SAP (Sobrantes / No registrados)", size=16, weight="bold", color="#2563eb"),
                    ft.Container(content=dt, border=ft.Border.all(1, "#93c5fd"), border_radius=8, padding=5)
                ]))

            # 3. Tabla Stock Negativo
            if res["stock_negativo"]:
                rows = []
                for item in res["stock_negativo"]:
                    rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(item["upc"], weight="bold")),
                        ft.DataCell(ft.Text(item["descripcion"])),
                        ft.DataCell(ft.Text(str(item["cant_sap"]), color="#dc2626", weight="bold")),
                        ft.DataCell(ft.Text(str(item["cant_escaneo"]))),
                        ft.DataCell(ft.Text(item["mensaje"], color="#ea580c"))
                    ]))
                dt = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("UPC")),
                        ft.DataColumn(ft.Text("Descripción Gafa")),
                        ft.DataColumn(ft.Text("SAP")),
                        ft.DataColumn(ft.Text("Escaneo")),
                        ft.DataColumn(ft.Text("Alerta / Diagnóstico"))
                    ],
                    rows=rows
                )
                tables_list.append(ft.Column([
                    ft.Text("⚠️ Piezas con Stock Negativo en SAP", size=16, weight="bold", color="#ea580c"),
                    ft.Container(content=dt, border=ft.Border.all(1, "#fdba74"), border_radius=8, padding=5)
                ]))

            if not tables_list:
                tables_list.append(ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color="#16a34a", size=30),
                        ft.Text("¡Excelente! No hay ninguna diferencia entre el escaneo y el reporte de SAP.", size=16, color="#15803d", weight="bold")
                    ]),
                    padding=20, bgcolor="#f0fdf4", border_radius=10
                ))

            container_tablas.controls = tables_list

            # REGLA EXPLICITA 2 & 3: GUARDADO AUTOMATICO E INMEDIATO EN BASE DE DATOS
            marca_val = txt_marca.value.strip() or "General"
            coment_val = txt_comentarios.value.strip()
            
            ok, msg_or_id = cs.guardar_ciclico_db(
                codigo_tienda=store_code,
                nombre_tienda=store_name,
                marca=marca_val,
                resumen=res["summary"],
                falta_esc=res["falta_en_escaneo"],
                falta_sap=res["falta_en_sap"],
                negativos=res["stock_negativo"],
                comentarios=coment_val,
                usuario="Tienda"
            )

            if ok:
                page.snack_bar = ft.SnackBar(ft.Text(f"🎉 Cíclico #{msg_or_id} conciliado y guardado automáticamente en LUXO."), open=True)
                cargar_historial(update_page=False)
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ Conciliado en pantalla, aviso de guardado: {msg_or_id}"), open=True)

            try: page.update()
            except Exception: pass

        except Exception as ex:
            print("Error en conciliar_click:", ex)
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error al procesar archivos: {ex}"), open=True)
            try: page.update()
            except Exception: pass

    btn_conciliar = ft.ElevatedButton(
        "⚡ Conciliar Cíclico",
        icon=ft.Icons.ANALYTICS,
        on_click=conciliar_click,
        style=ft.ButtonStyle(color="white", bgcolor="#1d4ed8")
    )

    # VISTA 1: Captura y Resultados inmediatos
    view_captura = ft.Column([
        ft.Text("📥 Carga y Conciliación de Cíclico", size=20, weight="bold"),
        ft.Row([txt_marca], spacing=15),
        ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("1. Escaneo Físico (.xlsx)", weight="bold"),
                    ft.Row([txt_escaneo_path, btn_buscar_escaneo], spacing=10)
                ]),
                padding=15, border=ft.Border.all(1, "#333344"), border_radius=10, bgcolor="#141424"
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("2. Inventario SAP (.xlsx)", weight="bold"),
                    ft.Row([txt_sap_path, btn_buscar_sap], spacing=10)
                ]),
                padding=15, border=ft.Border.all(1, "#333344"), border_radius=10, bgcolor="#141424"
            )
        ], spacing=15),
        ft.Row([txt_comentarios]),
        ft.Row([btn_conciliar], spacing=15),
        ft.Divider(),
        container_resumen,
        container_tablas
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)

    # VISTA 2: Historial con Despliegue Integrado
    container_historial_rows = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def cargar_historial(update_page=False):
        try:
            rows_db = cs.obtener_historial_ciclicos(codigo_tienda=store_code if user_role != "admin" else None)
            
            if not rows_db:
                container_historial_rows.controls = [
                    ft.Text("No hay ningún cíclico guardado en la base de datos.", color="#888888", italic=True)
                ]
                if update_page:
                    try: page.update()
                    except Exception: pass
                return

            items = []
            for r in rows_db:
                c_id = r["id"]
                t_nombre = r["nombre_tienda"] or r["codigo_tienda"]
                m_nombre = r["marca"] or "General"
                f_fecha = str(r["fecha_conteo"])
                var = r["varianza_pct"]
                coment = r["comentarios"] or "Sin comentarios"
                
                # REGLA EXPLICITA 1: Varianza 0% es VERDE, cualquier otro número es ROJO
                col_var = "#16a34a" if var == 0.0 else "#dc2626"

                # Obtener detalles del cíclico
                detalles = cs.obtener_detalle_ciclico(c_id)
                detail_rows = []
                if detalles:
                    for d in detalles:
                        color_tipo = "#dc2626" if d.get("tipo_alerta") == "FALTA_EN_ESCANEO" else ("#2563eb" if d.get("tipo_alerta") == "FALTA_EN_SAP" else "#ea580c")
                        detail_rows.append(ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(d.get("upc","")), weight="bold")),
                            ft.DataCell(ft.Text(str(d.get("descripcion","") or ""))),
                            ft.DataCell(ft.Text(str(d.get("cantidad_sap", 0)))),
                            ft.DataCell(ft.Text(str(d.get("cantidad_escaneo", 0)))),
                            ft.DataCell(ft.Text(str(d.get("tipo_alerta","")), color=color_tipo, weight="bold")),
                            ft.DataCell(ft.Text(str(d.get("comentario_item","") or "")))
                        ]))
                else:
                    detail_rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text("N/A", weight="bold")),
                        ft.DataCell(ft.Text("Sin discrepancias registradas")),
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("OK", color="#16a34a", weight="bold")),
                        ft.DataCell(ft.Text("Sin observaciones"))
                    ]))

                dt_detail = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("UPC")),
                        ft.DataColumn(ft.Text("Descripción")),
                        ft.DataColumn(ft.Text("SAP")),
                        ft.DataColumn(ft.Text("Escaneo")),
                        ft.DataColumn(ft.Text("Tipo Alerta")),
                        ft.DataColumn(ft.Text("Diagnóstico"))
                    ],
                    rows=detail_rows
                )

                # Contenedor desplegable integrado para la auditoría
                container_detalle = ft.Container(
                    content=ft.Column([
                        ft.Text(f"📋 Desglose Completo de Auditoría - Cíclico #{c_id}", weight="bold", size=14, color="#00FFFF"),
                        ft.Container(content=dt_detail, border=ft.Border.all(1, "#333344"), border_radius=8, padding=5)
                    ], spacing=10),
                    padding=10,
                    visible=False,
                    bgcolor="#0d0d18",
                    border_radius=8
                )

                def make_toggle_click(c_box):
                    def _handler(e):
                        c_box.visible = not c_box.visible
                        try: page.update()
                        except Exception: pass
                    return _handler

                items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(f"Cíclico #{c_id} - {m_nombre} ({t_nombre})", weight="bold", size=15),
                                    ft.Text(f"📅 Fecha: {f_fecha} | 💬 {coment}", size=12, color="#888888")
                                ], expand=True),
                                ft.Column([
                                    ft.Text(f"Varianza: {var}%", weight="bold", color=col_var, size=14),
                                    ft.Text(f"SAP: {r['total_sap_pzas']} pzas | Escaneo: {r['total_escaneo_pzas']} pzas", size=11, color="#888888")
                                ]),
                                ft.ElevatedButton(
                                    "👁️ Ver Detalle",
                                    icon=ft.Icons.UNFOLD_MORE,
                                    style=ft.ButtonStyle(color="white", bgcolor="#2563eb"),
                                    on_click=make_toggle_click(container_detalle)
                                )
                            ]),
                            container_detalle
                        ], spacing=8),
                        padding=12, border=ft.Border.all(1, "#333344"), border_radius=8, bgcolor="#141424"
                    )
                )

            container_historial_rows.controls = items
            if update_page:
                try: page.update()
                except Exception: pass
        except Exception as ex_h:
            print("Notice cargar_historial error:", ex_h)

    btn_refresh_historial = ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: cargar_historial(update_page=True), tooltip="Actualizar Historial")
    
    view_historial = ft.Column([
        ft.Row([
            ft.Text("📊 Historial de Conteos Cíclicos", size=20, weight="bold", expand=True),
            btn_refresh_historial
        ]),
        container_historial_rows
    ], expand=True, spacing=15)

    cargar_historial(update_page=False)

    # Subpestanas Robustas Personalizadas
    subtab_content = ft.Container(content=view_captura, expand=True)

    def switch_to_captura(e):
        subtab_content.content = view_captura
        btn_tab_captura.style = ft.ButtonStyle(color="white", bgcolor="#1d4ed8")
        btn_tab_historial.style = ft.ButtonStyle(color="white", bgcolor="#141424")
        try: page.update()
        except Exception: pass

    def switch_to_historial(e):
        cargar_historial(update_page=False)
        subtab_content.content = view_historial
        btn_tab_captura.style = ft.ButtonStyle(color="white", bgcolor="#141424")
        btn_tab_historial.style = ft.ButtonStyle(color="white", bgcolor="#1d4ed8")
        try: page.update()
        except Exception: pass

    btn_tab_captura = ft.ElevatedButton(
        "📥 Capturar y Conciliar",
        icon=ft.Icons.ADD_TASK,
        style=ft.ButtonStyle(color="white", bgcolor="#1d4ed8"),
        on_click=switch_to_captura
    )

    btn_tab_historial = ft.ElevatedButton(
        "📊 Historial y Auditoría",
        icon=ft.Icons.HISTORY,
        style=ft.ButtonStyle(color="white", bgcolor="#141424"),
        on_click=switch_to_historial
    )

    # Vista Principal del Módulo de Cíclicos
    return ft.Column([
        ft.Row([
            ft.Text("🔄 CONTEOS CÍCLICOS DE INVENTARIO", size=24, color="#00FFFF", weight="bold"),
        ]),
        ft.Text("Módulo de conciliación rápida entre tu escaneo físico y el reporte de inventario SAP.", color="#aaaaaa", size=13),
        ft.Row([btn_tab_captura, btn_tab_historial], spacing=10),
        ft.Divider(height=10, color="#333333"),
        subtab_content
    ], expand=True, spacing=12)
