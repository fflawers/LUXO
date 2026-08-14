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

def _build_historial_view(
    chat_display,
    conectar_db,
    historial_sesion,
    mostrar_snack,
    page,
    user_info
):
    historial_list = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def cargar_lista_historial():
        historial_list.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT Pregunta_Usuario, Respuesta_IA, Fecha_Hora 
                    FROM historial_conversaciones 
                    WHERE ID_Usuario = %s 
                    ORDER BY Fecha_Hora DESC 
                    LIMIT 30
                """, (user_info["id"],))
                historial = cursor.fetchall()
                db.close()
                
                if not historial:
                    historial_list.controls.append(
                        ft.Container(
                            content=ft.Text("No tienes consultas anteriores registradas.", color="#aaaaaa", size=14),
                            alignment=ft.alignment.Alignment(0, 0),
                            expand=True
                        )
                    )
                else:
                    for row in historial:
                        fecha = row["Fecha_Hora"].strftime("%d/%m/%Y %H:%M") if row["Fecha_Hora"] else ""
                        historial_list.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(f"📅 {fecha}", color="#aaaaaa", size=11),
                                    ft.Text(f"💬 Pregunta: {row['Pregunta_Usuario']}", color="white", weight="bold"),
                                    ft.Text(f"🤖 Respuesta: {row['Respuesta_IA']}", color="#D8B4FE"),
                                ], spacing=4),
                                bgcolor="#141424",
                                padding=15,
                                border_radius=8,
                                border=ft.Border.all(1, "#333333")
                            )
                        )
        except Exception as ex:
            print("ERROR HISTORIAL VIEW:", ex)
            historial_list.controls.append(ft.Text("Error al cargar el historial.", color="red"))
        page.update()
        
    cargar_lista_historial()
    
    def confirmar_borrado_historial(e):
        def on_confirmar(ev):
            try:
                db = conectar_db()
                if db:
                    cursor = db.cursor()
                    cursor.execute("""
                        DELETE FROM pendientes_actualizacion 
                        WHERE ID_Conversacion IN (
                            SELECT ID_Conversacion FROM historial_conversaciones WHERE ID_Usuario = %s
                        )
                    """, (user_info["id"],))
                    cursor.execute("DELETE FROM historial_conversaciones WHERE ID_Usuario = %s", (user_info["id"],))
                    db.commit()
                    db.close()
                    mostrar_snack("Historial borrado correctamente.")
                    cargar_lista_historial()
                    chat_display.controls.clear()
                    historial_sesion.clear()
                    page.pop_dialog()
                    page.update()
            except Exception as ex:
                print("ERROR BORRAR HISTORIAL:", ex)
                mostrar_snack("Error al borrar el historial.", color="red")
        
        def on_cancelar(ev):
            page.pop_dialog()
            
        dialog_confirm = ft.AlertDialog(
            title=ft.Text("Confirmar Borrado", color="#FF4500", weight="bold"),
            content=ft.Text("¿Seguro que deseas borrar todo tu historial de conversaciones? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=on_cancelar),
                ft.ElevatedButton("Borrar Todo", on_click=on_confirmar, bgcolor="#FF4500", color="white")
            ],
            actions_alignment="end",
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dialog_confirm)
    
    btn_clear = ft.Container(
        content=ft.Row([
            ft.Text("🗑️", size=14),
            ft.Text("Borrar Historial", color="white", weight="bold", size=12)
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#FF4500",
        padding=ft.padding.Padding(16, 10, 16, 10),
        border_radius=20,
        on_click=confirmar_borrado_historial,
        ink=True
    )
    
    return ft.SelectionArea(
        content=ft.Column([
            ft.Row([
                ft.Text("Historial de Consultas", size=24, color="#D8B4FE", weight="bold"),
                btn_clear
            ], alignment="spaceBetween", vertical_alignment="center"),
            ft.Divider(height=20, color="#333333"),
            historial_list
        ], expand=True)
    )