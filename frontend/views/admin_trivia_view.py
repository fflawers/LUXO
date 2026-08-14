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

def _build_admin_trivia_view(
    conectar_db,
    es_admin,
    mostrar_snack,
    page,
    preg_data
):
    
    """Vista de admin para gestionar preguntas del Reto del Día."""
    if not es_admin():
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK, color="red", size=48),
                ft.Text("Acceso Restringido ⚠️", size=20, color="red", weight="bold"),
                ft.Text("Esta sección de gestión de preguntas es exclusiva para Administradores.", color="#aaaaaa", size=14)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True
        )
    
    lista_preguntas_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
    
    # --- Formulario de nueva pregunta ---
    tf_pregunta = ft.TextField(
        label="Pregunta", multiline=True, min_lines=2, max_lines=4,
        border_color="#9D50BB", color="white", expand=True,
        label_style=ft.TextStyle(color="#aaaaaa", size=11)
    )
    tf_opcion_a = ft.TextField(label="Opci\u00f3n A", border_color="#9D50BB", color="white", expand=True,
                               label_style=ft.TextStyle(color="#aaaaaa", size=11))
    tf_opcion_b = ft.TextField(label="Opci\u00f3n B", border_color="#9D50BB", color="white", expand=True,
                               label_style=ft.TextStyle(color="#aaaaaa", size=11))
    tf_opcion_c = ft.TextField(label="Opci\u00f3n C", border_color="#9D50BB", color="white", expand=True,
                               label_style=ft.TextStyle(color="#aaaaaa", size=11))
    tf_opcion_d = ft.TextField(label="Opci\u00f3n D", border_color="#9D50BB", color="white", expand=True,
                               label_style=ft.TextStyle(color="#aaaaaa", size=11))
    tf_explicacion = ft.TextField(
        label="Explicaci\u00f3n (opcional)", multiline=True, min_lines=2, max_lines=3,
        border_color="#9D50BB", color="white", expand=True,
        label_style=ft.TextStyle(color="#aaaaaa", size=11)
    )
    dd_correcta = ft.Dropdown(
        label="Respuesta Correcta",
        border_color="#9D50BB", color="white",
        label_style=ft.TextStyle(color="#aaaaaa", size=11),
        options=[
            ft.dropdown.Option("A", "A"),
            ft.dropdown.Option("B", "B"),
            ft.dropdown.Option("C", "C"),
            ft.dropdown.Option("D", "D"),
        ],
        width=150
    )
    dd_dificultad = ft.Dropdown(
        label="Dificultad",
        border_color="#9D50BB", color="white", value="Fácil",
        label_style=ft.TextStyle(color="#aaaaaa", size=11),
        options=[
            ft.dropdown.Option("Fácil", "Fácil ⭐"),
            ft.dropdown.Option("Difícil", "Difícil 🔥"),
        ],
        width=150
    )
    
    def cargar_lista_preguntas():
        lista_preguntas_col.controls.clear()
        try:
            db = conectar_db()
            if db:
                cur = db.cursor(dictionary=True)
                cur.execute("SELECT * FROM reto_preguntas ORDER BY Dificultad, ID_Pregunta")
                rows = cur.fetchall()
                db.close()
    
                if not rows:
                    lista_preguntas_col.controls.append(
                        ft.Text("No hay preguntas registradas.", color="#aaaaaa", italic=True, size=12)
                    )
                    return
    
                for row in rows:
                    diff_color = "#00FF7F" if row["Dificultad"] == "Fácil" else "#FF6B6B"
                    id_p = row["ID_Pregunta"]
    
                    def make_edit(preg_data=row):
                        def do_edit(e):
                            pid = preg_data["ID_Pregunta"]
                            edit_tf_pregunta = ft.TextField(
                                label="Pregunta",
                                value=preg_data["Pregunta"],
                                multiline=True,
                                max_lines=3,
                                border_color="#9D50BB",
                                color="white",
                                text_size=11,
                                label_style=ft.TextStyle(color="#aaaaaa", size=11)
                            )
                            edit_tf_op_a = ft.TextField(label="Opción A", value=preg_data["Opcion_A"], border_color="#333333", color="white", text_size=11, label_style=ft.TextStyle(color="#aaaaaa", size=10), expand=True)
                            edit_tf_op_b = ft.TextField(label="Opción B", value=preg_data["Opcion_B"], border_color="#333333", color="white", text_size=11, label_style=ft.TextStyle(color="#aaaaaa", size=10), expand=True)
                            edit_tf_op_c = ft.TextField(label="Opción C", value=preg_data["Opcion_C"], border_color="#333333", color="white", text_size=11, label_style=ft.TextStyle(color="#aaaaaa", size=10), expand=True)
                            edit_tf_op_d = ft.TextField(label="Opción D", value=preg_data["Opcion_D"], border_color="#333333", color="white", text_size=11, label_style=ft.TextStyle(color="#aaaaaa", size=10), expand=True)
    
                            edit_dd_correcta = ft.Dropdown(
                                label="Respuesta Correcta",
                                value=preg_data["Respuesta_Correcta"],
                                border_color="#9D50BB",
                                color="white",
                                text_size=11,
                                label_style=ft.TextStyle(color="#aaaaaa", size=10),
                                options=[
                                    ft.dropdown.Option("A", "Opción A"),
                                    ft.dropdown.Option("B", "Opción B"),
                                    ft.dropdown.Option("C", "Opción C"),
                                    ft.dropdown.Option("D", "Opción D"),
                                ],
                                width=150
                            )
                            edit_dd_dificultad = ft.Dropdown(
                                label="Dificultad",
                                value=preg_data.get("Dificultad", "Fácil"),
                                border_color="#9D50BB",
                                color="white",
                                text_size=11,
                                label_style=ft.TextStyle(color="#aaaaaa", size=10),
                                options=[
                                    ft.dropdown.Option("Fácil", "Fácil ⭐"),
                                    ft.dropdown.Option("Difícil", "Difícil 🔥"),
                                ],
                                width=150
                            )
                            edit_tf_explicacion = ft.TextField(
                                label="Explicación o Justificación",
                                value=preg_data.get("Explicacion") or "",
                                multiline=True,
                                max_lines=2,
                                border_color="#333333",
                                color="white",
                                text_size=11,
                                label_style=ft.TextStyle(color="#aaaaaa", size=10)
                            )
    
                            def guardar_edicion_click(ev):
                                n_pregunta = edit_tf_pregunta.value.strip()
                                n_op_a = edit_tf_op_a.value.strip()
                                n_op_b = edit_tf_op_b.value.strip()
                                n_op_c = edit_tf_op_c.value.strip()
                                n_op_d = edit_tf_op_d.value.strip()
                                n_correcta = edit_dd_correcta.value
                                n_dificultad = edit_dd_dificultad.value or "Fácil"
                                n_explicacion = edit_tf_explicacion.value.strip() or None
    
                                if not n_pregunta or not n_op_a or not n_op_b or not n_op_c or not n_op_d or not n_correcta:
                                    mostrar_snack("Campos obligatorios incompletos.", color="red")
                                    return
    
                                try:
                                    db_ed = conectar_db()
                                    if db_ed:
                                        cur_ed = db_ed.cursor()
                                        cur_ed.execute("""
                                            UPDATE reto_preguntas 
                                            SET Pregunta = %s, Opcion_A = %s, Opcion_B = %s, Opcion_C = %s, Opcion_D = %s, Respuesta_Correcta = %s, Dificultad = %s, Explicacion = %s 
                                            WHERE ID_Pregunta = %s
                                        """, (n_pregunta, n_op_a, n_op_b, n_op_c, n_op_d, n_correcta, n_dificultad, n_explicacion, pid))
                                        db_ed.commit()
                                        db_ed.close()
    
                                    page.pop_dialog()
                                    mostrar_snack(f"✅ Pregunta #{pid} actualizada correctamente.", color="#7CFC00")
                                    cargar_lista_preguntas()
                                    try: page.update()
                                    except Exception: pass
                                except Exception as ex_ed:
                                    mostrar_snack(f"Error al actualizar: {ex_ed}", color="red")
    
                            dlg_edit = ft.AlertDialog(
                                title=ft.Text(f"Editar Pregunta #{pid} ✏️", color="white", weight="bold", size=15),
                                content=ft.Container(
                                    content=ft.Column([
                                        edit_tf_pregunta,
                                        ft.Row([edit_tf_op_a, edit_tf_op_b], spacing=6),
                                        ft.Row([edit_tf_op_c, edit_tf_op_d], spacing=6),
                                        ft.Row([edit_dd_correcta, edit_dd_dificultad], spacing=6, wrap=True),
                                        edit_tf_explicacion
                                    ], spacing=8, scroll=ft.ScrollMode.AUTO),
                                    width=450,
                                    height=400
                                ),
                                bgcolor="#0F0F1A",
                                actions=[
                                    ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
                                    ft.ElevatedButton("Guardar Cambios", on_click=guardar_edicion_click, bgcolor="#6E48AA", color="white")
                                ],
                                actions_alignment="end"
                            )
                            page.show_dialog(dlg_edit)
                            page.update()
    
                        return do_edit
    
                    def make_delete(pid=id_p, pregunta=row["Pregunta"][:40]):
                        def do_delete(e):
                            def confirmar(ev):
                                page.pop_dialog()
                                try:
                                    db2 = conectar_db()
                                    if db2:
                                        cur2 = db2.cursor()
                                        cur2.execute("DELETE FROM reto_preguntas WHERE ID_Pregunta = %s", (pid,))
                                        db2.commit()
                                        db2.close()
                                    mostrar_snack(f"Pregunta #{pid} eliminada.", color="#7CFC00")
                                    cargar_lista_preguntas()
                                    try:
                                        page.update()
                                    except Exception:
                                        pass
                                except Exception as ex:
                                    mostrar_snack(f"Error al eliminar: {ex}", color="red")
    
                            dlg = ft.AlertDialog(
                                title=ft.Text("¿Eliminar pregunta?", color="white"),
                                content=ft.Text(f'"{pregunta}..."', color="#aaaaaa", size=12),
                                bgcolor="#1e1e1e",
                                actions=[
                                    ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
                                    ft.TextButton("Eliminar", on_click=confirmar,
                                                  style=ft.ButtonStyle(color="#FF4500")),
                                ],
                                actions_alignment="end"
                            )
                            page.show_dialog(dlg)
                        return do_delete
    
                    card = ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(row["Dificultad"], size=10, color="black", weight="bold"),
                                        bgcolor=diff_color, border_radius=4, padding=ft.Padding(5, 2, 5, 2)
                                    ),
                                    ft.Text(f"#{row['ID_Pregunta']}", color="#666666", size=10),
                                ], spacing=6),
                                ft.Text(row["Pregunta"][:80] + ("..." if len(row["Pregunta"]) > 80 else ""),
                                        color="white", size=12, weight="bold"),
                                ft.Text(
                                    f"A:{row['Opcion_A'][:25]}  B:{row['Opcion_B'][:25]}  C:{row['Opcion_C'][:25]}  D:{row['Opcion_D'][:25]}",
                                    color="#888888", size=10
                                ),
                                ft.Text(f"✔ Correcta: {row['Respuesta_Correcta']}", color="#00FF7F", size=10),
                            ], expand=True, spacing=4),
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_ROUNDED,
                                    icon_color="#00FFFF",
                                    tooltip="Editar pregunta",
                                    on_click=make_edit()
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_ROUNDED,
                                    icon_color="#FF4500",
                                    tooltip="Eliminar pregunta",
                                    on_click=make_delete()
                                )
                            ], spacing=2)
                        ], alignment="spaceBetween", vertical_alignment="center"),
                        bgcolor="#1a1a1a",
                        border_radius=8,
                        padding=10,
                        border=ft.Border.all(1, "#333333")
                    )
                    lista_preguntas_col.controls.append(card)
        except Exception as ex:
            print("Error cargando preguntas admin:", ex)
            lista_preguntas_col.controls.append(
                ft.Text(f"Error: {ex}", color="red", size=11)
            )
        try:
            page.update()
        except Exception:
            pass
    
    def agregar_pregunta_click(e):
        pregunta = tf_pregunta.value.strip()
        op_a = tf_opcion_a.value.strip()
        op_b = tf_opcion_b.value.strip()
        op_c = tf_opcion_c.value.strip()
        op_d = tf_opcion_d.value.strip()
        correcta = dd_correcta.value
        dificultad = dd_dificultad.value or "Fácil"
        explicacion = tf_explicacion.value.strip() or None
    
        if not pregunta or not op_a or not op_b or not op_c or not op_d or not correcta:
            mostrar_snack("Por favor completa todos los campos obligatorios.", color="red")
            return
    
        try:
            db = conectar_db()
            if db:
                cur = db.cursor()
                cur.execute("""
                    INSERT INTO reto_preguntas 
                    (Pregunta, Opcion_A, Opcion_B, Opcion_C, Opcion_D, Respuesta_Correcta, Explicacion, Dificultad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (pregunta, op_a, op_b, op_c, op_d, correcta, explicacion, dificultad))
                db.commit()
                db.close()
    
            # Limpiar formulario
            tf_pregunta.value = ""
            tf_opcion_a.value = ""
            tf_opcion_b.value = ""
            tf_opcion_c.value = ""
            tf_opcion_d.value = ""
            tf_explicacion.value = ""
            dd_correcta.value = None
            dd_dificultad.value = "Fácil"
    
            mostrar_snack("✅ Pregunta agregada exitosamente.", color="#7CFC00")
            cargar_lista_preguntas()
            try:
                page.update()
            except Exception:
                pass
        except Exception as ex:
            mostrar_snack(f"Error al guardar: {ex}", color="red")
    
    cargar_lista_preguntas()
    
    try:
        db_count = conectar_db()
        total_preguntas = 0
        if db_count:
            cur_c = db_count.cursor()
            cur_c.execute("SELECT COUNT(*) FROM reto_preguntas")
            total_preguntas = cur_c.fetchone()[0]
            db_count.close()
    except Exception:
        total_preguntas = 0
    
    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.QUIZ_ROUNDED, color="#FFD700", size=28),
            ft.Text("Gestionar Trivia - Reto del Día 🧠", size=22, color="#D8B4FE", weight="bold"),
        ], spacing=10),
        ft.Text("Agrega nuevas preguntas al banco de trivia. Los usuarios verán 5 preguntas aleatorias cada vez que jueguen.",
                color="#aaaaaa", size=13),
        ft.Row([
            ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, color="#00FFFF", size=16),
            ft.Text(f"Total de preguntas en el banco: {total_preguntas}", color="#00FFFF", size=13, weight="bold"),
        ], spacing=6),
        ft.Divider(height=15, color="#333333"),
    
        # --- Formulario de nueva pregunta ---
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE_ROUNDED, color="#9D50BB", size=18),
                    ft.Text("Agregar Nueva Pregunta", color="#D8B4FE", size=15, weight="bold"),
                ], spacing=8),
                tf_pregunta,
                ft.Row([tf_opcion_a, tf_opcion_b], spacing=10),
                ft.Row([tf_opcion_c, tf_opcion_d], spacing=10),
                tf_explicacion,
                ft.Row([
                    dd_correcta,
                    dd_dificultad,
                    ft.ElevatedButton(
                        "Guardar Pregunta ➕",
                        bgcolor="#9D50BB",
                        color="white",
                        height=40,
                        on_click=agregar_pregunta_click
                    )
                ], spacing=15, wrap=True)
            ], spacing=10),
            bgcolor="#0F0F1A",
            padding=18,
            border_radius=12,
            border=ft.Border.all(1, "#333333")
        ),
    
        ft.Container(height=15),
    
        # --- Lista de preguntas existentes ---
        ft.Row([
            ft.Icon(ft.Icons.LIST_ALT_ROUNDED, color="#FFD700", size=18),
            ft.Text("Preguntas en el Banco", color="#FFD700", size=14, weight="bold"),
            ft.TextButton(
                content=ft.Row([ft.Icon(ft.Icons.REFRESH_ROUNDED, size=14, color="#00FFFF"),
                                ft.Text("Actualizar", color="#00FFFF", size=12)], spacing=4),
                on_click=lambda e: (cargar_lista_preguntas(), page.update())
            )
        ], spacing=10),
    
        ft.Container(
            content=lista_preguntas_col,
            expand=True
        )
    ], scroll=ft.ScrollMode.AUTO, expand=True)