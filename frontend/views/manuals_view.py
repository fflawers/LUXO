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

def _build_manuals_view(
    _up3,
    abrir_visor_modal_global,
    conectar_db,
    obtener_pdf_assets,
    page
):
    manuals_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def cargar_manuales():
        manuals_list.controls.clear()
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT ID_Manual, Nombre_Archivo, Titulo, Version, Abierto FROM manuales ORDER BY Nombre_Archivo")
                manuales = cursor.fetchall()
                db.close()
    
                manuals_list.controls.append(ft.Text(t("manuals_db_title"), size=14, color="#00FFFF", weight="bold"))
                if not manuales:
                    manuals_list.controls.append(ft.Text(t("no_manuals"), color="#aaaaaa", size=12))
                else:
                    for m in manuales:
                        id_m = m["ID_Manual"]
                        nombre = m.get("Nombre_Archivo") or ""
                        version = m.get("Version") or ""
                        titulo = m.get("Titulo") or ""
                        abierto = m.get("Abierto", 1)
    
                        nombre_f = obtener_pdf_assets(id_m)
                        url_dl = ""
                        
                        # Dynamic icon
                        ext_m = os.path.splitext(nombre)[1].lower() if nombre else ""
                        icon_m = ft.Icons.PICTURE_AS_PDF
                        color_m = "#00FFFF"
                        if ext_m in [".xlsx", ".xls"]:
                            icon_m = ft.Icons.TABLE_CHART
                            color_m = "#7CFC00"
                        elif ext_m in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                            icon_m = ft.Icons.IMAGE
                            color_m = "#FF00FF"
                        elif ext_m in [".mp4", ".mov", ".avi"]:
                            icon_m = ft.Icons.VIDEOCAM_ROUNDED
                            color_m = "#FF6B35"
                            
                        if nombre_f:
                            import urllib.parse as _up3
                            nombre_quoted = _up3.quote(nombre_f)
                            nombre_original_quoted = _up3.quote(nombre)
                            url_dl = f"/dl?file={nombre_quoted}&original={nombre_original_quoted}"
    
                        manuals_list.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(icon_m, color=color_m),
                                        ft.Column([
                                            ft.Text(nombre, color="white", weight="bold", size=14),
                                            ft.Text(f"{t('version')}: {version} | {titulo}", color="#aaaaaa", size=11)
                                        ], spacing=3, expand=True)
                                    ], spacing=5),
                                    ft.Row([
                                        ft.ElevatedButton(
                                            t("view_pdf"),
                                            icon=ft.Icons.VISIBILITY if abierto == 1 else ft.Icons.LOCK,
                                            on_click=lambda e, s=nombre_f, d=nombre: abrir_visor_modal_global(s, d) if (s and abierto == 1) else None,
                                            bgcolor="#6E48AA" if abierto == 1 else "#222222",
                                            color="white" if abierto == 1 else "#666666",
                                            expand=True,
                                            disabled=(not nombre_f or abierto == 0)
                                        ),
                                        ft.ElevatedButton(
                                            t("download_pdf") if abierto == 1 else "🔒 Bloqueado",
                                            icon=ft.Icons.DOWNLOAD if abierto == 1 else ft.Icons.LOCK,
                                            url=url_dl if abierto == 1 else None,
                                            bgcolor="#204870" if abierto == 1 else "#222222",
                                            color="white" if abierto == 1 else "#666666",
                                            expand=True,
                                            disabled=(url_dl == "" or abierto == 0)
                                        )
                                    ], spacing=5),
                                    ft.Text(
                                        "💡 Tip: Mantén presionado 'Descargar' y selecciona 'Descargar vínculo/enlace' para guardarlo en tu teléfono.",
                                        color="#aaaaaa",
                                        size=10,
                                        italic=True
                                    )
                                ], spacing=8),
                                bgcolor="#141424",
                                padding=12,
                                border_radius=8,
                                border=ft.Border.all(1, "#333333")
                            )
                        )
        except Exception as ex:
            print("ERROR MANUALS VIEW LIST:", ex)
            manuals_list.controls.append(ft.Text("Error", color="red"))
        page.update()
        
    cargar_manuales()
    
    return ft.Column([
        ft.Row([
            ft.Text(t("manuals_title"), size=24, color="#D8B4FE", weight="bold"),
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: cargar_manuales(), icon_color="#00FFFF")
        ], alignment="spaceBetween", vertical_alignment="center"),
        ft.Text(t("manuals_desc"), color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        manuals_list
    ], expand=True)