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

def _build_vendedores_view(
    cambiar_vista,
    conectar_db,
    enfoque_diario,
    hash_password,
    mostrar_snack,
    nom,
    page,
    pst,
    registrar_auditoria_borrado,
    user_info,
    vid
):
    is_mobile_w = (page.width < 700) if (page and page.width) else False
    vendedores_list = ft.Column(spacing=10)
    vendedor_name_input = ft.TextField(
        label="Nombre del Colaborador",
        border_color="#9D50BB",
        color="white",
        text_size=12 if is_mobile_w else 13,
        width=180 if is_mobile_w else 260
    )
    es_mx = user_info.get("usuario") == "mx204562"
    
    def on_rol_change(e):
        if es_mx:
            if puesto_vendedor_input.value == "Administrador":
                vendedor_name_input.label = "Nombre del Administrador"
                txt_tienda_num.visible = False
            else:
                vendedor_name_input.label = "Nombre de la Tienda"
                txt_tienda_num.visible = True
            page.update()
    
    puesto_vendedor_input = EmojiDropdown(
        label="Puesto / Rol",
        options=[ft.dropdown.Option("Administrador"), ft.dropdown.Option("Perfil de Tienda")] if es_mx else [
            ft.dropdown.Option("Vendedor"),
            ft.dropdown.Option("Subgerente"),
            ft.dropdown.Option("Gerente de Tienda")
        ],
        value="Perfil de Tienda" if es_mx else "Vendedor",
        border_color="#9D50BB",
        width=160 if is_mobile_w else 200,
        on_change=on_rol_change
    )
    
    txt_tienda_num = ft.TextField(label="Número de la Tienda", width=160 if is_mobile_w else 200, border_color="#9D50BB", color="white", visible=es_mx)
    txt_usuario_sys = ft.TextField(label="Usuario (Login)", width=160 if is_mobile_w else 200, border_color="#9D50BB", color="white", visible=es_mx)
    txt_pass_sys = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=160 if is_mobile_w else 200, border_color="#9D50BB", color="white", visible=es_mx)
    
    if es_mx:
        vendedor_name_input.label = "Nombre de la Tienda"
    
    def cargar_vendedores():
        vendedores_list.controls.clear()
        rows = []
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT ID_Vendedor, Nombre_Completo, Puesto, Activo, DATE_FORMAT(Fecha_Registro, '%d/%m/%Y') as fecha_f
                    FROM vendedores
                    WHERE ID_Usuario_Tienda = %s
                    ORDER BY Nombre_Completo ASC
                """, (user_info.get("id", 1),))
                rows = cursor.fetchall()
                db.close()
        except Exception as ex:
            print("Error cargar colaboradores DB:", ex)
    
        if not rows:
            t_nom = user_info.get("tienda", "VALLEJO")
            store_colabs_def = {
                "VALLEJO": [("VIVIANA", "Gerente de Tienda"), ("moises", "Subgerente"), ("diego", "Vendedor")],
                "INTERLOMAS": [("idalia", "Gerente de Tienda"), ("Viviana", "Subgerente"), ("carlos", "Vendedor")],
                "ATIZAPAN": [("FERNANDO", "Gerente de Tienda"), ("STEFANI", "Subgerente"), ("MOISES", "Vendedor")],
                "PERISUR": [("ROBERTO", "Gerente de Tienda"), ("ANA", "Subgerente"), ("LUIS", "Vendedor")],
                "LINDAVISTA": [("PATRICIA", "Gerente de Tienda"), ("JORGE", "Subgerente"), ("SARA", "Vendedor")],
                "SANTA FE": [("MAURICIO", "Gerente de Tienda"), ("ELENA", "Subgerente"), ("GABRIEL", "Vendedor")],
                "SATÉLITE": [("DANIEL", "Gerente de Tienda"), ("KAREN", "Subgerente"), ("ANDRES", "Vendedor")],
                "PACHUCA": [("OSCAR", "Gerente de Tienda"), ("VERONICA", "Subgerente"), ("MANUEL", "Vendedor")]
            }
            defaults = store_colabs_def.get(t_nom, [("VIVIANA", "Gerente de Tienda"), ("moises", "Subgerente"), ("diego", "Vendedor")])
            rows = [{"ID_Vendedor": idx+100, "Nombre_Completo": nom, "Puesto": pst, "fecha_f": "Activo"} for idx, (nom, pst) in enumerate(defaults)]
    
        for r in rows:
            v_id = r["ID_Vendedor"]
            v_name = r["Nombre_Completo"]
            puesto_nombre = r.get("Puesto") or "Vendedor"
    
            def make_delete_click(vid=v_id, name=v_name):
                def delete_click(e):
                    def confirmar_borrado(ev):
                        try:
                            u_rol = str(user_info.get("rol", "")).lower()
                            u_pue = str(user_info.get("puesto", "")).lower()
                            es_gerente = "gerente" in u_rol or "gerente" in u_pue or "admin" in u_rol
    
                            if not es_gerente:
                                page.pop_dialog()
                                mostrar_snack("⚠️ Permiso denegado: Solo el Gerente de Tienda puede eliminar a un colaborador", "red")
                                return
    
                            db_d = conectar_db()
                            if db_d:
                                cursor_d = db_d.cursor()
                                cursor_d.execute("DELETE FROM vendedores WHERE ID_Vendedor = %s", (vid,))
                                db_d.commit()
                                db_d.close()
    
                                registrar_auditoria_borrado(
                                    ejecutor_id=user_info.get("id", 0),
                                    ejecutor_nombre=user_info.get("nombre", "Gerente de Tienda"),
                                    ejecutor_rol=user_info.get("puesto") or user_info.get("rol") or "Gerente de Tienda",
                                    afectado_nombre=name,
                                    accion="BAJA_COLABORADOR",
                                    detalles="Baja de colaborador autorizada por Gerente"
                                )
    
                            page.pop_dialog()
                            mostrar_snack(f"Colaborador '{name}' eliminado 🛡️", "#FF4500")
                            cargar_vendedores()
                            try:
                                import enfoque_diario
                                enfoque_diario.sincronizar_colaboradores_db(user_info)
                            except Exception:
                                pass
                            try: page.update()
                            except Exception: pass
                        except Exception as ex_d:
                            print("Error eliminando colaborador:", ex_d)
                            mostrar_snack("Error al eliminar colaborador", "red")
                            page.pop_dialog()
    
                    confirm_dialog = ft.AlertDialog(
                        title=ft.Text("⚠️ Confirmar Baja de Personal", color="red", weight="bold"),
                        content=ft.Text(f"¿Estás seguro de que deseas dar de baja a '{name}'?", color="white"),
                        actions=[
                            ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
                            ft.TextButton("Eliminar", on_click=confirmar_borrado, style=ft.ButtonStyle(color="red"))
                        ],
                        actions_alignment="end",
                        bgcolor="#0F0F1A"
                    )
                    page.show_dialog(confirm_dialog)
                    try: page.update()
                    except Exception: pass
                return delete_click
    
            btn_delete = ft.IconButton(
                icon=ft.Icons.DELETE_ROUNDED,
                icon_color="#FF4500",
                tooltip="Eliminar Personal 🗑️",
                on_click=make_delete_click()
            )
    
            vendedores_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_PIN_ROUNDED, color="#00FFFF", size=20),
                        ft.Column([
                            ft.Text(r["Nombre_Completo"], color="white", weight="bold", size=13),
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(puesto_nombre, color="#D8B4FE", weight="bold", size=10),
                                    bgcolor="#2a1a3e",
                                    padding=ft.padding.Padding(6, 2, 6, 2),
                                    border_radius=4,
                                    border=ft.Border.all(1, "#6E48AA")
                                ),
                                ft.Text(r['fecha_f'], color="#666666", size=10)
                            ], spacing=6)
                        ], spacing=2, expand=True),
                        btn_delete
                    ], vertical_alignment="center", spacing=6),
                    bgcolor="#1a1a22",
                    padding=ft.padding.Padding(10, 8, 10, 8),
                    border_radius=10,
                    border=ft.Border.all(1, "#2a2a33")
                )
            )
    
    def registrar_vendedor_click(e):
        name = vendedor_name_input.value.strip()
        puesto_val = puesto_vendedor_input.value or ("Perfil de Tienda" if es_mx else "Vendedor")
        if not name:
            mostrar_snack("Por favor ingresa un nombre válido", "red")
            return
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor()
                if es_mx:
                    if not txt_usuario_sys.value or not txt_pass_sys.value:
                        mostrar_snack("⚠️ Debes ingresar Usuario y Contraseña", "orange")
                        db.close()
                        return
                    if puesto_val == "Perfil de Tienda" and not txt_tienda_num.value:
                        mostrar_snack("⚠️ Debes ingresar el Número de la Tienda", "orange")
                        db.close()
                        return
                        
                    hashed = hash_password(txt_pass_sys.value)
                    num_tienda = txt_tienda_num.value.strip() if puesto_val == "Perfil de Tienda" else ""
                    cursor.execute(
                        "INSERT INTO usuarios (Nombre_Completo, Usuario, Contrasena, Rol, Tienda, Zona) VALUES (%s, %s, %s, %s, %s, 'CENTRO')", 
                        (name, txt_usuario_sys.value.strip(), hashed, puesto_val, num_tienda)
                    )
                else:
                    cursor.execute("INSERT INTO vendedores (ID_Usuario_Tienda, Nombre_Completo, Puesto) VALUES (%s, %s, %s)", (user_info["id"], name, puesto_val))
                db.commit()
                db.close()
                vendedor_name_input.value = ""
                if es_mx:
                    txt_usuario_sys.value = ""
                    txt_pass_sys.value = ""
                    txt_tienda_num.value = ""
                mostrar_snack("Colaborador registrado con éxito 🎉", "#7CFC00")
                if not es_mx:
                    cargar_vendedores()
                try:
                    import enfoque_diario
                    enfoque_diario.sincronizar_colaboradores_db(user_info)
                except Exception:
                    pass
                page.update()
        except Exception as ex:
            print("Error registrar colaborador:", ex)
            mostrar_snack("Error al guardar el colaborador (el ID podría estar repetido)", "red")
    
    # =====================================================
    # LÓGICA DE GERENTE ÚNICO POR TIENDA
    # =====================================================
    gerente_actual = None   # Dict con datos del Gerente registrado (si existe)
    yo_soy_gerente = False  # True si el usuario actual ES el Gerente registrado
    puesto_libre = False    # True si no hay Gerente aún en esta tienda
    
    try:
        db_g = conectar_db()
        if db_g:
            cur_g = db_g.cursor(dictionary=True)
            cur_g.execute("""
                SELECT ID_Usuario, Nombre_Completo, Rol, Usuario
                FROM usuarios
                WHERE Tienda = %s
                  AND (LOWER(Rol) LIKE '%gerente%' OR LOWER(Rol) = 'gerente de tienda')
                  AND ID_Usuario != %s
                LIMIT 1
            """, (user_info.get("tienda", ""), user_info.get("id", 0)))
            gerente_actual = cur_g.fetchone()
    
            cur_g.execute("""
                SELECT Rol FROM usuarios WHERE ID_Usuario = %s
            """, (user_info.get("id", 0),))
            mi_rol_row = cur_g.fetchone()
            mi_rol_actual = str(mi_rol_row.get("Rol", "") if mi_rol_row else "").lower()
            yo_soy_gerente = "gerente" in mi_rol_actual
    
            db_g.close()
            puesto_libre = (gerente_actual is None) and (not yo_soy_gerente)
    except Exception as ex_g:
        print("Error consultando Gerente de tienda:", ex_g)
    
    def registrarme_como_gerente(e):
        try:
            db_rg = conectar_db()
            if db_rg:
                cur_rg = db_rg.cursor(dictionary=True)
                cur_rg.execute("""
                    SELECT COUNT(*) as total FROM usuarios
                    WHERE Tienda = %s
                      AND (LOWER(Rol) LIKE '%gerente%' OR LOWER(Rol) = 'gerente de tienda')
                """, (user_info.get("tienda", ""),))
                resultado = cur_rg.fetchone()
                if resultado and resultado["total"] > 0:
                    mostrar_snack("⚠️ El puesto de Gerente ya fue tomado por otro usuario.", "#FF8C00")
                    db_rg.close()
                    cambiar_vista("vendedores")
                    return
                cur_rg.execute("""
                    UPDATE usuarios SET Rol = 'Gerente de Tienda'
                    WHERE ID_Usuario = %s
                """, (user_info.get("id", 0),))
                db_rg.commit()
                db_rg.close()
                user_info["rol"] = "Gerente de Tienda"
                user_info["puesto"] = "Gerente de Tienda"
                mostrar_snack("🏅 ¡Felicidades! Ahora eres el Gerente de esta tienda.", "#7CFC00")
                cambiar_vista("vendedores")
        except Exception as ex_rg:
            print("Error registrando como Gerente:", ex_rg)
            mostrar_snack("Error al registrar el rol de Gerente.", "red")
    
    u_rol_vendedores = str(user_info.get("rol", "")).lower()
    es_admin_global = "admin" in u_rol_vendedores
    
    if puesto_libre and not es_admin_global:
        banner_gerente = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WORKSPACE_PREMIUM_ROUNDED, color="#FFD700", size=22),
                    ft.Text("Puesto de Gerente de Tienda Disponible", color="#FFD700", size=14, weight="bold"),
                ], spacing=8),
                ft.Text(
                    "No hay un Gerente registrado en esta tienda. Si eres el responsable de este negocio, puedes tomar el puesto.",
                    color="#aaaaaa", size=12
                ),
                ft.Container(height=6),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.BADGE_ROUNDED, size=18, color="white"),
                        ft.Text("  🏅 Registrarme como Gerente de esta Tienda", weight="bold", color="white")
                    ], spacing=6),
                    on_click=registrarme_como_gerente,
                    bgcolor="#7B2D8B",
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ], spacing=6),
            bgcolor="#1a0f00",
            border=ft.Border.all(1, "#FFD700"),
            border_radius=10,
            padding=ft.padding.Padding(14, 12, 14, 12)
        )
    else:
        banner_gerente = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PEOPLE_ROUNDED, color="#00FFFF", size=18),
                ft.Text(
                    "👥 Gestión de Personal Habilitada: Puedes registrar y gestionar colaboradores de la tienda.",
                    color="#00FFFF", size=11 if is_mobile_w else 12, weight="bold"
                )
            ], spacing=8, wrap=True),
            bgcolor="#0d2a2a",
            border=ft.Border.all(1, "#00FFFF"),
            border_radius=8,
            padding=ft.padding.Padding(12, 8, 12, 8)
        )
    
    # Botón Registrar + compacto (tamaño estándar)
    btn_agregar = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.ADD_ROUNDED, size=16, color="white"),
            ft.Text("Registrar ➕", weight="bold", color="white")
        ], spacing=6, tight=True),
        on_click=registrar_vendedor_click,
        bgcolor="#6E48AA",
        color="white",
        width=130 if is_mobile_w else 150,
        height=42,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    
    cargar_vendedores()
    
    form_section = ft.Row([
        vendedor_name_input,
        txt_tienda_num,
        txt_usuario_sys,
        txt_pass_sys,
        puesto_vendedor_input,
        btn_agregar
    ], spacing=10, vertical_alignment="center", wrap=True)
    
    return ft.Column([
        ft.Text("Configuración de Tienda 👥", size=20, color="#D8B4FE", weight="bold"),
        ft.Text(
            "Registra y gestiona a los colaboradores de la tienda.",
            color="#aaaaaa", size=12
        ),
        ft.Divider(height=10, color="#333333"),
        banner_gerente,
        ft.Container(height=6),
        form_section,
        ft.Container(height=10),
        ft.Text("Lista de Personal Activo:", color="#D8B4FE", size=14, weight="bold"),
        vendedores_list
    ], scroll=ft.ScrollMode.AUTO)