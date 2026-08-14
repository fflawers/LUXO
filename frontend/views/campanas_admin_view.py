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

def _build_campanas_admin_view(
    active_zone_filter,
    campo,
    conectar_db,
    crear_notificacion,
    crear_notificacion_a_rol,
    ent_id,
    guardar_config_key,
    id_ent,
    id_entrega,
    mostrar_snack,
    optimizar_imagen,
    page,
    path,
    seleccionar_archivo_async,
    t_name,
    tienda_name,
    valor
):
    # Estado de fotos guia en creacion de campaña
    # Formato: {"nombre": "...", "instrucciones": "...", "foto_bytes": b"...", "segmento": "Todos", "img_preview": ft.Image}
    guias_creacion = []
    
    # Contenedor para lista de guias en creacion
    guias_col = ft.Column(spacing=10)
    
    nombre_campana = ft.TextField(label="Nombre de la Campaña", border_color="#D8B4FE")
    desc_campana = ft.TextField(label="Instrucciones / Descripción de la Campaña", border_color="#D8B4FE", multiline=True, min_lines=2)
    
    # PDF de la guia
    pdf_guia_bytes = [None]
    pdf_guia_nombre = [None]
    text_pdf_info = ft.Text("No se ha cargado PDF de guía de instalación", color="#aaaaaa", italic=True)
    
    def on_pdf_guia_cargado(path):
        try:
            import os
            with open(path, "rb") as f:
                pdf_guia_bytes[0] = f.read()
            pdf_guia_nombre[0] = os.path.basename(path)
            text_pdf_info.value = f"PDF Cargado: {pdf_guia_nombre[0]}"
            text_pdf_info.color = "#00FF7F"
            mostrar_snack(f"Guía PDF '{pdf_guia_nombre[0]}' cargada correctamente.", color="#7CFC00")
            page.update()
        except Exception as ex:
            print("ERROR CARGANDO PDF GUIA:", ex)
            mostrar_snack("Error al cargar el archivo PDF.", color="red")
    
    btn_cargar_pdf_guia = ft.ElevatedButton(
        "Cargar Guía PDF (Opcional)",
        icon=ft.Icons.PICTURE_AS_PDF,
        bgcolor="#9D50BB",
        color="white",
        on_click=lambda e: seleccionar_archivo_async(
            "Seleccionar PDF de la Guía de Instalación",
            [("PDF files", "*.pdf")],
            on_pdf_guia_cargado
        )
    )
    
    def refrescar_guias_creacion():
        guias_col.controls.clear()
        for i, g in enumerate(guias_creacion):
            def make_on_click(idx):
                return lambda e: seleccionar_archivo_async(
                    f"Seleccionar Foto Guía {idx+1}",
                    [("Imágenes", "*.png *.jpg *.jpeg")],
                    lambda path: on_guia_file_selected(idx, path)
                )
            
            def make_on_delete(idx):
                return lambda e: eliminar_guia_creacion(idx)
                
            img_preview = g.get("img_preview")
            if not img_preview:
                if g.get("foto_bytes"):
                    import base64
                    img_b64 = base64.b64encode(g["foto_bytes"]).decode("utf-8")
                    img_preview = ft.Image(src=f"data:image/jpeg;base64,{img_b64}", width=120, height=120, fit="contain")
                    g["img_preview"] = img_preview
                else:
                    img_preview = ft.Icon(ft.Icons.IMAGE, size=40, color="#555555")
                    
            dd_guia = ft.Dropdown(
                label="Formato / Segmento de Tienda",
                value=g["segmento"],
                options=[
                    ft.dropdown.Option("Todos", "Todos"),
                    ft.dropdown.Option("Formato 6.000/2.0", "Formato 6.000/2.0"),
                    ft.dropdown.Option("Formato Inline 4.0", "Formato Inline 4.0"),
                    ft.dropdown.Option("Formato Inline Skin", "Formato Inline Skin"),
                    ft.dropdown.Option("Formato Inline Boxes", "Formato Inline Boxes"),
                    ft.dropdown.Option("Formato Open Airs (Kioskos)", "Formato Open Airs (Kioskos)"),
                    ft.dropdown.Option("Formato Inline Skin Kiosko", "Formato Inline Skin Kiosko")
                ],
                border_color="#333333",
                width=350
            )
            dd_guia.on_change = lambda e, idx=i: actualizar_guia_campo(idx, "segmento", e.control.value)
    
            guias_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"Foto Guía #{i+1}", weight="bold", color="#00FFFF"),
                            ft.IconButton(ft.Icons.DELETE, icon_color="#FF4500", on_click=make_on_delete(i))
                        ], alignment="spaceBetween"),
                        ft.Row([
                            ft.Column([
                                ft.TextField(
                                    label="Nombre de la Foto (ej. Muro Oakley)",
                                    value=g["nombre"],
                                    border_color="#333333",
                                    on_change=lambda e, idx=i: actualizar_guia_campo(idx, "nombre", e.control.value),
                                    width=350
                                ),
                                dd_guia,
                                ft.TextField(
                                    label="Instrucciones para la IA (ej. Logo centrado, sin espacios vacíos)",
                                    value=g["instrucciones"],
                                    border_color="#333333",
                                    multiline=True,
                                    min_lines=2,
                                    on_change=lambda e, idx=i: actualizar_guia_campo(idx, "instrucciones", e.control.value),
                                    width=350
                                ),
                            ], spacing=5, expand=True),
                            ft.Column([
                                img_preview,
                                ft.ElevatedButton(
                                    "Subir Guía",
                                    icon=ft.Icons.UPLOAD,
                                    bgcolor="#D8B4FE",
                                    color="black",
                                    on_click=make_on_click(i)
                                )
                            ], horizontal_alignment="center", spacing=5)
                        ], spacing=15)
                    ]),
                    bgcolor="#141424",
                    padding=12,
                    border_radius=8,
                    border=ft.Border.all(1, "#333333")
                )
            )
        
        # Botón "+" al final para añadir más guías cómodamente
        guias_col.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE_ROUNDED,
                        icon_color="#00FFFF",
                        icon_size=36,
                        tooltip="Añadir otra Foto Guía",
                        on_click=agregar_guia_creacion
                    ),
                    ft.Text("Añadir otra Foto Guía (+)", color="#00FFFF", weight="bold", size=14)
                ], alignment="center"),
                margin=ft.Margin(left=0, top=10, right=0, bottom=10)
            )
        )
        page.update()
    
    def actualizar_guia_campo(idx, campo, valor):
        if idx < len(guias_creacion):
            guias_creacion[idx][campo] = valor
    
    def on_guia_file_selected(idx, path):
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
            enhanced_bytes = optimizar_imagen(raw_bytes)
            if idx < len(guias_creacion):
                guias_creacion[idx]["foto_bytes"] = enhanced_bytes
                guias_creacion[idx]["img_preview"] = None
                refrescar_guias_creacion()
                mostrar_snack(f"Foto {idx+1} cargada y optimizada.", color="#7CFC00")
        except Exception as ex:
            print("ERROR CARGANDO GUIA:", ex)
            mostrar_snack("Error al cargar la foto.", color="red")
    
    def eliminar_guia_creacion(idx):
        if idx < len(guias_creacion):
            guias_creacion.pop(idx)
            refrescar_guias_creacion()
    
    def agregar_guia_creacion(e):
        guias_creacion.append({
            "nombre": "",
            "instrucciones": "",
            "segmento": "Todos",
            "foto_bytes": None,
            "img_preview": None
        })
        refrescar_guias_creacion()
    
    def guardar_campana_click(e):
        nom = nombre_campana.value.strip()
        desc = desc_campana.value.strip()
        if not nom:
            mostrar_snack("Por favor ingrese un nombre de campaña.", color="red")
            return
        if not guias_creacion:
            mostrar_snack("Debe añadir al menos una foto guía.", color="red")
            return
        # Verificar que todas tengan foto y nombre
        for i, g in enumerate(guias_creacion):
            if not g["nombre"].strip():
                mostrar_snack(f"La foto guía #{i+1} no tiene nombre.", color="red")
                return
            if not g["foto_bytes"]:
                mostrar_snack(f"La foto guía #{i+1} no tiene imagen.", color="red")
                return
        
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                # Desactivar otras campañas
                cursor.execute("UPDATE campanas SET Estatus = 'Inactiva' WHERE Estatus = 'Activa'")
                # Insertar nueva campaña
                cursor.execute(
                    "INSERT INTO campanas (Nombre, Descripcion, Estatus, Guia_PDF_Bytes, Guia_PDF_Nombre) VALUES (%s, %s, 'Activa', %s, %s)",
                    (nom, desc, pdf_guia_bytes[0], pdf_guia_nombre[0])
                )
                id_campana = cursor.lastrowid
                
                # Insertar fotos guia
                for g in guias_creacion:
                    cursor.execute(
                        "INSERT INTO campana_fotos_guia (ID_Campana, Nombre_Foto, Instrucciones, Imagen_Bytes, Segmento) VALUES (%s, %s, %s, %s, %s)",
                        (id_campana, g["nombre"], g["instrucciones"], g["foto_bytes"], g["segmento"])
                    )
                db.commit()
                db.close()
                
                # Notificar a todas las tiendas
                crear_notificacion_a_rol("Gerente", "Nueva Campaña Mensual 📸", f"Se ha activado la campaña: '{nom}'", "campana")
                
                nombre_campana.value = ""
                desc_campana.value = ""
                pdf_guia_bytes[0] = None
                pdf_guia_nombre[0] = None
                text_pdf_info.value = "No se ha cargado PDF de guía de instalación"
                text_pdf_info.color = "#aaaaaa"
                guias_creacion.clear()
                refrescar_guias_creacion()
                mostrar_snack("¡Campaña guardada y activada con éxito!", color="#7CFC00")
                # Recargar panel de entregas
                cargar_entregas_admin()
        except Exception as ex:
            print("ERROR GUARDANDO CAMPANA:", ex)
            mostrar_snack("Error de base de datos al guardar campaña.", color="red")
    
    # --- PANEL DE ENTREGAS ---
    entregas_col = ft.Column(spacing=10)
    detalle_entrega_col = ft.Column(spacing=15)
    
    def cargar_entregas_admin():
        entregas_col.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                # Buscar campaña activa
                cursor.execute("SELECT ID_Campana, Nombre FROM campanas WHERE Estatus = 'Activa'")
                campana = cursor.fetchone()
                if not campana:
                    entregas_col.controls.append(ft.Text("No hay ninguna campaña activa actualmente.", color="#aaaaaa", italic=True))
                    db.close()
                    page.update()
                    return
                
                id_campana = campana["ID_Campana"]
                entregas_col.controls.append(ft.Text(f"Campaña Activa: {campana['Nombre']}", size=14, color="#D8B4FE", weight="bold"))
                
                # Obtener todas las entregas de esta campaña
                query = """
                    SELECT e.ID_Entrega, e.Tienda, e.Fecha_Envio, e.Estatus, u.Nombre_Completo, u.Segmento as Segmento_Tienda
                    FROM campana_entregas_tienda e
                    JOIN usuarios u ON e.ID_Usuario = u.ID_Usuario
                    WHERE e.ID_Campana = %s
                """
                params = [id_campana]
                zona_act = active_zone_filter[0]
                if zona_act != "Todas":
                    query += " AND u.Zona = %s"
                    params.append(zona_act)
                query += " ORDER BY e.Fecha_Envio DESC"
                
                cursor.execute(query, tuple(params))
                entregas = cursor.fetchall()
                db.close()
                
                if not entregas:
                    entregas_col.controls.append(ft.Text("Ninguna tienda ha enviado fotos todavía.", color="#aaaaaa", italic=True))
                else:
                    for ent in entregas:
                        est_color = "#FF4500" if ent["Estatus"] == "Rechazado_IA" else ("#00FF7F" if ent["Estatus"] == "Visto_Bueno" else "#FFD700")
                        status_badge = ft.Container(
                            content=ft.Text(ent["Estatus"].upper().replace("_", " "), size=10, weight="bold", color="black"),
                            bgcolor=est_color,
                            padding=ft.Padding(left=10, right=10, top=5, bottom=5),
                            border_radius=4
                        )
                        
                        def make_view_details(id_ent, tienda_name):
                            return lambda e: ver_detalle_entrega_admin(id_ent, tienda_name)
                            
                        format_text = ent['Segmento_Tienda'] or "Sin Segmento"
                        entregas_col.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(f"Tienda: {ent['Tienda']} ({format_text})", weight="bold", color="white"),
                                        ft.Text(f"Enviado por: {ent['Nombre_Completo']} - {ent['Fecha_Envio']}", size=12, color="#aaaaaa")
                                    ], spacing=2, expand=True),
                                    status_badge,
                                    ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color="#00FFFF", on_click=make_view_details(ent["ID_Entrega"], ent["Tienda"]))
                                ], alignment="spaceBetween"),
                                bgcolor="#141424",
                                padding=12,
                                border_radius=8,
                                border=ft.Border.all(1, "#333333")
                            )
                        )
        except Exception as ex:
            print("ERROR CARGANDO ENTREGAS ADMIN:", ex)
            entregas_col.controls.append(ft.Text("Error al cargar las entregas.", color="red"))
        page.update()
    
    def ver_detalle_entrega_admin(id_entrega, tienda_name):
        detalle_entrega_col.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                # Obtener fotos entregadas por la tienda y su respectiva foto guia
                cursor.execute("""
                    SELECT f.ID_Foto_Tienda, f.Estatus_Auditoria, f.Resultado_IA, f.Imagen_Bytes as Foto_Tienda,
                           g.Nombre_Foto, g.Instrucciones, g.Imagen_Bytes as Foto_Guia, g.Segmento as Segmento_Foto
                    FROM campana_fotos_tienda f
                    JOIN campana_fotos_guia g ON f.ID_Foto_Guia = g.ID_Foto_Guia
                    WHERE f.ID_Entrega = %s
                """, (id_entrega,))
                fotos = cursor.fetchall()
                
                # Obtener estatus de la entrega
                cursor.execute("SELECT Estatus FROM campana_entregas_tienda WHERE ID_Entrega = %s", (id_entrega,))
                entrega_row = cursor.fetchone()
                db.close()
                
                detalle_entrega_col.controls.append(
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK, icon_color="#00FFFF", on_click=lambda e: volver_a_lista_entregas()),
                        ft.Text(f"Detalle de Entrega - {tienda_name}", size=16, color="#00FFFF", weight="bold")
                    ], spacing=10)
                )
                
                if not fotos:
                    detalle_entrega_col.controls.append(ft.Text("No hay fotos en esta entrega.", color="#aaaaaa", italic=True))
                else:
                    for f in fotos:
                        # Imagen de guia y de tienda en base64
                        import base64
                        img_guia_b64 = base64.b64encode(f["Foto_Guia"]).decode("utf-8")
                        img_tienda_b64 = base64.b64encode(f["Foto_Tienda"]).decode("utf-8")
                        
                        card_border_color = "#00FF7F" if f["Estatus_Auditoria"] == "Aprobado" else ("#FF4500" if f["Estatus_Auditoria"] == "Corregir" else "#333333")
                        
                        detail_card = ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"Sección: {f['Nombre_Foto']}", size=14, color="#D8B4FE", weight="bold"),
                                    ft.Container(
                                        content=ft.Text(f"Segmento: {f['Segmento_Foto']}", size=9, color="black", weight="bold"),
                                        bgcolor="#00FFFF",
                                        padding=3,
                                        border_radius=3
                                    )
                                ], alignment="spaceBetween"),
                                ft.Text(f"Instrucciones: {f['Instrucciones']}", size=12, color="#aaaaaa"),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("FOTO GUÍA", size=10, color="#aaaaaa", weight="bold"),
                                        ft.Image(src=f"data:image/jpeg;base64,{img_guia_b64}", width=200, height=150, fit="contain")
                                    ], horizontal_alignment="center"),
                                    ft.Column([
                                        ft.Text("FOTO TIENDA", size=10, color="#aaaaaa", weight="bold"),
                                        ft.Image(src=f"data:image/jpeg;base64,{img_tienda_b64}", width=200, height=150, fit="contain")
                                    ], horizontal_alignment="center")
                                ], spacing=20, alignment="center"),
                                ft.Divider(height=10, color="#333333"),
                                ft.Text(f"Estatus IA: {f['Estatus_Auditoria'].upper()}", color="#00FF7F" if f['Estatus_Auditoria'] == 'Aprobado' else "#FF4500", weight="bold", size=12),
                                ft.Text(f"Análisis de IA:
{f['Resultado_IA'] or 'Sin revisión.'}", size=12, color="white")
                            ], spacing=10),
                            bgcolor="#141424",
                            padding=15,
                            border_radius=8,
                            border=ft.Border.all(1.5, card_border_color)
                        )
                        detalle_entrega_col.controls.append(detail_card)
                        
                    # Botón de visto bueno
                    if entrega_row and entrega_row["Estatus"] != "Visto_Bueno":
                        def on_visto_bueno_click(e, ent_id=id_entrega, t_name=tienda_name):
                            dar_visto_bueno_entrega(ent_id, t_name)
                            
                        detalle_entrega_col.controls.append(
                            ft.Row([
                                ft.ElevatedButton(
                                    "Dar Visto Bueno Zonal 👑",
                                    icon=ft.Icons.CHECK_CIRCLE,
                                    bgcolor="#00FF7F",
                                    color="black",
                                    on_click=on_visto_bueno_click
                                )
                            ], alignment="center")
                        )
                    else:
                        detalle_entrega_col.controls.append(
                            ft.Row([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, color="#00FF7F"),
                                        ft.Text("Esta entrega tiene el Visto Bueno del Jefe Zonal", color="#00FF7F", weight="bold")
                                    ], spacing=5),
                                    padding=10,
                                    bgcolor="#112211",
                                    border_radius=8,
                                    border=ft.Border.all(1, "#00FF7F")
                                )
                            ], alignment="center")
                        )
                
                entregas_tabs.selected_index = 1 # Ir a la pestaña de entregas
                entregas_col.visible = False
                detalle_entrega_col.visible = True
        except Exception as ex:
            print("ERROR MOSTRANDO DETALLE ENTREGA ADMIN:", ex)
            detalle_entrega_col.controls.append(ft.Text("Error al cargar detalles de la entrega.", color="red"))
        page.update()
    
    def volver_a_lista_entregas():
        detalle_entrega_col.visible = False
        entregas_col.visible = True
        cargar_entregas_admin()
    
    def dar_visto_bueno_entrega(id_entrega, tienda_name):
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute("UPDATE campana_entregas_tienda SET Estatus = 'Visto_Bueno' WHERE ID_Entrega = %s", (id_entrega,))
                db.commit()
                
                # Obtener el ID_Usuario de la entrega y el Nombre de la campaña para enviar la notificación
                cursor.execute("""
                    SELECT e.ID_Usuario, c.Nombre 
                    FROM campana_entregas_tienda e
                    JOIN campanas c ON e.ID_Campana = c.ID_Campana
                    WHERE e.ID_Entrega = %s
                """, (id_entrega,))
                row_ent = cursor.fetchone()
                if row_ent:
                    id_gerente = row_ent[0]
                    camp_name = row_ent[1]
                    crear_notificacion(id_gerente, "Visto Bueno Otorgado 👑", f"Tu entrega de campaña '{camp_name}' ha recibido el visto bueno final.", "campana")
                    
                db.close()
                mostrar_snack(f"Visto Bueno otorgado para {tienda_name}.", color="#7CFC00")
                volver_a_lista_entregas()
        except Exception as ex:
            print("ERROR DANDO VISTO BUENO:", ex)
            mostrar_snack("Error al guardar estatus.", color="red")
    
    # --- CONFIGURACIÓN GEMINI KEY ---
    api_key_input = ft.TextField(
        label="Gemini API Key",
        value=GEMINI_API_KEY,
        password=True,
        can_reveal_password=True,
        border_color="#D8B4FE",
        width=450
    )
    
    def guardar_gemini_key_click(e):
        global GEMINI_API_KEY
        k = api_key_input.value.strip()
        if not k:
            mostrar_snack("Por favor ingrese una clave válida.", color="red")
            return
        if guardar_config_key("gemini_api_key", k):
            GEMINI_API_KEY = k
            mostrar_snack("API Key de Gemini guardada correctamente.", color="#7CFC00")
        else:
            mostrar_snack("Error al guardar la clave en config.json.", color="red")
    
    def depurar_fotos_viejas_click(e):
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                # Count how many would be affected
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM campana_fotos_tienda ft
                    JOIN campana_entregas_tienda et ON ft.ID_Entrega = et.ID_Entrega
                    WHERE et.Fecha_Envio < DATE_SUB(NOW(), INTERVAL 3 MONTH)
                      AND ft.Imagen_Bytes IS NOT NULL
                """)
                filas_a_depurar = cursor.fetchone()[0]
                
                if filas_a_depurar == 0:
                    mostrar_snack("No hay imágenes de más de 3 meses para depurar.", color="#00FFFF")
                    db.close()
                    return
                    
                # Perform the update
                cursor.execute("""
                    UPDATE campana_fotos_tienda ft
                    JOIN campana_entregas_tienda et ON ft.ID_Entrega = et.ID_Entrega
                    SET ft.Imagen_Bytes = NULL
                    WHERE et.Fecha_Envio < DATE_SUB(NOW(), INTERVAL 3 MONTH)
                """)
                filas_depuradas = cursor.rowcount
                
                # Optimize table
                cursor.execute("OPTIMIZE TABLE campana_fotos_tienda")
                cursor.fetchall() # Consume results of OPTIMIZE TABLE
                
                db.commit()
                db.close()
                mostrar_snack(f"Mantenimiento exitoso: Se eliminaron {filas_depuradas} fotos antiguas. Base de datos optimizada.", color="#7CFC00")
        except Exception as ex:
            print("ERROR DEPURANDO ALMACENAMIENTO:", ex)
            mostrar_snack("Error al ejecutar la depuración de base de datos.", color="red")
    
    config_key_view = ft.Column([
        ft.Text("Configuración de IA de Visión (Gemini)", size=16, color="#00FFFF", weight="bold"),
        ft.Text("La API Key se guarda localmente en el archivo config.json para autorizar las solicitudes a Gemini 1.5 Flash.", color="#aaaaaa", size=13),
        ft.Row([
            api_key_input,
            ft.ElevatedButton(
                "Guardar Clave 💾",
                bgcolor="#9D50BB",
                color="white",
                on_click=guardar_gemini_key_click
            )
        ], spacing=10),
        ft.Divider(height=15, color="#333333"),
        ft.Container(
            content=ft.Column([
                ft.Text("Mantenimiento y Almacenamiento 🧹", size=16, color="#00FFFF", weight="bold"),
                ft.Text("Depura el almacenamiento de base de datos liberando espacio ocupado por imágenes binarias de campañas con más de 3 meses de antigüedad. Se conserva la metadata y las auditorías de IA para el historial.", color="#aaaaaa", size=13),
                ft.ElevatedButton(
                    "Liberar Almacenamiento (Fotos > 3 Meses) 🧹",
                    icon=ft.Icons.CLEANING_SERVICES_ROUNDED,
                    bgcolor="#FF4500",
                    color="white",
                    on_click=depurar_fotos_viejas_click
                )
            ], spacing=10),
            padding=15,
            bgcolor="#0F0F1A",
            border_radius=8,
            border=ft.Border.all(1, "#333333")
        )
    ], spacing=10)
    
    # Evitar error de content/tabs en Tabs constructor usando TabBar y TabBarView
    entregas_tabs = ft.Tabs(
        selected_index=0,
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Crear Campaña 📸", icon=ft.Icons.ADD_A_PHOTO),
                        ft.Tab(label="Revisar Entregas 📋", icon=ft.Icons.CHECKLIST),
                        ft.Tab(label="Configuración IA ⚙", icon=ft.Icons.SETTINGS)
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        # Tab 1 content: Crear Campaña
                        ft.Column([
                            nombre_campana,
                            desc_campana,
                            ft.Row([
                                btn_cargar_pdf_guia,
                                text_pdf_info
                            ], spacing=15, vertical_alignment="center"),
                            ft.Row([
                                ft.Text("Secciones / Fotos requeridas de la Campaña", size=14, color="#D8B4FE", weight="bold"),
                                ft.ElevatedButton(
                                    "Añadir Foto Guía",
                                    icon=ft.Icons.ADD,
                                    bgcolor="#00FFFF",
                                    color="black",
                                    on_click=agregar_guia_creacion
                                )
                            ], alignment="spaceBetween", vertical_alignment="center"),
                            guias_col,
                            ft.Divider(height=15, color="#333333"),
                            ft.Row([
                                ft.ElevatedButton(
                                    "Activar y Guardar Campaña 💾",
                                    icon=ft.Icons.SAVE,
                                    bgcolor="#00FF7F",
                                    color="black",
                                    height=45,
                                    on_click=guardar_campana_click
                                )
                            ], alignment="center")
                        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True),
                        
                        # Tab 2 content: Revisar Entregas
                        ft.Column([
                            entregas_col,
                            detalle_entrega_col
                        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True),
                        
                        # Tab 3 content: Configuración IA
                        ft.Column([
                            config_key_view
                        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
                    ]
                )
            ]
        )
    )
    
    # Cargar guías iniciales y entregas
    agregar_guia_creacion(None)
    cargar_entregas_admin()
    detalle_entrega_col.visible = False
    
    return ft.Column([
        ft.Row([
            ft.Text("Fotos de Campaña — Administrador", size=24, color="#D8B4FE", weight="bold")
        ]),
        ft.Text("Define las fotos guía del mes para las exhibiciones de Sunglass Hut y audita las entregas de las tiendas.", color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        entregas_tabs
    ], expand=True, scroll=ft.ScrollMode.AUTO)