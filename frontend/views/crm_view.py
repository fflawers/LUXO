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

def _build_crm_view(
    BASE_PATH,
    chk,
    comp,
    compra,
    conectar_db,
    err_ocr,
    es_admin,
    f_in,
    f_name,
    f_out,
    f_path,
    ft_img,
    id_c,
    modelo_val,
    mostrar_snack,
    optimizar_imagen,
    page,
    parsed_data,
    path,
    procesar_ticket_con_gemini,
    seleccionar_archivo_async,
    tf,
    timedelta,
    upc_val,
    user_info
):
    """Vista principal del Módulo CRM & Garantías de 1 Año con Notificaciones al Mes 11."""
    
    # --- ASEGURAR COLUMNA EN BASE DE DATOS ---
    try:
        db_m = conectar_db()
        if db_m:
            cur_m = db_m.cursor()
            cur_m.execute("SHOW COLUMNS FROM crm_compras LIKE 'Ruta_Ticket'")
            if not cur_m.fetchone():
                cur_m.execute("ALTER TABLE crm_compras ADD COLUMN Ruta_Ticket VARCHAR(500) NULL AFTER Notas")
                db_m.commit()
            db_m.close()
    except Exception as ex_mig:
        print("Error verificando columna Ruta_Ticket:", ex_mig)
    
    is_mobile_w = (page.width < 700) if (page and page.width) else False
    ticket_img_path = {"val": None}
    img_preview_container = ft.Container(visible=False)
    
    tf_transaccion = ft.TextField(label="N° Transacción / Ticket", border_color="#9D50BB", color="white", text_size=12, width=280)
    tf_fecha_compra = ft.TextField(label="Fecha de Compra (AAAA-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"), border_color="#9D50BB", color="white", text_size=12, width=220)
    tf_nombre_cliente = ft.TextField(label="Nombre del Cliente", border_color="#9D50BB", color="white", text_size=12, width=300)
    tf_telefono_cliente = ft.TextField(label="Teléfono del Cliente (Manual)", border_color="#9D50BB", color="white", text_size=12, width=200)
    tf_nombre_vendedor = ft.TextField(label="Nombre del Vendedor (o Vendedores)", value=user_info.get("nombre", ""), border_color="#9D50BB", color="white", text_size=12, width=320)
    tf_precio = ft.TextField(label="Precio Total con IVA ($ MXN)", border_color="#7CFC00", color="#7CFC00", text_style=ft.TextStyle(weight="bold"), text_size=13, width=220)
    tf_notas = ft.TextField(label="Notas Adicionales (Descuentos, Promociones, Observaciones)", border_color="#9D50BB", color="white", text_size=12, multiline=True, min_lines=2, max_lines=4)
    
    items_rows_container = ft.Column(spacing=8)
    
    def recalcular_gran_total():
        total_sum = 0.0
        for row_container in items_rows_container.controls:
            try:
                row_controls = row_container.content.controls
                p_tf = row_controls[2]
                if p_tf and p_tf.value and p_tf.value.strip():
                    val = float(p_tf.value.replace("$", "").replace(",", "").strip())
                    total_sum += val
            except Exception:
                pass
        if total_sum > 0:
            tf_precio.value = f"{total_sum:,.2f}"
        try: page.update()
        except Exception: pass
    
    def agregar_fila_articulo(upc_val="", modelo_val="", precio_val=""):
        tf_item_upc = ft.TextField(
            label="UPC / Código de Lente",
            value=str(upc_val or ""),
            border_color="#9D50BB",
            color="white",
            text_size=12,
            width=200 if is_mobile_w else 240
        )
        tf_item_modelo = ft.TextField(
            label="Modelo (ej: VE4436U G81/87 57/18)",
            value=str(modelo_val or ""),
            border_color="#9D50BB",
            color="white",
            text_size=12,
            width=280 if is_mobile_w else 360
        )
        tf_item_precio = ft.TextField(
            label="Precio Artículo ($ MXN)",
            value=str(precio_val or ""),
            border_color="#00FFFF",
            color="#00FFFF",
            text_size=12,
            width=140 if is_mobile_w else 180,
            on_change=lambda e: recalcular_gran_total()
        )
    
        def eliminar_fila(e_del):
            if len(items_rows_container.controls) > 1:
                items_rows_container.controls.remove(row_item)
                recalcular_gran_total()
                try: page.update()
                except Exception: pass
            else:
                tf_item_upc.value = ""
                tf_item_modelo.value = ""
                tf_item_precio.value = ""
                recalcular_gran_total()
                try: page.update()
                except Exception: pass
    
        row_item = ft.Container(
            content=ft.Row([
                tf_item_upc,
                tf_item_modelo,
                tf_item_precio,
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINED,
                    icon_color="#FF4500",
                    tooltip="Quitar este artículo",
                    on_click=eliminar_fila
                )
            ], wrap=True, spacing=8, vertical_alignment="center"),
            bgcolor="#181828",
            padding=8,
            border_radius=8,
            border=ft.Border.all(1, "#9D50BB")
        )
        items_rows_container.controls.append(row_item)
        recalcular_gran_total()
        try: page.update()
        except Exception: pass
    
    # Inicializar con 1 fila por defecto
    agregar_fila_articulo()
    
    crm_history_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    crm_notif_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    notif_badge_text = ft.Text("0", color="#00FFFF", weight="bold", size=12)
    
    # --- FUNCIÓN DE LIMPIAR FORMULARIO ---
    def limpiar_form_crm():
        tf_transaccion.value = ""
        tf_fecha_compra.value = datetime.now().strftime("%Y-%m-%d")
        tf_nombre_cliente.value = ""
        tf_telefono_cliente.value = ""
        tf_nombre_vendedor.value = user_info.get("nombre", "")
        tf_precio.value = ""
        tf_notas.value = ""
        items_rows_container.controls.clear()
        agregar_fila_articulo()
        ticket_img_path["val"] = None
        img_preview_container.visible = False
        img_preview_container.content = None
        page.update()
    
    # --- GUARDAR VENTA EN CRM ---
    def guardar_compra_crm(e):
        upcs_list = []
        modelos_list = []
        for row_container in items_rows_container.controls:
            try:
                r_ctrls = row_container.content.controls
                u_val = (r_ctrls[0].value or "").strip()
                m_val = (r_ctrls[1].value or "").strip()
                if u_val:
                    upcs_list.append(u_val)
                if m_val:
                    modelos_list.append(m_val)
            except Exception: pass
    
        upc_final = ", ".join(upcs_list) if upcs_list else ""
        modelos_str = " | ".join(modelos_list) if modelos_list else ""
        notas_final = f"Modelos: {modelos_str}. {tf_notas.value.strip()}".strip() if modelos_str else tf_notas.value.strip()
    
        if not tf_transaccion.value.strip() or not tf_nombre_cliente.value.strip() or not upc_final or not tf_precio.value.strip():
            mostrar_snack("Por favor completa los campos obligatorios: Transacción, Cliente, al menos 1 UPC y Precio.", color="orange")
            return
    
        try:
            precio_val = float(tf_precio.value.replace("$", "").replace(",", "").strip())
        except Exception:
            mostrar_snack("El precio ingresado no es válido.", color="red")
            return
    
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO crm_compras (Transaccion, Fecha_Compra, Nombre_Cliente, Telefono_Cliente, Nombre_Vendedor, ID_Usuario, UPC, Precio_Con_IVA, Tienda, Estatus_Seguimiento, Notas, Ruta_Ticket)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pendiente', %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        Fecha_Compra=%s, Nombre_Cliente=%s, Telefono_Cliente=%s, Nombre_Vendedor=%s, UPC=%s, Precio_Con_IVA=%s, Notas=%s, Ruta_Ticket=%s
                """, (
                    tf_transaccion.value.strip(),
                    tf_fecha_compra.value.strip(),
                    tf_nombre_cliente.value.strip(),
                    tf_telefono_cliente.value.strip(),
                    tf_nombre_vendedor.value.strip(),
                    user_info["id"],
                    upc_final,
                    precio_val,
                    user_info.get("tienda", "Tienda Luxo"),
                    notas_final,
                    ticket_img_path["val"],
                    # Update values
                    tf_fecha_compra.value.strip(),
                    tf_nombre_cliente.value.strip(),
                    tf_telefono_cliente.value.strip(),
                    tf_nombre_vendedor.value.strip(),
                    upc_final,
                    precio_val,
                    notas_final,
                    ticket_img_path["val"]
                ))
                db.commit()
                db.close()
                mostrar_snack("✅ Venta y datos de garantía guardados correctamente en CRM.", color="green")
                limpiar_form_crm()
                cargar_historial_crm()
                cargar_notificaciones_crm()
        except Exception as ex:
            print("Error guardando CRM:", ex)
            mostrar_snack(f"Error al guardar venta: {ex}", color="red")
    
    # --- FILE PICKER Y CÁMARA PARA ESCÁNER DE TICKET POR IA (SOPORTE WEB/MÓVIL Y DESKTOP) ---
    def procesar_y_cargar_ticket(f_path, f_name):
        try:
            mostrar_snack(f"📷 Procesando imagen de ticket '{f_name}' con OCR IA...", color="#00FFFF")
            
            # 1. Guardar copia local permanente en uploads/tickets/
            dir_tickets = os.path.join(BASE_PATH, "uploads", "tickets")
            os.makedirs(dir_tickets, exist_ok=True)
            nom_seguro = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{re.sub(r'[^a-zA-Z0-9_.]', '_', f_name)}"
            ruta_destino = os.path.join(dir_tickets, nom_seguro)
            
            with open(f_path, "rb") as f_in:
                img_bytes = f_in.read()
                
            img_bytes = optimizar_imagen(img_bytes)
            
            with open(ruta_destino, "wb") as f_out:
                f_out.write(img_bytes)
                
            ticket_img_path["val"] = ruta_destino
            
            import base64
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            img_preview_container.content = ft.Container(
                content=ft.Column([
                    ft.Text("📸 Foto del Ticket Almacenado:", color="#00FFFF", size=11, weight="bold"),
                    ft.Image(src=f"data:image/jpeg;base64,{img_b64}", width=240, height=160, fit="contain")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#161922", padding=8, border_radius=8, border=ft.Border.all(1, "#00FFFF")
            )
            img_preview_container.visible = True
            try:
                page.update()
            except Exception: pass
            
            # 2. OCR con EasyOCR + Groq Llama-3.3-70b
            parsed_data, err_ocr = procesar_ticket_con_gemini(img_bytes)
            print("OCR RESULT PARSED:", parsed_data)
            print("OCR RESULT ERR:", err_ocr)
    
            if parsed_data:
                if parsed_data.get("transaccion"):
                    tf_transaccion.value = str(parsed_data["transaccion"])
                else:
                    tf_transaccion.value = f"TRX-{datetime.now().strftime('%M%S%f')[:6]}"
                    
                if parsed_data.get("fecha_compra"):
                    tf_fecha_compra.value = str(parsed_data["fecha_compra"])
                    
                if parsed_data.get("nombre_cliente"):
                    tf_nombre_cliente.value = str(parsed_data["nombre_cliente"])
                    
                if parsed_data.get("vendedor"):
                    tf_nombre_vendedor.value = str(parsed_data["vendedor"])
    
                if parsed_data.get("notas"):
                    tf_notas.value = str(parsed_data["notas"])
                    
                # Limpiar filas y cargar artículos escaneados
                items_rows_container.controls.clear()
                items = parsed_data.get("items", [])
                if items and isinstance(items, list):
                    for it in items:
                        u_item = it.get("upc", "") if isinstance(it, dict) else ""
                        m_item = it.get("modelo", "") if isinstance(it, dict) else ""
                        p_item = it.get("precio", "") if isinstance(it, dict) else ""
                        agregar_fila_articulo(u_item, m_item, p_item)
                else:
                    u_single = parsed_data.get("upc", "")
                    p_single = parsed_data.get("precio", "")
                    agregar_fila_articulo(u_single, "", p_single)
    
                if parsed_data.get("precio") and not tf_precio.value:
                    tf_precio.value = str(parsed_data["precio"])
                    
                mostrar_snack("✅ ¡Ticket escaneado con éxito! Ingresa el teléfono del cliente.", color="green")
            else:
                if not tf_transaccion.value:
                    tf_transaccion.value = f"TRX-{datetime.now().strftime('%M%S%f')[:6]}"
                mostrar_snack(f"⚠️ Foto guardada. {err_ocr or 'No se leyeron datos automáticos, llena los campos manualmente.'}", color="orange")
            
            try:
                page.update()
            except Exception: pass
        except Exception as ex_proc:
            print("Error procesando foto ticket:", ex_proc)
            mostrar_snack(f"Error al procesar ticket: {ex_proc}", color="red")
    
    # --- ESCÁNER DE TICKET POR IA ---
    def escanear_ticket_click(e):
        def on_ticket_selected(path):
            if path and os.path.exists(path):
                procesar_y_cargar_ticket(path, os.path.basename(path))
    
        seleccionar_archivo_async("Tomar Foto o Seleccionar Ticket", "media", on_ticket_selected, captureMode=True)
    
    # --- VISUALIZADOR DE TICKET DE COMPRA Y DETALLES EN MODAL ---
    def mostrar_detalle_notificacion(compra):
        fecha_c = compra["Fecha_Compra"]
        if isinstance(fecha_c, str):
            try:
                dt_c = datetime.strptime(fecha_c, "%Y-%m-%d")
            except Exception:
                dt_c = datetime.now()
        else:
            dt_c = fecha_c
    
        dt_venc = dt_c + timedelta(days=365)
        fecha_venc_str = dt_venc.strftime("%d/%m/%Y")
        fecha_compra_str = dt_c.strftime("%d/%m/%Y")
    
        # Cargar vista de imagen de ticket físico si existe
        img_ticket_modal = None
        ruta_t = compra.get("Ruta_Ticket")
        if ruta_t and os.path.exists(ruta_t):
            try:
                with open(ruta_t, "rb") as ft_img:
                    import base64
                    b64_t = base64.b64encode(ft_img.read()).decode("utf-8")
                    img_ticket_modal = ft.Container(
                        content=ft.Column([
                            ft.Text("📸 COMPROBANTE / TICKET FÍSICO ESCANEADO:", color="#00FFFF", weight="bold", size=11),
                            ft.Image(src=f"data:image/jpeg;base64,{b64_t}", width=400, height=220, fit="contain")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#161922", padding=10, border_radius=8, border=ft.Border.all(1, "#333333")
                    )
            except Exception as ex_t:
                print("Error cargando imagen ticket modal:", ex_t)
    
        ticket_column_items = [
            # Encabezado del Ticket
            ft.Column([
                ft.Text("🕶️ SUNGLASS HUT MEXICO 🕶️", color="#00FFFF", weight="bold", size=16, text_align=ft.TextAlign.CENTER),
                ft.Text("STORE #4052 - PLAZA SATÉLITE", color="#aaaaaa", size=11, text_align=ft.TextAlign.CENTER),
                ft.Text("TICKET DE COMPRA Y GARANTÍA DIGITAL", color="#D8B4FE", weight="bold", size=12, text_align=ft.TextAlign.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            ft.Divider(height=12, color="#00FFFF"),
            
            # Datos de Transacción
            ft.Row([ft.Text("N° TRANSACCIÓN:", color="#aaaaaa", size=11, width=150), ft.Text(compra['Transaccion'], color="white", weight="bold", size=12)]),
            ft.Row([ft.Text("FECHA DE EMISIÓN:", color="#aaaaaa", size=11, width=150), ft.Text(fecha_compra_str, color="white", size=12)]),
            ft.Row([ft.Text("VENDEDOR ATENDIÓ:", color="#aaaaaa", size=11, width=150), ft.Text(compra['Nombre_Vendedor'] or "Atención Luxo", color="white", size=12)]),
            ft.Row([ft.Text("TIENDA DE ORIGEN:", color="#aaaaaa", size=11, width=150), ft.Text(compra['Tienda'] or "Sunglass Hut", color="white", size=12)]),
            ft.Divider(height=8, color="#333333"),
            
            # Datos del Cliente
            ft.Text("👤 DATOS DEL CLIENTE:", color="#00FFFF", weight="bold", size=12),
            ft.Row([ft.Text("Nombre del Cliente:", color="#aaaaaa", size=11, width=150), ft.Text(compra['Nombre_Cliente'], color="white", weight="bold", size=12)]),
            ft.Row([ft.Text("Teléfono de Contacto:", color="#aaaaaa", size=11, width=150), ft.Text(compra['Telefono_Cliente'] or "Sin Teléfono", color="#7CFC00", weight="bold", size=12)]),
            ft.Divider(height=8, color="#333333"),
            
            # Detalle de Producto
            ft.Text("🛍️ DETALLE DEL LENTE ADQUIRIDO:", color="#D8B4FE", weight="bold", size=12),
            ft.Row([ft.Text("UPC / Código Lente:", color="#aaaaaa", size=11, width=150), ft.Text(compra['UPC'], color="white", weight="bold", size=12)]),
            ft.Row([ft.Text("Precio Con IVA:", color="#aaaaaa", size=11, width=150), ft.Text(f"${compra['Precio_Con_IVA']:,.2f} MXN", color="#7CFC00", weight="bold", size=13)]),
            ft.Row([ft.Text("Notas / Modelo:", color="#aaaaaa", size=11, width=150), ft.Text(compra.get('Notas') or "Ray-Ban / Oakley", color="#E2E8F0", size=11)]),
            ft.Divider(height=8, color="#333333"),
        ]
    
        if img_ticket_modal:
            ticket_column_items.extend([img_ticket_modal, ft.Divider(height=8, color="#333333")])
    
        ticket_column_items.extend([
            # Coberturas de Garantía LUXO
            ft.Container(
                content=ft.Column([
                    ft.Text("📜 COBERTURAS DE GARANTÍA LUXO (1 AÑO):", color="#FFD700", weight="bold", size=11),
                    ft.Text(f"• Garantía por Ruptura / Daño: VIGENTE HASTA EL {fecha_venc_str}", color="#7CFC00", size=11),
                    ft.Text("• Garantía por Robo: 50% descuento en pieza de menor valor presentando Acta de Denuncia en tienda.", color="white", size=11)
                ], spacing=4),
                bgcolor="#1E2330",
                padding=10,
                border_radius=8,
                border=ft.Border.all(1, "#FFD700")
            ),
            ft.Divider(height=8, color="#333333"),
    
            # Estado de Asistencia
            ft.Row([
                ft.Text("Estatus en Tienda:", color="#aaaaaa", size=11, width=150),
                ft.Text("Asistió a Tienda 🏬" if compra.get("Cliente_Asistio") == 1 else "Pendiente de Visita", color="#7CFC00" if compra.get("Cliente_Asistio") == 1 else "#00FFFF", weight="bold", size=12)
            ]),
            ft.Row([
                ft.Text("Nueva Venta Generada:", color="#aaaaaa", size=11, width=150),
                ft.Text(f"${compra.get('Monto_Nueva_Venta') or 0:,.2f} MXN", color="#7CFC00", weight="bold", size=12)
            ]),
        ])
    
        ticket_content = ft.Container(
            width=460,
            bgcolor="#0D1117",
            padding=20,
            border_radius=12,
            border=ft.Border.all(2, "#00FFFF"),
            content=ft.Column(ticket_column_items, spacing=6, scroll=ft.ScrollMode.AUTO)
        )
    
        def cerrar_ticket(e):
            try:
                page.close(dialog)
            except Exception:
                pass
            dialog.open = False
            page.update()
    
        dialog = ft.AlertDialog(
            open=True,
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color="#00FFFF"),
                ft.Text("Ticket de Compra Digital 🧾", color="white", weight="bold", size=16)
            ]),
            content=ticket_content,
            actions=[
                ft.ElevatedButton("🖨️ Imprimir Ticket", bgcolor="#333333", color="#00FFFF", on_click=lambda e: mostrar_snack("🖨️ Enviando ticket a la impresora de tienda...", color="#00FFFF")),
                ft.ElevatedButton("Cerrar Ticket ❌", bgcolor="#FF4B4B", color="white", on_click=cerrar_ticket)
            ]
        )
    
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    # --- CARGAR NOTIFICACIONES AL MES 11 ---
    def cargar_notificaciones_crm():
        crm_notif_col.controls.clear()
        count_notif = 0
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT ID_Compra, Transaccion, Fecha_Compra, Nombre_Cliente, Telefono_Cliente, Nombre_Vendedor, UPC, Precio_Con_IVA, Tienda, Estatus_Seguimiento, Cliente_Asistio, Monto_Nueva_Venta, Notas, Ruta_Ticket, DATEDIFF(CURDATE(), Fecha_Compra) as dias_transcurridos
                    FROM crm_compras
                    WHERE (DATEDIFF(CURDATE(), Fecha_Compra) BETWEEN 330 AND 395 OR (DATEDIFF(CURDATE(), Fecha_Compra) >= 330 AND Estatus_Seguimiento = 'Pendiente'))
                    ORDER BY Fecha_Compra ASC
                """)
                rows = cursor.fetchall()
                db.close()
    
                if not rows:
                    crm_notif_col.controls.append(
                        ft.Container(
                            content=ft.Text("No hay notificaciones de garantías por cumplir 1 año pendientes por contactar.", color="#aaaaaa", italic=True),
                            padding=15
                        )
                    )
                else:
                    count_notif = len(rows)
                    for r in rows:
                        fecha_c = r["Fecha_Compra"]
                        dt_c = datetime.strptime(str(fecha_c), "%Y-%m-%d") if isinstance(fecha_c, str) else fecha_c
                        dt_venc = dt_c + timedelta(days=365)
                        fecha_venc_str = dt_venc.strftime("%d/%m/%Y")
    
                        is_contactado = r.get("Estatus_Seguimiento") in ("Contactado / Venta Realizada", "Venta Realizada")
    
                        crm_notif_col.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Container(
                                            content=ft.Text("⚠️ ALERTA MES 11 — ANIVERSARIO DE COMPRA", color="#000000", weight="bold", size=10),
                                            bgcolor="#FFD700" if not is_contactado else "#7CFC00",
                                            padding=ft.Padding(8, 3, 8, 3),
                                            border_radius=4
                                        ),
                                        ft.Text(f"Ticket: {r['Transaccion']}", color="white", weight="bold", size=12),
                                        ft.Text(f"Vence: {fecha_venc_str}", color="#FF8C00", weight="bold", size=12)
                                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Text(f"📢 Recomendación de Venta: El cliente {r['Nombre_Cliente']} ({r['Telefono_Cliente'] or 'Sin Teléfono'}) compró el lente UPC {r['UPC']} (${r['Precio_Con_IVA']:,.2f} MXN) y su garantía de 1 año vence el {fecha_venc_str}. Comunícate para recordarle sus coberturas de Ruptura y Robo (50% de descuento en la pieza de menor valor) e iniciar labor de venta.", color="#E2E8F0", size=12),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            "Ver Todos los Datos y Registrar Venta 📄",
                                            icon=ft.Icons.DESCRIPTION_ROUNDED,
                                            bgcolor="#333333",
                                            color="#00FFFF",
                                            on_click=lambda e, comp=r: mostrar_detalle_notificacion(comp)
                                        ),
                                        ft.Text(f"Venta Generada: ${r.get('Monto_Nueva_Venta') or 0:,.2f} MXN", color="#7CFC00", size=11, weight="bold")
                                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                                ], spacing=8),
                                bgcolor="#1A1A2E",
                                border=ft.Border.all(1, "#FFD700" if not is_contactado else "#7CFC00"),
                                padding=12,
                                border_radius=10
                            )
                        )
        except Exception as ex:
            print("Error notif crm:", ex)
        
        notif_badge_text.value = str(count_notif)
        page.update()
    
    # --- CARGAR HISTORIAL DE COMPRAS CRM & BÚSQUEDA POR TELÉFONO ---
    tf_buscar_crm = ft.TextField(label="🔍 Buscar por Ticket, Cliente o UPC...", border_color="#9D50BB", color="white", text_size=12, width=280, on_change=lambda e: cargar_historial_crm())
    tf_buscar_telefono = ft.TextField(label="📱 Buscar por Teléfono...", prefix_icon=ft.Icons.PHONE, border_color="#00FFFF", color="white", text_size=12, width=240, on_change=lambda e: cargar_historial_crm())
    
    def cargar_historial_crm():
        crm_history_col.controls.clear()
        q_search = tf_buscar_crm.value.strip().lower() if tf_buscar_crm.value else ""
        q_tel = tf_buscar_telefono.value.strip().lower() if tf_buscar_telefono.value else ""
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT ID_Compra, Transaccion, Fecha_Compra, Nombre_Cliente, Telefono_Cliente, Nombre_Vendedor, UPC, Precio_Con_IVA, Tienda, Estatus_Seguimiento, Cliente_Asistio, Monto_Nueva_Venta, Notas, Ruta_Ticket, DATEDIFF(CURDATE(), Fecha_Compra) as dias
                    FROM crm_compras
                    ORDER BY Fecha_Compra DESC
                """)
                rows = cursor.fetchall()
                db.close()
    
                if q_search:
                    rows = [r for r in rows if q_search in r["Transaccion"].lower() or q_search in r["Nombre_Cliente"].lower() or q_search in (r["Telefono_Cliente"] or "").lower() or q_search in r["UPC"].lower()]
                if q_tel:
                    rows = [r for r in rows if q_tel in (r["Telefono_Cliente"] or "").lower()]
    
                if not rows:
                    crm_history_col.controls.append(ft.Text("No hay registros en el CRM.", color="#aaaaaa", italic=True))
                else:
                    for r in rows:
                        dias = r.get("dias") or 0
                        if dias >= 365:
                            tag_garantia = ft.Container(content=ft.Text("🔴 Garantía Vencida", color="white", size=10, weight="bold"), bgcolor="#DC2626", padding=4, border_radius=4)
                        elif dias >= 330:
                            tag_garantia = ft.Container(content=ft.Text("⚠️ Alerta Mes 11 (Vence Pronto)", color="black", size=10, weight="bold"), bgcolor="#FFD700", padding=4, border_radius=4)
                        else:
                            tag_garantia = ft.Container(content=ft.Text("🟢 Garantía Vigente (Ruptura/Robo)", color="black", size=10, weight="bold"), bgcolor="#7CFC00", padding=4, border_radius=4)
    
                        def del_crm(id_c=r["ID_Compra"]):
                            try:
                                db_d = conectar_db()
                                if db_d:
                                    cur_d = db_d.cursor()
                                    cur_d.execute("DELETE FROM crm_compras WHERE ID_Compra = %s", (id_c,))
                                    db_d.commit()
                                    db_d.close()
                                    mostrar_snack("Registro eliminado del CRM.", color="orange")
                                    cargar_historial_crm()
                                    cargar_notificaciones_crm()
                                    cargar_metricas_crm()
                            except Exception as ex:
                                print("Error delete CRM:", ex)
    
                        def guardar_asistencia_card(comp=r, chk=None, tf=None):
                            try:
                                asist = 1 if chk.value else 0
                                monto = 0.0
                                if tf.value.strip():
                                    try:
                                        monto = float(tf.value.replace("$", "").replace(",", "").strip())
                                    except Exception:
                                        mostrar_snack("Monto de venta inválido.", color="red")
                                        return
                                estatus = "Venta Realizada" if (asist and monto > 0) else ("Contactado / Asistió" if asist else "Contactado / Pendiente")
                                db = conectar_db()
                                if db:
                                    cur = db.cursor()
                                    cur.execute("""
                                        UPDATE crm_compras 
                                        SET Cliente_Asistio = %s, Monto_Nueva_Venta = %s, Estatus_Seguimiento = %s, Fecha_Asistencia = NOW()
                                        WHERE ID_Compra = %s
                                    """, (asist, monto, estatus, comp["ID_Compra"]))
                                    db.commit()
                                    db.close()
                                    mostrar_snack(f"✅ Asistencia y venta de ${monto:,.2f} MXN registradas para {comp['Nombre_Cliente']}.", color="green")
                                    cargar_historial_crm()
                                    cargar_notificaciones_crm()
                                    cargar_metricas_crm()
                            except Exception as ex:
                                print("Error guardando asistencia card:", ex)
    
                        chk_card_asistio = ft.Checkbox(label="Cliente Asistió 🏬", value=r.get("Cliente_Asistio") == 1)
                        tf_card_monto = ft.TextField(
                            label="Monto Nueva Venta ($ MXN)",
                            value=str(r.get("Monto_Nueva_Venta") or ""),
                            border_color="#7CFC00",
                            color="white",
                            text_size=11,
                            width=170
                        )
    
                        crm_history_col.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        tag_garantia,
                                        ft.Text(f"Ticket: {r['Transaccion']}", color="white", weight="bold", size=13),
                                        ft.Text(f"Fecha: {r['Fecha_Compra']}", color="#aaaaaa", size=11)
                                    ], spacing=8, wrap=True),
                                    ft.Text(f"Cliente: {r['Nombre_Cliente']}", color="#D8B4FE", size=12),
                                    ft.Text(f"Tel: {r['Telefono_Cliente'] or 'S/N'} | Vendedor: {r['Nombre_Vendedor']}", color="#aaaaaa", size=11),
                                    ft.Text(f"UPC: {r['UPC']} | Precio: ${r['Precio_Con_IVA']:,.2f} MXN", color="white", size=11),
                                    ft.Row([
                                        chk_card_asistio,
                                        tf_card_monto,
                                    ], spacing=10, wrap=True),
                                    ft.Row([
                                        ft.ElevatedButton("Guardar Venta 💰", bgcolor="#7CFC00", color="black", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)), on_click=lambda e, comp=r, chk=chk_card_asistio, tf=tf_card_monto: guardar_asistencia_card(comp, chk, tf)),
                                        ft.ElevatedButton("Ver Ticket 🧾", icon=ft.Icons.RECEIPT_LONG, bgcolor="#1E2330", color="#00FFFF", on_click=lambda e, comp=r: mostrar_detalle_notificacion(comp)),
                                        ft.IconButton(ft.Icons.DELETE, icon_color="#FF4B4B", tooltip="Eliminar (Admin)", visible=es_admin(), on_click=lambda e, id_c=r["ID_Compra"]: del_crm(id_c))
                                    ], spacing=8, wrap=True)
                                ], spacing=6),
                                bgcolor="#161922",
                                padding=12,
                                border_radius=8,
                                border=ft.Border.all(1, "#333333")
                            )
                        )
        except Exception as ex:
            print("Error historial CRM:", ex)
        page.update()
    
    # --- SUB-PESTAÑA DE MÉTRICAS Y RENTABILIDAD CRM 📊 ---
    crm_metrics_container = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def cargar_metricas_crm():
        crm_metrics_container.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_registros,
                        COUNT(CASE WHEN DATEDIFF(CURDATE(), Fecha_Compra) >= 330 THEN 1 END) as notificados_mes11,
                        COUNT(CASE WHEN Cliente_Asistio = 1 THEN 1 END) as asistieron_tienda,
                        COALESCE(SUM(Monto_Nueva_Venta), 0) as venta_total_crm,
                        COALESCE(AVG(CASE WHEN Cliente_Asistio = 1 AND Monto_Nueva_Venta > 0 THEN Monto_Nueva_Venta END), 0) as venta_promedio
                    FROM crm_compras
                """)
                row = cursor.fetchone()
                db.close()
    
                tot_reg = row["total_registros"] or 0
                notif_11 = row["notificados_mes11"] or 0
                asist = row["asistieron_tienda"] or 0
                venta_tot = float(row["venta_total_crm"] or 0)
                venta_prom = float(row["venta_promedio"] or 0)
    
                tasa_conversion = (asist / notif_11 * 100.0) if notif_11 > 0 else 0.0
    
                crm_metrics_container.controls.extend([
                    ft.Text("Métricas de Efectividad y Rentabilidad del CRM 📊", color="#FFD700", weight="bold", size=16),
                    ft.Text("Análisis en tiempo real de las ventas adicionales generadas por la campaña de recordatorio de garantías al mes 11.", color="#aaaaaa", size=12),
                    ft.Divider(height=10, color="#333333"),
                    # KPI CARDS
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("VENTA TOTAL GENERADA CRM", color="#aaaaaa", size=10, weight="bold"),
                                ft.Text(f"${venta_tot:,.2f} MXN", color="#7CFC00", size=20, weight="bold")
                            ]), bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#7CFC00"), expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("TASA DE CONVERSIÓN (% ASISTENCIA)", color="#aaaaaa", size=10, weight="bold"),
                                ft.Text(f"{tasa_conversion:.1f}%", color="#00FFFF", size=20, weight="bold")
                            ]), bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#00FFFF"), expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("VENTA PROMEDIO POR CLIENTE", color="#aaaaaa", size=10, weight="bold"),
                                ft.Text(f"${venta_prom:,.2f} MXN", color="#D8B4FE", size=20, weight="bold")
                            ]), bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#D8B4FE"), expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("CLIENTES QUE ASISTIERON", color="#aaaaaa", size=10, weight="bold"),
                                ft.Text(f"{asist} / {notif_11}", color="#FFD700", size=20, weight="bold")
                            ]), bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#FFD700"), expand=True
                        )
                    ]),
                    ft.Divider(height=10, color="#333333"),
                    ft.Text("GRÁFICA COMPARATIVA DE RENDIMIENTO DEL CRM:", color="#D8B4FE", weight="bold", size=14),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Clientes Notificados (Mes 11):", color="white", width=220),
                                ft.ProgressBar(value=1.0 if notif_11 > 0 else 0, color="#FFD700", bgcolor="#333333", expand=True),
                                ft.Text(f"{notif_11} Clientes", color="#FFD700", weight="bold", width=90)
                            ]),
                            ft.Row([
                                ft.Text("Clientes que Asistieron a Tienda:", color="white", width=220),
                                ft.ProgressBar(value=(asist / notif_11) if notif_11 > 0 else 0, color="#00FFFF", bgcolor="#333333", expand=True),
                                ft.Text(f"{asist} Clientes", color="#00FFFF", weight="bold", width=90)
                            ]),
                            ft.Row([
                                ft.Text("Ventas Concretadas ($):", color="white", width=220),
                                ft.ProgressBar(value=min(1.0, venta_tot / 20000.0) if venta_tot > 0 else 0, color="#7CFC00", bgcolor="#333333", expand=True),
                                ft.Text(f"${venta_tot:,.0f} MXN", color="#7CFC00", weight="bold", width=90)
                            ])
                        ], spacing=12),
                        bgcolor="#161922", padding=16, border_radius=10, border=ft.Border.all(1, "#333333")
                    )
                ])
        except Exception as ex:
            print("Error métricas crm:", ex)
        page.update()
    
    # --- SECCIÓN GUÍA DE REGLAS DE GARANTÍA ---
    guia_garantias_view = ft.Container(
        content=ft.Column([
            ft.Text("REGLAS Y COBERTURAS DE GARANTÍAS SUNGLASS HUT (1 AÑO) 📜", color="#FFD700", weight="bold", size=16),
            ft.Divider(height=10, color="#333333"),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.BUILD_ROUNDED, color="#00FFFF"), ft.Text("1. GARANTÍA POR RUPTURA / DAÑO (VIGENCIA 1 AÑO)", color="#00FFFF", weight="bold", size=14)]),
                    ft.Text("• Aplica cuando el cliente acude a la tienda con su gafa que sufrió alguna ruptura o daño accidental (sin importar el estado físico en el que se encuentre la pieza).", color="white", size=12),
                    ft.Text("• El cliente debe entregar la gafa en tienda.", color="white", size=12),
                    ft.Text("• SE APLICA EL 50% DE DESCUENTO SOBRE LA PIEZA DE MENOR VALOR (ya sea la pieza que entrega el cliente o la nueva gafa que se lleva).", color="#7CFC00", weight="bold", size=12)
                ], spacing=6),
                bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#00FFFF")
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.SECURITY_ROUNDED, color="#FF8C00"), ft.Text("2. GARANTÍA POR ROBO (VIGENCIA 1 AÑO)", color="#FF8C00", weight="bold", size=14)]),
                    ft.Text("• Aplica cuando al cliente le roban sus gafas dentro del primer año de compra.", color="white", size=12),
                    ft.Text("• El cliente debe presentar en tienda su ticket de compra y el ACTA DE DENUNCIA emitida por la autoridad competente con los datos del lente.", color="white", size=12),
                    ft.Text("• EL ACTA DE DENUNCIA IMPRESA DEBE QUEDAR FÍSICAMENTE ARCHIVADA EN LA TIENDA.", color="#FFD700", weight="bold", size=12),
                    ft.Text("• SE APLICA EL 50% DE DESCUENTO SOBRE LA PIEZA DE MISMO O MENOR VALOR.", color="#7CFC00", weight="bold", size=12)
                ], spacing=6),
                bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#FF8C00")
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.ALARM_ON_ROUNDED, color="#D8B4FE"), ft.Text("3. ESTRATEGIA DE FIDELIZACIÓN AL MES 11", color="#D8B4FE", weight="bold", size=14)]),
                    ft.Text("• LUXO genera alertas automáticas a los 11 meses de la compra (1 mes antes de vencer).", color="white", size=12),
                    ft.Text("• La tienda debe ponerse en contacto con el cliente para recordarle sus garantías de Ruptura y Robo antes de que venza su ticket y realizar labor de venta para ofrecerle las nuevas colecciones.", color="white", size=12)
                ], spacing=6),
                bgcolor="#1E2330", padding=14, border_radius=10, border=ft.Border.all(1, "#D8B4FE")
            )
        ], spacing=14, scroll=ft.ScrollMode.AUTO),
        expand=True
    )
    
    # --- TABS PRINCIPALES DEL CRM ---
    tab_captura = ft.Column([
        ft.Text("Capturar Nueva Venta / Ticket 📝", color="#D8B4FE", weight="bold", size=15),
        ft.Row([
            ft.ElevatedButton("📷 Escanear Ticket / Tomar Foto", icon=ft.Icons.CAMERA_ALT, bgcolor="#1f6f43", color="white", on_click=escanear_ticket_click),
            ft.Text("Ingresa los datos o toma foto directa del ticket con tu celular.", color="#aaaaaa", size=11)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        img_preview_container,
        ft.Divider(height=10, color="#333333"),
        ft.Row([tf_transaccion, tf_fecha_compra], wrap=True, spacing=10),
        ft.Row([tf_nombre_cliente, tf_telefono_cliente], wrap=True, spacing=10),
        ft.Row([tf_nombre_vendedor], wrap=True, spacing=10),
        ft.Divider(height=5, color="transparent"),
        ft.Text("🛍️ Productos / Artículos del Ticket (1 o más):", color="#00FFFF", weight="bold", size=13),
        items_rows_container,
        ft.Row([
            ft.ElevatedButton("➕ Agregar Otro Artículo", icon=ft.Icons.ADD_SHOPPING_CART, bgcolor="#333333", color="#00FFFF", on_click=lambda e: agregar_fila_articulo()),
            tf_precio
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        ft.Divider(height=5, color="transparent"),
        tf_notas,
        ft.Row([
            ft.ElevatedButton("Guardar Registro en CRM 💾", icon=ft.Icons.SAVE, bgcolor="#9D50BB", color="white", on_click=guardar_compra_crm),
            ft.OutlinedButton("Limpiar Campos 🔄", on_click=lambda e: limpiar_form_crm())
        ], alignment=ft.MainAxisAlignment.END, wrap=True, spacing=10)
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    
    tab_historial_crm = ft.Column([
        ft.Text("Historial de CRM y Garantías 📋", color="#D8B4FE", weight="bold", size=15),
        ft.Row([tf_buscar_crm, tf_buscar_telefono], wrap=True, spacing=10),
        crm_history_col
    ], expand=True, scroll=ft.ScrollMode.AUTO)
    
    tab_notificaciones = ft.Column([
        ft.Row([
            ft.Text("Notificaciones & Alertas Mes 11 (Fidelización) 🔔", color="#FFD700", weight="bold", size=15),
            ft.ElevatedButton("Actualizar Alertas 🔄", bgcolor="#333333", color="white", on_click=lambda e: cargar_notificaciones_crm())
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("A continuación se enlistan las compras que están por cumplir 1 año (al mes 11). Haz clic en 'Ver Todos los Datos y Registrar Venta' para iniciar la labor de venta y registrar la asistencia y nueva venta.", color="#aaaaaa", size=12),
        ft.Divider(height=10, color="#333333"),
        crm_notif_col
    ], expand=True)
    
    crm_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        length=5,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Captura y Registro 📝"),
                        ft.Tab(label="Historial CRM 📋"),
                        ft.Tab(label="Notificaciones (Mes 11) 🔔"),
                        ft.Tab(label="Métricas & ROI CRM 📊"),
                        ft.Tab(label="Reglas de Garantía 📜")
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        tab_captura,
                        tab_historial_crm,
                        tab_notificaciones,
                        crm_metrics_container,
                        guia_garantias_view
                    ]
                )
            ]
        )
    )
    
    cargar_historial_crm()
    cargar_notificaciones_crm()
    cargar_metricas_crm()
    
    return ft.Column([
        ft.Row([
            ft.Text("CRM Cobertura Oops 👓", size=24, color="#D8B4FE", weight="bold"),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color="#00FFFF", size=16),
                    notif_badge_text,
                    ft.Text("Alertas Pendientes", color="white", size=11, weight="bold")
                ]),
                bgcolor="#1E2330",
                padding=ft.Padding(10, 5, 10, 5),
                border_radius=8,
                border=ft.Border.all(1, "#00FFFF")
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("Gestión de clientes, escáner de tickets con IA, coberturas por Ruptura o Robo (1 año) y alertas automáticas al mes 11.", color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        crm_tabs
    ], expand=True)