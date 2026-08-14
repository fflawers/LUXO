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

def _build_dashboard_view(
    b_i,
    build_admin_checklist_tab,
    build_manuals_tab,
    build_missing_questions_tab,
    build_stats_tab,
    build_suggestions_tab,
    build_support_tickets_tab,
    build_tareas_admin_tab,
    builder_fn,
    conectar_db,
    dashboard_tab_index,
    fn,
    icon_name,
    label,
    mostrar_snack,
    operacion_tiendas,
    page,
    tr,
    user_info
):
    is_mobile = (page.width < 800) if (page and page.width) else False
    tab_defs = [
        ("Estadísticas", ft.Icons.BAR_CHART, build_stats_tab),
        ("Preguntas sin Contestar", ft.Icons.QUESTION_MARK_ROUNDED, build_missing_questions_tab),
        ("Gestión de Manuales", ft.Icons.FOLDER_OPEN_ROUNDED, build_manuals_tab),
        ("Sugerencias", ft.Icons.LIGHTBULB_ROUNDED, build_suggestions_tab),
        ("Soporte 🎫", ft.Icons.CONFIRMATION_NUMBER_ROUNDED, build_support_tickets_tab),
        ("Editar Checklists 📋", ft.Icons.CHECKLIST_ROUNDED, build_admin_checklist_tab),
        ("Tareas Consolidadas 📊", ft.Icons.ASSIGNMENT, build_tareas_admin_tab),
        ("Aperturas y Cierres 🔑", ft.Icons.KEY_ROUNDED, lambda: operacion_tiendas.build_aperturas_cierres_tab(page, user_info, conectar_db, mostrar_snack, tr)),
    ]
    
    
    curr_idx = dashboard_tab_index[0]
    if curr_idx < 0 or curr_idx >= len(tab_defs):
        curr_idx = 0
        dashboard_tab_index[0] = 0
    
    content_box = ft.Container(content=tab_defs[curr_idx][2](), expand=True)
    
    tab_buttons = []
    for idx, (label, icon_name, builder_fn) in enumerate(tab_defs):
        def make_click(i, fn):
            def click(e):
                dashboard_tab_index[0] = i
                content_box.content = fn()
                for b_i, btn_c in enumerate(tab_buttons):
                    is_active = (b_i == i)
                    btn_c.bgcolor = "#7c3aed" if is_active else "#1e1e1e"
                    btn_c.border = ft.Border.all(1, "#9D50BB" if is_active else "#333333")
                try: page.update()
                except Exception: pass
            return click
    
        is_sel = (idx == curr_idx)
        btn_c = ft.Container(
            content=ft.Row([
                ft.Icon(icon_name, size=13 if is_mobile else 15, color="#00FFFF" if is_sel else "#aaaaaa"),
                ft.Text(label, size=10.5 if is_mobile else 12, weight="bold", color="white" if is_sel else "#aaaaaa")
            ], spacing=4 if is_mobile else 6, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#7c3aed" if is_sel else "#1e1e1e",
            padding=ft.padding.Padding(8, 5, 8, 5) if is_mobile else ft.padding.Padding(12, 8, 12, 8),
            border_radius=8,
            border=ft.Border.all(1, "#9D50BB" if is_sel else "#333333"),
            on_click=make_click(idx, builder_fn),
            ink=True
        )
        tab_buttons.append(btn_c)
    
    tab_bar_row = ft.Row(tab_buttons, scroll=ft.ScrollMode.AUTO, spacing=6 if is_mobile else 8)
    
    return ft.Column([
        ft.Text("Panel de Control Operativo", size=20 if is_mobile else 24, color="#D8B4FE", weight="bold"),
        ft.Divider(height=10 if is_mobile else 12, color="#333333"),
        tab_bar_row,
        ft.Container(height=5),
        content_box
    ], expand=True)