import flet as ft
import os
import re
import json
from datetime import datetime, timedelta, time

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def conectar_db_local():
    import mysql.connector
    try:
        from main import DB_CONFIG
        return mysql.connector.connect(**DB_CONFIG)
    except Exception:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="los4valtierra",
            database="sgh_portal"
        )

def obtener_hora_limite_apertura():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_path, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("hora_limite_apertura", "10:00")
    except Exception:
        pass
    return "10:00"

def guardar_hora_limite_apertura(hora_str):
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_path, "config.json")
        config_data = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    config_data = json.load(f)
                except Exception:
                    pass
        config_data["hora_limite_apertura"] = hora_str
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print("Error al guardar hora limite:", e)
    return False

def obtener_tiendas_activas(db):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT Tienda FROM usuarios WHERE Usuario LIKE 'sgh%' AND Tienda IS NOT NULL AND Tienda != '' ORDER BY Tienda ASC")
        rows = cursor.fetchall()
        return [r["Tienda"].strip() for r in rows if r.get("Tienda")]
    except Exception as e:
        print("Error obteniendo tiendas activas:", e)
        return []

def crear_tabla_operacion_diaria_if_not_exists(db):
    if not db:
        return
    try:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operacion_diaria_tiendas (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                Numero_Tienda VARCHAR(100) NOT NULL,
                Fecha DATE NOT NULL,
                Hora_Apertura TIME NULL,
                Foto_Apertura VARCHAR(500) NULL,
                Estado_Apertura VARCHAR(50) NULL,
                Hora_Cierre TIME NULL,
                Venta_Con_Iva DECIMAL(12, 2) NULL,
                Piezas_Vendidas INT NULL,
                UNIQUE KEY unique_tienda_fecha (Numero_Tienda, Fecha)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        db.commit()
    except Exception as ex:
        print("Error asegurando tabla operacion_diaria_tiendas:", ex)

def actualizar_estrella_aperturas(page, star_icon_container, conectar_db_fn=None, abrir_modal=False):
    db = conectar_db_fn() if conectar_db_fn else conectar_db_local()
    if not db:
        return
        
    try:
        tiendas = obtener_tiendas_activas(db)
        if not tiendas:
            db.close()
            return
            
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT Numero_Tienda 
            FROM operacion_diaria_tiendas 
            WHERE Fecha = CURDATE() AND Hora_Apertura IS NOT NULL AND Hora_Apertura != ''
        """)
        rows_rep = cursor.fetchall()
        reportados = set(str(r["Numero_Tienda"]).strip() for r in rows_rep if r["Numero_Tienda"])
        db.close()
        
        limit_str = obtener_hora_limite_apertura()
        limit_time = datetime.strptime(limit_str, "%H:%M").time()
        now_time = datetime.now().time()
        
        total_tiendas = len(tiendas)
        total_reportadas = len(reportados)
        faltantes = [t for t in tiendas if t not in reportados]
        
        color = "#888888" 
        tooltip = f"Aperturas hoy: {total_reportadas} de {total_tiendas} reportadas"
        icon = ft.Icons.STAR_BORDER_ROUNDED
        
        if total_reportadas >= total_tiendas:
            color = "#FFD700"
            tooltip = "¡Todas las tiendas han reportado su apertura hoy! 🌟"
            icon = ft.Icons.STAR_ROUNDED
        elif now_time > limit_time:
            color = "#FF4500"
            tooltip = f"¡ALERTA: Faltan {len(faltantes)} aperturas por reportar! 🚨"
            icon = ft.Icons.STAR_ROUNDED
        else:
            color = "#888888"
            tooltip = f"Aperturas hoy: {total_reportadas}/{total_tiendas} reportadas (Límite: {limit_str})"
            icon = ft.Icons.STAR_BORDER_ROUNDED

        def on_star_click(e):
            def cerrar_modal(ev):
                page.pop_dialog()
                
            items_dialog = []
            
            items_dialog.append(
                ft.Row([
                    ft.Text(f"Tiendas reportadas: {total_reportadas} de {total_tiendas}", color="#00FFFF", weight="bold", size=13),
                    ft.Text(f"Hora límite: {limit_str}", color="#aaaaaa", size=12)
                ], alignment="spaceBetween")
            )
            
            if total_reportadas >= total_tiendas:
                items_dialog.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text("🌟 ¡Excelente! Todas las tiendas han reportado su apertura el día de hoy.", color="#7CFC00", weight="bold")
                        ], alignment="center"),
                        bgcolor="#0A290A",
                        padding=15,
                        border_radius=8,
                        border=ft.Border.all(1, "#7CFC00")
                    )
                )
            else:
                rows_faltantes = []
                for store_num in faltantes:
                    store_name = f"Tienda {store_num}"
                    rows_faltantes.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.STORE_ROUNDED, color="#FF4500", size=18),
                                ft.Text(store_name, color="white", weight="bold", size=13, expand=True),
                                ft.Container(
                                    content=ft.Text("SIN APERTURA", size=10, color="white", weight="bold"),
                                    bgcolor="#FF4500",
                                    padding=ft.padding.Padding(6, 2, 6, 2),
                                    border_radius=4
                                )
                            ], alignment="spaceBetween", vertical_alignment="center"),
                            bgcolor="#1F1424",
                            padding=10,
                            border_radius=6,
                            border=ft.Border.all(1, "#333333")
                        )
                    )
                
                items_dialog.append(
                    ft.Container(
                        content=ft.Column(rows_faltantes, spacing=6, scroll=ft.ScrollMode.AUTO),
                        height=280
                    )
                )

            dialog_star = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.STAR_ROUNDED, color=color, size=22),
                    ft.Text("Monitoreo de Aperturas de Tienda", color="white", weight="bold", size=16)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column(items_dialog, spacing=10, tight=True),
                    width=480,
                    padding=10
                ),
                actions=[
                    ft.TextButton("Entendido", on_click=cerrar_modal)
                ],
                actions_alignment="end",
                bgcolor="#0F0F1A"
            )
            page.show_dialog(dialog_star)

        btn_star = ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=18,
            tooltip=tooltip,
            on_click=on_star_click,
            style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=0)
        )
            
        star_icon_container.content = ft.Container(
            content=btn_star,
            width=32,
            height=32,
            alignment=ft.alignment.Alignment(0, 0)
        )
        if abrir_modal:
            on_star_click(None)
        else:
            page.update()
    except Exception as ex:
        print("Error actualizando estrella aperturas:", ex)

def verificar_alertas_apertura_incumplida(conectar_db_fn=None):
    limit_str = obtener_hora_limite_apertura()
    limit_time = datetime.strptime(limit_str, "%H:%M").time()
    now_time = datetime.now().time()
    
    if now_time <= limit_time:
        return
        
    db = conectar_db_fn() if conectar_db_fn else conectar_db_local()
    if not db:
        return
        
    try:
        tiendas = obtener_tiendas_activas(db)
        if not tiendas:
            db.close()
            return
            
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT Numero_Tienda FROM operacion_diaria_tiendas WHERE Fecha = CURRENT_DATE() AND Hora_Apertura IS NOT NULL")
        reportadas = [r["Numero_Tienda"] for r in cursor.fetchall()]
        
        faltantes = [t for t in tiendas if t not in reportadas]
        
        if faltantes:
            for t in faltantes:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM notificaciones 
                    WHERE Titulo = 'Falta Apertura' 
                      AND Mensaje LIKE %s 
                      AND DATE(Fecha_Hora) = CURRENT_DATE()
                """, (f"%{t}%",))
                if cursor.fetchone()["total"] == 0:
                    cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Rol = 'Admin'")
                    admins = cursor.fetchall()
                    for a in admins:
                        cursor.execute("""
                            INSERT INTO notificaciones (ID_Usuario, Titulo, Mensaje, Tipo) 
                            VALUES (%s, 'Falta Apertura', %s, 'sistema')
                        """, (a[0], f"Falta reporte de apertura de la tienda {t}"))
            db.commit()
        db.close()
    except Exception as ex:
        print("Error verificando alertas apertura:", ex)

def build_operacion_diaria_view(page, user_info, conectar_db_fn, mostrar_snack_fn, tr_fn, seleccionar_archivo_async):
    db_fn = conectar_db_fn or conectar_db_local
    mostrar_snack = mostrar_snack_fn
    tr = tr_fn
    
    tienda_usuario = (user_info.get("tienda") or "").strip()
    rol_usuario = user_info.get("rol")
    
    view_content = ft.Column(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)
    
    if not tienda_usuario or tienda_usuario == "":
        view_content.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ Sin Tienda Asignada", size=18, weight="bold", color="#FF4500"),
                    ft.Text("Tu usuario no tiene asignada una sucursal. Comunícate con el Administrador para poder reportar tu apertura o cierre diario.", color="#aaaaaa")
                ], spacing=10),
                padding=20,
                bgcolor="#1E1E2E",
                border_radius=10,
                border=ft.Border.all(1, "#FF4500")
            )
        )
        return view_content
    
    def procesar_registro_apertura(foto_rel_path):
        db = db_fn()
        if not db:
            mostrar_snack("Error de conexión a la base de datos", "red")
            return
            
        try:
            limit_str = obtener_hora_limite_apertura()
            limit_time = datetime.strptime(limit_str, "%H:%M").time()
            now_time = datetime.now().time()
            
            estado = "Puntual" if now_time <= limit_time else "Tarde"
            
            # Usar hora local de Python, no CURRENT_TIME() de MySQL (que puede ser UTC)
            now_dt = datetime.now()
            now_str = now_dt.strftime("%H:%M:%S")
            fecha_str = now_dt.strftime("%Y-%m-%d")
            
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO operacion_diaria_tiendas (Numero_Tienda, Fecha, Hora_Apertura, Foto_Apertura, Estado_Apertura)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    Hora_Apertura = IF(Hora_Apertura IS NULL, %s, Hora_Apertura),
                    Foto_Apertura = IF(Hora_Apertura IS NULL, %s, Foto_Apertura),
                    Estado_Apertura = IF(Hora_Apertura IS NULL, %s, Estado_Apertura)
            """, (tienda_usuario, fecha_str, now_str, foto_rel_path, estado, now_str, foto_rel_path, estado))
            db.commit()
            db.close()
            
            mostrar_snack(f"Apertura registrada con éxito ({estado})!", "#7CFC00")
            
            try:
                from main import star_icon_container
                actualizar_estrella_aperturas(page, star_icon_container, db_fn)
            except Exception:
                pass
                
            refrescar_vista_operacion()
        except Exception as ex:
            print("Error registrando apertura:", ex)
            mostrar_snack("Error al guardar registro en base de datos", "red")

    def tomar_foto_click(e):
        def on_foto_selected(path):
            print(f"[Daily Operations on_foto_selected] Received path: {path}")
            if not path or not os.path.exists(path):
                print("[Daily Operations on_foto_selected] Invalid file path received.")
                mostrar_snack("Error: No se recibió ninguna imagen.", "red")
                return
            
            try:
                # Validar que el archivo no esté vacío o dañado (al menos 100 bytes)
                f_size = os.path.getsize(path)
                if f_size < 100:
                    print(f"[Daily Operations on_foto_selected] File is empty or corrupt (size: {f_size} bytes).")
                    mostrar_snack("⚠️ La foto tomada está vacía o incompleta. Por favor tómala nuevamente.", "orange")
                    return

                dest_dir = os.path.join(BASE_PATH, "uploads", "aperturas")
                os.makedirs(dest_dir, exist_ok=True)
                t_num = str(user_info.get("tienda") or "tienda").replace(" ", "_")
                f_name = f"apertura_{t_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                dest_path = os.path.join(dest_dir, f_name)
                
                with open(path, "rb") as f_in:
                    raw_bytes = f_in.read()
                
                try:
                    from main import optimizar_imagen
                    opt_bytes = optimizar_imagen(raw_bytes)
                except Exception as ex_opt:
                    print("Notice optimizar_imagen apertura:", ex_opt)
                    opt_bytes = raw_bytes

                with open(dest_path, "wb") as f_out:
                    f_out.write(opt_bytes)

                print(f"[Daily Operations on_foto_selected] Foto guardada ({len(opt_bytes)} bytes): {dest_path}")
                procesar_registro_apertura(f"uploads/aperturas/{f_name}")
            except Exception as ex:
                print("Error guardando foto local de apertura:", ex)
                mostrar_snack("Error al guardar la foto de apertura", "red")

        seleccionar_archivo_async("Tomar Foto o Seleccionar Foto de Apertura", "media", on_foto_selected, captureMode=True)

    # Inputs Cierre
    venta_input = ft.TextField(
        label="Venta con IVA ($)",
        border_color="#00FFFF",
        color="white",
        keyboard_type=ft.KeyboardType.TEXT,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string=""),
        width=200
    )
    piezas_input = ft.TextField(
        label="Piezas vendidas (Pz)",
        border_color="#00FFFF",
        color="white",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=200
    )

    def guardar_cierre_click(e):
        v_val = venta_input.value.strip()
        p_val = piezas_input.value.strip()
        
        if not v_val or not p_val:
            mostrar_snack("Por favor completa ambos campos del cierre", "orange")
            return
            
        try:
            venta = float(v_val.replace("$", "").replace(",", ""))
            piezas = int(p_val)
        except ValueError:
            mostrar_snack("Valores ingresados no válidos", "red")
            return
            
        db = db_fn()
        if not db:
            mostrar_snack("Error de conexión", "red")
            return
            
        try:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO operacion_diaria_tiendas (Numero_Tienda, Fecha, Hora_Cierre, Venta_Con_Iva, Piezas_Vendidas)
                VALUES (%s, CURRENT_DATE(), CURRENT_TIME(), %s, %s)
                ON DUPLICATE KEY UPDATE 
                    Hora_Cierre = CURRENT_TIME(), 
                    Venta_Con_Iva = %s, 
                    Piezas_Vendidas = %s
            """, (tienda_usuario, venta, piezas, venta, piezas))
            db.commit()
            db.close()
            
            mostrar_snack("Cierre diario guardado exitosamente!", "#7CFC00")
            refrescar_vista_operacion()
        except Exception as ex:
            print("Error al guardar cierre:", ex)
            mostrar_snack("Error de base de datos al guardar cierre", "red")

    apertura_card = ft.Container(padding=15, bgcolor="#141424", border_radius=10, border=ft.Border.all(1, "#333333"))
    cierre_card = ft.Container(padding=15, bgcolor="#141424", border_radius=10, border=ft.Border.all(1, "#333333"))

    def refrescar_vista_operacion():
        apertura_card.content = ft.ProgressRing(width=20, height=20)
        cierre_card.content = ft.ProgressRing(width=20, height=20)
        page.update()
        
        db = db_fn()
        reg = None
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT * FROM operacion_diaria_tiendas WHERE TRIM(Numero_Tienda) = TRIM(%s) AND Fecha = CURRENT_DATE()", (tienda_usuario,))
                reg = cursor.fetchone()
                db.close()
            except Exception as ex:
                print("Error cargando estatus hoy:", ex)
                
        if reg and reg["Hora_Apertura"]:
            ap_time = (datetime.min + reg["Hora_Apertura"]).strftime("%I:%M %p")
            ap_estado = reg["Estado_Apertura"]
            badge_color = "#7CFC00" if ap_estado == "Puntual" else "#FF4500"
            
            apertura_card.content = ft.Column([
                ft.Row([
                    ft.Text("🔑 Reporte de Apertura", size=14, weight="bold", color="white"),
                    ft.Container(
                        content=ft.Text(ap_estado, size=11, color="white", weight="bold"),
                        bgcolor=badge_color,
                        padding=ft.padding.Padding(8, 2, 8, 2),
                        border_radius=4
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"Apertura registrada a las: {ap_time}", color="#aaaaaa"),
                ft.Container(
                    content=ft.Image(
                        src="/" + reg["Foto_Apertura"].lstrip("/") if reg["Foto_Apertura"] else None,
                        width=200, height=200, fit=ft.BoxFit.COVER, border_radius=8
                    ) if reg["Foto_Apertura"] else ft.Icon(ft.Icons.IMAGE, size=40, color="#aaaaaa"),
                    bgcolor="#222233",
                    border_radius=8,
                    padding=2
                )
            ], spacing=10)
        else:
            apertura_card.content = ft.Column([
                ft.Text("🔑 Reporte de Apertura", size=14, weight="bold", color="white"),
                ft.Text("Por favor captura y sube la foto de la fachada o vitrina de la tienda abierta.", color="#aaaaaa"),
                ft.ElevatedButton(
                    "📸 Tomar Foto y Abrir Tienda",
                    color="white",
                    bgcolor="#7CFC00",
                    icon=ft.Icons.CAMERA_ALT_ROUNDED,
                    on_click=tomar_foto_click
                )
            ], spacing=10)

        if reg and reg["Hora_Cierre"]:
            c_time = (datetime.min + reg["Hora_Cierre"]).strftime("%I:%M %p")
            cierre_card.content = ft.Column([
                ft.Text("💰 Reporte de Cierre", size=14, weight="bold", color="white"),
                ft.Text("El cierre de hoy ha sido enviado exitosamente.", color="#7CFC00", weight="bold"),
                ft.Row([
                    ft.Text("Venta con IVA:", color="#aaaaaa"),
                    ft.Text(f"${reg['Venta_Con_Iva']:,.2f}", color="white", weight="bold")
                ]),
                ft.Row([
                    ft.Text("Piezas Vendidas (Pz):", color="#aaaaaa"),
                    ft.Text(f"{reg['Piezas_Vendidas']} Pz", color="white", weight="bold")
                ]),
                ft.Text(f"Registrado a las: {c_time}", color="#888888", size=10)
            ], spacing=8)
        else:
            cierre_card.content = ft.Column([
                ft.Text("💰 Reporte de Cierre", size=14, weight="bold", color="white"),
                ft.Text("Registra el corte de caja e inventario final del día.", color="#aaaaaa"),
                venta_input,
                piezas_input,
                ft.ElevatedButton(
                    "💾 Reportar Cierre de Tienda",
                    color="white",
                    bgcolor="#00FFFF",
                    icon=ft.Icons.SAVE_ROUNDED,
                    on_click=guardar_cierre_click
                )
            ], spacing=10)
            
        page.update()

    refrescar_vista_operacion()
    
    dias_semana = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo"
    }
    ahora = datetime.now()
    dia_nombre = dias_semana[ahora.weekday()]
    hoy_str = f"{dia_nombre} {ahora.strftime('%d/%m/%Y')}"

    view_header = ft.Container(
        content=ft.Row([
            ft.Text(f"Operación de Sucursal - {tienda_usuario} ({hoy_str})", size=18, weight="bold", color="white"),
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: refrescar_vista_operacion(), icon_color="#00FFFF")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.Padding(0, 0, 0, 10),
        border=ft.Border(bottom=ft.BorderSide(1, "#333333"))
    )
    
    view_content.controls.extend([
        view_header,
        apertura_card,
        cierre_card
    ])
    
    return view_content

def build_aperturas_cierres_tab(page, user_info, conectar_db_fn, mostrar_snack_fn, tr_fn):
    db_fn = conectar_db_fn or conectar_db_local
    mostrar_snack = mostrar_snack_fn
    tr = tr_fn
    
    is_mobile_w = (page.width < 700) if (page and page.width) else False
    tab_container = ft.Column(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)
    
    limit_time_input = ft.TextField(
        label="Hora Límite de Apertura (HH:MM)",
        value=obtener_hora_limite_apertura(),
        width=180 if is_mobile_w else 220,
        text_size=12 if is_mobile_w else 14,
        color="white",
        border_color="#00FFFF"
    )
    
    def guardar_config_click(e):
        val = limit_time_input.value.strip()
        if not re.match(r"^\d{2}:\d{2}$", val):
            mostrar_snack("Formato de hora no válido. Use HH:MM (ej. 10:00)", "red")
            return
        if guardar_hora_limite_apertura(val):
            mostrar_snack("Hora límite configurada con éxito!", "#7CFC00")
            try:
                from main import star_icon_container
                actualizar_estrella_aperturas(page, star_icon_container, db_fn)
            except Exception:
                pass
        else:
            mostrar_snack("Error al guardar configuración", "red")
            
    config_row = ft.Row([
        limit_time_input,
        ft.ElevatedButton(
            "Guardar Hora",
            bgcolor="#9D50BB",
            color="white",
            on_click=guardar_config_click,
            icon=ft.Icons.SAVE
        )
    ], alignment=ft.MainAxisAlignment.START, vertical_alignment="center", spacing=10 if is_mobile_w else 15, wrap=True)
    
    hoy_date = datetime.now().date()
    fecha_consulta = [hoy_date]
    
    fecha_text = ft.Text(
        f"Operación: {hoy_date.strftime('%Y-%m-%d')}" if is_mobile_w else f"Mostrando operación para el día: {hoy_date.strftime('%Y-%m-%d')}",
        size=11 if is_mobile_w else 14,
        weight="bold",
        color="white"
    )
    
    tabla_container = ft.Container(expand=True)
    
    def refrescar_tabla():
        tabla_container.content = ft.ProgressRing(width=30, height=30)
        page.update()
        
        db = db_fn()
        tiendas = []
        registros = {}
        if db:
            try:
                crear_tabla_operacion_diaria_if_not_exists(db)
                tiendas = obtener_tiendas_activas(db)
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM operacion_diaria_tiendas 
                    WHERE Fecha = %s
                """, (fecha_consulta[0],))
                rows = cursor.fetchall()
                registros = {str(r["Numero_Tienda"]).strip(): r for r in rows}
                db.close()
            except Exception as ex:
                print("Error al refrescar tabla admin:", ex)
                
        if not tiendas:
            tabla_container.content = ft.Text("No hay tiendas activas registradas en la base de datos (Rol Gerente).", color="#aaaaaa")
            page.update()
            return
            
        rows_data = []
        for store in tiendas:
            reg = registros.get(store)
            
            if reg and reg["Hora_Apertura"]:
                ap_time = (datetime.min + reg["Hora_Apertura"]).strftime("%I:%M %p")
                ap_estado = reg["Estado_Apertura"]
                ap_color = "#7CFC00" if ap_estado == "Puntual" else "#FF4500"
                
                def make_foto_click(path_val, name_val):
                    def ver_foto_click(e):
                        def cerrar_dialog(ev):
                            page.pop_dialog()
                        fixed_path = "/" + path_val.lstrip("/") if path_val else None
                        dlg = ft.AlertDialog(
                            title=ft.Text(f"Foto de Apertura - {name_val}", color="#00FFFF", weight="bold"),
                            content=ft.Container(
                                content=ft.Image(src=fixed_path, fit=ft.BoxFit.CONTAIN),
                                width=600,
                                height=500
                            ),
                            actions=[ft.TextButton("Cerrar", on_click=cerrar_dialog)],
                            bgcolor="#0F0F1A"
                        )
                        page.show_dialog(dlg)
                    return ver_foto_click
                
                apert_cell = ft.Row([
                    ft.Text(ap_time, color="white", size=10 if is_mobile_w else 12),
                    ft.Container(
                        content=ft.Text(ap_estado, size=8 if is_mobile_w else 9, color="white", weight="bold"),
                        bgcolor=ap_color,
                        padding=ft.padding.Padding(4, 2, 4, 2) if is_mobile_w else ft.padding.Padding(6, 2, 6, 2),
                        border_radius=3
                    ),
                    ft.IconButton(
                        ft.Icons.REMOVE_RED_EYE_ROUNDED, 
                        icon_color="#00FFFF", 
                        icon_size=14 if is_mobile_w else 16, 
                        tooltip="Ver Foto de Apertura", 
                        on_click=make_foto_click(reg["Foto_Apertura"], store)
                    )
                ], spacing=4 if is_mobile_w else 6, wrap=True)
            else:
                apert_cell = ft.Text("SIN APERTURA", color="#FF4500", weight="bold", size=10 if is_mobile_w else 11)
                
            if reg and reg["Hora_Cierre"]:
                cl_time = (datetime.min + reg["Hora_Cierre"]).strftime("%I:%M %p")
                venta_str = f"${reg['Venta_Con_Iva']:,.2f}"
                piezas_str = f"{reg['Piezas_Vendidas']} Pz"
                
                cierre_cell = ft.Column([
                    ft.Text(f"Venta: {venta_str}", color="#7CFC00", weight="bold", size=10 if is_mobile_w else 12),
                    ft.Text(f"Pzs: {piezas_str}", color="white", size=9 if is_mobile_w else 11),
                    ft.Text(f"Cerró: {cl_time}", color="#888888", size=8 if is_mobile_w else 9)
                ], spacing=2)
            else:
                cierre_cell = ft.Text("SIN CIERRE", color="#aaaaaa", italic=True, size=10 if is_mobile_w else 11)
                
            rows_data.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(store, color="white", weight="bold", size=10 if is_mobile_w else 13)),
                        ft.DataCell(apert_cell),
                        ft.DataCell(cierre_cell)
                    ]
                )
            )
            
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Sucursal / Tienda", color="#00FFFF", weight="bold", size=10 if is_mobile_w else 13)),
                ft.DataColumn(ft.Text("Apertura", color="#00FFFF", weight="bold", size=10 if is_mobile_w else 13)),
                ft.DataColumn(ft.Text("Cierre", color="#00FFFF", weight="bold", size=10 if is_mobile_w else 13))
            ],
            rows=rows_data,
            border=ft.Border.all(1, "#333333"),
            border_radius=8,
            column_spacing=8 if is_mobile_w else 24,
            horizontal_margin=6 if is_mobile_w else 16,
            heading_row_color="#1E1E2E"
        )
        
        tabla_container.content = ft.Row([table], scroll=ft.ScrollMode.AUTO, expand=True)
        page.update()

    def cambiar_dia(offset_days):
        fecha_consulta[0] = fecha_consulta[0] + timedelta(days=offset_days)
        fecha_text.value = f"Operación: {fecha_consulta[0].strftime('%Y-%m-%d')}" if is_mobile_w else f"Mostrando operación para el día: {fecha_consulta[0].strftime('%Y-%m-%d')}"
        refrescar_tabla()

    def on_date_selected(e):
        if e.control.value:
            fecha_consulta[0] = e.control.value.date()
            fecha_text.value = f"Operación: {fecha_consulta[0].strftime('%Y-%m-%d')}" if is_mobile_w else f"Mostrando operación para el día: {fecha_consulta[0].strftime('%Y-%m-%d')}"
            refrescar_tabla()

    calendar_picker = ft.DatePicker(
        on_change=on_date_selected,
        first_date=datetime(2025, 1, 1),
        last_date=datetime(2030, 12, 31)
    )
    page.overlay.append(calendar_picker)

    def abrir_calendario(e):
        calendar_picker.open = True
        page.update()

    fecha_nav = ft.Row([
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_ROUNDED, on_click=lambda e: cambiar_dia(-1), icon_color="#00FFFF", icon_size=14 if is_mobile_w else 20),
            fecha_text,
            ft.IconButton(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, on_click=lambda e: cambiar_dia(1), icon_color="#00FFFF", icon_size=14 if is_mobile_w else 20),
        ], spacing=2 if is_mobile_w else 8, vertical_alignment="center"),
        ft.Row([
            ft.IconButton(
                ft.Icons.CALENDAR_MONTH_ROUNDED, 
                on_click=abrir_calendario, 
                icon_color="#D8B4FE",
                icon_size=16 if is_mobile_w else 20,
                tooltip="Seleccionar fecha"
            ),
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: refrescar_tabla(), icon_color="#00FFFF", icon_size=16 if is_mobile_w else 20)
        ], spacing=2 if is_mobile_w else 5)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment="center")

    tab_container.controls.extend([
        ft.Text("Configuración de Horarios", size=16, weight="bold", color="white"),
        config_row,
        ft.Divider(height=10, color="#333333"),
        fecha_nav,
        tabla_container
    ])
    
    refrescar_tabla()
    return tab_container
