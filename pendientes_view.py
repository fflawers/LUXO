import flet as ft
import os
import json
from datetime import datetime, date, timedelta

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PENDIENTES_DIR = os.path.join(BASE_PATH, "uploads", "pendientes")

def asegurar_directorios():
    os.makedirs(PENDIENTES_DIR, exist_ok=True)

def get_state_file(user_id):
    asegurar_directorios()
    clean_uid = "".join(c for c in str(user_id) if c.isalnum() or c in ("-", "_"))
    return os.path.join(PENDIENTES_DIR, f"pendientes_{clean_uid}.json")

def crear_tablas_pendientes_if_not_exists(db):
    if not db:
        return False
    try:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pendientes_usuario (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                tienda_id INT DEFAULT 0,
                titulo VARCHAR(255) NOT NULL,
                descripcion TEXT,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_limite DATE NULL,
                estado VARCHAR(20) DEFAULT 'pendiente',
                fecha_concluido DATETIME NULL,
                notificado INT DEFAULT 0,
                INDEX idx_user_estado (user_id, estado),
                INDEX idx_fecha_limite (fecha_limite)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        db.commit()
        cursor.close()
        return True
    except Exception as ex:
        print("Notice crear_tablas_pendientes_if_not_exists:", ex)
        return False

# --- OPERACIONES DE DATOS (MYSQL CON FALLBACK A JSON) ---

def cargar_pendientes(user_id, conectar_db_fn=None):
    user_id_str = str(user_id)
    items = []
    loaded_from_db = False

    if conectar_db_fn:
        db = None
        try:
            db = conectar_db_fn()
            if db:
                crear_tablas_pendientes_if_not_exists(db)
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, user_id, tienda_id, titulo, descripcion, 
                           DATE_FORMAT(fecha_creacion, '%Y-%m-%d %H:%i:%s') as fecha_creacion,
                           DATE_FORMAT(fecha_limite, '%Y-%m-%d') as fecha_limite,
                           estado,
                           DATE_FORMAT(fecha_concluido, '%Y-%m-%d %H:%i:%s') as fecha_concluido,
                           notificado
                    FROM pendientes_usuario
                    WHERE user_id = %s
                    ORDER BY estado ASC, fecha_limite ASC, id DESC
                """, (user_id_str,))
                items = cursor.fetchall()
                loaded_from_db = True
                cursor.close()
        except Exception as ex:
            print("Notice cargar_pendientes DB:", ex)
        finally:
            if db:
                try: db.close()
                except Exception: pass

    if not loaded_from_db:
        sf = get_state_file(user_id_str)
        if os.path.exists(sf):
            try:
                with open(sf, "r", encoding="utf-8") as f:
                    items = json.load(f)
            except Exception as ex_json:
                print("Notice cargar_pendientes JSON:", ex_json)
                items = []

    # Sincronizar copia local siempre
    try:
        sf = get_state_file(user_id_str)
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception: pass

    return items

def guardar_pendiente_db(user_id, titulo, fecha_limite=None, tienda_id=0, conectar_db_fn=None):
    user_id_str = str(user_id)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    item_nuevo = {
        "id": int(datetime.now().timestamp() * 1000),
        "user_id": user_id_str,
        "tienda_id": tienda_id,
        "titulo": titulo.strip(),
        "descripcion": "",
        "fecha_creacion": now_str,
        "fecha_limite": fecha_limite if fecha_limite else None,
        "estado": "pendiente",
        "fecha_concluido": None,
        "notificado": 0
    }

    saved_db = False
    if conectar_db_fn:
        db = None
        try:
            db = conectar_db_fn()
            if db:
                crear_tablas_pendientes_if_not_exists(db)
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO pendientes_usuario (user_id, tienda_id, titulo, descripcion, fecha_limite, estado)
                    VALUES (%s, %s, %s, %s, %s, 'pendiente')
                """, (user_id_str, tienda_id, titulo.strip(), "", fecha_limite if fecha_limite else None))
                db.commit()
                item_nuevo["id"] = cursor.lastrowid
                cursor.close()
                saved_db = True
        except Exception as ex:
            print("Notice guardar_pendiente DB:", ex)
        finally:
            if db:
                try: db.close()
                except Exception: pass

    # Actualizar archivo JSON local
    try:
        sf = get_state_file(user_id_str)
        items = []
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                items = json.load(f)
        items.insert(0, item_nuevo)
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as ex_j:
        print("Notice guardar_pendiente JSON:", ex_j)

    return item_nuevo

def marcar_pendiente_concluido_db(item_id, user_id, conectar_db_fn=None):
    user_id_str = str(user_id)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if conectar_db_fn:
        db = None
        try:
            db = conectar_db_fn()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    UPDATE pendientes_usuario 
                    SET estado = 'concluido', fecha_concluido = %s
                    WHERE id = %s AND user_id = %s
                """, (now_str, item_id, user_id_str))
                db.commit()
                cursor.close()
        except Exception as ex:
            print("Notice marcar_concluido DB:", ex)
        finally:
            if db:
                try: db.close()
                except Exception: pass

    # Actualizar local JSON
    try:
        sf = get_state_file(user_id_str)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                items = json.load(f)
            for it in items:
                if str(it.get("id")) == str(item_id):
                    it["estado"] = "concluido"
                    it["fecha_concluido"] = now_str
                    break
            with open(sf, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as ex_j:
        print("Notice marcar_concluido JSON:", ex_j)

def reactivar_pendiente_db(item_id, user_id, conectar_db_fn=None):
    user_id_str = str(user_id)
    if conectar_db_fn:
        db = None
        try:
            db = conectar_db_fn()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    UPDATE pendientes_usuario 
                    SET estado = 'pendiente', fecha_concluido = NULL
                    WHERE id = %s AND user_id = %s
                """, (item_id, user_id_str))
                db.commit()
                cursor.close()
        except Exception as ex:
            print("Notice reactivar_pendiente DB:", ex)
        finally:
            if db:
                try: db.close()
                except Exception: pass

    try:
        sf = get_state_file(user_id_str)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                items = json.load(f)
            for it in items:
                if str(it.get("id")) == str(item_id):
                    it["estado"] = "pendiente"
                    it["fecha_concluido"] = None
                    break
            with open(sf, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as ex_j:
        print("Notice reactivar_pendiente JSON:", ex_j)

def eliminar_pendiente_db(item_id, user_id, conectar_db_fn=None):
    user_id_str = str(user_id)
    if conectar_db_fn:
        db = None
        try:
            db = conectar_db_fn()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    DELETE FROM pendientes_usuario 
                    WHERE id = %s AND user_id = %s
                """, (item_id, user_id_str))
                db.commit()
                cursor.close()
        except Exception as ex:
            print("Notice eliminar_pendiente DB:", ex)
        finally:
            if db:
                try: db.close()
                except Exception: pass

    try:
        sf = get_state_file(user_id_str)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                items = json.load(f)
            items = [it for it in items if str(it.get("id")) != str(item_id)]
            with open(sf, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as ex_j:
        print("Notice eliminar_pendiente JSON:", ex_j)

def eliminar_todos_concluidos_db(user_id, conectar_db_fn=None):
    user_id_str = str(user_id)
    if conectar_db_fn:
        db = None
        try:
            db = conectar_db_fn()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    DELETE FROM pendientes_usuario 
                    WHERE estado = 'concluido' AND user_id = %s
                """, (user_id_str,))
                db.commit()
                cursor.close()
        except Exception as ex:
            print("Notice eliminar_todos_concluidos DB:", ex)
        finally:
            if db:
                try: db.close()
                except Exception: pass

    try:
        sf = get_state_file(user_id_str)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                items = json.load(f)
            items = [it for it in items if it.get("estado") != "concluido"]
            with open(sf, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as ex_j:
        print("Notice eliminar_todos_concluidos JSON:", ex_j)

# --- VISTA PRINCIPAL FLET ---

def build_pendientes_view(page: ft.Page, user_info=None, conectar_db_fn=None, mostrar_snack_fn=None):
    if user_info is None:
        user_info = {}
    
    user_id = str(user_info.get("id") or user_info.get("usuario") or user_info.get("user") or "invitado")
    tienda_nombre = str(user_info.get("tienda") or user_info.get("nombre_tienda") or "General")
    try: tienda_id = int(user_info.get("tienda_id") or 0)
    except Exception: tienda_id = 0

    is_mobile = (page.width < 750) if (page and hasattr(page, 'width') and isinstance(page.width, (int, float))) else False

    def notify_user(msg, color="#10B981"):
        if mostrar_snack_fn:
            try: mostrar_snack_fn(msg, color=color)
            except Exception: pass
        elif page:
            try:
                snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except Exception: pass

    # Estado de la pestaña seleccionada ('pendientes' o 'concluidos')
    tab_activa = ["pendientes"]
    all_items = cargar_pendientes(user_id, conectar_db_fn)

    # Contenedores de interfaz
    lista_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    contador_pendientes_txt = ft.Text("0", color="#00FFFF", weight="bold", size=12)
    contador_concluidos_txt = ft.Text("0", color="#10B981", weight="bold", size=12)
    alerta_banner = ft.Container(visible=False)

    # Inputs de Creación
    tf_nuevo_pendiente = ft.TextField(
        hint_text="Escribe aquí un nuevo pendiente o tarea...",
        hint_style=ft.TextStyle(color="#6B7280"),
        bgcolor="#111827",
        border_color="#374151",
        focused_border_color="#00FFFF",
        color="white",
        text_size=13,
        expand=True,
        dense=True
    )

    hoy_str = date.today().strftime('%Y-%m-%d')
    tf_fecha_limite = ft.TextField(
        value=hoy_str,
        label="Fecha Límite (AAAA-MM-DD)",
        label_style=ft.TextStyle(color="#9CA3AF", size=11),
        bgcolor="#111827",
        border_color="#374151",
        focused_border_color="#00FFFF",
        color="white",
        text_size=12,
        width=170 if not is_mobile else None,
        expand=True if is_mobile else False,
        dense=True
    )

    # DatePicker nativo de Flet
    date_picker = ft.DatePicker(
        first_date=datetime(2025, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=lambda e: on_date_picked(e)
    )
    if date_picker not in page.overlay:
        page.overlay.append(date_picker)

    def on_date_picked(e):
        if date_picker.value:
            tf_fecha_limite.value = date_picker.value.strftime('%Y-%m-%d')
            tf_fecha_limite.update()

    def abrir_calendario(e):
        date_picker.open = True
        page.update()

    btn_calendario = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
        icon_color="#00FFFF",
        tooltip="Seleccionar fecha con calendario",
        on_click=abrir_calendario
    )

    def parse_fecha(fecha_str):
        if not fecha_str:
            return None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(str(fecha_str).strip(), fmt).date()
            except Exception:
                pass
        return None

    def verificar_notificaciones_fecha_limite(items):
        """Revisa si hay pendientes vencidos o que vencen hoy y activa la alerta visual personalizada."""
        hoy = date.today()
        vencidos = 0
        por_vencer_hoy = 0

        for it in items:
            if it.get("estado") == "pendiente" and it.get("fecha_limite"):
                f_lim = parse_fecha(it.get("fecha_limite"))
                if f_lim:
                    if f_lim < hoy:
                        vencidos += 1
                    elif f_lim == hoy:
                        por_vencer_hoy += 1

        if vencidos > 0 or por_vencer_hoy > 0:
            alerta_banner.visible = True
            msg_parts = []
            if vencidos > 0:
                msg_parts.append(f"{vencidos} pendiente(s) vencido(s)")
            if por_vencer_hoy > 0:
                msg_parts.append(f"{por_vencer_hoy} pendiente(s) que vencen HOY")
            
            alerta_banner.content = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED, color="#EF4444", size=22),
                    ft.Column([
                        ft.Text("🔔 RECORDATORIO DE FECHA LÍMITE:", color="#FCA5A5", weight="bold", size=12),
                        ft.Text(f"Tienes {', y '.join(msg_parts)}. Revisa tus tareas pendientes.", color="white", size=11)
                    ], spacing=2, expand=True)
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#7F1D1D",
                padding=10,
                border_radius=8,
                border=ft.Border.all(1.5, "#EF4444")
            )
        else:
            alerta_banner.visible = False

    def renderizar_lista():
        nonlocal all_items
        lista_container.controls.clear()
        hoy = date.today()

        pendientes_activos = [it for it in all_items if it.get("estado") == "pendiente"]
        concluidos = [it for it in all_items if it.get("estado") == "concluido"]

        contador_pendientes_txt.value = str(len(pendientes_activos))
        contador_concluidos_txt.value = str(len(concluidos))

        verificar_notificaciones_fecha_limite(all_items)

        items_a_mostrar = pendientes_activos if tab_activa[0] == "pendientes" else concluidos

        if not items_a_mostrar:
            msg_vacio = "¡Felicidades! No tienes pendientes activos por el momento. 🎉" if tab_activa[0] == "pendientes" else "No hay pendientes concluidos aún. Al marcar un pendiente como terminado aparecerá aquí."
            icon_vacio = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED if tab_activa[0] == "pendientes" else ft.Icons.INBOX_ROUNDED
            color_vacio = "#10B981" if tab_activa[0] == "pendientes" else "#6B7280"

            lista_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(icon_vacio, size=48, color=color_vacio),
                        ft.Text(msg_vacio, color="#9CA3AF", size=13, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=30,
                    alignment=ft.alignment.Alignment(0, 0)
                )
            )
        else:
            for item in items_a_mostrar:
                item_id = item.get("id")
                titulo = str(item.get("titulo") or "").strip()
                estado = item.get("estado", "pendiente")
                f_lim_str = item.get("fecha_limite")
                f_lim = parse_fecha(f_lim_str)
                f_concluido_str = item.get("fecha_concluido")

                # Badge de estado de fecha
                badge_fecha = None
                if estado == "pendiente":
                    if f_lim:
                        dias_dif = (f_lim - hoy).days
                        if dias_dif < 0:
                            # Vencido
                            badge_fecha = ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.WARNING_ROUNDED, color="#EF4444", size=14),
                                    ft.Text(f"🚨 Vencido ({abs(dias_dif)} d)", color="#EF4444", weight="bold", size=10)
                                ], spacing=3),
                                bgcolor="#371B1B",
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6,
                                border=ft.Border.all(1, "#EF4444")
                            )
                        elif dias_dif == 0:
                            # Vence hoy
                            badge_fecha = ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ALARM_ROUNDED, color="#F59E0B", size=14),
                                    ft.Text("⚠️ VENCE HOY", color="#F59E0B", weight="bold", size=10)
                                ], spacing=3),
                                bgcolor="#3E2E10",
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6,
                                border=ft.Border.all(1, "#F59E0B")
                            )
                        else:
                            # A tiempo
                            badge_fecha = ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.EVENT_ROUNDED, color="#00FFFF", size=14),
                                    ft.Text(f"📅 Vence: {f_lim.strftime('%d/%m/%Y')} ({dias_dif}d)", color="#00FFFF", size=10)
                                ], spacing=3),
                                bgcolor="#0F2942",
                                padding=ft.Padding(6, 2, 6, 2),
                                border_radius=6,
                                border=ft.Border.all(1, "#00FFFF")
                            )
                    else:
                        badge_fecha = ft.Container(
                            content=ft.Text("📅 Sin fecha límite", color="#9CA3AF", size=10),
                            bgcolor="#1F2937",
                            padding=ft.Padding(6, 2, 6, 2),
                            border_radius=6
                        )
                else:
                    # Concluido
                    fecha_c_txt = ""
                    if f_concluido_str:
                        try:
                            f_c_obj = datetime.strptime(f_concluido_str, '%Y-%m-%d %H:%M:%S')
                            fecha_c_txt = f" el {f_c_obj.strftime('%d/%m/%Y %H:%M')}"
                        except Exception:
                            fecha_c_txt = f" ({f_concluido_str})"
                    badge_fecha = ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#10B981", size=14),
                            ft.Text(f"Concluido{fecha_c_txt}", color="#10B981", weight="bold", size=10)
                        ], spacing=3),
                        bgcolor="#064E3B",
                        padding=ft.Padding(6, 2, 6, 2),
                        border_radius=6,
                        border=ft.Border.all(1, "#10B981")
                    )

                # Acciones por fila
                if estado == "pendiente":
                    def make_concluir_handler(it_id):
                        return lambda e: on_toggle_concluido(it_id)

                    chk_control = ft.Checkbox(
                        value=False,
                        tooltip="Marcar como concluido",
                        active_color="#10B981",
                        check_color="white",
                        on_change=make_concluir_handler(item_id)
                    )

                    btn_del_activo = ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_color="#EF4444",
                        icon_size=18,
                        tooltip="Eliminar pendiente",
                        on_click=lambda e, it_id=item_id: on_eliminar_individual(it_id)
                    )

                    row_content = ft.Container(
                        content=ft.Row([
                            chk_control,
                            ft.Column([
                                ft.Text(titulo, color="white", weight="bold", size=13),
                                ft.Row([badge_fecha], spacing=6)
                            ], spacing=3, expand=True),
                            btn_del_activo
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                        bgcolor="#111827",
                        padding=ft.Padding(10, 8, 10, 8),
                        border_radius=10,
                        border=ft.Border.all(1, "#374151")
                    )
                else:
                    # En lista de concluidos: botón borrar uno por uno y opción de reactivar
                    def make_reactivar_handler(it_id):
                        return lambda e: on_reactivar(it_id)

                    chk_concluido = ft.Checkbox(
                        value=True,
                        tooltip="Desmarcar para reactivar",
                        active_color="#10B981",
                        check_color="white",
                        on_change=make_reactivar_handler(item_id)
                    )

                    btn_borrar_uno = ft.IconButton(
                        icon=ft.Icons.DELETE_ROUNDED,
                        icon_color="#EF4444",
                        icon_size=18,
                        tooltip="Borrar este concluido",
                        on_click=lambda e, it_id=item_id: on_eliminar_individual(it_id)
                    )

                    row_content = ft.Container(
                        content=ft.Row([
                            chk_concluido,
                            ft.Column([
                                ft.Text(titulo, color="#9CA3AF", size=13, style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH)),
                                ft.Row([badge_fecha], spacing=6)
                            ], spacing=3, expand=True),
                            btn_borrar_uno
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                        bgcolor="#0D1520",
                        padding=ft.Padding(10, 8, 10, 8),
                        border_radius=10,
                        border=ft.Border.all(1, "#1E293B")
                    )

                lista_container.controls.append(row_content)

        try:
            page.update()
        except Exception: pass

    def on_agregar_click(e):
        txt = tf_nuevo_pendiente.value.strip() if tf_nuevo_pendiente.value else ""
        if not txt:
            notify_user("⚠️ Por favor escribe el título o descripción del pendiente.", color="#F59E0B")
            return
        f_lim = tf_fecha_limite.value.strip() if tf_fecha_limite.value else None
        if f_lim:
            f_valid = parse_fecha(f_lim)
            if not f_valid:
                notify_user("⚠️ Formato de fecha inválido. Usa AAAA-MM-DD o el selector de calendario.", color="#EF4444")
                return
            f_lim = f_valid.strftime('%Y-%m-%d')

        nuevo = guardar_pendiente_db(user_id, txt, f_lim, tienda_id, conectar_db_fn)
        all_items.insert(0, nuevo)
        tf_nuevo_pendiente.value = ""
        notify_user("✅ Pendiente agregado correctamente.", color="#10B981")
        renderizar_lista()

    tf_nuevo_pendiente.on_submit = on_agregar_click

    def on_toggle_concluido(item_id):
        marcar_pendiente_concluido_db(item_id, user_id, conectar_db_fn)
        for it in all_items:
            if str(it.get("id")) == str(item_id):
                it["estado"] = "concluido"
                it["fecha_concluido"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break
        notify_user("🎉 ¡Pendiente marcado como concluido!", color="#10B981")
        renderizar_lista()

    def on_reactivar(item_id):
        reactivar_pendiente_db(item_id, user_id, conectar_db_fn)
        for it in all_items:
            if str(it.get("id")) == str(item_id):
                it["estado"] = "pendiente"
                it["fecha_concluido"] = None
                break
        notify_user("🔄 Pendiente reactivado y movido a pendientes activos.", color="#00FFFF")
        renderizar_lista()

    def on_eliminar_individual(item_id):
        eliminar_pendiente_db(item_id, user_id, conectar_db_fn)
        nonlocal all_items
        all_items = [it for it in all_items if str(it.get("id")) != str(item_id)]
        notify_user("🗑️ Pendiente eliminado.", color="#EF4444")
        renderizar_lista()

    def on_borrar_todos_concluidos_click(e):
        concluidos = [it for it in all_items if it.get("estado") == "concluido"]
        if not concluidos:
            notify_user("No hay pendientes concluidos para borrar.", color="#6B7280")
            return

        def confirmar_borrado(ev):
            eliminar_todos_concluidos_db(user_id, conectar_db_fn)
            nonlocal all_items
            all_items = [it for it in all_items if it.get("estado") != "concluido"]
            dlg_conf.open = False
            page.update()
            notify_user("🗑️ Se han eliminado todos los pendientes concluidos.", color="#EF4444")
            renderizar_lista()

        def cancelar_borrado(ev):
            dlg_conf.open = False
            page.update()

        dlg_conf = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color="#EF4444", size=24),
                ft.Text("¿Borrar todos los concluidos?", color="white", weight="bold", size=16)
            ], spacing=8),
            content=ft.Text(f"Se eliminarán permanentemente {len(concluidos)} tarea(s) concluida(s). Esta acción no se puede deshacer.", color="#CCCCCC", size=12),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_borrado),
                ft.ElevatedButton("Sí, Borrar Todos", bgcolor="#EF4444", color="white", on_click=confirmar_borrado)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.overlay.append(dlg_conf)
        dlg_conf.open = True
        page.update()

    # Botones de Sub-Pestañas
    btn_tab_pendientes = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CHECKLIST_ROUNDED, color="#00FFFF", size=16),
            ft.Text("📌 Pendientes", weight="bold", color="white", size=13),
            ft.Container(content=contador_pendientes_txt, bgcolor="#1F2937", padding=ft.Padding(6, 2, 6, 2), border_radius=10)
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.Padding(14, 8, 14, 8),
        bgcolor="#00FFFF22",
        border=ft.Border.all(1.5, "#00FFFF"),
        border_radius=10,
        on_click=lambda e: cambiar_tab("pendientes")
    )

    btn_tab_concluidos = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.TASK_ALT_ROUNDED, color="#10B981", size=16),
            ft.Text("✅ Concluidos", weight="bold", color="#9CA3AF", size=13),
            ft.Container(content=contador_concluidos_txt, bgcolor="#1F2937", padding=ft.Padding(6, 2, 6, 2), border_radius=10)
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.Padding(14, 8, 14, 8),
        bgcolor="#111827",
        border=ft.Border.all(1.5, "#374151"),
        border_radius=10,
        on_click=lambda e: cambiar_tab("concluidos")
    )

    btn_borrar_todos = ft.ElevatedButton(
        "Borrar Todos los Concluidos",
        icon=ft.Icons.DELETE_SWEEP_ROUNDED,
        bgcolor="#EF4444",
        color="white",
        visible=False,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            text_style=ft.TextStyle(weight="bold", size=11)
        ),
        on_click=on_borrar_todos_concluidos_click
    )

    def cambiar_tab(nueva_tab):
        tab_activa[0] = nueva_tab
        if nueva_tab == "pendientes":
            btn_tab_pendientes.bgcolor = "#00FFFF22"
            btn_tab_pendientes.border = ft.Border.all(1.5, "#00FFFF")
            btn_tab_pendientes.content.controls[1].color = "white"

            btn_tab_concluidos.bgcolor = "#111827"
            btn_tab_concluidos.border = ft.Border.all(1.5, "#374151")
            btn_tab_concluidos.content.controls[1].color = "#9CA3AF"
            btn_borrar_todos.visible = False
        else:
            btn_tab_pendientes.bgcolor = "#111827"
            btn_tab_pendientes.border = ft.Border.all(1.5, "#374151")
            btn_tab_pendientes.content.controls[1].color = "#9CA3AF"

            btn_tab_concluidos.bgcolor = "#10B98122"
            btn_tab_concluidos.border = ft.Border.all(1.5, "#10B981")
            btn_tab_concluidos.content.controls[1].color = "white"
            btn_borrar_todos.visible = True

        renderizar_lista()

    # Formulario de Nuevo Pendiente
    btn_agregar = ft.ElevatedButton(
        "Agregar",
        icon=ft.Icons.ADD_TASK_ROUNDED,
        bgcolor="#00FFFF",
        color="#000000",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            text_style=ft.TextStyle(weight="bold", size=12)
        ),
        on_click=on_agregar_click
    )

    card_creacion = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color="#00FFFF", size=18),
                ft.Text("NUEVO PENDIENTE O TAREA", color="#00FFFF", weight="bold", size=12)
            ], spacing=6),
            ft.Divider(height=6, color="#374151"),
            ft.Row([
                tf_nuevo_pendiente,
                tf_fecha_limite,
                btn_calendario,
                btn_agregar
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER) if not is_mobile else ft.Column([
                tf_nuevo_pendiente,
                ft.Row([tf_fecha_limite, btn_calendario], spacing=4),
                btn_agregar
            ], spacing=8)
        ], spacing=8),
        bgcolor="#0B0E17",
        padding=12,
        border_radius=12,
        border=ft.Border.all(1.5, "#00FFFF")
    )

    # Encabezado General
    header_view = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.PLAYLIST_ADD_CHECK_ROUNDED, color="#000000", size=22),
                    bgcolor="#00FFFF",
                    width=38,
                    height=38,
                    border_radius=10,
                    alignment=ft.alignment.Alignment(0, 0)
                ),
                ft.Column([
                    ft.Text("MIS PENDIENTES Y TAREAS", color="white", weight="bold", size=16),
                    ft.Text(f"Gestión personal independiente para: {user_id} ({tienda_nombre})", color="#9CA3AF", size=11)
                ], spacing=1)
            ], spacing=10),
            ft.Container(expand=True),
            btn_borrar_todos
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(0, 0, 0, 8)
    )

    tabs_header_row = ft.Row([
        btn_tab_pendientes,
        btn_tab_concluidos
    ], spacing=10)

    # Render inicial
    renderizar_lista()

    return ft.Container(
        content=ft.Column([
            header_view,
            alerta_banner,
            card_creacion,
            ft.Container(height=4),
            tabs_header_row,
            ft.Divider(height=6, color="#374151"),
            lista_container
        ], spacing=10, expand=True),
        padding=14,
        expand=True
    )
