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

def _build_checklists_view(
    API_URL,
    GROQ_API_KEY,
    URL_GROQ,
    cambiar_vista,
    categoria,
    completado_val,
    conectar_db,
    dashboard_tab_index,
    descripcion,
    es_admin,
    file_picker_vitrina,
    i_p,
    id_plantilla,
    image_file,
    mostrar_snack,
    p_bar,
    p_text,
    page,
    user_info
):
    apertura_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    cierre_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    venta_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    dropdown_vendedor_venta = ft.Dropdown(
        label="Asesor que realizó la Venta",
        border_color="#A100F2",
        color="white",
        width=300
    )
    
    def cargar_vendedores_dropdown_venta():
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT ID_Vendedor, Nombre_Completo FROM vendedores WHERE ID_Usuario_Tienda = %s AND Activo = 1 ORDER BY Nombre_Completo ASC", (user_info["id"],))
                rows = cursor.fetchall()
                db.close()
                dropdown_vendedor_venta.options = [ft.dropdown.Option(str(r["ID_Vendedor"]), r["Nombre_Completo"]) for r in rows]
        except Exception as ex:
            print("Error cargar dropdown venta exitosa:", ex)
    
    cargar_vendedores_dropdown_venta()
    
    # file_picker_vitrina is initialized globally and appended in cargar_chat
    
    def en_archivo_seleccionado_vitrina(e):
        if not e.files:
            return
        filepath = e.files[0].path
        mostrar_snack("Analizando imagen de vitrina con IA Vision. Por favor espera...", "#00FFFF")
        
        try:
            import base64
            with open(filepath, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.2-11b-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analiza esta fotografía de la vitrina de la boutique de lentes Sunglass Hut. Evalúa si cumple con el lineamiento premium de visual merchandising: 1. Alineación recta de los lentes. 2. Espacios vacíos notables que deban rellenarse. 3. Limpieza de cristales (polvo o huellas visibles). 4. Etiquetas de precios bien colocadas. Responde de forma muy concisa en español comenzando con 'APROBADO' o 'CORREGIR' y una lista breve de puntos a solucionar."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_string}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            res = requests.post(URL_GROQ, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                resultado = res.json()["choices"][0]["message"]["content"]
                color_res = "#7CFC00" if "APROBADO" in resultado.upper() else "#FF4500"
                
                dlg_res = ft.AlertDialog(
                    title=ft.Text("🔍 Diagnóstico Visual de Vitrina con IA", color=color_res, weight="bold", size=16),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(resultado, color="white", size=13, selectable=True)
                        ], scroll=ft.ScrollMode.AUTO),
                        width=480,
                        height=250
                    ),
                    actions=[
                        ft.TextButton("Entendido", on_click=lambda ev: page.pop_dialog())
                    ],
                    bgcolor="#0F0F1A"
                )
                page.show_dialog(dlg_res)
                page.update()
            else:
                print("Error Groq Vision:", res.status_code, res.text)
                mostrar_snack("Error al procesar la imagen con IA Vision", "red")
        except Exception as ex_v:
            print("Error auditar vitrina:", ex_v)
            mostrar_snack("Error al abrir o procesar la imagen de vitrina", "red")
    
    file_picker_vitrina.on_result = en_archivo_seleccionado_vitrina
    
    btn_auditar_vitrina = ft.ElevatedButton(
        "Auditar Vitrina 📸",
        icon=ft.Icons.CAMERA_ALT,
        on_click=lambda e: file_picker_vitrina.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE),
        bgcolor="#00FFFF",
        color="black",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    
    progress_apertura = ft.ProgressBar(value=0.0, color="#7CFC00", bgcolor="#141424")
    progress_cierre = ft.ProgressBar(value=0.0, color="#00FFFF", bgcolor="#141424")
    progress_venta = ft.ProgressBar(value=0.0, color="#A100F2", bgcolor="#141424")
    
    text_apertura = ft.Text(f"{t('progress')}: 0%", color="#7CFC00", size=13, weight="bold")
    text_cierre = ft.Text(f"{t('progress')}: 0%", color="#00FFFF", size=13, weight="bold")
    text_venta = ft.Text(f"{t('progress')}: 0%", color="#A100F2", size=13, weight="bold")
    
    def calcular_progreso(categoria, col, p_bar, p_text):
        try:
            total = 0
            completados = 0
            for container in col.controls:
                if isinstance(container, ft.Container) and container.content:
                    content = container.content
                    chk = None
                    if isinstance(content, ft.Row) and content.controls:
                        # Modo Admin: Row([Checkbox, IconButton])
                        chk = content.controls[0]
                    elif isinstance(content, ft.Checkbox):
                        # Modo Asociado: Checkbox directo
                        chk = content
                    
                    if isinstance(chk, ft.Checkbox):
                        total += 1
                        if chk.value:
                            completados += 1
                            
            val = 0.0
            if total > 0:
                val = completados / total
            p_bar.value = val
            p_text.value = f"{t('progress')}: {int(val * 100)}% ({completados} {t('of')} {total} {t('completed')})"
        except Exception as ex:
            print("ERROR CALCULAR PROGRESO CHECKLIST:", ex)
        page.update()
    
    def mostrar_retro_venta_exitosa():
        consejos = [
            "¡Excelente trabajo! Recuerda que según el Manual de Servicio al Cliente, siempre debemos ofrecer al menos 3 opciones de armazones que se adapten a la forma del rostro del cliente para incrementar el ticket promedio y garantizar su satisfacción.",
            "¡Checklist de Venta completado! El Manual de Ventas indica que el 80% de los clientes decide su compra tras probarse físicamente el producto. Asegúrate de limpiar siempre las vitrinas de exhibición y los lentes frente al cliente.",
            "¡Muy bien hecho! Recuerda que al finalizar una venta exitosa, debes reiterar claramente las condiciones de la garantía de fábrica (2 años) y limpiar los lentes minuciosamente antes de entregarlos en su estuche original.",
            "¡Venta exitosa registrada! El Manual de Operaciones destaca la importancia del doble chequeo del ticket de cobro y de las piezas físicas entregadas en su estuche para evitar discrepancias en inventario."
        ]
        import random
        tip = random.choice(consejos)
        
        def cerrar_retro_dialog(ev):
            page.pop_dialog()
            page.update()
        
        dlg_retro = ft.AlertDialog(
            title=ft.Text("💡 Retroalimentación de Venta Exitosa", color="#00FF7F", weight="bold", size=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("¡Felicidades por completar el checklist de Venta Exitosa al 100%! 🎉", color="white", weight="bold", size=14),
                    ft.Container(height=10),
                    ft.Text(tip, color="#D8B4FE", size=13, italic=True)
                ], spacing=5, tight=True),
                width=450
            ),
            actions=[
                ft.ElevatedButton("Entendido", on_click=cerrar_retro_dialog, bgcolor="#00FF7F", color="black")
            ],
            actions_alignment="end",
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dlg_retro)
        page.update()
    
    def mostrar_retro_checklist_completado(categoria):
        if categoria == 1:
            titulo = "🌅 ¡Checklist de Apertura Completado!"
            medalla = "Medalla Madrugador 🌅"
            color_accent = "#7CFC00"
            tips = [
                "Recuerda realizar siempre el conteo físico del fondo de caja en presencia de un testigo antes de abrir las puertas de la tienda.",
                "Revisa que todas las gafas inteligentes Ray-Ban Meta en vitrina estén limpias y encendidas para las demostraciones con clientes.",
                "Asegúrate de que la música ambiental de la tienda esté a un volumen agradable y profesional antes del ingreso de los primeros clientes."
            ]
        elif categoria == 2:
            titulo = "🌙 ¡Checklist de Cierre Completado!"
            medalla = "Medalla Cierre Perfecto 🌙"
            color_accent = "#00FFFF"
            tips = [
                "Antes de salir de la tienda, valida dos veces que la caja fuerte esté cerrada bajo llave y el sistema de alarma activado correctamente.",
                "Recuerda que todas las terminales de venta (Pinpads) deben quedar apagadas y desconectadas de acuerdo al protocolo de finanzas.",
                "Valida que no queden clientes ni personas ajenas al personal dentro de la periferia física de la tienda antes de cerrar las cortinas."
            ]
        else:
            return
        
        import random
        tip = random.choice(tips)
        
        def cerrar_retro_dialog(ev):
            page.pop_dialog()
            page.update()
        
        dlg_retro = ft.AlertDialog(
            title=ft.Text(titulo, color=color_accent, weight="bold", size=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"¡Felicidades por completar todas las tareas al 100% hoy! 🎉
Has ganado la {medalla}.", color="white", weight="bold", size=13),
                    ft.Container(height=10),
                    ft.Text("💡 Recordatorio del Manual Operativo:", color="white", size=12, weight="bold"),
                    ft.Text(tip, color="#D8B4FE", size=12, italic=True)
                ], spacing=5, tight=True),
                width=450
            ),
            actions=[
                ft.ElevatedButton("Excelente", on_click=cerrar_retro_dialog, bgcolor=color_accent, color="black")
            ],
            actions_alignment="end",
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dlg_retro)
        page.update()
    
    def obtener_consejo_para_tarea(descripcion):
        desc_lower = descripcion.lower()
        
        # Apertura
        if "computadora principal" in desc_lower or "pos" in desc_lower:
            return "Encender los sistemas a tiempo previene retrasos con los primeros clientes y asegura la correcta sincronización del inventario diario."
        if "epson" in desc_lower or "papel térmico" in desc_lower:
            return "Tener consumibles listos evita demoras al momento del cobro y asegura que no detengas la fila de clientes en caja."
        if "cobro con tarjeta" in desc_lower or ("terminal" in desc_lower and "encendida" in desc_lower):
            return "Verificar la conectividad de la terminal bancaria a primera hora garantiza que no pierdas transacciones electrónicas."
        if "vitrina" in desc_lower or "limpiar" in desc_lower or "acomodar" in desc_lower or "exhibición" in desc_lower:
            return "Las vitrinas impecables aumentan la conversión. Usa el paño oficial y microfibra para mantener la imagen premium de Sunglass Hut."
        if "trapear" in desc_lower:
            return "Un piso limpio y reluciente da la primera y mejor impresión de higiene y profesionalismo al ingresar a la boutique."
    
        # Cierre
        if "corte de caja" in desc_lower or "conciliación" in desc_lower or "arqueo" in desc_lower or "valores" in desc_lower or "caja" in desc_lower or "efectivo" in desc_lower:
            return "El conteo físico preciso y el arqueo previenen discrepancias contables y son auditados minuciosamente todos los días."
        if "bajo llave" in desc_lower or ("asegurar" in desc_lower and "mercancía" in desc_lower):
            return "El resguardo de mercancía en vitrinas cerradas es obligatorio para cumplir con los estándares de prevención de pérdidas de la tienda."
        if "mostrador" in desc_lower or "empaque" in desc_lower or ("limpiar" in desc_lower and "área" in desc_lower):
            return "Dejar el mostrador limpio y ordenado facilita una apertura ágil y organizada para el turno del día siguiente."
        if "apagar luces" in desc_lower or "apagar" in desc_lower or "pantallas" in desc_lower or "desconectar" in desc_lower:
            return "Desconectar equipos y apagar luminarias de noche ayuda al ahorro energético y alarga la vida útil del equipo tecnológico."
        if "alarma" in desc_lower or "seguridad" in desc_lower or "cerradura" in desc_lower or "llave" in desc_lower:
            return "El protocolo de seguridad de tienda exige el resguardo doble de valores y el armado del sistema de alarma para garantizar la cobertura del seguro."
        if "música" in desc_lower or "volumen" in desc_lower or "ambiente" in desc_lower:
            return "La música ambiental oficial a volumen moderado influye positivamente en el estado de ánimo y aumenta el tiempo de permanencia del cliente."
    
        # Venta Exitosa
        if "kit de limpieza" in desc_lower or "estuche premium" in desc_lower or "ofrecer" in desc_lower:
            return "El kit de limpieza y estuches adicionales añaden valor a la compra e incrementan el ticket promedio (UPT) de la tienda."
        if "datos de correo" in desc_lower or "registrar" in desc_lower or "garantía" in desc_lower:
            return "Capturar el correo del cliente alimenta nuestra base CRM, permitiendo enviarle campañas de lealtad y registrar su garantía digital."
        if "aprobada" in desc_lower or "terminal bancaria" in desc_lower or "transacción" in desc_lower:
            return "Siempre confirma en físico que el ticket de la terminal diga 'APROBADA' y coincida con el cobro en el POS antes de entregar el producto."
        if "ticket de compra" in desc_lower or "bolsa" in desc_lower or "sunglass hut" in desc_lower:
            return "El empaquetado premium y la entrega cordial del ticket de compra cierran el ciclo del servicio de excelencia de Sunglass Hut."
        if "nombre" in desc_lower:
            return "Presentarte por tu nombre genera una conexión de confianza y personaliza la experiencia del cliente para futuras visitas."
    
        # Fallback generalizado inteligente
        return "Completar todos los puntos operativos garantiza que la tienda mantenga el estándar de servicio Premium de Sunglass Hut."
    
    def mostrar_retro_puntos_faltantes(categoria, tareas_faltantes):
        if categoria == 1:
            titulo_cat = "Apertura 🌅"
        elif categoria == 2:
            titulo_cat = "Cierre 🌙"
        else:
            titulo_cat = "Venta Exitosa 💰"
        
        controles_tareas = []
        for t_desc in tareas_faltantes:
            consejo = obtener_consejo_para_tarea(t_desc)
            controles_tareas.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.WARNING_ROUNDED, color="#FFCC00", size=18),
                            ft.Text(t_desc, color="white", weight="bold", size=13, expand=True)
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(f"💡 Sugerencia de mejora: {consejo}", color="#D8B4FE", size=12, italic=True),
                            margin=ft.Margin(left=26, top=2, right=0, bottom=8)
                        )
                    ], spacing=2),
                    padding=ft.Padding(0, 4, 0, 4)
                )
            )
        
        def cerrar_dialog(e):
            page.pop_dialog()
            page.update()
        
        lista_view = ft.ListView(
            controls=controles_tareas,
            spacing=5,
            height=250,
            expand=True
        )
        
        dlg_faltantes = ft.AlertDialog(
            title=ft.Text(f"📋 Puntos de Mejora - {titulo_cat}", color="#FFCC00", weight="bold", size=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Para mantener el estándar de excelencia operativa de la tienda, te sugerimos completar y revisar estos puntos pendientes:", color="white", size=13),
                    ft.Divider(height=10, color="transparent"),
                    lista_view
                ], spacing=5, tight=True),
                width=480
            ),
            actions=[
                ft.ElevatedButton("Ir a Completar", on_click=cerrar_dialog, bgcolor="#FFCC00", color="black")
            ],
            actions_alignment="end",
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dlg_faltantes)
        page.update()
    
    def guardar_checklist_click(categoria):
        col = apertura_list if categoria == 1 else (cierre_list if categoria == 2 else venta_list)
        
        # Actualizar medallas en la sidebar
        if hasattr(page, "actualizar_medallas_sidebar"):
            try:
                page.actualizar_medallas_sidebar()
            except Exception:
                pass
        
        total = 0
        completados = 0
        tareas_faltantes = []
        for container in col.controls:
            if isinstance(container, ft.Container) and container.content:
                content = container.content
                chk = None
                if isinstance(content, ft.Row) and content.controls:
                    chk = content.controls[0]
                elif isinstance(content, ft.Checkbox):
                    chk = content
                
                if isinstance(chk, ft.Checkbox):
                    total += 1
                    if chk.value:
                        completados += 1
                    else:
                        tareas_faltantes.append(chk.label)
        
        # Validar vendedor para Venta Exitosa (Categoría 3)
        if categoria == 3 and not es_admin():
            if not dropdown_vendedor_venta.value:
                mostrar_snack("Por favor selecciona al vendedor que realizó la venta exitosa antes de guardar", "red")
                return
            
            vendedor_id = int(dropdown_vendedor_venta.value)
            faltantes_txt = ", ".join(tareas_faltantes) if tareas_faltantes else ""
            try:
                db_s = conectar_db()
                if db_s:
                    cursor_s = db_s.cursor()
                    cursor_s.execute("""
                        INSERT INTO registro_venta_exitosa 
                        (ID_Usuario_Tienda, ID_Vendedor, Puntos_Completados, Puntos_Totales, Detalle_Faltantes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_info["id"], vendedor_id, completados, total, faltantes_txt))
                    db_s.commit()
                    db_s.close()
            except Exception as ex_s:
                print("Error al guardar venta exitosa por vendedor:", ex_s)
    
        es_perfecto = (total > 0 and completados == total)
        
        if es_perfecto:
            if categoria == 1:
                mostrar_retro_checklist_completado(1)
            elif categoria == 2:
                mostrar_retro_checklist_completado(2)
            elif categoria == 3:
                mostrar_retro_venta_exitosa()
        else:
            porcentaje = int((completados / total) * 100) if total > 0 else 0
            if tareas_faltantes:
                mostrar_retro_puntos_faltantes(categoria, tareas_faltantes)
            else:
                mostrar_snack(f"Checklist guardado parcialmente. Progreso actual: {porcentaje}%. Completa el 100% para tu medalla.", color="#00FFFF")
    
    def toggle_tarea(id_plantilla, completado_val, categoria, col, p_bar, p_text):
        try:
            import datetime
            fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
            payload = {
                "id_usuario": user_info["id"],
                "id_plantilla": id_plantilla,
                "fecha": fecha_hoy
            }
            resp = requests.post(f"{API_URL}/api/tasks/toggle", json=payload)
            if resp.status_code != 200:
                print("Error en toggle_tarea:", resp.text)
        except Exception as ex:
            print("ERROR TOGGLE TAREA CHECKLIST API:", ex)
        
        # Si completó al 100% la categoría 3 (Venta Exitosa), mostrar retroalimentación
        if completado_val and categoria == 3:
            try:
                import datetime
                fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
                resp_chk = requests.get(f"{API_URL}/api/tasks/3/{user_info['id']}/{fecha_hoy}")
                if resp_chk.status_code == 200:
                    data_chk = resp_chk.json()
                    if data_chk.get("status") == "ok":
                        tareas_3 = data_chk.get("data", [])
                        tot3 = len(tareas_3)
                        comp3 = sum(1 for t in tareas_3 if t["Completado"])
                        
                        if tot3 > 0 and comp3 == tot3:
                            mostrar_retro_venta_exitosa()
            except Exception as e_chk:
                print("Error al verificar retro de venta API:", e_chk)
    
        # Actualizar medallas en la sidebar en tiempo real si corresponde
        if hasattr(page, "actualizar_medallas_sidebar"):
            try:
                page.actualizar_medallas_sidebar()
            except Exception:
                pass
        
        calcular_progreso(categoria, col, p_bar, p_text)
    
    def cargar_checklist_por_categoria(categoria, col, p_bar, p_text):
        col.controls.clear()
        try:
            import datetime
            fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
            resp = requests.get(f"{API_URL}/api/tasks/{categoria}/{user_info['id']}/{fecha_hoy}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    tareas = data.get("data", [])
                    # Reconstruir lista de completadas para que el código de abajo funcione
                    completadas_hoy = {t["ID_Plantilla"] for t in tareas if t["Completado"]}
                
                if not tareas:
                    col.controls.append(ft.Text(t("no_tasks"), color="#aaaaaa", italic=True))
                else:
                    for t_item in tareas:
                        id_pl = t_item["ID_Plantilla"]
                        desc = t_item["Descripcion"]
                        esta_completada = id_pl in completadas_hoy
                        
                        chk_box = ft.Checkbox(
                            value=esta_completada,
                            fill_color="#7CFC00" if categoria == 1 else ("#00FFFF" if categoria == 2 else "#A100F2")
                        )
                        
                        txt_tarea = ft.Text(
                            desc,
                            color="white",
                            size=11.5,
                            weight="w500",
                            expand=True
                        )
    
                        chk_box.on_change = lambda e, i_p=id_pl, chk=chk_box: toggle_tarea(
                            i_p, 
                            chk.value, 
                            categoria, 
                            col, 
                            p_bar, 
                            p_text
                        )
    
                        row_controls = [chk_box, txt_tarea]
    
                        if es_admin():
                            def make_delete_click(i_p=id_pl):
                                def delete_item(e):
                                    try:
                                        db_del = conectar_db()
                                        if db_del:
                                            cursor_del = db_del.cursor()
                                            cursor_del.execute("DELETE FROM registro_checklist WHERE ID_Plantilla = %s", (i_p,))
                                            cursor_del.execute("DELETE FROM plantillas_checklist WHERE ID_Plantilla = %s", (i_p,))
                                            db_del.commit()
                                            db_del.close()
                                            mostrar_snack(t("task_deleted"))
                                            # Reload all checklists to keep UI in sync
                                            cargar_checklist_por_categoria(1, apertura_list, progress_apertura, text_apertura)
                                            cargar_checklist_por_categoria(2, cierre_list, progress_cierre, text_cierre)
                                            cargar_checklist_por_categoria(3, venta_list, progress_venta, text_venta)
                                    except Exception as ex:
                                        print("ERROR ELIMINAR TAREA:", ex)
                                        mostrar_snack("Error", color="red")
                                return delete_item
    
                            row_controls.append(
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                    icon_color="#FF4500",
                                    icon_size=18,
                                    tooltip="Eliminar tarea",
                                    on_click=make_delete_click()
                                )
                            )
    
                        col.controls.append(
                            ft.Container(
                                content=ft.Row(row_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                                bgcolor="#0F0F1A",
                                padding=6,
                                border_radius=6,
                                border=ft.Border.all(1, "#222222")
                            )
                        )
        except Exception as ex:
            print("ERROR CARGAR CHECKLIST POR CATEGORIA:", ex)
            col.controls.append(ft.Text("Error", color="red"))
        calcular_progreso(categoria, col, p_bar, p_text)
    
    def build_admin_inline_form(categoria, col, p_bar, p_text):
        input_new_task = ft.TextField(
            label=t("add_task"),
            expand=True,
            border_color="#7CFC00" if categoria == 1 else ("#00FFFF" if categoria == 2 else "#A100F2"),
            label_style=ft.TextStyle(color="#aaaaaa", size=11),
            text_style=ft.TextStyle(color="white", size=12),
            height=40
        )
        
        def agregar_inline_click(e):
            desc_val = input_new_task.value.strip()
            if not desc_val:
                return
            try:
                db = conectar_db()
                if db:
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO plantillas_checklist (Categoria, Descripcion) VALUES (%s, %s)", (categoria, desc_val))
                    db.commit()
                    db.close()
                    input_new_task.value = ""
                    mostrar_snack(t("task_added"))
                    # Reload this checklist category
                    cargar_checklist_por_categoria(categoria, col, p_bar, p_text)
            except Exception as ex:
                print("ERROR AGREGAR TAREA INLINE:", ex)
                mostrar_snack("Error", color="red")
        
        btn_add = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
            icon_color="#7CFC00" if categoria == 1 else ("#00FFFF" if categoria == 2 else "#A100F2"),
            tooltip=t("add_task"),
            on_click=agregar_inline_click
        )
        
        return ft.Container(
            content=ft.Row([
                input_new_task,
                btn_add
            ], spacing=10),
            margin=ft.Margin(left=0, top=0, right=0, bottom=10)
        )
    
    cargar_checklist_por_categoria(1, apertura_list, progress_apertura, text_apertura)
    cargar_checklist_por_categoria(2, cierre_list, progress_cierre, text_cierre)
    cargar_checklist_por_categoria(3, venta_list, progress_venta, text_venta)
    
    tabs_checklist = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Apertura 🌅", icon=ft.Icons.LIGHT_MODE),
                        ft.Tab(label="Cierre 🌌", icon=ft.Icons.NIGHTLIGHT_ROUNDED),
                        ft.Tab(label="Venta 💰", icon=ft.Icons.MONETIZATION_ON_ROUNDED)
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Column([
                            ft.Divider(height=10, color="transparent"),
                            text_apertura,
                            progress_apertura,
                            ft.Divider(height=10, color="transparent"),
                            build_admin_inline_form(1, apertura_list, progress_apertura, text_apertura) if es_admin() else ft.Container(content=btn_auditar_vitrina, margin=ft.Margin(0, 0, 0, 10)),
                            apertura_list,
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Guardar Apertura 💾",
                                    on_click=lambda e: guardar_checklist_click(1),
                                    bgcolor="#7CFC00",
                                    color="black",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                padding=ft.Padding(0, 10, 0, 10)
                            ) if not es_admin() else ft.Container()
                        ], expand=True, scroll=ft.ScrollMode.AUTO),
                        ft.Column([
                            ft.Divider(height=10, color="transparent"),
                            text_cierre,
                            progress_cierre,
                            ft.Divider(height=10, color="transparent"),
                            build_admin_inline_form(2, cierre_list, progress_cierre, text_cierre) if es_admin() else ft.Container(),
                            cierre_list,
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Guardar Cierre 💾",
                                    on_click=lambda e: guardar_checklist_click(2),
                                    bgcolor="#00FFFF",
                                    color="black",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                padding=ft.Padding(0, 10, 0, 10)
                            ) if not es_admin() else ft.Container()
                        ], expand=True, scroll=ft.ScrollMode.AUTO),
                        ft.Column([
                            ft.Divider(height=10, color="transparent"),
                            text_venta,
                            progress_venta,
                            ft.Divider(height=10, color="transparent"),
                            build_admin_inline_form(3, venta_list, progress_venta, text_venta) if es_admin() else ft.Container(content=dropdown_vendedor_venta, margin=ft.Margin(0, 0, 0, 10)),
                            venta_list,
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Guardar Venta 💾",
                                    on_click=lambda e: guardar_checklist_click(3),
                                    bgcolor="#A100F2",
                                    color="white",
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                                ),
                                alignment=ft.alignment.Alignment(0, 0),
                                padding=ft.Padding(0, 10, 0, 10)
                            ) if not es_admin() else ft.Container()
                        ], expand=True, scroll=ft.ScrollMode.AUTO)
                    ]
                )
            ]
        )
    )
    
    # Botones del encabezado de checklist
    header_buttons = []
    if es_admin():
        def ir_a_editar_checklists(e):
            dashboard_tab_index[0] = 5  # Selecciona la pestaña 6: Editar Checklists
            cambiar_vista("dashboard")
        header_buttons.append(
            ft.ElevatedButton(
                t("edit_options"),
                icon=ft.Icons.EDIT_ROUNDED,
                bgcolor="#9D50BB",
                color="white",
                on_click=ir_a_editar_checklists
            )
        )
    
    header_buttons.append(
        ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            tooltip=t("refresh"),
            on_click=lambda e: [
                cargar_checklist_por_categoria(1, apertura_list, progress_apertura, text_apertura),
                cargar_checklist_por_categoria(2, cierre_list, progress_cierre, text_cierre),
                cargar_checklist_por_categoria(3, venta_list, progress_venta, text_venta)
            ]
        )
    )
    
    return ft.Column([
        ft.Row([
            ft.Text(t("checklist_title"), size=24, color="#D8B4FE", weight="bold"),
            ft.Row(header_buttons, spacing=10)
        ], alignment="spaceBetween", vertical_alignment="center"),
        ft.Text(t("checklist_desc"), color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        tabs_checklist
    ], expand=True)