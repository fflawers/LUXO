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

def _build_modulo_tareas_gerente_view(
    check_tareas_bloqueadas,
    check_tareas_url
):
    bloqueada = check_tareas_bloqueadas()
    
    if bloqueada:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_ROUNDED, size=50, color="#FF4500"),
                ft.Text("Módulo de Tareas Cerrado", size=18, weight="bold", color="white"),
                ft.Text("El acceso al módulo de tareas se encuentra deshabilitado por el administrador.", color="#aaaaaa", text_align="center", size=12)
            ], alignment="center", horizontal_alignment="center", spacing=12),
            alignment=ft.alignment.Alignment(0, 0),
            padding=30
        )
    
    url = check_tareas_url()
    if not url:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INFO_ROUNDED, size=50, color="#D8B4FE"),
                ft.Text("Tareas No Configuradas", size=18, weight="bold", color="white"),
                ft.Text("El administrador aún no ha configurado el enlace de tareas.", color="#aaaaaa", text_align="center", size=12)
            ], alignment="center", horizontal_alignment="center", spacing=12),
            alignment=ft.alignment.Alignment(0, 0),
            padding=30
        )
    
    botones = [
        ft.ElevatedButton(
            "Abrir Documento de Tareas",
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
                ft.Icon(ft.Icons.ASSIGNMENT_ROUNDED, size=22, color="#00FFFF"),
                ft.Text("Módulo de Tareas", size=16, weight="bold", color="white")
            ], alignment="center", spacing=8, wrap=True),
            ft.Text("Accede al documento en la nube para revisar y gestionar tus tareas asignadas.", color="#aaaaaa", size=11, text_align="center"),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("Opciones del Documento", size=14, weight="bold", color="#D8B4FE"),
                    ft.Text("Haz clic en el botón para abrir el documento de tareas.", color="#aaaaaa", size=10.5, text_align="center"),
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