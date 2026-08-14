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

def _build_meta_semanal_view(
    _ex,
    conectar_db,
    dd_control,
    es_admin,
    guardar_biometria_db,
    mostrar_snack,
    msg,
    n_val,
    page,
    registrar_auditoria_borrado,
    res,
    tab,
    target_uid,
    tf,
    user_info,
    v_item
):
    import json, datetime
    
    # --- ESTADOS Y CONFIGURACIÓN ---
    meta_id_holder = [None]
    active_subtab = ["diarias"] # Default "diarias" (Hoja Domingo)
    target_user_id = [user_info["id"]]
    # Variables de tienda activa en consulta
    current_store_name_holder = ["MI TIENDA"]
    tienda_label_diarias = ft.Text("🏬 Tienda en consulta: ", color="#00FFFF", size=14, weight="bold")
    tienda_label_vendedores = ft.Text("🏬 ", color="#00FFFF", size=14, weight="bold")
    
    def actualizar_titulos_tienda():
        s_name = current_store_name_holder[0]
        tienda_label_diarias.value = f"🏬 Tienda en consulta: {s_name}"
        tienda_label_vendedores.value = f"🏬 {s_name}"
    
    admin_store_bar = ft.Container()
    
    if es_admin():
        tiendas_opciones = []
        try:
            db_t = conectar_db()
            if db_t:
                cur_t = db_t.cursor(dictionary=True)
                cur_t.execute("SELECT ID_Usuario, Nombre_Completo, Tienda FROM usuarios WHERE Tienda IS NOT NULL AND Tienda != '' ORDER BY Tienda ASC")
                rows_t = cur_t.fetchall()
                db_t.close()
                for r in rows_t:
                    tiendas_opciones.append(
                        ft.dropdown.Option(
                            key=str(r["ID_Usuario"]),
                            text=f"{r['Tienda']} ({r['Nombre_Completo']})"
                        )
                    )
        except Exception as ex_t:
            print("Error cargando tiendas admin:", ex_t)
    
        if tiendas_opciones:
            target_user_id[0] = int(tiendas_opciones[0].key)
            current_store_name_holder[0] = tiendas_opciones[0].text
            actualizar_titulos_tienda()
    
            dd_tiendas_admin = ft.Dropdown(
                options=tiendas_opciones,
                value=tiendas_opciones[0].key,
                border_color="#9D50BB",
                color="white",
                bgcolor="#0F0F1A",
                expand=True
            )
    
            def ejecutar_cargar_tienda_admin(e=None):
                if dd_tiendas_admin and dd_tiendas_admin.value:
                    t_id = int(dd_tiendas_admin.value)
                    target_user_id[0] = t_id
                    t_name = "TIENDA"
                    for opt in dd_tiendas_admin.options:
                        if opt.key == str(t_id):
                            t_name = opt.text
                            break
                    current_store_name_holder[0] = t_name
                    actualizar_titulos_tienda()
                    cargar_datos(t_id)
                    if active_subtab[0] == "diarias":
                        subtab_content.content = build_subtab_diarias_view()
                    else:
                        subtab_content.content = build_subtab_vendedores_view()
                    try: page.update()
                    except Exception: pass
                    mostrar_snack(f"Metas cargadas para: {t_name}", color="#7CFC00")
    
            btn_cargar_tienda_admin = ft.ElevatedButton(
                "🔄 Cargar Tienda",
                bgcolor="#0284c7",
                color="white",
                height=38,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=ejecutar_cargar_tienda_admin
            )
    
            admin_store_bar = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED, color="#00FFFF", size=20),
                        ft.Text("Consultar Tienda (Admin):", color="white", weight="bold", size=13),
                    ]),
                    ft.Row([
                        dd_tiendas_admin,
                        btn_cargar_tienda_admin
                    ], spacing=10)
                ], spacing=8),
                bgcolor="#1e1b4b",
                padding=10,
                border_radius=8,
                border=ft.Border.all(1, "#9D50BB")
            )
    else:
        current_store_name_holder[0] = user_info.get("tienda") or user_info.get("nombre") or "Mi Tienda"
        actualizar_titulos_tienda()
    
    # Semana empieza de DOMINGO a SÁBADO
    dias_semana = ["Domingo", "Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]
    
    # Contenedores principales
    vendedores_container = ft.Column(spacing=20)
    subtab_content = ft.Container(expand=True)
    
    # Etiquetas de texto calculadas (Diarias)
    pct_labels = {}
    meta_labels = {}
    acum_ly_labels = {}
    acum_meta_labels = {}
    tot_vly_label = ft.Text("$0", color="#facc15", weight="bold", size=8.5, no_wrap=True)
    
    # Ajustes adaptativos para PC vs Celular
    is_mobile = (page.width < 700) if (page and page.width) else False
    f_size = 8.5 if is_mobile else 12.0
    inp_h = 24 if is_mobile else 34
    p_val = 2 if is_mobile else 6
    s_val = 4 if is_mobile else 8
    
    def habilitar_seleccion_inteligente(tf):
        state = {"click_count": 0}
    
        def on_focus(e):
            state["click_count"] = 1
            if tf.value:
                tf.selection = ft.TextSelection(0, len(str(tf.value)))
                try: tf.update()
                except Exception: pass
    
        def on_click(e):
            if state["click_count"] == 1:
                state["click_count"] = 2
                tf.selection = None
                try: tf.update()
                except Exception: pass
            else:
                state["click_count"] = 1
                if tf.value:
                    tf.selection = ft.TextSelection(0, len(str(tf.value)))
                    try: tf.update()
                    except Exception: pass
    
        def on_blur(e):
            state["click_count"] = 0
    
        tf.on_focus = on_focus
        tf.on_click = on_click
        tf.on_blur = on_blur
    
    # Inputs amarillos para VLY (Venta Año Pasado) - Hoja Domingo
    inputs_vly = {}
    for d in dias_semana:
        default_val = "0"
        if d == "Lunes": default_val = "9164"
        elif d == "Miercoles": default_val = "7576"
        elif d == "Jueves": default_val = "8203"
        elif d == "Viernes": default_val = "12047"
        elif d == "Sabado": default_val = "8860"
        
        tf_vly = ft.TextField(
            value=default_val,
            bgcolor="#fef08a",
            color="#000000",
            border_color="#eab308",
            height=inp_h,
            content_padding=ft.padding.Padding(4, 2, 4, 2) if not is_mobile else 1,
            text_align=ft.TextAlign.RIGHT,
            text_size=f_size,
            text_style=ft.TextStyle(weight="bold"),
            on_change=lambda e: recalcular_todo(e)
        )
        habilitar_seleccion_inteligente(tf_vly)
        inputs_vly[d] = tf_vly
    
        pct_labels[d] = ft.Text("0.0%", color="#D8B4FE", size=f_size, no_wrap=True)
        meta_labels[d] = ft.Text("$0", color="#00FFFF", weight="bold", size=f_size, no_wrap=True)
        acum_ly_labels[d] = ft.Text("$0", color="#aaaaaa", size=f_size, no_wrap=True)
        acum_meta_labels[d] = ft.Text("$0", color="#00FFFF", weight="bold", size=f_size, no_wrap=True)
    
    tot_acum_ly_label = ft.Text("$0", color="#aaaaaa", size=f_size, no_wrap=True)
    tot_acum_meta_label = ft.Text("$0", color="#00FFFF", weight="bold", size=f_size, no_wrap=True)
    
    tot_vly_label = ft.Text("$0", color="#facc15", weight="bold", size=f_size, no_wrap=True)
    # Meta Total General ($60,000 en amarillo - Celda D10 del Excel)
    meta_total_input = ft.TextField(
        value="60000",
        bgcolor="#facc15",
        color="#000000",
        border_color="#ca8a04",
        height=inp_h,
        content_padding=ft.padding.Padding(4, 2, 4, 2) if not is_mobile else 1,
        text_align=ft.TextAlign.RIGHT,
        text_size=f_size,
        text_style=ft.TextStyle(weight="bold"),
        on_change=lambda e: recalcular_todo(e)
    )
    habilitar_seleccion_inteligente(meta_total_input)
    
    # Construir la estructura estática Adaptativa (Celular/PC) para Metas Diarias
    diarias_rows = []
    header_diarias = ft.Container(
        content=ft.Row([
            ft.Text("DÍA", expand=10, weight="bold", color="#D8B4FE", size=f_size, no_wrap=True),
            ft.Text("VLY 🟨", expand=18, weight="bold", color="#facc15", text_align=ft.TextAlign.RIGHT, size=f_size, no_wrap=True),
            ft.Text("%", expand=10, weight="bold", color="#D8B4FE", text_align=ft.TextAlign.RIGHT, size=f_size, no_wrap=True),
            ft.Text("META", expand=20, weight="bold", color="#00FFFF", text_align=ft.TextAlign.RIGHT, size=f_size, no_wrap=True),
            ft.Text("ACUM.LY", expand=20, weight="bold", color="#aaaaaa", text_align=ft.TextAlign.RIGHT, size=f_size, no_wrap=True),
            ft.Text("ACUM.META", expand=28, weight="bold", color="#00FFFF", text_align=ft.TextAlign.CENTER, size=f_size, no_wrap=True),
        ], spacing=2, expand=True),
        bgcolor="#262626", padding=ft.padding.Padding(p_val+2, p_val+2, p_val+2, p_val+2), border_radius=4, expand=True
    )
    diarias_rows.append(header_diarias)
    
    for idx, d in enumerate(dias_semana):
        row_bg = "#1e1e1e" if idx % 2 == 0 else "#252525"
        d_short = d[:3].upper() if len(d) > 3 else d.upper()
        if d == "Miercoles": d_short = "MIÉ"
        elif d == "Sabado": d_short = "SÁB"
    
        diarias_rows.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(d_short, expand=10, weight="bold", color="white", size=f_size, no_wrap=True),
                    ft.Container(inputs_vly[d], expand=18),
                    ft.Container(pct_labels[d], expand=10, alignment=ft.alignment.Alignment(1, 0)),
                    ft.Container(meta_labels[d], expand=20, alignment=ft.alignment.Alignment(1, 0)),
                    ft.Container(acum_ly_labels[d], expand=20, alignment=ft.alignment.Alignment(1, 0)),
                    ft.Container(acum_meta_labels[d], expand=28, alignment=ft.alignment.Alignment(0, 0)),
                ], spacing=2, expand=True),
                bgcolor=row_bg, padding=ft.padding.Padding(p_val, p_val, p_val, p_val), border_radius=4, expand=True
            )
        )
    
    totales_row = ft.Container(
        content=ft.Row([
            ft.Text("TOTAL", expand=10, weight="bold", color="#facc15", size=f_size, no_wrap=True),
            ft.Container(tot_vly_label, expand=18, alignment=ft.alignment.Alignment(1, 0)),
            ft.Container(ft.Text("100%", color="#facc15", weight="bold", size=f_size, no_wrap=True), expand=10, alignment=ft.alignment.Alignment(1, 0)),
            ft.Container(meta_total_input, expand=20, alignment=ft.alignment.Alignment(1, 0)),
            ft.Container(tot_acum_ly_label, expand=20, alignment=ft.alignment.Alignment(1, 0)),
            ft.Container(tot_acum_meta_label, expand=28, alignment=ft.alignment.Alignment(0, 0)),
        ], spacing=2, expand=True),
        bgcolor="#1e1b4b", padding=ft.padding.Padding(p_val+2, p_val+2, p_val+2, p_val+2), border_radius=6, border=ft.Border.all(1, "#facc15")
    )
    diarias_rows.append(totales_row)
    
    # Contenedor de Metas Diarias FLUIDO
    diarias_container = ft.Column(controls=diarias_rows, spacing=s_val, expand=True)
    
    # Controles Vendedores (Hoja Vendedor)
    aur_input = ft.TextField(
        value="3553",
        bgcolor="#1e1b4b",
        color="#facc15",
        border_color="#facc15",
        width=120,
        text_align=ft.TextAlign.RIGHT,
        text_size=13,
        text_style=ft.TextStyle(weight="bold"),
        on_change=lambda e: recalcular_todo(e)
    )
    aur_piezas_tienda_label = ft.Text("16.89 pz", color="#00FFFF", weight="bold", size=13)
    
    num_vendedores_input = ft.TextField(
        label="N° Vendedores",
        value="3",
        border_color="#9D50BB",
        color="white",
        width=140,
        on_change=lambda e: ajustar_vendedores()
    )
    
    vendedores_list = []
    
    kpi_table_rows_container = ft.Column(spacing=4)
    _kpi_recalc = [False]  # flag anti-recursión
    tbl_f_size = 11.0 if is_mobile else 13.5
    tbl_inp_h  = 30   if is_mobile else 38
    tbl_inp_ts = 10.5 if is_mobile else 13.0
    tbl_pad    = 3    if is_mobile else 6
    
    w_vend     = 65 if is_mobile else 140
    w_meta     = 65 if is_mobile else 130
    w_pct_pol  = 42 if is_mobile else 75
    w_pol_n    = 30 if is_mobile else 50
    w_pct_mult = 42 if is_mobile else 75
    w_mult_n   = 30 if is_mobile else 50
    w_ppt      = 38 if is_mobile else 65
    w_pct_lujo = 42 if is_mobile else 75
    w_lujo_n   = 30 if is_mobile else 50
    w_pz       = 35 if is_mobile else 60
    
    total_kpi_meta_label   = ft.Text("$0",    color="#facc15", weight="bold", size=tbl_f_size)
    total_kpi_pol_label    = ft.Text("0",     color="#facc15", weight="bold", size=tbl_f_size)
    total_kpi_mult_label   = ft.Text("0",     color="#facc15", weight="bold", size=tbl_f_size)
    total_kpi_ppt_label    = ft.Text("1.50",  color="#ffffff", weight="bold", size=tbl_f_size)
    total_kpi_lujo_label   = ft.Text("0",     color="#facc15", weight="bold", size=tbl_f_size)
    total_kpi_piezas_label = ft.Text("0",     color="#00FFFF", weight="bold", size=tbl_f_size)
    # Labels de PROMEDIO para la fila total
    total_kpi_pct_pol_label  = ft.Text("0%",   color="#aaaaaa", size=tbl_f_size)
    total_kpi_pct_mult_label = ft.Text("0%",   color="#aaaaaa", size=tbl_f_size)
    total_kpi_pct_lujo_label = ft.Text("0%",   color="#aaaaaa", size=tbl_f_size)
    
    def refrescar_kpi_table():
        rows = []
        header = ft.Container(
            content=ft.Row([
                ft.Text("VEND", width=w_vend, weight="bold", color="#ffffff", size=tbl_f_size),
                ft.Text("META$", width=w_meta, weight="bold", color="#ffffff", size=tbl_f_size, text_align=ft.TextAlign.RIGHT),
                ft.Text("%POL", width=w_pct_pol, weight="bold", color="#facc15", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("#P", width=w_pol_n, weight="bold", color="#ffffff", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("%MUL", width=w_pct_mult, weight="bold", color="#facc15", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("#M", width=w_mult_n, weight="bold", color="#ffffff", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("PPT", width=w_ppt, weight="bold", color="#ffffff", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("%LUJ", width=w_pct_lujo, weight="bold", color="#facc15", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("#L", width=w_lujo_n, weight="bold", color="#ffffff", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
                ft.Text("PZ", width=w_pz, weight="bold", color="#00FFFF", size=tbl_f_size, text_align=ft.TextAlign.CENTER),
            ], spacing=2 if is_mobile else 6),
            bgcolor="#080812", padding=4 if is_mobile else 6, border_radius=4
        )
        rows.append(header)
    
        for idx, v in enumerate(vendedores_list):
            r_bg = "#1e1e1e" if idx % 2 == 0 else "#252525"
            n_str = str(v["nombre"].value or "").strip().upper()
            if is_mobile and len(n_str) > 7: n_str = n_str[:7]
            v_name_lbl = ft.Text(n_str, size=tbl_f_size, weight="bold", color="white")
    
            row_c = ft.Container(
                content=ft.Row([
                    ft.Container(v_name_lbl, width=w_vend),
                    ft.Container(v["kpi_meta_text"], width=w_meta, alignment=ft.alignment.Alignment(1, 0)),
                    ft.Container(v["kpi_pct_pol_input"], width=w_pct_pol, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_pol_text"], width=w_pol_n, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_pct_mult_input"], width=w_pct_mult, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_mult_text"], width=w_mult_n, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_ppt_input"], width=w_ppt, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_pct_lujo_input"], width=w_pct_lujo, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_lujo_text"], width=w_lujo_n, alignment=ft.alignment.Alignment(0, 0)),
                    ft.Container(v["kpi_piezas_text"], width=w_pz, alignment=ft.alignment.Alignment(0, 0)),
                ], spacing=2 if is_mobile else 6),
                bgcolor=r_bg, padding=3 if is_mobile else 5, border_radius=4
            )
            rows.append(row_c)
    
        tot_row = ft.Container(
            content=ft.Row([
                ft.Text("TOTAL", width=w_vend, weight="bold", color="#ffffff", size=tbl_f_size),
                ft.Container(total_kpi_meta_label,    width=w_meta, alignment=ft.alignment.Alignment(1, 0)),
                ft.Container(total_kpi_pct_pol_label, width=w_pct_pol, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_pol_label,     width=w_pol_n, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_pct_mult_label,width=w_pct_mult, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_mult_label,    width=w_mult_n, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_ppt_label,     width=w_ppt, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_pct_lujo_label,width=w_pct_lujo, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_lujo_label,    width=w_lujo_n, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(total_kpi_piezas_label,  width=w_pz, alignment=ft.alignment.Alignment(0, 0)),
            ], spacing=2 if is_mobile else 6),
            bgcolor="#404040", padding=4 if is_mobile else 6, border_radius=4
        )
        rows.append(tot_row)
        kpi_table_rows_container.controls = rows
    
    kpi_summary_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Meta por vendedor", weight="bold", color="#ffffff", size=16),
                ft.Row([
                    ft.Text("cual es tu aur anual:", color="#facc15", weight="bold", size=13),
                    aur_input,
                    ft.Text("piezas para llegar a meta:", color="#aaaaaa", size=12),
                    aur_piezas_tienda_label,
                    ft.ElevatedButton(
                        "🔄 Actualizar Tabla",
                        bgcolor="#7c3aed",
                        color="white",
                        height=36,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda e: forzar_recalculo(e)
                    ),
                ], spacing=10, wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ft.Row([kpi_table_rows_container], scroll=ft.ScrollMode.AUTO)
        ], spacing=10),
        bgcolor="#171717", padding=15, border_radius=10, border=ft.Border.all(1, "#333333")
    )
    
    def crear_vendedor_item(n_val, d_val="6"):
        dd = ft.Dropdown(
            value=str(d_val),
            options=[ft.dropdown.Option(str(d)) for d in range(0, 7)],
            border_color="#333333",
            color="white",
            width=75 if is_mobile else 90,
            height=36 if is_mobile else 40
        )
        
        lbl_w = 45 if is_mobile else 70
        box_w = 85 if is_mobile else 150
        f_sz  = 10.0 if is_mobile else 12.0
    
        meta_diaria_texts = [ft.Text("$ 0.00", color="#000000", weight="bold", size=f_sz) for _ in range(6)]
        meta_diaria_containers = [
            ft.Container(
                meta_diaria_texts[i],
                width=box_w,
                alignment=ft.alignment.Alignment(1, 0),
                bgcolor="#fef08a",
                padding=3 if is_mobile else 5,
                border_radius=4
            ) for i in range(6)
        ]
        acum_texts = [ft.Text("$ 0.00", color="#000000", weight="bold", size=f_sz) for _ in range(6)]
        day_label_texts = [ft.Text(f"Día {d_i}", width=lbl_w, color="#ffffff", weight="bold", size=f_sz) for d_i in range(1, 7)]
        row_containers = []
        
        header_title = ft.Text(n_val.upper(), width=lbl_w, weight="bold", color="#000000", size=f_sz)
        meta_vend_text = ft.Text("Meta Vendedor: $ 0.00", color="#00FFFF", weight="bold", size=11.0 if is_mobile else 13.0)
    
        kpi_meta_text = ft.Text("$0", color="#ffffff", weight="bold", size=tbl_f_size)
        kpi_pct_pol_input  = ft.TextField(value="45%", bgcolor="#1e1e1e", color="#facc15", border_color="#333333", width=w_pct_pol, height=tbl_inp_h, content_padding=tbl_pad, text_align=ft.TextAlign.CENTER, text_size=tbl_inp_ts)
        kpi_pol_text       = ft.Text("0", color="#facc15", weight="bold", size=tbl_inp_ts)
        kpi_pct_mult_input = ft.TextField(value="45%", bgcolor="#1e1e1e", color="#facc15", border_color="#333333", width=w_pct_mult, height=tbl_inp_h, content_padding=tbl_pad, text_align=ft.TextAlign.CENTER, text_size=tbl_inp_ts)
        kpi_mult_text      = ft.Text("0", color="#facc15", weight="bold", size=tbl_inp_ts)
        kpi_ppt_input      = ft.TextField(value="1.45", bgcolor="#1e1e1e", color="#ffffff", border_color="#333333", width=w_ppt, height=tbl_inp_h, content_padding=tbl_pad, text_align=ft.TextAlign.CENTER, text_size=tbl_inp_ts, read_only=True)
        kpi_pct_lujo_input = ft.TextField(value="45%", bgcolor="#1e1e1e", color="#facc15", border_color="#333333", width=w_pct_lujo, height=tbl_inp_h, content_padding=tbl_pad, text_align=ft.TextAlign.CENTER, text_size=tbl_inp_ts)
        kpi_lujo_text      = ft.Text("0", color="#facc15", weight="bold", size=tbl_inp_ts)
        kpi_piezas_text    = ft.Text("0", color="#00FFFF", weight="bold", size=tbl_inp_ts)
    
        habilitar_seleccion_inteligente(kpi_pct_pol_input)
        habilitar_seleccion_inteligente(kpi_pct_mult_input)
        habilitar_seleccion_inteligente(kpi_pct_lujo_input)
        
        v_header = ft.Container(
            content=ft.Row([
                header_title,
                ft.Text("META 🟨", width=box_w, weight="bold", color="#000000", size=f_sz, text_align=ft.TextAlign.RIGHT),
                ft.Text("ACUM 🟨" if is_mobile else "ACUMULADO 🟨", width=box_w, weight="bold", color="#000000", size=f_sz, text_align=ft.TextAlign.RIGHT),
            ], spacing=3 if is_mobile else 6),
            bgcolor="#facc15", padding=4 if is_mobile else 6, border_radius=4
        )
        
        v_rows = [v_header]
        for d_i in range(1, 7):
            c = ft.Container(
                content=ft.Row([
                    day_label_texts[d_i-1],
                    meta_diaria_containers[d_i-1],
                    ft.Container(acum_texts[d_i-1], width=box_w, alignment=ft.alignment.Alignment(1, 0), bgcolor="#fef08a", padding=3 if is_mobile else 5, border_radius=4),
                ], spacing=3 if is_mobile else 6),
                bgcolor="#1e1e1e" if d_i % 2 == 1 else "#252525",
                padding=3 if is_mobile else 5, border_radius=4
            )
            v_rows.append(c)
            row_containers.append(c)
    
        nombre_tf = ft.TextField(value=n_val, border_color="#444444", color="white", width=110 if is_mobile else 140, height=34 if is_mobile else 38, text_size=11 if is_mobile else 12, text_style=ft.TextStyle(weight="bold"), content_padding=4 if is_mobile else 6)
        nombre_tf.on_change = lambda e: (setattr(header_title, "value", nombre_tf.value.upper()), page.update() if page else None)
    
        item = {
            "nombre": nombre_tf,
            "dias": dd,
            "header_title": header_title,
            "meta_vend_text": meta_vend_text,
            "meta_diaria_texts": meta_diaria_texts,
            "meta_diaria_containers": meta_diaria_containers,
            "day_label_texts": day_label_texts,
            "acum_texts": acum_texts,
            "row_containers": row_containers,
            "card_container": None,
            "kpi_meta_text": kpi_meta_text,
            "kpi_pct_pol_input": kpi_pct_pol_input,
            "kpi_pol_text": kpi_pol_text,
            "kpi_pct_mult_input": kpi_pct_mult_input,
            "kpi_mult_text": kpi_mult_text,
            "kpi_ppt_input": kpi_ppt_input,
            "kpi_pct_lujo_input": kpi_pct_lujo_input,
            "kpi_lujo_text": kpi_lujo_text,
            "kpi_piezas_text": kpi_piezas_text
        }
    
        def make_on_dias_change(dd_control, v_item):
            def on_dias_change(e):
                val_str = None
                if e and hasattr(e, "control") and e.control and e.control.value:
                    val_str = str(e.control.value).strip()
                if (not val_str or val_str not in ["0", "1", "2", "3", "4", "5", "6"]) and e and hasattr(e, "data") and e.data:
                    val_str = str(e.data).strip()
                
                if val_str in ["0", "1", "2", "3", "4", "5", "6"]:
                    dd_control.value = val_str
                    v_item["dias"].value = val_str
                recalcular_todo(e)
            return on_dias_change
    
        dd.on_change = make_on_dias_change(dd, item)
    
        def eliminar_vendedor_click(e):
            if len(vendedores_list) > 1:
                if item in vendedores_list:
                    vendedores_list.remove(item)
                    num_vendedores_input.value = str(len(vendedores_list))
                    refrescar_vendedores_container()
                    recalcular_vendedores()
    
        
        # --- CONTROL DE BIOMETRÍA Y PERMISOS DE GERENTE ---
        def registrar_rostro_vend_click(e):
            res, msg = guardar_biometria_db(user_info["id"], item.get("nombre", "Vendedor"), encoding_rostro="[ENCODING_ROSTRO_VECTOR_128_FLOAT_DUMMY]")
            mostrar_snack(msg, "#7CFC00" if res else "red")
    
        def registrar_huella_vend_click(e):
            res, msg = guardar_biometria_db(user_info["id"], item.get("nombre", "Vendedor"), hash_huella="[HASH_HUELLA_MINUTIAS_DUMMY]")
            mostrar_snack(msg, "#7CFC00" if res else "red")
    
        def eliminar_biometria_vend_click(e):
            # Verificar si el usuario activo tiene puesto o rol de Gerente
            es_gerente = any(k in str(user_info.get("rol", "")).lower() or k in str(user_info.get("puesto", "")).lower() for k in ["gerente", "admin"])
            if not es_gerente:
                mostrar_snack("⚠️ Permiso denegado: Solo el Gerente de Tienda puede eliminar datos biométricos", "red")
                return
            
            registrar_auditoria_borrado(
                ejecutor_id=user_info.get("id", 0),
                ejecutor_nombre=user_info.get("nombre", "Gerente"),
                ejecutor_rol=user_info.get("rol", "Gerente de Tienda"),
                afectado_nombre=item.get("nombre", "Vendedor"),
                accion="ELIMINACION_BIOMETRIA",
                detalles="Eliminación de datos biométricos autorizada por Gerente de Tienda"
            )
            mostrar_snack(f"Biometría de {item.get('nombre', 'Vendedor')} eliminada y registrada en auditoría 🛡️", "#7CFC00")
    
        btn_bio_rostro = ft.IconButton(icon=ft.Icons.FACE_ROUNDED, tooltip="Registrar Rostro (Face ID)", icon_color="#003366", on_click=registrar_rostro_vend_click)
        btn_bio_huella = ft.IconButton(icon=ft.Icons.FINGERPRINT_ROUNDED, tooltip="Registrar Huella Dactilar", icon_color="#003366", on_click=registrar_huella_vend_click)
        btn_bio_del = ft.IconButton(icon=ft.Icons.SHIELD_ROUNDED, tooltip="Eliminar Biometría (Solo Gerente de Tienda)", icon_color="#FF4500", on_click=eliminar_biometria_vend_click)
    
    
        v_table_box = ft.Container(
            content=ft.Column([v_header] + row_containers, spacing=3),
            width=230 if is_mobile else 400
        )
    
        item["card_container"] = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        nombre_tf,
                        ft.Text("Días:", color="#aaaaaa", size=11 if is_mobile else 12, weight="bold"),
                        dd,
                    ], spacing=4 if is_mobile else 6, wrap=True),
                    ft.Row([
                        meta_vend_text,
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color="#FF4500",
                            icon_size=18 if is_mobile else 20,
                            tooltip="Eliminar Vendedor",
                            on_click=eliminar_vendedor_click
                        )
                    ], spacing=4 if is_mobile else 6, wrap=True)
                ], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                v_table_box
            ], spacing=6),
            bgcolor="#171717", padding=8 if is_mobile else 12, border_radius=8, border=ft.Border.all(1, "#333333")
        )
    
        return item
    
    def refrescar_vendedores_container():
        vendedores_container.controls = [v["card_container"] for v in vendedores_list]
        try: page.update()
        except Exception: pass
    
    def inicializar_vendedores_default(n):
        vendedores_list.clear()
        for i in range(1, n + 1):
            vendedores_list.append(crear_vendedor_item(f"VENDEDOR {i}", "6"))
        refrescar_vendedores_container()
    
    def ajustar_vendedores():
        try:
            n = int(num_vendedores_input.value or 3)
            n = max(1, min(15, n))
        except ValueError:
            n = 3
        
        curr_len = len(vendedores_list)
        if n > curr_len:
            for i in range(curr_len + 1, n + 1):
                vendedores_list.append(crear_vendedor_item(f"VENDEDOR {i}", "6"))
        elif n < curr_len:
            del vendedores_list[n:]
        
        refrescar_vendedores_container()
        recalcular_vendedores()
    
    def recalcular_diarias():
        try:
            meta_total = float(meta_total_input.value or 0)
        except ValueError:
            meta_total = 0.0
    
        vly_vals = {}
        tot_vly = 0.0
        for d in dias_semana:
            try: val = float(inputs_vly[d].value or 0)
            except ValueError: val = 0.0
            vly_vals[d] = val
            tot_vly += val
    
        tot_vly_label.value = f"${tot_vly:,.0f}"
    
        acum_ly = 0.0
        acum_meta = 0.0
    
        for d in dias_semana:
            vly_d = vly_vals[d]
            pct_d = (vly_d / tot_vly * 100.0) if tot_vly > 0 else (100.0 / 7.0)
            meta_d = (meta_total * pct_d / 100.0)
    
            acum_ly += vly_d
            acum_meta += meta_d
    
            pct_labels[d].value = f"{pct_d:.1f}%"
            meta_labels[d].value = f"${meta_d:,.0f}"
            acum_ly_labels[d].value = f"${acum_ly:,.0f}"
            acum_meta_labels[d].value = f"${acum_meta:,.0f}"
    
        tot_acum_ly_label.value = f"${acum_ly:,.0f}"
        tot_acum_meta_label.value = f"${acum_meta:,.0f}"
    
    def recalcular_vendedores():
        # Guard: evita re-entrada recursiva cuando se actualizan
        # los TextField de % desde dentro de este mismo método
        if _kpi_recalc[0]:
            return
        _kpi_recalc[0] = True
        try:
            _recalcular_vendedores_inner()
        except Exception as _ex:
            print(f"[recalcular_vendedores] error: {_ex}")
        finally:
            _kpi_recalc[0] = False  # SIEMPRE liberar, con o sin error
    
    def _recalcular_vendedores_inner():
        try:
            meta_total = float(meta_total_input.value or 0)
        except ValueError:
            meta_total = 0.0
    
        num_v = len(vendedores_list)
        if num_v == 0:
            return
    
        base_meta_per_seller = meta_total / float(num_v)
        base_daily_meta = base_meta_per_seller / 6.0
    
        dias_trab = []
        for v in vendedores_list:
            raw_val = v["dias"].value
            if raw_val is not None and str(raw_val).strip() in ["0", "1", "2", "3", "4", "5", "6"]:
                d = int(str(raw_val).strip())
            else:
                try: d = int(float(str(raw_val).strip() if raw_val is not None else 6))
                except Exception: d = 6
            dias_trab.append(max(0, min(6, d)))
    
        total_lost_goal = 0.0
        full_time_count = 0
    
        for d in dias_trab:
            if d < 6:
                total_lost_goal += (6 - d) * base_daily_meta
            else:
                full_time_count += 1
    
        absorbed_per_full_timer = (total_lost_goal / float(full_time_count)) if full_time_count > 0 else (total_lost_goal / float(num_v))
    
        # KPI Calculations
        try:
            aur_val = float(aur_input.value or 3553)
            if aur_val <= 0: aur_val = 3553.0
        except ValueError:
            aur_val = 3553.0
    
        exact_store_pz = (meta_total / aur_val) if aur_val > 0 else 0.0
        aur_piezas_tienda_label.value = f"{exact_store_pz:.2f} pz"
    
        tot_kpi_meta = 0.0
        tot_kpi_pol  = 0
        tot_kpi_mult = 0
        tot_kpi_lujo = 0
        tot_kpi_piezas = 0
        sum_eff_pol  = 0
        sum_eff_mult = 0
        sum_eff_ppt  = 0.0
        sum_eff_lujo = 0
        count_active = 0
    
        for idx, v in enumerate(vendedores_list):
            d = dias_trab[idx]
            if d == 0:
                seller_meta = 0.0
            elif d < 6:
                seller_meta = d * base_daily_meta
            else:
                seller_meta = base_meta_per_seller + absorbed_per_full_timer
    
            daily_quota = seller_meta / float(d) if d > 0 else 0.0
            v["meta_vend_text"].value = f"Meta Vendedor: $ {seller_meta:,.2f}"
    
            import math
            def std_round(x):
                return int(math.floor(x + 0.5))
    
            if seller_meta > 0 and aur_val > 0:
                s_piezas = math.ceil(seller_meta / aur_val)
            else:
                s_piezas = 0
    
            try:
                pct_pol = float(str(v["kpi_pct_pol_input"].value or "45").replace("%", "").strip()) / 100.0
                if pct_pol <= 0 or pct_pol >= 1.0: pct_pol = 0.45  # mínimo 45%, máx <100%
            except Exception: pct_pol = 0.45
    
            try:
                pct_mult = float(str(v["kpi_pct_mult_input"].value or "45").replace("%", "").strip()) / 100.0
                if pct_mult < 0.45 or pct_mult >= 1.0: pct_mult = 0.45
            except Exception: pct_mult = 0.45
    
            try:
                ppt_v = float(str(v["kpi_ppt_input"].value or "1.45").strip())
                if ppt_v < 1.45: ppt_v = 1.45  # mínimo operativo 1.45
            except Exception: ppt_v = 1.45
    
            try:
                pct_lujo = float(str(v["kpi_pct_lujo_input"].value or "45").replace("%", "").strip()) / 100.0
                if pct_lujo <= 0 or pct_lujo >= 1.0: pct_lujo = 0.45
            except Exception: pct_lujo = 0.45
    
    
            # FÓRMULA FÍSICA Y PISOS MÍNIMOS DE NEGOCIO:
            # n_mult = pct_mult × piezas / (1 + pct_mult)
            mult_pz = std_round(pct_mult * s_piezas / (1.0 + pct_mult)) if s_piezas > 0 else 0
    
            # Garantizar pisos mínimos operativos (%múltiples >= 45% y PPT >= 1.45)
            while s_piezas > 0 and mult_pz < s_piezas:
                tot_t = max(1, s_piezas - mult_pz)
                m_pct = std_round(mult_pz * 100 / tot_t)
                ppt_val = round(s_piezas / tot_t, 2)
                if m_pct >= 45 and ppt_val >= 1.45:
                    break
                mult_pz += 1
    
            # total_tickets derivado exactamente
            total_tickets = max(1, s_piezas - mult_pz) if s_piezas > 0 else 0
    
            # Consistencia física
            if mult_pz > total_tickets:
                mult_pz = total_tickets
    
            pol_pz  = std_round(pct_pol  * s_piezas)
            lujo_pz = std_round(pct_lujo  * s_piezas)
    
            # Efectivos auto-consistentes final
            eff_mult_pct = std_round(mult_pz * 100 / total_tickets)  if total_tickets > 0 else 0
            eff_ppt      = round(s_piezas / total_tickets, 2)        if total_tickets > 0 else 1.45
            eff_pol_pct  = std_round(pol_pz  * 100 / s_piezas)       if s_piezas > 0 else 0
            eff_lujo_pct = std_round(lujo_pz * 100 / s_piezas)       if s_piezas > 0 else 0
    
            # Actualizar campos de pantalla: % efectivos + PPT
            if s_piezas > 0:
                v["kpi_pct_pol_input"].value  = f"{eff_pol_pct}%"
                v["kpi_pct_mult_input"].value = f"{eff_mult_pct}%"
                v["kpi_ppt_input"].value      = f"{eff_ppt:.2f}"
                v["kpi_pct_lujo_input"].value = f"{eff_lujo_pct}%"
    
            v["kpi_meta_text"].value   = f"${seller_meta:,.0f}"
            v["kpi_pol_text"].value    = str(pol_pz)
            v["kpi_mult_text"].value   = str(mult_pz)
            v["kpi_lujo_text"].value   = str(lujo_pz)
            v["kpi_piezas_text"].value = str(s_piezas)
    
    
    
            tot_kpi_meta   += seller_meta
            tot_kpi_pol    += pol_pz
            tot_kpi_mult   += mult_pz
            tot_kpi_lujo   += lujo_pz
            tot_kpi_piezas += s_piezas
    
            if s_piezas > 0:
                sum_eff_pol  += eff_pol_pct
                sum_eff_mult += eff_mult_pct
                sum_eff_ppt  += eff_ppt
                sum_eff_lujo += eff_lujo_pct
                count_active += 1
    
            acum = 0.0
            for row_idx in range(6):
                v["row_containers"][row_idx].visible = True
                if d > 0 and row_idx < d:
                    acum += daily_quota
                    v["row_containers"][row_idx].bgcolor = "#1e1e1e" if row_idx % 2 == 0 else "#252525"
                    v["day_label_texts"][row_idx].value = f"Día {row_idx + 1}"
                    v["day_label_texts"][row_idx].color = "#ffffff"
                    v["meta_diaria_containers"][row_idx].bgcolor = "#fef08a"
                    v["meta_diaria_texts"][row_idx].value = f"$ {daily_quota:,.2f}"
                    v["meta_diaria_texts"][row_idx].color = "#000000"
                    v["acum_texts"][row_idx].value = f"$ {acum:,.2f}"
                else:
                    v["row_containers"][row_idx].bgcolor = "#450a0a"
                    v["day_label_texts"][row_idx].value = f"Día {row_idx + 1}"
                    v["day_label_texts"][row_idx].color = "#fca5a5"
                    v["meta_diaria_containers"][row_idx].bgcolor = "#7f1d1d"
                    v["meta_diaria_texts"][row_idx].value = "$ 0.00"
                    v["meta_diaria_texts"][row_idx].color = "#ffffff"
                    v["acum_texts"][row_idx].value = f"$ {acum:,.2f}"
    
        total_kpi_meta_label.value   = f"${tot_kpi_meta:,.0f}"
        total_kpi_pol_label.value    = str(tot_kpi_pol)
        total_kpi_mult_label.value   = str(tot_kpi_mult)
        total_kpi_lujo_label.value   = str(tot_kpi_lujo)
        total_kpi_piezas_label.value = str(tot_kpi_piezas)
    
        # Promedios de % efectivos para la fila total
        if count_active > 0:
            import math
            def std_round_tot(x): return int(math.floor(x + 0.5))
            avg_pol  = std_round_tot(sum_eff_pol  / count_active)
            avg_mult = std_round_tot(sum_eff_mult / count_active)
            avg_ppt  = round(sum_eff_ppt / count_active, 2)
            avg_lujo = std_round_tot(sum_eff_lujo / count_active)
            total_kpi_pct_pol_label.value  = f"{avg_pol}%"
            total_kpi_pct_mult_label.value = f"{avg_mult}%"
            total_kpi_ppt_label.value      = f"{avg_ppt:.2f}"
            total_kpi_pct_lujo_label.value = f"{avg_lujo}%"
        else:
            total_kpi_pct_pol_label.value  = "0%"
            total_kpi_pct_mult_label.value = "0%"
            total_kpi_ppt_label.value      = "0.00"
            total_kpi_pct_lujo_label.value = "0%"
        # page.update() ANTES de refrescar para que Flet confirme los
        # cambios de .value en los widgets antes de reasignarlos a
        # nuevos Containers (si no, Flet puede ignorar los cambios)
        try: page.update()
        except Exception: pass
        refrescar_kpi_table()
        refrescar_vendedores_container()
    
    def recalcular_todo(e=None):
        recalcular_diarias()
        recalcular_vendedores()
        try: page.update()
        except Exception: pass
        if e and hasattr(e, "control") and e.control:
            try: e.control.focus()
            except Exception: pass
    
    def forzar_recalculo(e=None):
        """Fuerza el recálculo limpiando el flag de anti-recursión primero.
        Se usa en el botón Recalcular/Aplicar Días para garantizar que
        siempre se ejecute aunque el flag haya quedado bloqueado."""
        _kpi_recalc[0] = False
        recalcular_todo(e)
    
    def guardar_todo_click(e):
        try:
            meta_val = float(meta_total_input.value or 0)
            vend_export = []
            for v in vendedores_list:
                vend_export.append({
                    "nombre": v["nombre"].value,
                    "dias": v["dias"].value
                })
    
            import datetime
            hoy = datetime.date.today()
            # Semana de Domingo a Sábado
            domingo = hoy - datetime.timedelta(days=(hoy.weekday() + 1) % 7)
            sabado = domingo + datetime.timedelta(days=6)
    
            db = conectar_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("SHOW COLUMNS FROM metas_semanales")
                    cols_result = cursor.fetchall()
                    existing_cols = [r[0] if isinstance(r, (tuple, list)) else r.get("Field") for r in cols_result]
    
                    if "Vendedores_JSON" not in existing_cols:
                        try: cursor.execute("ALTER TABLE metas_semanales ADD COLUMN Vendedores_JSON TEXT")
                        except Exception: pass
    
                    for d in ["AP_Domingo", "AP_Lunes", "AP_Martes", "AP_Miercoles", "AP_Jueves", "AP_Viernes", "AP_Sabado"]:
                        if d not in existing_cols:
                            try: cursor.execute(f"ALTER TABLE metas_semanales ADD COLUMN {d} DECIMAL(15,2) DEFAULT 0.00")
                            except Exception: pass
                except Exception as ex_col:
                    print("Error al verificar/crear columnas:", ex_col)
    
                uid = target_user_id[0]
                if meta_id_holder[0] is None:
                    cursor.execute("""
                        INSERT INTO metas_semanales 
                        (ID_Usuario_Tienda, Fecha_Inicio, Fecha_Fin, Monto_Meta, 
                         AP_Domingo, AP_Lunes, AP_Martes, AP_Miercoles, AP_Jueves, AP_Viernes, AP_Sabado,
                         Vendedores_JSON)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        uid, domingo, sabado, meta_val,
                        float(inputs_vly["Domingo"].value or 0), float(inputs_vly["Lunes"].value or 0), float(inputs_vly["Martes"].value or 0),
                        float(inputs_vly["Miercoles"].value or 0), float(inputs_vly["Jueves"].value or 0), float(inputs_vly["Viernes"].value or 0), float(inputs_vly["Sabado"].value or 0),
                        json.dumps(vend_export)
                    ))
                    meta_id_holder[0] = cursor.lastrowid
                else:
                    cursor.execute("""
                        UPDATE metas_semanales SET 
                        Monto_Meta = %s, 
                        AP_Domingo = %s, AP_Lunes = %s, AP_Martes = %s, AP_Miercoles = %s, AP_Jueves = %s, AP_Viernes = %s, AP_Sabado = %s,
                        Vendedores_JSON = %s
                        WHERE ID_Meta = %s
                    """, (
                        meta_val,
                        float(inputs_vly["Domingo"].value or 0), float(inputs_vly["Lunes"].value or 0), float(inputs_vly["Martes"].value or 0),
                        float(inputs_vly["Miercoles"].value or 0), float(inputs_vly["Jueves"].value or 0), float(inputs_vly["Viernes"].value or 0), float(inputs_vly["Sabado"].value or 0),
                        json.dumps(vend_export),
                        meta_id_holder[0]
                    ))
                db.commit()
                db.close()
                mostrar_snack("Metas guardadas exitosamente en LUXO 💾", "#7CFC00")
        except Exception as ex:
            print("Error al guardar metas:", ex)
            mostrar_snack("Error al guardar información", "red")
    
    def obtener_vendedores_tienda(uid):
        names = []
        try:
            db_v = conectar_db()
            if db_v:
                cur_v = db_v.cursor(dictionary=True)
                cur_v.execute("SELECT Nombre_Completo FROM vendedores WHERE ID_Usuario_Tienda = %s AND Activo = 1 ORDER BY ID_Vendedor ASC", (uid,))
                rows_v = cur_v.fetchall()
                db_v.close()
                for r in rows_v:
                    if r.get("Nombre_Completo"):
                        names.append(r["Nombre_Completo"].strip().upper())
        except Exception as ex_v:
            print("Error leyendo vendedores:", ex_v)
        return names
    
    def cargar_datos(target_uid=None):
        import datetime
        hoy = datetime.date.today()
        domingo = hoy - datetime.timedelta(days=(hoy.weekday() + 1) % 7)
        uid = target_uid if target_uid is not None else target_user_id[0]
    
        # Reset de estado inicial a CERO para tiendas nuevas o sin datos
        meta_id_holder[0] = None
        meta_total_input.value = "0"
        for d in dias_semana:
            inputs_vly[d].value = "0"
    
        # Cargar vendedores desde DB de esa tienda si existen
        v_db_names = obtener_vendedores_tienda(uid)
        if v_db_names:
            vendedores_list.clear()
            for n_name in v_db_names:
                vendedores_list.append(crear_vendedor_item(n_name, "6"))
            num_vendedores_input.value = str(len(v_db_names))
            refrescar_vendedores_container()
        else:
            inicializar_vendedores_default(3)
            num_vendedores_input.value = "3"
    
        recalcular_todo()
        
        try:
            db = conectar_db()
            if db:
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM metas_semanales 
                    WHERE ID_Usuario_Tienda = %s AND Fecha_Inicio = %s
                """, (uid, domingo))
                row = cursor.fetchone()
                db.close()
                
                if row:
                    meta_id_holder[0] = row["ID_Meta"]
                    meta_val = float(row.get("Monto_Meta", 0.0))
                    meta_total_input.value = str(int(meta_val) if meta_val.is_integer() else meta_val)
    
                    for d in dias_semana:
                        v_ap = row.get(f"AP_{d}")
                        if v_ap is not None:
                            inputs_vly[d].value = str(int(float(v_ap)) if float(v_ap).is_integer() else float(v_ap))
    
                    v_json = row.get("Vendedores_JSON")
                    if v_json:
                        v_data = json.loads(v_json)
                        num_vendedores_input.value = str(len(v_data))
                        vendedores_list.clear()
                        for idx, item in enumerate(v_data):
                            n_name = item.get("nombre", f"VENDEDOR {idx+1}")
                            d_val = str(item.get("dias", "6"))
                            vendedores_list.append(crear_vendedor_item(n_name, d_val))
                        refrescar_vendedores_container()
                    
                    recalcular_todo()
        except Exception as ex:
            print("Error al cargar metas:", ex)
    
    # Botones Pestañas Superiores
    btn_subtab_diarias = ft.ElevatedButton(
        "📅 Metas Diarias (Año Pasado - Hoja Domingo)",
        bgcolor="#6E48AA", color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: cambiar_subtab("diarias")
    )
    btn_subtab_vendedores = ft.ElevatedButton(
        "👥 Vendedores (Hoja Vendedor)",
        bgcolor="#141424", color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=lambda e: cambiar_subtab("vendedores")
    )
    
    def cambiar_subtab(tab):
        active_subtab[0] = tab
        if tab == "diarias":
            btn_subtab_diarias.bgcolor = "#6E48AA"
            btn_subtab_vendedores.bgcolor = "#222222"
            subtab_content.content = build_subtab_diarias_view()
        else:
            btn_subtab_diarias.bgcolor = "#222222"
            btn_subtab_vendedores.bgcolor = "#6E48AA"
            subtab_content.content = build_subtab_vendedores_view()
        try: page.update()
        except Exception: pass
    
    def agregar_un_vendedor():
        n = len(vendedores_list) + 1
        num_vendedores_input.value = str(n)
        ajustar_vendedores()
    
    def build_subtab_diarias_view():
        return ft.Column([
            tienda_label_diarias,
            diarias_container
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def build_subtab_vendedores_view():
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
    
    btn_guardar_registro = ft.ElevatedButton(
        "Guardar Registro 💾",
        on_click=guardar_todo_click,
        bgcolor="#7CFC00",
        color="#1e1b4b",
        height=45,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )
    
    # Carga e inicialización
    cargar_datos()
    recalcular_todo()
    subtab_content.content = build_subtab_diarias_view()
    
    return ft.Column([
        ft.Row([
            ft.Text("🎯 METAS Y METRICAS", size=24, color="#D8B4FE", weight="bold"),
            btn_guardar_registro
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        ft.Text("Módulo calcado de tu modelo de Excel para el control diario de metas y ventas por vendedor.", color="#aaaaaa", size=13),
        admin_store_bar,
        ft.Divider(height=15, color="#333333"),
        ft.Row([btn_subtab_diarias, btn_subtab_vendedores], spacing=10, wrap=True),
        ft.Container(height=10),
        subtab_content
    ], scroll=ft.ScrollMode.AUTO, expand=True)