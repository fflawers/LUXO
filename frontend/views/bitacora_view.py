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

def _build_bitacora_view(
    ASSETS_PATH,
    conectar_db,
    f_temp,
    mostrar_snack,
    page
):
    """Vista de Bitácora de Seguridad exclusiva para Administradores."""
    rows_container = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
    status_text = ft.Text("Cargando registros...", color="#aaaaaa", size=13, italic=True)
    
    def cargar_bitacora():
        rows_container.controls.clear()
        try:
            db_bit = conectar_db()
            if not db_bit:
                status_text.value = "Error de conexión a MySQL."
                page.update()
                return
            cur_bit = db_bit.cursor(dictionary=True)
            cur_bit.execute("""
                SELECT Nombre_Usuario, Empleado_Identificado, IP_Acceso, Dispositivo,
                       DATE_FORMAT(Fecha_Hora, '%d/%m/%Y %H:%i:%s') as Fecha_Hora
                FROM bitacora_sesiones_biometricas
                ORDER BY Fecha_Hora DESC
                LIMIT 200
            """)
            registros = cur_bit.fetchall()
            db_bit.close()
    
            if not registros:
                status_text.value = "No hay inicios de sesión registrados aún."
                page.update()
                return
    
            status_text.value = f"Mostrando los últimos {len(registros)} ingresos de seguridad:"
    
            for r in registros:
                nombre_emp = r.get("Empleado_Identificado", "") or r.get("Nombre_Usuario", "")
                ip_val = r.get("IP_Acceso", "127.0.0.1")
                disp_val = r.get("Dispositivo", "Localhost, Local / Desarrollo")
                if not disp_val or disp_val == "Navegador Web":
                    disp_val = "Localhost, Local / Desarrollo"
                fecha_val = r.get("Fecha_Hora", "")
    
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"📅 {fecha_val}", color="#aaaaaa", size=11),
                            ft.Text(f"👤 {nombre_emp}", color="white", weight="bold"),
                        ], alignment="spaceBetween"),
                        ft.Row([
                            ft.Text(f"🌐 IP: {ip_val}", color="#00FFFF", size=12),
                            ft.Text(f"📍 {disp_val}", color="#D8B4FE", size=12),
                        ], alignment="spaceBetween"),
                    ], spacing=4),
                    bgcolor="#141424",
                    padding=15,
                    border_radius=8,
                    border=ft.Border.all(1, "#333333")
                )
                rows_container.controls.append(card)
            page.update()
    
            # Pre-generar el archivo CSV de la bitácora para descarga instantánea
            try:
                temp_dir = os.path.join(ASSETS_PATH, "temp_pdfs")
                os.makedirs(temp_dir, exist_ok=True)
                filepath_temp = os.path.join(temp_dir, "Bitacora_Seguridad.csv")
                import csv
                with open(filepath_temp, "w", encoding="utf-8-sig", newline="") as f_temp:
                    writer = csv.writer(f_temp)
                    writer.writerow(["Fecha y Hora", "Empleado / Usuario", "Cuenta de Usuario", "IP de Acceso", "Dispositivo"])
                    for r in registros:
                        writer.writerow([
                            r.get("Fecha_Hora", ""),
                            r.get("Empleado_Identificado", ""),
                            r.get("Nombre_Usuario", ""),
                            r.get("IP_Acceso", "127.0.0.1"),
                            r.get("Dispositivo", "Navegador Web")
                        ])
            except Exception as ex_pre:
                print("Error pre-generando CSV:", ex_pre)
    
        except Exception as ex_bit:
            status_text.value = f"Error al cargar bitácora: {ex_bit}"
            page.update()
    
    def descargar_excel_bitacora(e=None):
        try:
            db_exp = conectar_db()
            if not db_exp:
                mostrar_snack("Error al conectar a la base de datos", color="red")
                return
            cur_exp = db_exp.cursor(dictionary=True)
            cur_exp.execute("""
                SELECT DATE_FORMAT(Fecha_Hora, '%d/%m/%Y %H:%i:%s') as Fecha_Hora,
                       Empleado_Identificado, Nombre_Usuario, IP_Acceso, Dispositivo
                FROM bitacora_sesiones_biometricas
                ORDER BY Fecha_Hora DESC
            """)
            filas = cur_exp.fetchall()
            db_exp.close()
    
            if not filas:
                mostrar_snack("No hay registros en la bitácora para exportar", color="orange")
                return
    
            import csv
            from datetime import datetime
    
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "Bitacora_Seguridad.csv"
            filename_user = f"Bitacora_Seguridad_{timestamp_str}.csv"
    
            temp_dir = os.path.join(ASSETS_PATH, "temp_pdfs")
            os.makedirs(temp_dir, exist_ok=True)
            filepath_temp = os.path.join(temp_dir, filename)
    
            downloads_user_dir = os.path.expanduser("~/Downloads")
            filepath_user = os.path.join(downloads_user_dir, filename_user)
    
            with open(filepath_temp, "w", encoding="utf-8-sig", newline="") as f_temp:
                writer = csv.writer(f_temp)
                writer.writerow(["Fecha y Hora", "Empleado / Usuario", "Cuenta de Usuario", "IP de Acceso", "Dispositivo"])
                for r in filas:
                    writer.writerow([
                        r.get("Fecha_Hora", ""),
                        r.get("Empleado_Identificado", ""),
                        r.get("Nombre_Usuario", ""),
                        r.get("IP_Acceso", "127.0.0.1"),
                        r.get("Dispositivo", "Navegador Web")
                    ])
    
            import shutil
            shutil.copy2(filepath_temp, filepath_user)
    
            mostrar_snack(f"✅ Archivo exportado ({len(filas)} registros totales) en tu carpeta de Descargas", color="#7CFC00")
    
        except Exception as ex_exp:
            print("ERROR EXPORTANDO EXCEL BITÁCORA:", ex_exp)
            mostrar_snack(f"Error al generar Excel: {ex_exp}", color="red")
    
    import threading
    threading.Thread(target=cargar_bitacora, daemon=True).start()
    
    url_dl = "/dl?file=Bitacora_Seguridad.csv&original=Bitacora_Seguridad.csv"
    
    btn_descargar_excel = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.TABLE_CHART_ROUNDED, color="white", size=18),
            ft.Text("Descargar Excel", color="white", weight="bold")
        ], spacing=6),
        bgcolor="#008080",
        color="white",
        url=url_dl,
        on_click=descargar_excel_bitacora,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
    )
    
    is_mobile = (page.width < 800) if (page and page.width) else False
    
    header_top = ft.Column([
        ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.SECURITY_ROUNDED, color="#00FFAA", size=22),
                ft.Text("Bitácora de Seguridad 🛡️", size=17, color="#00FFAA", weight="bold"),
            ], spacing=6),
            ft.IconButton(icon=ft.Icons.REFRESH_ROUNDED, icon_color="#00FFAA", tooltip="Actualizar bitácora",
                          on_click=lambda e: threading.Thread(target=cargar_bitacora, daemon=True).start())
        ], alignment="spaceBetween", vertical_alignment="center"),
        btn_descargar_excel
    ], spacing=8) if is_mobile else ft.Row([
        ft.Icon(ft.Icons.SECURITY_ROUNDED, color="#00FFAA", size=26),
        ft.Text("Bitácora de Seguridad 🛡️", size=22, color="#00FFAA", weight="bold"),
        ft.Container(expand=True),
        btn_descargar_excel,
        ft.IconButton(icon=ft.Icons.REFRESH_ROUNDED, icon_color="#00FFAA", tooltip="Actualizar bitácora",
                      on_click=lambda e: threading.Thread(target=cargar_bitacora, daemon=True).start())
    ], vertical_alignment="center")
    
    return ft.Column([
        header_top,
        ft.Text("Registro de todos los inicios de sesión. Visible solo para Administradores.", color="#aaaaaa", size=12),
        ft.Divider(height=12, color="#333333"),
        status_text,
        ft.Container(height=4),
        rows_container
    ], expand=True)