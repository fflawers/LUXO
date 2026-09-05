import flet as ft
import os
import json
from datetime import datetime, timezone, timedelta

PARROQUIALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "parroquiales")
MINUTAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "minutas")

def asegurar_directorios():
    os.makedirs(PARROQUIALES_DIR, exist_ok=True)
    os.makedirs(MINUTAS_DIR, exist_ok=True)

def get_now_mexico_city():
    utc_now = datetime.now(timezone.utc)
    return utc_now - timedelta(hours=6)

def crear_tablas_parroquiales_if_not_exists(db):
    if not db:
        return False
    try:
        cursor = db.cursor()
        
        # 1. Tabla de Avisos Parroquiales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parroquiales_avisos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                zona_id VARCHAR(50) DEFAULT '0',
                titulo VARCHAR(255) NOT NULL,
                descripcion TEXT,
                url_enlace VARCHAR(500) DEFAULT '',
                tipo VARCHAR(50) DEFAULT 'Aviso',
                fecha_limite DATE NULL,
                creado_por VARCHAR(100) DEFAULT '',
                usuario_id INT DEFAULT 0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Tabla de Minutas Semanales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS minutas_zonales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                zona_id VARCHAR(50) DEFAULT '1',
                numero_semana INT NOT NULL,
                anio INT NOT NULL,
                fecha_junta DATE NULL,
                titulo VARCHAR(255) NOT NULL,
                asistentes TEXT,
                temas_tratados TEXT,
                acuerdos_compromisos TEXT,
                foto_minuta VARCHAR(255) DEFAULT '',
                creado_por VARCHAR(100) DEFAULT '',
                usuario_id INT DEFAULT 0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Tabla de Permisos de Redactor
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permisos_redaccion_minutas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                zona_id VARCHAR(50) DEFAULT '1',
                activo TINYINT DEFAULT 1,
                asignado_por VARCHAR(100) DEFAULT '',
                fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_usr_zona (usuario_id, zona_id)
            )
        """)
        
        db.commit()
        cursor.close()
        return True
    except Exception as ex:
        print("Notice crear_tablas_parroquiales_if_not_exists:", ex)
        return False

def enviar_notificacion_campana(db, titulo, mensaje, tipo="parroquial", zona_id="0"):
    """Inserta una notificacion en la campana de alertas para los usuarios destinatarios."""
    if not db:
        return
    try:
        cursor = db.cursor(dictionary=True)
        if str(zona_id) == "0" or str(zona_id).upper() == "GENERAL":
            cursor.execute("SELECT ID_Usuario FROM usuarios")
        else:
            z_clean = str(zona_id).strip()
            cursor.execute("""
                SELECT ID_Usuario FROM usuarios 
                WHERE Zona LIKE %s OR Zona = %s OR Rol = 'Admin'
            """, (f"%{z_clean}%", z_clean))
            
        users = cursor.fetchall()
        for u in users:
            uid = u.get("ID_Usuario")
            if uid:
                cursor.execute("""
                    INSERT INTO notificaciones (ID_Usuario, Titulo, Mensaje, Tipo, Fecha_Hora, Leida)
                    VALUES (%s, %s, %s, %s, %s, 0)
                """, (uid, titulo, mensaje, tipo, get_now_mexico_city().strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        cursor.close()
    except Exception as ex:
        print("Notice enviar_notificacion_campana:", ex)

def usuario_tiene_permiso_redactor(db, usuario_id, rol_usuario, zona_id):
    """Determina si un usuario puede redactar/publicar en su zona."""
    if str(rol_usuario).lower() == "admin":
        return True
    if not db or not usuario_id:
        return False
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT activo FROM permisos_redaccion_minutas 
            WHERE usuario_id = %s AND (zona_id = %s OR zona_id = '0')
        """, (usuario_id, str(zona_id)))
        row = cursor.fetchone()
        cursor.close()
        if row and row.get("activo") == 1:
            return True
    except Exception as ex:
        print("Notice usuario_tiene_permiso_redactor:", ex)
    return False

def build_parroquiales_minutas_view(page, user_info, conectar_db_fn, mostrar_snack_fn, tr_fn=None, get_zona_region_fn=None, seleccionar_archivo_async=None, actualizar_campana_fn=None):
    asegurar_directorios()
    db_fn = conectar_db_fn
    mostrar_snack = mostrar_snack_fn or (lambda msg, col: print(msg))
    tr = tr_fn or (lambda es, en, *args: es)
    
    usuario_id = user_info.get("id") or 1
    rol_usuario = (user_info.get("rol") or "").strip()
    nombre_usuario = user_info.get("nombre") or "Usuario"
    es_admin = (rol_usuario.lower() == "admin")
    
    # Obtener zona activa actual
    def get_curr_zona():
        if get_zona_region_fn:
            try:
                z, _ = get_zona_region_fn()
                if z and str(z) != "0": return str(z)
            except Exception: pass
        raw_z = user_info.get("zona") or "Zona Centro"
        z_map = {"ZONA CENTRO": "1", "ZONA NORTE": "2", "ZONA OCCIDENTE": "3", "ZONA SUR": "4", "CENTRO": "1", "NORTE": "2", "OCCIDENTE": "3", "SUR": "4"}
        clean = str(raw_z).replace("📍", "").replace("Zona:", "").strip().upper()
        return z_map.get(clean, "1")
        
    zona_activa = [get_curr_zona()]
    
    # Comprobar tablas
    db_init = db_fn()
    if db_init:
        crear_tablas_parroquiales_if_not_exists(db_init)
        db_init.close()
        
    tab_activa = ["parroquiales"] # "parroquiales", "minutas", "permisos"
    
    # Contenedores principales
    content_area = ft.Container(expand=True)
    
    # -------------------------------------------------------------
    # 1. PESTAÑA: AVISOS PARROQUIALES (CURSOS, TAREAS, ACTIVIDADES)
    # -------------------------------------------------------------
    def build_parroquiales_tab():
        is_mobile = (page.width < 700) if (page and page.width) else False
        db = db_fn()
        puede_publicar = False
        avisos = []
        
        if db:
            puede_publicar = usuario_tiene_permiso_redactor(db, usuario_id, rol_usuario, zona_activa[0])
            try:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM parroquiales_avisos 
                    WHERE zona_id = %s OR zona_id = '0' OR zona_id = 'GENERAL'
                    ORDER BY id DESC LIMIT 50
                """, (zona_activa[0],))
                avisos = cursor.fetchall()
                cursor.close()
            except Exception as ex:
                print("Error cargando parroquiales:", ex)
            db.close()
            
        avisos_cards = []
        
        if not avisos:
            avisos_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("📢", size=36, text_align="center"),
                        ft.Text("No hay avisos parroquiales activos por el momento.", color="#aaaaaa", size=14, text_align="center", italic=True),
                        ft.Text("Aquí aparecerán los comunicados oficiales, enlaces a cursos y tareas de la semana.", color="#777777", size=12, text_align="center")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=30,
                    bgcolor="#10101C",
                    border_radius=12,
                    border=ft.Border.all(1, "#222233"),
                    alignment=ft.alignment.Alignment(0, 0)
                )
            )
        else:
            for av in avisos:
                tipo = av.get("tipo") or "Aviso"
                badge_info = {
                    "Curso": ("📚 CURSO / CAPACITACIÓN", "#00FFFF", "#003344"),
                    "Actividad": ("⚡ ACTIVIDAD / TAREA", "#FFD700", "#332B00"),
                    "Urgente": ("🔥 URGENTE / IMPORTANTE", "#FF4500", "#330D00"),
                    "Aviso": ("📢 AVISO OFICIAL", "#D8B4FE", "#251238")
                }.get(tipo, ("📢 AVISO", "#D8B4FE", "#251238"))
                
                f_crea = av.get("fecha_creacion")
                f_crea_str = f_crea.strftime("%d/%m/%Y %H:%M") if f_crea else ""
                
                f_lim = av.get("fecha_limite")
                f_lim_str = f"⏳ Fecha Límite: {f_lim.strftime('%d/%m/%Y')}" if f_lim else None
                
                url_btn = None
                if av.get("url_enlace") and str(av.get("url_enlace")).strip().startswith("http"):
                    target_url = av.get("url_enlace").strip()
                    url_btn = ft.ElevatedButton(
                        "🌐 Abrir Curso / Enlace",
                        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                        bgcolor="#00FFFF",
                        color="#05070D",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(weight="bold", size=12)),
                        on_click=lambda e, u=target_url: page.launch_url(u)
                    )
                
                def make_eliminar_aviso(av_id, av_tit):
                    def on_eliminar(ev):
                        def confirmar_delete(e_conf):
                            db_del = db_fn()
                            if db_del:
                                try:
                                    cur_d = db_del.cursor()
                                    cur_d.execute("DELETE FROM parroquiales_avisos WHERE id = %s", (av_id,))
                                    db_del.commit()
                                    db_del.close()
                                    page.pop_dialog()
                                    mostrar_snack("🗑️ Aviso Parroquial eliminado correctamente", "#FF4500")
                                    recargar_vista()
                                except Exception as ex_d:
                                    print("Error eliminando aviso:", ex_d)
                                    mostrar_snack("Error al eliminar aviso", "red")
                        
                        dlg_conf = ft.AlertDialog(
                            title=ft.Text("🗑️ Eliminar Aviso Parroquial", color="#FF4500", weight="bold"),
                            content=ft.Text(f"¿Estás seguro de que deseas eliminar el aviso '{av_tit}'?", color="white"),
                            actions=[
                                ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
                                ft.ElevatedButton("Eliminar", bgcolor="#FF4500", color="white", on_click=confirmar_delete)
                            ],
                            actions_alignment="end",
                            bgcolor="#10101C"
                        )
                        page.show_dialog(dlg_conf)
                    return on_eliminar

                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(badge_info[0], color=badge_info[1], size=10, weight="bold"),
                                bgcolor=badge_info[2],
                                padding=ft.padding.Padding(8, 3, 8, 3),
                                border_radius=6,
                                border=ft.Border.all(1, badge_info[1])
                            ),
                            ft.Container(expand=True),
                            ft.Text(f_crea_str, color="#777777", size=10),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                icon_color="#FF4500",
                                icon_size=18,
                                tooltip="Eliminar Aviso",
                                on_click=make_eliminar_aviso(av.get("id"), av.get("titulo") or "Aviso")
                            ) if (es_admin or av.get("usuario_id") == usuario_id) else ft.Container()
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(av.get("titulo") or "Aviso", color="white", size=15 if is_mobile else 16, weight="bold"),
                        ft.Text(av.get("descripcion") or "", color="#cccccc", size=12 if is_mobile else 13),
                        ft.Divider(height=8, color="#222233"),
                        ft.Row([
                            ft.Text(f"👤 Publicado por: {av.get('creado_por') or 'Administración'}", color="#888888", size=10, italic=True),
                            ft.Container(expand=True),
                            ft.Text(f_lim_str, color="#FFD700", size=11, weight="bold") if f_lim_str else ft.Container()
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([url_btn]) if url_btn else ft.Container()
                    ], spacing=8),
                    padding=16,
                    bgcolor="#141424",
                    border_radius=12,
                    border=ft.Border.all(1.2, "#2A2A3E"),
                    shadow=[ft.BoxShadow(color="#10000000", blur_radius=8, spread_radius=1)]
                )
                avisos_cards.append(card)
                
        def abrir_dialog_nuevo_aviso(e):
            tf_tit = ft.TextField(label="Título del Aviso o Curso *", border_color="#00FFFF", color="white", dense=True)
            tf_desc = ft.TextField(label="Descripción / Instrucciones *", multiline=True, min_lines=3, max_lines=6, border_color="#00FFFF", color="white")
            tf_url = ft.TextField(label="URL / Enlace (Opcional, ej: https://...)", border_color="#D8B4FE", color="white", dense=True)
            
            dd_tipo = ft.Dropdown(
                label="Tipo de Parroquial",
                options=[
                    ft.dropdown.Option("Aviso", "📢 Aviso Oficial"),
                    ft.dropdown.Option("Curso", "📚 Curso / Capacitación"),
                    ft.dropdown.Option("Actividad", "⚡ Actividad / Tarea Obligatoria"),
                    ft.dropdown.Option("Urgente", "🔥 Urgente / Crítico")
                ],
                value="Aviso",
                border_color="#00FFFF",
                color="white"
            )
            
            default_lim = (get_now_mexico_city() + timedelta(days=7)).strftime("%d/%m/%Y")
            tf_fecha_lim = ft.TextField(
                label="Fecha Límite (DD/MM/AAAA)",
                value=default_lim,
                width=240,
                border_color="#00FFFF",
                color="white",
                dense=True,
                hint_text="DD/MM/AAAA"
            )
            
            def guardar_aviso_click(ev):
                if not tf_tit.value or not tf_tit.value.strip():
                    mostrar_snack("Por favor ingresa un título para el aviso", "orange")
                    return
                if not tf_desc.value or not tf_desc.value.strip():
                    mostrar_snack("Por favor ingresa una descripción o instrucciones", "orange")
                    return
                    
                db_g = db_fn()
                if db_g:
                    try:
                        f_lim_date = None
                        if tf_fecha_lim.value and tf_fecha_lim.value.strip():
                            val_raw = tf_fecha_lim.value.strip()
                            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"]:
                                try:
                                    parsed = datetime.strptime(val_raw, fmt)
                                    f_lim_date = parsed.strftime("%Y-%m-%d")
                                    break
                                except Exception:
                                    pass
                        
                        cur_g = db_g.cursor()
                        cur_g.execute("""
                            INSERT INTO parroquiales_avisos 
                                (zona_id, titulo, descripcion, url_enlace, tipo, fecha_limite, creado_por, usuario_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            zona_activa[0],
                            tf_tit.value.strip(),
                            tf_desc.value.strip(),
                            tf_url.value.strip() if tf_url.value else "",
                            dd_tipo.value,
                            f_lim_date,
                            nombre_usuario,
                            usuario_id
                        ))
                        db_g.commit()
                        
                        # Generar notificación en la campanita
                        enviar_notificacion_campana(
                            db_g, 
                            f"📢 Parroquial: {tf_tit.value.strip()}", 
                            f"Nuevo aviso de {dd_tipo.value} publicado por {nombre_usuario}.",
                            tipo="parroquial",
                            zona_id=zona_activa[0]
                        )
                        
                        db_g.close()
                        page.pop_dialog()
                        mostrar_snack("✅ ¡Aviso Parroquial publicado exitosamente!", "#7CFC00")
                        if actualizar_campana_fn:
                            actualizar_campana_fn()
                        recargar_vista()
                    except Exception as ex_sv:
                        print("Error guardando aviso:", ex_sv)
                        mostrar_snack("Error de base de datos al publicar aviso", "red")
                else:
                    mostrar_snack("Error de conexión con la base de datos", "red")
            
            d_width = min(page.width - 30, 480) if (page and page.width and page.width > 0) else 460
            d_height = min(page.height - 120, 480) if (page and page.height and page.height > 0) else 400
            
            dlg = ft.AlertDialog(
                title=ft.Text("📢 Publicar Aviso Parroquial", color="#00FFFF", weight="bold"),
                content=ft.Container(
                    content=ft.Column([
                        tf_tit,
                        dd_tipo,
                        tf_desc,
                        tf_url,
                        tf_fecha_lim
                    ], spacing=12, scroll=ft.ScrollMode.AUTO),
                    width=d_width,
                    height=d_height
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
                    ft.ElevatedButton("🚀 Publicar", bgcolor="#7CFC00", color="#05070D", on_click=guardar_aviso_click)
                ],
                actions_alignment="end",
                bgcolor="#10101C"
            )
            page.show_dialog(dlg)

        btn_nuevo = ft.ElevatedButton(
            "➕ Publicar Aviso",
            icon=ft.Icons.CAMPAIGN_ROUNDED,
            bgcolor="#7CFC00",
            color="#05070D",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(weight="bold")),
            on_click=abrir_dialog_nuevo_aviso,
            visible=puede_publicar
        )

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("📢 AVISOS PARROQUIALES Y CURSOS", size=16 if is_mobile else 20, color="#00FFFF", weight="bold"),
                    ft.Text("Comunicados oficiales, enlaces a cursos de capacitación y tareas prioritarias.", color="#888888", size=11 if is_mobile else 12)
                ], expand=True),
                btn_nuevo
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=10, color="#333333"),
            *avisos_cards
        ], expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)

    # -------------------------------------------------------------
    # 2. PESTAÑA: MINUTAS DE JUNTA SEMANAL
    # -------------------------------------------------------------
    def build_minutas_tab():
        is_mobile = (page.width < 700) if (page and page.width) else False
        db = db_fn()
        puede_redactar = False
        minutas = []
        
        now_dt = get_now_mexico_city()
        cal_sem = now_dt.isocalendar()
        sem_actual = cal_sem[1]
        anio_actual = cal_sem[0]
        
        if db:
            puede_redactar = usuario_tiene_permiso_redactor(db, usuario_id, rol_usuario, zona_activa[0])
            try:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM minutas_zonales 
                    WHERE zona_id = %s 
                    ORDER BY anio DESC, numero_semana DESC, id DESC LIMIT 30
                """, (zona_activa[0],))
                minutas = cursor.fetchall()
                cursor.close()
            except Exception as ex:
                print("Error cargando minutas:", ex)
            db.close()
            
        minutas_cards = []
        if not minutas:
            minutas_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("📝", size=36, text_align="center"),
                        ft.Text("No hay minutas de junta registradas para esta zona.", color="#aaaaaa", size=14, text_align="center", italic=True),
                        ft.Text("Las minutas de las juntas semanales quedarán archivadas aquí con sus acuerdos y compromisos para que nunca se pierdan.", color="#777777", size=12, text_align="center")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=30,
                    bgcolor="#10101C",
                    border_radius=12,
                    border=ft.Border.all(1, "#222233"),
                    alignment=ft.alignment.Alignment(0, 0)
                )
            )
        else:
            for m in minutas:
                sem = m.get("numero_semana") or 1
                anio = m.get("anio") or anio_actual
                f_junta = m.get("fecha_junta")
                f_junta_str = f_junta.strftime("%d/%m/%Y") if f_junta else "Semanal"
                
                # Parsear compromisos
                compromisos_raw = m.get("acuerdos_compromisos") or ""
                comp_rows = []
                for line in compromisos_raw.split("\n"):
                    line = line.strip()
                    if line:
                        comp_rows.append(
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#7CFC00", size=14),
                                ft.Text(line, color="#dddddd", size=12, expand=True)
                            ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=6)
                        )
                
                foto_widget = None
                foto_rel = m.get("foto_minuta")
                if foto_rel and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), foto_rel)):
                    foto_widget = ft.Container(
                        content=ft.Image(
                            src="/" + foto_rel.lstrip("/"),
                            width=180,
                            height=120,
                            fit=ft.BoxFit.COVER,
                            border_radius=8
                        ),
                        bgcolor="#0A0A14",
                        border_radius=8,
                        padding=2,
                        border=ft.Border.all(1, "#00FFFF")
                    )

                def make_eliminar_minuta(m_id, m_tit):
                    def on_eliminar_m(ev):
                        def confirmar_delete_m(e_conf):
                            db_del = db_fn()
                            if db_del:
                                try:
                                    cur_d = db_del.cursor()
                                    cur_d.execute("DELETE FROM minutas_zonales WHERE id = %s", (m_id,))
                                    db_del.commit()
                                    db_del.close()
                                    page.pop_dialog()
                                    mostrar_snack("🗑️ Minuta de Junta eliminada correctamente", "#FF4500")
                                    recargar_vista()
                                except Exception as ex_d:
                                    print("Error eliminando minuta:", ex_d)
                                    mostrar_snack("Error al eliminar minuta", "red")
                        
                        dlg_conf_m = ft.AlertDialog(
                            title=ft.Text("🗑️ Eliminar Minuta de Junta", color="#FF4500", weight="bold"),
                            content=ft.Text(f"¿Estás seguro de que deseas eliminar la minuta '{m_tit}'?", color="white"),
                            actions=[
                                ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
                                ft.ElevatedButton("Eliminar", bgcolor="#FF4500", color="white", on_click=confirmar_delete_m)
                            ],
                            actions_alignment="end",
                            bgcolor="#10101C"
                        )
                        page.show_dialog(dlg_conf_m)
                    return on_eliminar_m

                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(f"SEMANA {sem} - {anio}", color="#00FFFF", size=11, weight="bold"),
                                bgcolor="#002B36",
                                padding=ft.padding.Padding(10, 4, 10, 4),
                                border_radius=6,
                                border=ft.Border.all(1, "#00FFFF")
                            ),
                            ft.Text(f"📅 Fecha de Junta: {f_junta_str}", color="#aaaaaa", size=11),
                            ft.Container(expand=True),
                            ft.Text(f"✍️ Redactó: {m.get('creado_por') or 'Gerente'}", color="#888888", size=11, italic=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                icon_color="#FF4500",
                                icon_size=18,
                                tooltip="Eliminar Minuta",
                                on_click=make_eliminar_minuta(m.get("id"), m.get("titulo") or f"Minuta Semana {sem}")
                            ) if (es_admin or m.get("usuario_id") == usuario_id) else ft.Container()
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
                        ft.Text(m.get("titulo") or f"Minuta Junta Semanal {sem}", color="white", size=16, weight="bold"),
                        ft.Divider(height=6, color="#222233"),
                        ft.Text("📌 TEMAS, PUNTOS Y ACUERDOS DE LA JUNTA:", color="#00FFFF", size=11, weight="bold"),
                        ft.Text(m.get("temas_tratados") or "Sin temas capturados.", color="#cccccc", size=13),
                        foto_widget if foto_widget else ft.Container()
                    ], spacing=8),
                    padding=16,
                    bgcolor="#141424",
                    border_radius=12,
                    border=ft.Border.all(1.2, "#2A2A3E"),
                    shadow=[ft.BoxShadow(color="#10000000", blur_radius=8, spread_radius=1)]
                )
                minutas_cards.append(card)

        def abrir_dialog_nueva_minuta(e):
            tf_sem = ft.TextField(label="Semana # *", value=str(sem_actual), keyboard_type=ft.KeyboardType.NUMBER, width=100, border_color="#00FFFF", color="white", dense=True)
            tf_tit = ft.TextField(label="Título de la Minuta *", value=f"Minuta Junta Zonal - Semana {sem_actual}", border_color="#00FFFF", color="white", dense=True)
            tf_temas = ft.TextField(
                label="Temas, Puntos y Acuerdos de la Junta *",
                border_color="#00FFFF",
                color="white",
                multiline=True,
                min_lines=10,
                max_lines=18,
                hint_text="Escribe aquí los temas tratados, puntos relevantes, acuerdos y notas de la junta..."
            )
            
            foto_path_holder = [None]
            foto_status_txt = ft.Text("📷 Sin foto adjunta", color="#888888", size=11, italic=True)
            
            def tomar_foto_minuta_click(ev):
                if seleccionar_archivo_async:
                    def on_foto_done(path):
                        if path and os.path.exists(path):
                            dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "minutas")
                            os.makedirs(dest_dir, exist_ok=True)
                            fname = f"minuta_z{zona_activa[0]}_s{tf_sem.value}_{get_now_mexico_city().strftime('%Y%m%d_%H%M%S')}.jpg"
                            dest_file = os.path.join(dest_dir, fname)
                            try:
                                with open(path, "rb") as fi, open(dest_file, "wb") as fo:
                                    fo.write(fi.read())
                                foto_path_holder[0] = f"uploads/minutas/{fname}"
                                foto_status_txt.value = f"✅ Foto adjuntada: {fname}"
                                foto_status_txt.color = "#7CFC00"
                                page.update()
                            except Exception as ex_f:
                                print("Error copiando foto minuta:", ex_f)
                    seleccionar_archivo_async("Adjuntar Foto de Notas o Minuta", "media", on_foto_done, captureMode=True)
                else:
                    mostrar_snack("Selector de foto no disponible", "orange")

            btn_foto = ft.ElevatedButton("📷 Tomar / Adjuntar Foto de Notas", bgcolor="#1E1E2E", color="#00FFFF", on_click=tomar_foto_minuta_click)

            def guardar_minuta_click(ev):
                if not tf_tit.value or not tf_tit.value.strip():
                    mostrar_snack("Por favor ingresa un título para la minuta", "orange")
                    return
                if not tf_temas.value or not tf_temas.value.strip():
                    mostrar_snack("Por favor ingresa los temas y acuerdos tratados", "orange")
                    return
                    
                db_m = db_fn()
                if db_m:
                    try:
                        s_num = int(tf_sem.value.strip()) if (tf_sem.value and tf_sem.value.strip().isdigit()) else sem_actual
                        cur_m = db_m.cursor()
                        cur_m.execute("""
                            INSERT INTO minutas_zonales 
                                (zona_id, numero_semana, anio, fecha_junta, titulo, asistentes, temas_tratados, acuerdos_compromisos, foto_minuta, creado_por, usuario_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            zona_activa[0],
                            s_num,
                            anio_actual,
                            now_dt.strftime("%Y-%m-%d"),
                            tf_tit.value.strip(),
                            "",
                            tf_temas.value.strip(),
                            "",
                            foto_path_holder[0] or "",
                            nombre_usuario,
                            usuario_id
                        ))
                        db_m.commit()
                        
                        # Notificar a la zona en la campanita
                        enviar_notificacion_campana(
                            db_m, 
                            f"📝 Minuta Junta Semana {s_num}", 
                            f"Minuta de la junta semanal publicada por {nombre_usuario}.",
                            tipo="minuta",
                            zona_id=zona_activa[0]
                        )
                        
                        db_m.close()
                        page.pop_dialog()
                        mostrar_snack("✅ ¡Minuta de Junta guardada y publicada exitosamente!", "#7CFC00")
                        if actualizar_campana_fn:
                            actualizar_campana_fn()
                        recargar_vista()
                    except Exception as ex_m:
                        print("Error guardando minuta:", ex_m)
                        mostrar_snack("Error de base de datos al guardar minuta", "red")
                else:
                    mostrar_snack("Error de conexión", "red")

            d_width_m = min(page.width - 30, 520) if (page and page.width and page.width > 0) else 480
            d_height_m = min(page.height - 120, 500) if (page and page.height and page.height > 0) else 460

            dlg_m = ft.AlertDialog(
                title=ft.Text("📝 Redactar Minuta de Junta Zonal", color="#00FFFF", weight="bold"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([tf_sem, ft.Container(expand=True), ft.Text(f"Año: {anio_actual}", color="#aaaaaa")]),
                        tf_tit,
                        tf_temas,
                        ft.Row([btn_foto, foto_status_txt], vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True)
                    ], spacing=12, scroll=ft.ScrollMode.AUTO),
                    width=d_width_m,
                    height=d_height_m
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
                    ft.ElevatedButton("💾 Publicar Minuta", bgcolor="#7CFC00", color="#05070D", on_click=guardar_minuta_click)
                ],
                actions_alignment="end",
                bgcolor="#10101C"
            )
            page.show_dialog(dlg_m)

        btn_nueva_minuta = ft.ElevatedButton(
            "✍️ Redactar / Subir Minuta",
            icon=ft.Icons.NOTE_ALT_ROUNDED,
            bgcolor="#00FFFF",
            color="#05070D",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(weight="bold")),
            on_click=abrir_dialog_nueva_minuta,
            visible=puede_redactar
        )

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("📝 MINUTAS DE JUNTAS ZONALES", size=18 if is_mobile else 20, color="#D8B4FE", weight="bold"),
                    ft.Text("Acuerdos, compromisos y bitácora oficial de cada junta semanal.", color="#888888", size=11 if is_mobile else 12)
                ], expand=True),
                btn_nueva_minuta
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=10, color="#333333"),
            *minutas_cards
        ], expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)

    # -------------------------------------------------------------
    # 3. PESTAÑA: GESTIÓN DE PERMISOS DE REDACTOR (SOLO ADMINS)
    # -------------------------------------------------------------
    def build_permisos_tab():
        is_mobile = (page.width < 700) if (page and page.width) else False
        if not es_admin:
            return ft.Container(
                content=ft.Text("🔒 Módulo exclusivo para Administradores y Jefes Zonales.", color="#FF4500", size=14, weight="bold"),
                padding=20
            )
            
        db = db_fn()
        usuarios_tienda = []
        permisos_map = {}
        if db:
            try:
                cur_u = db.cursor(dictionary=True)
                cur_u.execute("SELECT ID_Usuario, Nombre_Completo, Tienda, Zona, Usuario FROM usuarios WHERE Rol != 'Admin' ORDER BY Tienda ASC, Nombre_Completo ASC")
                usuarios_tienda = cur_u.fetchall()
                
                cur_u.execute("SELECT * FROM permisos_redaccion_minutas WHERE zona_id = %s", (zona_activa[0],))
                for row in cur_u.fetchall():
                    permisos_map[row["usuario_id"]] = (row["activo"] == 1)
                cur_u.close()
            except Exception as ex_p:
                print("Error cargando permisos:", ex_p)
            db.close()

        lista_gerentes = []
        for u in usuarios_tienda:
            uid = u["ID_Usuario"]
            esta_activo = permisos_map.get(uid, False)
            
            def make_toggle(target_uid):
                def on_toggle(ev):
                    val_activo = 1 if ev.control.value else 0
                    db_t = db_fn()
                    if db_t:
                        try:
                            cur_t = db_t.cursor()
                            cur_t.execute("""
                                INSERT INTO permisos_redaccion_minutas (usuario_id, zona_id, activo, asignado_por)
                                VALUES (%s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE activo = %s, asignado_por = %s
                            """, (target_uid, zona_activa[0], val_activo, nombre_usuario, val_activo, nombre_usuario))
                            db_t.commit()
                            db_t.close()
                            mostrar_snack(f"✅ Permisos actualizados para usuario ID {target_uid}", "#7CFC00")
                        except Exception as ex_t:
                            print("Error guardando toggle permiso:", ex_t)
                            mostrar_snack("Error al guardar permiso", "red")
                return on_toggle

            sw = ft.Switch(value=esta_activo, active_color="#7CFC00", on_change=make_toggle(uid))
            t_name = u.get("Tienda") or "Sin Tienda"
            
            lista_gerentes.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ROUNDED, color="#00FFFF", size=20),
                        ft.Column([
                            ft.Text(f"{u.get('Nombre_Completo')} ({u.get('Usuario')})", color="white", weight="bold", size=13),
                            ft.Text(f"Sucursal: {t_name} | Zona: {u.get('Zona') or zona_activa[0]}", color="#aaaaaa", size=11)
                        ], expand=True, spacing=2),
                        ft.Column([
                            ft.Text("Autorizado para Redactar", size=10, color="#7CFC00" if esta_activo else "#888888"),
                            sw
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=12,
                    bgcolor="#141424",
                    border_radius=8,
                    border=ft.Border.all(1, "#7CFC00" if esta_activo else "#222233")
                )
            )

        return ft.Column([
            ft.Text("🛡️ AUTORIZACIÓN DE REDACTORES DE MINUTA", size=18 if is_mobile else 20, color="#7CFC00", weight="bold"),
            ft.Text("Desbloquea al Gerente responsable para que pueda capturar y publicar la minuta de la junta de tu zona.", color="#888888", size=11 if is_mobile else 12),
            ft.Divider(height=10, color="#333333"),
            *(lista_gerentes if lista_gerentes else [ft.Text("No se encontraron usuarios de tienda.", color="#aaaaaa", italic=True)])
        ], expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)

    # -------------------------------------------------------------
    # HEADER Y NAVEGACIÓN ENTRE SUB-PESTAÑAS
    # -------------------------------------------------------------
    txt_p = ft.Text("Avisos Parroquiales", weight="bold", size=12, color="#00FFFF")
    txt_m = ft.Text("Minutas de Junta", weight="bold", size=12, color="#aaaaaa")
    txt_pm = ft.Text("Desbloquear Redactor", weight="bold", size=12, color="#aaaaaa")

    btn_tab_parroq = ft.Container(
        content=ft.Row([ft.Text("📢", size=14), txt_p], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#003344",
        border=ft.Border.all(1.2, "#00FFFF"),
        border_radius=8,
        padding=ft.padding.Padding(12, 7, 12, 7),
        ink=True,
        on_click=lambda e: cambiar_subtab("parroquiales")
    )
    
    btn_tab_minutas = ft.Container(
        content=ft.Row([ft.Text("📝", size=14), txt_m], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#141424",
        border=ft.Border.all(1.2, "#2A2A3E"),
        border_radius=8,
        padding=ft.padding.Padding(12, 7, 12, 7),
        ink=True,
        on_click=lambda e: cambiar_subtab("minutas")
    )
    
    btn_tab_permisos = ft.Container(
        content=ft.Row([ft.Text("🛡️", size=14), txt_pm], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#141424",
        border=ft.Border.all(1.2, "#2A2A3E"),
        border_radius=8,
        padding=ft.padding.Padding(12, 7, 12, 7),
        ink=True,
        on_click=lambda e: cambiar_subtab("permisos"),
        visible=es_admin
    )
    
    def recargar_vista():
        if tab_activa[0] == "parroquiales":
            btn_tab_parroq.bgcolor = "#003344"
            btn_tab_parroq.border = ft.Border.all(1.2, "#00FFFF")
            txt_p.color = "#00FFFF"
            
            btn_tab_minutas.bgcolor = "#141424"
            btn_tab_minutas.border = ft.Border.all(1.2, "#2A2A3E")
            txt_m.color = "#aaaaaa"
            
            btn_tab_permisos.bgcolor = "#141424"
            btn_tab_permisos.border = ft.Border.all(1.2, "#2A2A3E")
            txt_pm.color = "#aaaaaa"
            content_area.content = build_parroquiales_tab()
        elif tab_activa[0] == "minutas":
            btn_tab_parroq.bgcolor = "#141424"
            btn_tab_parroq.border = ft.Border.all(1.2, "#2A2A3E")
            txt_p.color = "#aaaaaa"
            
            btn_tab_minutas.bgcolor = "#251238"
            btn_tab_minutas.border = ft.Border.all(1.2, "#D8B4FE")
            txt_m.color = "#D8B4FE"
            
            btn_tab_permisos.bgcolor = "#141424"
            btn_tab_permisos.border = ft.Border.all(1.2, "#2A2A3E")
            txt_pm.color = "#aaaaaa"
            content_area.content = build_minutas_tab()
        elif tab_activa[0] == "permisos":
            btn_tab_parroq.bgcolor = "#141424"
            btn_tab_parroq.border = ft.Border.all(1.2, "#2A2A3E")
            txt_p.color = "#aaaaaa"
            
            btn_tab_minutas.bgcolor = "#141424"
            btn_tab_minutas.border = ft.Border.all(1.2, "#2A2A3E")
            txt_m.color = "#aaaaaa"
            
            btn_tab_permisos.bgcolor = "#143014"
            btn_tab_permisos.border = ft.Border.all(1.2, "#7CFC00")
            txt_pm.color = "#7CFC00"
            content_area.content = build_permisos_tab()
        try: page.update()
        except Exception: pass

    def cambiar_subtab(nueva_tab):
        tab_activa[0] = nueva_tab
        recargar_vista()

    recargar_vista()

    zona_nombres = {"1": "Zona Centro", "2": "Zona Norte", "3": "Zona Occidente", "4": "Zona Sur"}
    z_nom = zona_nombres.get(zona_activa[0], f"Zona {zona_activa[0]}")

    main_layout = ft.Column([
        ft.Row([
            ft.Row([
                ft.Text("📋", size=24),
                ft.Column([
                    ft.Text("PARROQUIALES Y MINUTAS ZONALES", size=16, weight="bold", color="white"),
                    ft.Text(f"📍 {z_nom} | Central de Comunicación y Juntas", size=11, color="#00FFFF")
                ], spacing=1)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                btn_tab_parroq,
                btn_tab_minutas,
                btn_tab_permisos
            ], spacing=8)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Divider(height=12, color="#333333"),
        content_area
    ], expand=True, spacing=10)

    return main_layout
