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

def _build_tareas_gerente_view(
    check_garantias_bloqueadas,
    check_garantias_url
):
    
    bloqueada = check_garantias_bloqueadas()
    
    if bloqueada:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_ROUNDED, size=50, color="#FF4500"),
                ft.Text("Módulo de Garantías Cerrado", size=18, weight="bold", color="white"),
                ft.Text("El acceso al consolidado de garantías se encuentra temporalmente deshabilitado por el administrador.", color="#aaaaaa", text_align="center", size=12)
            ], alignment="center", horizontal_alignment="center", spacing=12),
            alignment=ft.alignment.Alignment(0, 0),
            padding=30
        )
    
    url = check_garantias_url()
    if not url:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INFO_ROUNDED, size=50, color="#D8B4FE"),
                ft.Text("Consolidado No Configurado", size=18, weight="bold", color="white"),
                ft.Text("El administrador aún no ha configurado el enlace de garantías consolidado.", color="#aaaaaa", text_align="center", size=12)
            ], alignment="center", horizontal_alignment="center", spacing=12),
            alignment=ft.alignment.Alignment(0, 0),
            padding=30
        )
    
    # Controles para abrir
    botones = [
        ft.ElevatedButton(
            "Abrir Excel Consolidado",
            icon=ft.Icons.OPEN_IN_NEW,
            bgcolor="#6E48AA",
            color="white",
            height=42,
            url=url
        )
    ]
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.VERIFIED_ROUNDED, size=22, color="#00FFFF"),
                ft.Text("Consolidación de Garantías", size=16, weight="bold", color="white")
            ], alignment="center", spacing=8, wrap=True),
            ft.Text("Accede al archivo Excel consolidado en la nube para registrar o consultar información de garantías.", color="#aaaaaa", size=11, text_align="center"),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("Opciones del Documento", size=14, weight="bold", color="#D8B4FE"),
                    ft.Text("Haz clic en el botón de abajo para editar o consultar el archivo en línea.", color="#aaaaaa", size=10.5, text_align="center"),
                    ft.Container(height=8),
                    ft.Row(botones, spacing=8, alignment="center", wrap=True)
                ], spacing=8, horizontal_alignment="center"),
                bgcolor="#0F0F1A",
                padding=15,
                border_radius=8,
                border=ft.Border.all(1, "#222222")
            )
        ], alignment="start", horizontal_alignment="center", spacing=10, scroll=ft.ScrollMode.AUTO),
        padding=12
    )