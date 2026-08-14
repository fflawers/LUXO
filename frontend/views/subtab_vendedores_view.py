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

def _build_subtab_vendedores_view(
    agregar_un_vendedor,
    forzar_recalculo,
    kpi_summary_container,
    num_vendedores_input,
    tienda_label_vendedores,
    vendedores_container
):
    return ft.Column([
        ft.Row([
            ft.Row([
                ft.ElevatedButton(
                    "➕ Agregar Vendedor",
                    bgcolor="#9D50BB",
                    color="white",
                    height=40,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda e: agregar_un_vendedor()
                ),
                tienda_label_vendedores,
            ], spacing=10, vertical_alignment="center", wrap=True),
            num_vendedores_input
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        kpi_summary_container,
        ft.Row([
            ft.ElevatedButton(
                "🔄 Recalcular / Aplicar Días",
                bgcolor="#0284c7",
                color="white",
                height=40,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e: forzar_recalculo(e)
            ),
        ]),
        vendedores_container
    ], spacing=15, scroll=ft.ScrollMode.AUTO)