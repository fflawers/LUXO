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

def _build_campanas_gerente_view(
    auditar_foto_con_gemini,
    conectar_db,
    crear_notificacion,
    crear_notificacion_a_rol,
    ent_id,
    f_pdf,
    file_path,
    g_id,
    id_c,
    id_camp,
    id_guia,
    mostrar_snack,
    optimizar_imagen,
    page,
    path,
    seleccionar_archivo_async,
    user_info
):
    gerente_campana_col = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    u_id = user_info.get("id")
    
    # Cargar el segmento y la zona del usuario desde la BD si no están en user_info
    if "segmento" not in user_info or "zona" not in user_info:
        try:
            db_u = conectar_db()
            if db_u:
                cur_u = db_u.cursor(dictionary=True)
                cur_u.execute("SELECT Segmento, Zona FROM usuarios WHERE ID_Usuario = %s", (u_id,))
                user_row = cur_u.fetchone()
                db_u.close()
                if user_row:
                    user_info["segmento"] = user_row["Segmento"] if user_row["Segmento"] else "Todos"
                    user_info["zona"] = user_row["Zona"] if user_row["Zona"] else "Zona Centro"
                else:
                    user_info["segmento"] = "Todos"
                    user_info["zona"] = "Zona Centro"
        except Exception as ex_u:
            print("ERROR CARGANDO SEGMENTO/ZONA USUARIO:", ex_u)
            user_info["segmento"] = "Todos"
            user_info["zona"] = "Zona Centro"
    
    segmento_actual = user_info.get("segmento") or "Todos"
    zona_actual = user_info.get("zona") or "Zona Centro"
    
    def cambiar_segmento_gerente(e):
        nuevo_seg = e.control.value
        user_info["segmento"] = nuevo_seg
        try:
            db_seg = conectar_db()
            if db_seg:
                cursor_seg = db_seg.cursor()
                cursor_seg.execute("UPDATE usuarios SET Segmento = %s WHERE ID_Usuario = %s", (nuevo_seg, u_id))
                db_seg.commit()
                db_seg.close()
                mostrar_snack(f"Segmento de tienda actualizado a: {nuevo_seg}", color="#7CFC00")
        except Exception as ex:
            print("ERROR ACTUALIZANDO SEGMENTO GERENTE:", ex)
        cargar_campana_gerente()
    
    def cambiar_zona_gerente(e):
        nueva_zona = e.control.value
        user_info["zona"] = nueva_zona
        try:
            db_z = conectar_db()
            if db_z:
                cursor_z = db_z.cursor()
                cursor_z.execute("UPDATE usuarios SET Zona = %s WHERE ID_Usuario = %s", (nueva_zona, u_id))
                db_z.commit()
                db_z.close()
                mostrar_snack(f"Zona de tienda actualizada a: {nueva_zona}", color="#7CFC00")
        except Exception as ex:
            print("ERROR ACTUALIZANDO ZONA GERENTE:", ex)
        cargar_campana_gerente()
    
    dropdown_segmento = ft.Dropdown(
        label="Formato / Segmento de tu Tienda",
        value=segmento_actual,
        options=[
            ft.dropdown.Option("Todos", "Todos"),
            ft.dropdown.Option("Formato 6.000/2.0", "Formato 6.000/2.0"),
            ft.dropdown.Option("Formato Inline 4.0", "Formato Inline 4.0"),
            ft.dropdown.Option("Formato Inline Skin", "Formato Inline Skin"),
            ft.dropdown.Option("Formato Inline Boxes", "Formato Inline Boxes"),
            ft.dropdown.Option("Formato Open Airs (Kioskos)", "Formato Open Airs (Kioskos)"),
            ft.dropdown.Option("Formato Inline Skin Kiosko", "Formato Inline Skin Kiosko")
        ],
        border_color="#00FFFF",
        width=350
    )
    dropdown_segmento.on_change = cambiar_segmento_gerente
    
    def abrir_pdf_campana(id_camp):
        try:
            db_p = conectar_db()
            if not db_p:
                return
            cursor_p = db_p.cursor(dictionary=True)
            cursor_p.execute("SELECT Guia_PDF_Nombre, Guia_PDF_Bytes FROM campanas WHERE ID_Campana = %s", (id_camp,))
            row = cursor_p.fetchone()
            db_p.close()
            if row and row["Guia_PDF_Bytes"]:
                import tempfile
                ruta_temp = os.path.join(tempfile.gettempdir(), row["Guia_PDF_Nombre"])
                with open(ruta_temp, "wb") as f_pdf:
                    f_pdf.write(row["Guia_PDF_Bytes"])
                import os
                os.startfile(ruta_temp)
                mostrar_snack(f"Abriendo PDF de la campaña: {row['Guia_PDF_Nombre']}", color="#7CFC00")
            else:
                mostrar_snack("No hay archivo PDF cargado para esta campaña.", color="#FF4500")
        except Exception as ex:
            print("ERROR ABRIR PDF CAMPANA:", ex)
            mostrar_snack("Error al abrir el archivo PDF.", color="red")
    
    def cargar_campana_gerente():
        gerente_campana_col.controls.clear()
        
        # Verificar que el gerente tenga tienda asignada
        t_nombre = user_info.get("tienda")
        if not t_nombre:
            gerente_campana_col.controls.append(
                ft.Text("Advertencia: No tienes una tienda asignada en tu perfil. Contacta al Administrador para poder subir tus fotos de campaña.", color="#FF4500", weight="bold")
            )
            page.update()
            return
        
        # Renderizar selector de formato
        gerente_campana_col.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Filtro de Guías por Formato:", weight="bold"),
                        dropdown_segmento
                    ], alignment="spaceBetween", vertical_alignment="center")
                ], spacing=10),
                bgcolor="#1e1e1e",
                padding=15,
                border_radius=8
            )
        )
    
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                # Buscar campaña activa
                cursor.execute("SELECT ID_Campana, Nombre, Descripcion, Guia_PDF_Nombre FROM campanas WHERE Estatus = 'Activa'")
                campana = cursor.fetchone()
                
                if not campana:
                    gerente_campana_col.controls.append(
                        ft.Text("No hay ninguna campaña mensual activa en este momento. Vuelve más tarde.", color="#aaaaaa", italic=True)
                    )
                    db.close()
                    page.update()
                    return
                
                id_campana = campana["ID_Campana"]
                
                # Obtener entrega de esta tienda o crearla
                cursor.execute("""
                    SELECT ID_Entrega, Estatus FROM campana_entregas_tienda
                    WHERE ID_Campana = %s AND Tienda = %s
                """, (id_campana, t_nombre))
                entrega = cursor.fetchone()
                if not entrega:
                    cursor.execute("""
                        INSERT INTO campana_entregas_tienda (ID_Campana, Tienda, ID_Usuario, Estatus)
                        VALUES (%s, %s, %s, 'Pendiente')
                    """, (id_campana, t_nombre, u_id))
                    db.commit()
                    id_entrega = cursor.lastrowid
                    entrega_status = "Pendiente"
                else:
                    id_entrega = entrega["ID_Entrega"]
                    entrega_status = entrega["Estatus"]
                    
                # Obtener fotos guías de la campaña filtrando por el segmento seleccionado o Todos
                seg_filtro = user_info.get("segmento") or "Todos"
                cursor.execute("""
                    SELECT ID_Foto_Guia, Nombre_Foto, Instrucciones, Imagen_Bytes, Segmento FROM campana_fotos_guia
                    WHERE ID_Campana = %s AND (Segmento = 'Todos' OR Segmento = %s)
                    ORDER BY ID_Foto_Guia
                """, (id_campana, seg_filtro))
                guias = cursor.fetchall()
                
                # Obtener fotos subidas por la tienda en esta entrega
                cursor.execute("""
                    SELECT ID_Foto_Tienda, ID_Foto_Guia, Imagen_Bytes, Estatus_Auditoria, Resultado_IA FROM campana_fotos_tienda
                    WHERE ID_Entrega = %s
                """, (id_entrega,))
                fotos_tienda = {f["ID_Foto_Guia"]: f for f in cursor.fetchall()}
                db.close()
                
                # PDF de la guia
                header_row_widgets = [
                    ft.Text(f"Campaña Activa: {campana['Nombre']}", size=18, color="#00FFFF", weight="bold"),
                ]
                if campana.get("Guia_PDF_Nombre"):
                    btn_ver_pdf = ft.ElevatedButton(
                        "Ver Guía de Instalación PDF 📄",
                        icon=ft.Icons.PICTURE_AS_PDF,
                        bgcolor="#9D50BB",
                        color="white",
                        on_click=lambda e, id_c=id_campana: abrir_pdf_campana(id_c)
                    )
                    header_row_widgets.append(btn_ver_pdf)
                    
                header_row_widgets.append(
                    ft.Container(
                        content=ft.Text(f"ESTATUS: {entrega_status.upper().replace('_', ' ')}", size=10, weight="bold", color="black"),
                        bgcolor="#00FF7F" if entrega_status == "Visto_Bueno" else ("#FFD700" if entrega_status == "Aprobado_IA" else "#FF4500"),
                        padding=5,
                        border_radius=4
                    )
                )
    
                # UI Encabezado
                gerente_campana_col.controls.append(
                    ft.Row(header_row_widgets, alignment="spaceBetween")
                )
                if campana["Descripcion"]:
                    gerente_campana_col.controls.append(ft.Text(campana["Descripcion"], size=13, color="#cccccc"))
                gerente_campana_col.controls.append(ft.Divider(height=10, color="#333333"))
                
                if not guias:
                    gerente_campana_col.controls.append(
                        ft.Text(f"No hay fotos guía configuradas para tu segmento ({seg_filtro}) o para todos.", color="#aaaaaa", italic=True)
                    )
                else:
                    # Renderizar cada guía
                    for g in guias:
                        id_g = g["ID_Foto_Guia"]
                        nom_foto = g["Nombre_Foto"]
                        instrucciones = g["Instrucciones"]
                        seg_guia = g["Segmento"]
                        
                        import base64
                        img_guia_b64 = base64.b64encode(g["Imagen_Bytes"]).decode("utf-8")
                        
                        subida = fotos_tienda.get(id_g)
                        
                        # Construir interfaz de esta foto
                        tienda_img_widget = None
                        status_txt = "Pendiente de subir"
                        status_color = "#aaaaaa"
                        audit_feedback = ""
                        
                        if subida:
                            img_tienda_b64 = base64.b64encode(subida["Imagen_Bytes"]).decode("utf-8")
                            tienda_img_widget = ft.Image(src=f"data:image/jpeg;base64,{img_tienda_b64}", width=180, height=135, fit="contain")
                            est = subida["Estatus_Auditoria"]
                            if est == "Aprobado":
                                status_txt = "APROBADO POR IA"
                                status_color = "#00FF7F"
                            elif est == "Corregir":
                                status_txt = "CORREGIR (Ver observaciones abajo)"
                                status_color = "#FF4500"
                            else:
                                status_txt = "REVISANDO CON IA..."
                                status_color = "#FFD700"
                                
                            if subida["Resultado_IA"]:
                                audit_feedback = subida["Resultado_IA"]
                        else:
                            tienda_img_widget = ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.ADD_A_PHOTO_ROUNDED, color="#00FFFF", size=30),
                                    ft.Text("Subir foto real
de tu tienda", color="#00FFFF", size=11, text_align=ft.TextAlign.CENTER)
                                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=180,
                                height=135,
                                bgcolor="#0F0F1A",
                                border_radius=8,
                                border=ft.Border.all(1, "#00FFFF")
                            )
                            
                        card_border = ft.Border.all(1.5, "#00FF7F" if status_txt.startswith("APROBADO") else ("#FF4500" if status_txt.startswith("CORREGIR") else "#333333"))
                        
                        def make_on_upload(g_id=id_g, ent_id=id_entrega):
                            return lambda e: seleccionar_archivo_async(
                                f"Subir Foto para {nom_foto}",
                                [("Imágenes", "*.png *.jpg *.jpeg")],
                                lambda path: subir_foto_tienda_gerente(path, g_id, ent_id)
                            )
                            
                        gerente_campana_col.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Row([
                                            ft.Text(nom_foto, size=15, color="#D8B4FE", weight="bold"),
                                            ft.Container(
                                                content=ft.Text(f"Segmento: {seg_guia}", size=8, color="black", weight="bold"),
                                                bgcolor="#00FFFF",
                                                padding=2,
                                                border_radius=2
                                            )
                                        ], spacing=10),
                                        ft.Container(
                                            content=ft.Text(status_txt, size=9, weight="bold", color="black"),
                                            bgcolor=status_color,
                                            padding=3,
                                            border_radius=3
                                        )
                                    ], alignment="spaceBetween"),
                                    ft.Text(f"Instrucciones de Montaje: {instrucciones}", size=12, color="#aaaaaa"),
                                    ft.Row([
                                        ft.Column([
                                            ft.Text("FOTO GUÍA DE MONTAJE", size=9, color="#aaaaaa", weight="bold"),
                                            ft.Image(src=f"data:image/jpeg;base64,{img_guia_b64}", width=180, height=135, fit=ft.ImageFit.CONTAIN)
                                        ], horizontal_alignment="center"),
                                        ft.Column([
                                            ft.Text("FOTO REAL DE TU TIENDA", size=9, color="#aaaaaa", weight="bold"),
                                            tienda_img_widget
                                        ], horizontal_alignment="center")
                                    ], spacing=20, alignment="center"),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            "Subir Foto" if not subida else "Volver a subir",
                                            icon=ft.Icons.UPLOAD_FILE,
                                            bgcolor="#00FFFF",
                                            color="black",
                                            on_click=make_on_upload()
                                        )
                                    ], alignment="center"),
                                    ft.Column([
                                        ft.Text("Análisis de IA de Visión:", size=11, color="#aaaaaa", weight="bold"),
                                        ft.Text(audit_feedback, size=11, color="white")
                                    ], spacing=3, visible=bool(audit_feedback))
                                ], spacing=10),
                                bgcolor="#141424",
                                padding=15,
                                border_radius=8,
                                border=card_border
                            )
                        )
        except Exception as ex:
            print("ERROR CARGANDO VISTA GERENTE CAMPANA:", ex)
            gerente_campana_col.controls.append(ft.Text("Error al cargar la campaña activa.", color="red"))
        page.update()
    
    def subir_foto_tienda_gerente(file_path, id_guia, id_entrega):
        try:
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            
            # Optimizar imagen
            img_optimized = optimizar_imagen(raw_bytes)
            
            mostrar_snack("Foto subida. Iniciando auditoría con IA...", color="#00FFFF")
            
            # Guardar foto en la base de datos con estatus temporal 'Auditando'
            db = conectar_db()
            if db:
                cursor = db.cursor()
                # Verificar si ya existe un registro para esta foto guia
                cursor.execute("""
                    SELECT ID_Foto_Tienda FROM campana_fotos_tienda
                    WHERE ID_Entrega = %s AND ID_Foto_Guia = %s
                """, (id_entrega, id_guia))
                row = cursor.fetchone()
                
                if row:
                    id_foto_tienda = row[0]
                    cursor.execute("""
                        UPDATE campana_fotos_tienda
                        SET Imagen_Bytes = %s, Estatus_Auditoria = 'Auditando', Resultado_IA = 'Revisando imagen con IA de visión...'
                        WHERE ID_Foto_Tienda = %s
                    """, (img_optimized, id_foto_tienda))
                else:
                    cursor.execute("""
                        INSERT INTO campana_fotos_tienda (ID_Entrega, ID_Foto_Guia, Imagen_Bytes, Estatus_Auditoria, Resultado_IA)
                        VALUES (%s, %s, %s, 'Auditando', 'Revisando imagen con IA de visión...')
                    """, (id_entrega, id_guia, img_optimized))
                
                db.commit()
                db.close()
                
                # Notificar al Administrador de la entrega de fotos
                crear_notificacion_a_rol("Administrador", "Nueva Foto de Campaña 📸", f"La tienda '{t_nombre}' ha subido una foto para revisión.", "campana")
                
            # Refrescar UI antes de llamar a Gemini
            cargar_campana_gerente()
            
            # Lanzar auditoría en hilo separado para no bloquear la UI
            def thread_auditoria():
                try:
                    # 1. Recuperar fotos guía e instrucciones de la BD
                    db_aud = conectar_db()
                    if db_aud:
                        cursor_aud = db_aud.cursor(dictionary=True)
                        cursor_aud.execute("""
                            SELECT Imagen_Bytes, Instrucciones, Nombre_Foto FROM campana_fotos_guia
                            WHERE ID_Foto_Guia = %s
                        """, (id_guia,))
                        guia_row = cursor_aud.fetchone()
                        db_aud.close()
                        
                        if guia_row:
                            guia_bytes = guia_row["Imagen_Bytes"]
                            instrucciones = guia_row["Instrucciones"]
                            nombre_foto = guia_row["Nombre_Foto"]
                            
                            # 2. Llamar a la IA
                            resultado_ia = auditar_foto_con_gemini(guia_bytes, img_optimized, instrucciones)
                            
                            # 3. Determinar estatus según la primera palabra
                            resultado_limpio = resultado_ia.strip()
                            if resultado_limpio.upper().startswith("APROBADO"):
                                estatus_final = "Aprobado"
                            elif resultado_limpio.upper().startswith("CORREGIR"):
                                estatus_final = "Corregir"
                            else:
                                # Buscar palabras clave si no empieza exactamente
                                if "APROBADO" in resultado_limpio.upper()[:15]:
                                    estatus_final = "Aprobado"
                                else:
                                    estatus_final = "Corregir"
                                    
                            # 4. Actualizar en base de datos
                            db_upd = conectar_db()
                            if db_upd:
                                cursor_upd = db_upd.cursor()
                                cursor_upd.execute("""
                                    UPDATE campana_fotos_tienda
                                    SET Estatus_Auditoria = %s, Resultado_IA = %s, Fecha_Auditoria = CURRENT_TIMESTAMP
                                    WHERE ID_Entrega = %s AND ID_Foto_Guia = %s
                                """, (estatus_final, resultado_limpio, id_entrega, id_guia))
                                
                                # Comprobar si todas las fotos de la entrega están aprobadas para actualizar la entrega a 'Aprobado_IA'
                                cursor_upd.execute("""
                                    SELECT COUNT(*) FROM campana_fotos_guia g
                                    WHERE g.ID_Campana = (SELECT ID_Campana FROM campana_entregas_tienda WHERE ID_Entrega = %s)
                                """, (id_entrega,))
                                total_requeridas = cursor_upd.fetchone()[0]
                                
                                cursor_upd.execute("""
                                    SELECT COUNT(*) FROM campana_fotos_tienda
                                    WHERE ID_Entrega = %s AND Estatus_Auditoria = 'Aprobado'
                                """, (id_entrega,))
                                total_aprobadas = cursor_upd.fetchone()[0]
                                
                                if total_aprobadas >= total_requeridas:
                                    cursor_upd.execute("""
                                        UPDATE campana_entregas_tienda
                                        SET Estatus = 'Aprobado_IA'
                                        WHERE ID_Entrega = %s AND Estatus != 'Visto_Bueno'
                                    """, (id_entrega,))
                                else:
                                    cursor_upd.execute("""
                                        UPDATE campana_entregas_tienda
                                        SET Estatus = 'Rechazado_IA'
                                        WHERE ID_Entrega = %s AND Estatus != 'Visto_Bueno'
                                    """, (id_entrega,))
                                    
                                db_upd.commit()
                                db_upd.close()
                                
                                # Notificar al gerente de la sucursal sobre la auditoría IA
                                crear_notificacion(u_id, "Auditoría IA de Campaña 🤖", f"La sección '{nombre_foto}' ha sido calificada como: {estatus_final.upper()}", "campana")
                                
                            # Notificar y refrescar
                            mostrar_snack("Auditoría de IA completada.", color="#7CFC00" if estatus_final == "Aprobado" else "#FF4500")
                            cargar_campana_gerente()
                except Exception as ex_t:
                    print("ERROR EN THREAD AUDITORIA:", ex_t)
                    mostrar_snack("Error en proceso de auditoría con la IA.", color="red")
                    
            threading.Thread(target=thread_auditoria, daemon=True).start()
            
        except Exception as ex:
            print("ERROR SUBIENDO FOTO TIENDA:", ex)
            mostrar_snack("Error al guardar la foto.", color="red")
            
    cargar_campana_gerente()
    
    return ft.Column([
        ft.Row([
            ft.Text("Fotos de Campaña — Tiendas", size=24, color="#D8B4FE", weight="bold")
        ]),
        ft.Text("Sube las fotos de exhibición de tu tienda y deja que el auditor de IA valide el montaje según las guías.", color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        gerente_campana_col
    ], expand=True, scroll=ft.ScrollMode.AUTO)