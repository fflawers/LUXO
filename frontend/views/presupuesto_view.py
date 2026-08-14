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

def _build_presupuesto_view(
    accum_pzs,
    accum_sin,
    active_zone_filter,
    conectar_db,
    d_pzs,
    d_sin,
    day_num,
    dia,
    es_admin,
    first_weekday_py,
    meta_p,
    meta_v_con_iva,
    mostrar_snack,
    num_days,
    page,
    sales_diarias,
    t_list,
    user_info
):
    import datetime
    import calendar
    
    hoy = datetime.date.today()
    current_month = [hoy.month]
    current_year = [hoy.year]
    
    selected_zona = [user_info.get("zona") or "Zona Centro"]
    selected_tienda = [user_info.get("tienda") or ""]
    
    tiendas_por_zona = {}
    try:
        db_t = conectar_db()
        if db_t:
            cur_t = db_t.cursor(dictionary=True)
            cur_t.execute("SELECT DISTINCT Tienda, Zona FROM usuarios WHERE Tienda IS NOT NULL AND Tienda != '' ORDER BY Tienda ASC")
            for row in cur_t.fetchall():
                z = row["Zona"] or "Sin Zona"
                t_val = row["Tienda"]
                if z not in tiendas_por_zona:
                    tiendas_por_zona[z] = []
                if t_val not in tiendas_por_zona[z]:
                    tiendas_por_zona[z].append(t_val)
            db_t.close()
    except Exception as e_db:
        print("Error loading tiendas list:", e_db)
    
    # Salvaguarda: Asegurar que tiendas_por_zona nunca esté vacío
    if not tiendas_por_zona:
        tiendas_por_zona["Sin Zona"] = ["Sin Tienda"]
    
    is_mobile = (page.width < 800) if (page and page.width) else False
    
    # Si es admin, determinar selected_zona y selected_tienda
    if es_admin():
        active_z = active_zone_filter[0] if active_zone_filter[0] != "Todas" else "Zona Centro"
        if active_z not in tiendas_por_zona:
            active_z = list(tiendas_por_zona.keys())[0]
        selected_zona[0] = active_z
        if active_z in tiendas_por_zona and tiendas_por_zona[active_z]:
            if selected_tienda[0] not in tiendas_por_zona[active_z]:
                selected_tienda[0] = tiendas_por_zona[active_z][0]
    else:
        # Gerente
        selected_tienda[0] = user_info.get("tienda") or ""
        # Encontrar a qué zona pertenece esta tienda en los datos
        found_zone = "Sin Zona"
        for z, t_list in tiendas_por_zona.items():
            if selected_tienda[0] in t_list:
                found_zone = z
                break
        selected_zona[0] = found_zone
    
    # Asegurar que el valor inicial exista en las opciones del Dropdown para evitar crash de renderizado de Flet
    if selected_zona[0] not in tiendas_por_zona:
        selected_zona[0] = list(tiendas_por_zona.keys())[0]
    
    zona_tiendas = tiendas_por_zona.get(selected_zona[0], [])
    if not selected_tienda[0] or selected_tienda[0] not in zona_tiendas:
        selected_tienda[0] = zona_tiendas[0] if zona_tiendas else ""
    
    meta_venta_tf = ft.TextField(
        label="Meta Venta (Sin IVA) 💰",
        value="",
        border_color="#9D50BB",
        focused_border_color="#00FFFF",
        color="white",
        text_size=13,
        height=45,
        expand=True,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    meta_piezas_tf = ft.TextField(
        label="Meta Piezas 📦",
        value="",
        border_color="#9D50BB",
        focused_border_color="#00FFFF",
        color="white",
        text_size=13,
        height=45,
        expand=True,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    
    progress_bar_venta = ft.ProgressBar(value=0.0, color="#FF4B4B", bgcolor="#141424", height=10, border_radius=5)
    progress_text_venta = ft.Text("Venta: 0% ($0.00 / $0.00 sin IVA)", color="white", size=12)
    
    progress_bar_piezas = ft.ProgressBar(value=0.0, color="#FF4B4B", bgcolor="#141424", height=10, border_radius=5)
    progress_text_piezas = ft.Text("Piezas: 0% (0 / 0 pzs)", color="white", size=12)
    
    meses_logrados_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=180)
    
    calendar_grid = ft.Column(spacing=10, expand=True)
    
    tienda_title_txt = ft.Text("", size=18, color="#00FFFF", weight="bold")
    zona_title_txt = ft.Text("", size=12, color="#aaaaaa")
    period_title_txt = ft.Text("", size=16, color="white", weight="bold")
    
    # Rediseño: Tienda es ahora campo de texto
    txt_tienda = ft.TextField(
        label="Tienda",
        value=selected_tienda[0],
        border_color="#00FFFF",
        focused_border_color="#00FFFF",
        color="white",
        text_size=12,
        height=45,
        width=180,
        on_submit=lambda e: refresh_data()
    )
    txt_num_tienda = ft.TextField(
        label="Nº Tienda",
        value="",
        border_color="#00FFFF",
        focused_border_color="#00FFFF",
        color="white",
        text_size=12,
        height=45,
        width=100,
        on_submit=lambda e: refresh_data()
    )
    
    
    # Campos de Presupuesto Anual y Trimestres (Q1-Q4)
    txt_presupuesto_anual = ft.TextField(
        label="Presupuesto Anual (Sin IVA) 💰",
        value="",
        border_color="#9D50BB",
        focused_border_color="#00FFFF",
        color="white",
        text_size=12,
        height=45,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    txt_q1 = ft.TextField(label="Q1 Meta", value="", border_color="#9D50BB", focused_border_color="#00FFFF", color="white", text_size=11, height=38, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
    txt_q1_logro = ft.TextField(label="Q1 Venta", value="", border_color="#333333", color="#aaaaaa", text_size=11, height=38, expand=True, read_only=True)
    txt_q1_pct = ft.TextField(label="Q1 %", value="", border_color="#333333", color="#00FF7F", text_size=11, height=38, expand=True, read_only=True)
    
    txt_q2 = ft.TextField(label="Q2 Meta", value="", border_color="#9D50BB", focused_border_color="#00FFFF", color="white", text_size=11, height=38, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
    txt_q2_logro = ft.TextField(label="Q2 Venta", value="", border_color="#333333", color="#aaaaaa", text_size=11, height=38, expand=True, read_only=True)
    txt_q2_pct = ft.TextField(label="Q2 %", value="", border_color="#333333", color="#00FF7F", text_size=11, height=38, expand=True, read_only=True)
    
    txt_q3 = ft.TextField(label="Q3 Meta", value="", border_color="#9D50BB", focused_border_color="#00FFFF", color="white", text_size=11, height=38, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
    txt_q3_logro = ft.TextField(label="Q3 Venta", value="", border_color="#333333", color="#aaaaaa", text_size=11, height=38, expand=True, read_only=True)
    txt_q3_pct = ft.TextField(label="Q3 %", value="", border_color="#333333", color="#00FF7F", text_size=11, height=38, expand=True, read_only=True)
    
    txt_q4 = ft.TextField(label="Q4 Meta", value="", border_color="#9D50BB", focused_border_color="#00FFFF", color="white", text_size=11, height=38, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
    txt_q4_logro = ft.TextField(label="Q4 Venta", value="", border_color="#333333", color="#aaaaaa", text_size=11, height=38, expand=True, read_only=True)
    txt_q4_pct = ft.TextField(label="Q4 %", value="", border_color="#333333", color="#00FF7F", text_size=11, height=38, expand=True, read_only=True)
    
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    chk_meses = [
        ft.Checkbox(label=meses_nombres[i], value=False)
        for i in range(12)
    ]
    
    dd_mes = ft.Dropdown(
        label="Mes",
        value=str(current_month[0]),
        border_color="#9D50BB",
        color="white",
        text_size=12,
        height=45,
        width=120,
        options=[ft.dropdown.Option(str(i+1), meses_nombres[i]) for i in range(12)]
    )
    
    dd_anio = ft.Dropdown(
        label="Año",
        value=str(current_year[0]),
        border_color="#9D50BB",
        color="white",
        text_size=12,
        height=45,
        width=100,
        options=[ft.dropdown.Option(str(y), str(y)) for y in [2025, 2026, 2027]]
    )
    
    # Configuración de permisos/modos del Presupuesto
    if not es_admin():
        # Gerente: puede editar metas y días, pero solo de su tienda fija
        txt_tienda.disabled = True
        txt_num_tienda.disabled = True
    else:
        # Administrador: solo visualización (read-only en todos los campos de metas)
        meta_venta_tf.disabled = True
        meta_piezas_tf.disabled = True
        txt_presupuesto_anual.disabled = True
        txt_q1.disabled = True
        txt_q2.disabled = True
        txt_q3.disabled = True
        txt_q4.disabled = True
        for chk in chk_meses:
            chk.disabled = True
    
    def cargar_datos_presupuesto():
        tienda_actual = selected_tienda[0]
        mes_actual = current_month[0]
        anio_actual = current_year[0]
        
        if not tienda_actual:
            return 0.0, 0, []
        
        meta_venta = 0.0
        meta_piezas = 0
        
        try:
            db = conectar_db()
            if db:
                cur = db.cursor(dictionary=True)
                cur.execute("""
                    SELECT Meta_Venta, Meta_Piezas 
                    FROM presupuesto_mensual 
                    WHERE Tienda = %s AND Mes = %s AND Anio = %s
                """, (tienda_actual, mes_actual, anio_actual))
                row_meta = cur.fetchone()
                if row_meta:
                    meta_venta = float(row_meta["Meta_Venta"] or 0.0)
                    meta_piezas = int(row_meta["Meta_Piezas"] or 0)
                
                cur.execute("""
                    SELECT DAY(Fecha) as Dia, Venta_Con_IVA, Venta_Sin_IVA, Piezas 
                    FROM presupuesto_diario 
                    WHERE Tienda = %s AND MONTH(Fecha) = %s AND YEAR(Fecha) = %s
                """, (tienda_actual, mes_actual, anio_actual))
                ventas_diarias = cur.fetchall()
                db.close()
                return meta_venta, meta_piezas, ventas_diarias
        except Exception as ex:
            print("Error loading budget data:", ex)
        
        return 0.0, 0, []
    
    def open_edit_day_dialog(dia):
        tienda_actual = selected_tienda[0]
        mes_actual = current_month[0]
        anio_actual = current_year[0]
        
        fecha_str = f"{anio_actual:04d}-{mes_actual:02d}-{dia:02d}"
        
        existing_venta_con_iva = 0.0
        existing_piezas = 0
        
        try:
            db = conectar_db()
            if db:
                cur = db.cursor(dictionary=True)
                cur.execute("""
                    SELECT Venta_Con_IVA, Piezas 
                    FROM presupuesto_diario 
                    WHERE Tienda = %s AND Fecha = %s
                """, (tienda_actual, fecha_str))
                row = cur.fetchone()
                if row:
                    existing_venta_con_iva = float(row["Venta_Con_IVA"] or 0.0)
                    existing_piezas = int(row["Piezas"] or 0)
                db.close()
        except Exception as ex:
            print("Error loading existing day values:", ex)
        
        venta_dia_tf = ft.TextField(
            label="Venta del día con IVA ($)",
            value=str(existing_venta_con_iva) if existing_venta_con_iva > 0 else "",
            border_color="#9D50BB",
            focused_border_color="#00FFFF",
            color="white",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        piezas_dia_tf = ft.TextField(
            label="Piezas vendidas",
            value=str(existing_piezas) if existing_piezas > 0 else "",
            border_color="#9D50BB",
            focused_border_color="#00FFFF",
            color="white",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        def guardar_dia_click(e):
            try:
                v_con_iva = float(venta_dia_tf.value.strip() or 0.0)
                p_dia = int(piezas_dia_tf.value.strip() or 0)
            except ValueError:
                mostrar_snack("Por favor ingresa números válidos.", color="red")
                return
            
            v_sin_iva = v_con_iva / 1.16
            
            try:
                db = conectar_db()
                if db:
                    cur = db.cursor()
                    cur.execute("""
                        INSERT INTO presupuesto_diario (Tienda, Fecha, Venta_Con_IVA, Venta_Sin_IVA, Piezas)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            Venta_Con_IVA = %s,
                            Venta_Sin_IVA = %s,
                            Piezas = %s
                    """, (tienda_actual, fecha_str, v_con_iva, v_sin_iva, p_dia, v_con_iva, v_sin_iva, p_dia))
                    db.commit()
                    db.close()
                    
                    page.pop_dialog()
                    mostrar_snack(f"Día {dia} guardado exitosamente.", color="#7CFC00")
                    refresh_data()
            except Exception as ex:
                print("Error saving day details:", ex)
                mostrar_snack("Error al guardar en base de datos.", color="red")
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Registrar Venta - Día {dia}", color="#00FFFF", weight="bold"),
            content=ft.Column([
                ft.Text(f"Tienda: {tienda_actual}", color="#aaaaaa", size=12),
                ft.Text(f"Fecha: {fecha_str}", color="#aaaaaa", size=12),
                ft.Container(height=10),
                venta_dia_tf,
                piezas_dia_tf
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton("Guardar 💾", bgcolor="#9D50BB", color="white", on_click=guardar_dia_click)
            ],
            actions_alignment="end",
            bgcolor="#0F0F1A"
        )
        page.show_dialog(dlg)
    
    def render_meses_logrados():
        meses_logrados_col.controls.clear()
        tienda_actual = selected_tienda[0]
        anio_actual = current_year[0]
        if not tienda_actual:
            meses_logrados_col.controls.append(ft.Text("Selecciona una tienda", color="#aaaaaa", italic=True, size=12))
            return
        
        try:
            db = conectar_db()
            if db:
                cur = db.cursor(dictionary=True)
                cur.execute("""
                    SELECT 
                        m_list.Mes,
                        m.Meta_Venta,
                        m.Meta_Piezas,
                        COALESCE(SUM(d.Venta_Sin_IVA), 0) as Venta_Lograda,
                        COALESCE(SUM(d.Piezas), 0) as Piezas_Logradas
                    FROM (
                        SELECT 1 as Mes UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
                        UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 
                        UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12
                    ) m_list
                    LEFT JOIN presupuesto_mensual m ON m.Mes = m_list.Mes AND m.Tienda = %s AND m.Anio = %s
                    LEFT JOIN presupuesto_diario d ON MONTH(d.Fecha) = m_list.Mes AND YEAR(d.Fecha) = %s AND d.Tienda = %s
                    GROUP BY m_list.Mes, m.Meta_Venta, m.Meta_Piezas
                    ORDER BY m_list.Mes ASC
                """, (tienda_actual, anio_actual, anio_actual, tienda_actual))
                rows = cur.fetchall()
                db.close()
                
                has_any = False
                for row in rows:
                    m_idx = row["Mes"]
                    meta_v = float(row["Meta_Venta"] or 0.0)
                    venta_log = float(row["Venta_Lograda"] or 0.0)
                    
                    if meta_v > 0.0:
                        meta_v_sin = meta_v
                        v_pct = (venta_log / meta_v_sin) * 100 if meta_v_sin > 0 else 0.0
                        lograda = venta_log >= meta_v_sin
                        
                        has_any = True
                        icon_color = "#00FF7F" if lograda else "#FFCC00"
                        icon_name = ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED if lograda else ft.Icons.RADIO_BUTTON_UNCHECKED_OUTROUNDED
                        status_txt = "LOGRADO" if lograda else f"{v_pct:.0f}%"
                        
                        meses_logrados_col.controls.append(
                            ft.Row([
                                ft.Icon(icon_name, color=icon_color, size=16),
                                ft.Text(f"{meses_nombres[m_idx-1]} ({status_txt})", color="white" if lograda else "#cccccc", size=12, weight="bold" if lograda else "normal"),
                            ], spacing=5)
                        )
                
                if not has_any:
                    meses_logrados_col.controls.append(ft.Text("Ninguna meta de ventas definida en este año.", color="#aaaaaa", italic=True, size=11))
        except Exception as ex:
            print("Error in render_meses_logrados:", ex)
            meses_logrados_col.controls.append(ft.Text("Error al cargar logros.", color="red", size=12))
    
    def render_calendar(daily_accum_map):
        calendar_grid.controls.clear()
        
    
    
    
        days_headers = ["DOM", "LUN", "MAR", "MIE", "JUE", "VIE", "SAB"]
        header_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(h, color="#D8B4FE", weight="bold", size=10, text_align="center"),
                    expand=True,
                    alignment=ft.alignment.Alignment(0, 0),
                    padding=5
                ) for h in days_headers
            ],
            spacing=5
        )
        calendar_grid.controls.append(header_row)
    
        year = current_year[0]
        month = current_month[0]
        first_weekday_py, num_days = calendar.monthrange(year, month)
        start_offset = (first_weekday_py + 1) % 7
    
        cells = []
    
        for _ in range(start_offset):
            cells.append(
                ft.Container(
                    expand=True,
                    height=70,
                    bgcolor="#0F0F1A",
                    border_radius=6,
                    opacity=0.3,
                    border=ft.Border.all(1, "#222222")
                )
            )
    
        for d in range(1, num_days + 1):
            d_sin, d_pzs, accum_sin, accum_pzs = daily_accum_map.get(d, (0.0, 0, 0.0, 0))
    
            cell_content = None
            if d == 1:
                if is_mobile:
                    cell_content = ft.Column([
                        ft.Row([
                            ft.Text(str(d), size=10, weight="bold", color="#00FFFF"),
                        ], alignment="spaceBetween"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${d_sin:,.0f}", size=8, color="white", weight="bold"),
                                ft.Text(f"{d_pzs} pzs", size=7, color="#aaaaaa")
                            ], spacing=1, alignment="center"),
                            alignment=ft.alignment.Alignment(0, 0),
                            expand=True
                        )
                    ], spacing=2, expand=True)
                else:
                    cell_content = ft.Column([
                        ft.Row([
                            ft.Text(str(d), size=12, weight="bold", color="#00FFFF"),
                        ], alignment="spaceBetween"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${d_sin:,.0f}", size=11, color="white", weight="bold"),
                                ft.Text(f"{d_pzs} pzs", size=9, color="#aaaaaa")
                            ], spacing=1, alignment="center"),
                            alignment=ft.alignment.Alignment(0, 0),
                            expand=True
                        )
                    ], spacing=2, expand=True)
            else:
                if is_mobile:
                    cell_content = ft.Column([
                        ft.Row([
                            ft.Text(str(d), size=10, weight="bold", color="#00FFFF"),
                        ], alignment="spaceBetween"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${d_sin:,.0f}|{d_pzs}p", size=7.5, color="white"),
                            ], spacing=0, alignment="center"),
                            alignment=ft.alignment.Alignment(0, 0),
                            height=20
                        ),
                        ft.Divider(height=1, color="#333333"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${accum_sin:,.0f}|{accum_pzs}p", size=7.5, color="#7CFC00", weight="bold"),
                            ], spacing=0, alignment="center"),
                            alignment=ft.alignment.Alignment(0, 0),
                            height=20
                        )
                    ], spacing=2, expand=True)
                else:
                    cell_content = ft.Column([
                        ft.Row([
                            ft.Text(str(d), size=12, weight="bold", color="#00FFFF"),
                        ], alignment="spaceBetween"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${d_sin:,.0f} | {d_pzs}p", size=10, color="white"),
                            ], spacing=0, alignment="center"),
                            alignment=ft.alignment.Alignment(0, 0),
                            height=20
                        ),
                        ft.Divider(height=1, color="#333333"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${accum_sin:,.0f} | {accum_pzs}p", size=10, color="#7CFC00", weight="bold"),
                            ], spacing=0, alignment="center"),
                            alignment=ft.alignment.Alignment(0, 0),
                            height=20
                        )
                    ], spacing=2, expand=True)
    
            cell_container = ft.Container(
                content=cell_content,
                expand=True,
                height=75,
                bgcolor="#152238" if (d_sin > 0 or d_pzs > 0) else "#111111",
                border_radius=8,
                padding=ft.Padding(left=2, top=4, right=2, bottom=4) if is_mobile else ft.Padding(left=6, top=4, right=6, bottom=4),
                border=ft.Border.all(1, "#3c5c8c" if (d_sin > 0 or d_pzs > 0) else "#222222"),
                on_click=None if es_admin() else (lambda e, day_num=d: open_edit_day_dialog(day_num))
            )
            cells.append(cell_container)
    
        while len(cells) % 7 != 0:
            cells.append(
                ft.Container(
                    expand=True,
                    height=70,
                    bgcolor="#0F0F1A",
                    border_radius=6,
                    opacity=0.3,
                    border=ft.Border.all(1, "#222222")
                )
            )
    
        for i in range(0, len(cells), 7):
            week_cells = cells[i:i+7]
            calendar_grid.controls.append(
                ft.Row(controls=week_cells, spacing=5)
            )
    
    def cargar_datos_presupuesto_anual():
        tienda_actual = selected_tienda[0]
        anio_actual = current_year[0]
        
        if not tienda_actual:
            return
        
        try:
            db = conectar_db()
            if db:
                cur = db.cursor(dictionary=True)
                cur.execute("""
                    SELECT Numero_Tienda, Presupuesto_Anual, Presupuesto_Q1, Presupuesto_Q2, Presupuesto_Q3, Presupuesto_Q4, Meses_Logrados 
                    FROM presupuesto_anual 
                    WHERE Tienda = %s AND Anio = %s
                """, (tienda_actual, anio_actual))
                row = cur.fetchone()
                db.close()
                
                # Cargar logros reales de presupuesto_diario para los trimestres
                q_logros = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
                try:
                    db_q = conectar_db()
                    if db_q:
                        cur_q = db_q.cursor(dictionary=True)
                        cur_q.execute("""
                            SELECT MONTH(Fecha) as Mes, COALESCE(SUM(Venta_Sin_IVA), 0) as Total
                            FROM presupuesto_diario
                            WHERE Tienda = %s AND YEAR(Fecha) = %s
                            GROUP BY MONTH(Fecha)
                        """, (tienda_actual, anio_actual))
                        for row_q in cur_q.fetchall():
                            m = row_q["Mes"]
                            tot = float(row_q["Total"] or 0.0)
                            if m in (1, 2, 3):
                                q_logros[1] += tot
                            elif m in (4, 5, 6):
                                q_logros[2] += tot
                            elif m in (7, 8, 9):
                                q_logros[3] += tot
                            elif m in (10, 11, 12):
                                q_logros[4] += tot
                        db_q.close()
                except Exception as ex_q:
                    print("Error querying quarter sales:", ex_q)
    
                txt_q1_logro.value = f"${q_logros[1]:,.2f}"
                txt_q2_logro.value = f"${q_logros[2]:,.2f}"
                txt_q3_logro.value = f"${q_logros[3]:,.2f}"
                txt_q4_logro.value = f"${q_logros[4]:,.2f}"
    
                if row:
                    txt_num_tienda.value = str(row["Numero_Tienda"] or "")
                    txt_presupuesto_anual.value = str(row["Presupuesto_Anual"] or "")
                    txt_q1.value = str(row["Presupuesto_Q1"] or "")
                    txt_q2.value = str(row["Presupuesto_Q2"] or "")
                    txt_q3.value = str(row["Presupuesto_Q3"] or "")
                    txt_q4.value = str(row["Presupuesto_Q4"] or "")
                    
                    # Calcular porcentajes
                    try:
                        q1_meta = float(row["Presupuesto_Q1"] or 0.0)
                        txt_q1_pct.value = f"{(q_logros[1] / q1_meta * 100):.1f}%" if q1_meta > 0 else "0.0%"
                    except Exception:
                        txt_q1_pct.value = "0.0%"
    
                    try:
                        q2_meta = float(row["Presupuesto_Q2"] or 0.0)
                        txt_q2_pct.value = f"{(q_logros[2] / q2_meta * 100):.1f}%" if q2_meta > 0 else "0.0%"
                    except Exception:
                        txt_q2_pct.value = "0.0%"
    
                    try:
                        q3_meta = float(row["Presupuesto_Q3"] or 0.0)
                        txt_q3_pct.value = f"{(q_logros[3] / q3_meta * 100):.1f}%" if q3_meta > 0 else "0.0%"
                    except Exception:
                        txt_q3_pct.value = "0.0%"
    
                    try:
                        q4_meta = float(row["Presupuesto_Q4"] or 0.0)
                        txt_q4_pct.value = f"{(q_logros[4] / q4_meta * 100):.1f}%" if q4_meta > 0 else "0.0%"
                    except Exception:
                        txt_q4_pct.value = "0.0%"
    
                    logrados_str = row["Meses_Logrados"] or ""
                    logrados_list = [m.strip().lower() for m in logrados_str.split(",") if m.strip()]
                    for i, chk in enumerate(chk_meses):
                        chk.value = meses_nombres[i].lower() in logrados_list
                else:
                    txt_num_tienda.value = ""
                    txt_presupuesto_anual.value = ""
                    txt_q1.value = ""
                    txt_q2.value = ""
                    txt_q3.value = ""
                    txt_q4.value = ""
                    
                    txt_q1_pct.value = "0.0%"
                    txt_q2_pct.value = "0.0%"
                    txt_q3_pct.value = "0.0%"
                    txt_q4_pct.value = "0.0%"
                    
                    for chk in chk_meses:
                        chk.value = False
        except Exception as ex:
            print("Error loading presupuesto anual:", ex)
    
    def guardar_presupuesto_anual_click(e):
        tienda_actual = selected_tienda[0]
        anio_actual = current_year[0]
        
        if not tienda_actual:
            mostrar_snack("Por favor ingresa una tienda.", color="red")
            return
        
        num_t = txt_num_tienda.value.strip()
        p_anual = 0.0
        try:
            p_anual = float(txt_presupuesto_anual.value.strip()) if txt_presupuesto_anual.value.strip() else 0.0
        except ValueError:
            mostrar_snack("El presupuesto anual debe ser un número válido.", color="red")
            return
        
        q1_val = 0.0
        try:
            q1_val = float(txt_q1.value.strip()) if txt_q1.value.strip() else 0.0
        except ValueError:
            mostrar_snack("El presupuesto Q1 debe ser un número válido.", color="red")
            return
    
        q2_val = 0.0
        try:
            q2_val = float(txt_q2.value.strip()) if txt_q2.value.strip() else 0.0
        except ValueError:
            mostrar_snack("El presupuesto Q2 debe ser un número válido.", color="red")
            return
    
        q3_val = 0.0
        try:
            q3_val = float(txt_q3.value.strip()) if txt_q3.value.strip() else 0.0
        except ValueError:
            mostrar_snack("El presupuesto Q3 debe ser un número válido.", color="red")
            return
    
        q4_val = 0.0
        try:
            q4_val = float(txt_q4.value.strip()) if txt_q4.value.strip() else 0.0
        except ValueError:
            mostrar_snack("El presupuesto Q4 debe ser un número válido.", color="red")
            return
    
        logrados = []
        for i, chk in enumerate(chk_meses):
            if chk.value:
                logrados.append(meses_nombres[i])
        logrados_str = ",".join(logrados)
    
        try:
            db = conectar_db()
            if db:
                cur = db.cursor()
                cur.execute("SELECT COUNT(*) FROM presupuesto_anual WHERE Tienda = %s AND Anio = %s", (tienda_actual, anio_actual))
                exists = cur.fetchone()[0] > 0
                
                if exists:
                    cur.execute("""
                        UPDATE presupuesto_anual 
                        SET Numero_Tienda = %s, Presupuesto_Anual = %s, Presupuesto_Q1 = %s, Presupuesto_Q2 = %s, Presupuesto_Q3 = %s, Presupuesto_Q4 = %s, Meses_Logrados = %s 
                        WHERE Tienda = %s AND Anio = %s
                    """, (num_t, p_anual, q1_val, q2_val, q3_val, q4_val, logrados_str, tienda_actual, anio_actual))
                else:
                    cur.execute("""
                        INSERT INTO presupuesto_anual (Tienda, Anio, Numero_Tienda, Presupuesto_Anual, Presupuesto_Q1, Presupuesto_Q2, Presupuesto_Q3, Presupuesto_Q4, Meses_Logrados) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (tienda_actual, anio_actual, num_t, p_anual, q1_val, q2_val, q3_val, q4_val, logrados_str))
                db.commit()
                db.close()
                mostrar_snack("✅ Configuración de Bouget Anual guardada.", color="#7CFC00")
                refresh_data()
        except Exception as ex:
            print("Error saving presupuesto anual:", ex)
            mostrar_snack("Error al guardar la configuración anual.", color="red")
    
    last_tienda = [selected_tienda[0]]
    last_num_tienda = [""]
    
    def autorellenar_tienda():
        t_nombre = txt_tienda.value.strip()
        t_numero = txt_num_tienda.value.strip()
        
        cambio_nombre = (t_nombre != last_tienda[0])
        cambio_numero = (t_numero != last_num_tienda[0])
        
        if cambio_nombre and not cambio_numero:
            try:
                db = conectar_db()
                if db:
                    cur = db.cursor()
                    cur.execute("SELECT Numero_Tienda FROM presupuesto_anual WHERE Tienda = %s LIMIT 1", (t_nombre,))
                    row = cur.fetchone()
                    db.close()
                    if row and row[0]:
                        txt_num_tienda.value = str(row[0])
                        last_num_tienda[0] = str(row[0])
                    else:
                        txt_num_tienda.value = ""
                        last_num_tienda[0] = ""
            except Exception as e:
                print("Error buscando número:", e)
            last_tienda[0] = t_nombre
        elif cambio_numero and not cambio_nombre:
            try:
                db = conectar_db()
                if db:
                    cur = db.cursor()
                    cur.execute("SELECT Tienda FROM presupuesto_anual WHERE Numero_Tienda = %s LIMIT 1", (t_numero,))
                    row = cur.fetchone()
                    db.close()
                    if row and row[0]:
                        txt_tienda.value = str(row[0])
                        selected_tienda[0] = str(row[0])
                        last_tienda[0] = str(row[0])
                    else:
                        txt_tienda.value = ""
                        selected_tienda[0] = ""
                        last_tienda[0] = ""
            except Exception as e:
                print("Error buscando nombre:", e)
            last_num_tienda[0] = t_numero
        else:
            if t_nombre and not t_numero:
                try:
                    db = conectar_db()
                    if db:
                        cur = db.cursor()
                        cur.execute("SELECT Numero_Tienda FROM presupuesto_anual WHERE Tienda = %s LIMIT 1", (t_nombre,))
                        row = cur.fetchone()
                        db.close()
                        if row and row[0]:
                            txt_num_tienda.value = str(row[0])
                            last_num_tienda[0] = str(row[0])
                except Exception:
                    pass
            elif t_numero and not t_nombre:
                try:
                    db = conectar_db()
                    if db:
                        cur = db.cursor()
                        cur.execute("SELECT Tienda FROM presupuesto_anual WHERE Numero_Tienda = %s LIMIT 1", (t_numero,))
                        row = cur.fetchone()
                        db.close()
                        if row and row[0]:
                            txt_tienda.value = str(row[0])
                            selected_tienda[0] = str(row[0])
                            last_tienda[0] = str(row[0])
                except Exception:
                    pass
    
    def refresh_data():
        autorellenar_tienda()
        if dd_mes.value:
            current_month[0] = int(dd_mes.value)
        if dd_anio.value:
            current_year[0] = int(dd_anio.value)
        selected_tienda[0] = txt_tienda.value.strip()
        cargar_datos_presupuesto_anual()
        
        meta_v_con_iva, meta_p, sales_diarias = cargar_datos_presupuesto()
    
        # Mostrar el valor cargado; si es admin mostrar aunque sea 0 para que pueda ver lo que el gerente guardó
        if es_admin():
            meta_venta_tf.value = str(int(meta_v_con_iva)) if meta_v_con_iva == int(meta_v_con_iva) else str(meta_v_con_iva)
            meta_piezas_tf.value = str(meta_p)
        else:
            meta_venta_tf.value = str(meta_v_con_iva) if meta_v_con_iva > 0 else ""
            meta_piezas_tf.value = str(meta_p) if meta_p > 0 else ""
    
        meta_v_sin_iva = meta_v_con_iva if meta_v_con_iva > 0 else 0.0
    
        sales_map = {row["Dia"]: (float(row["Venta_Con_IVA"]), float(row["Venta_Sin_IVA"]), int(row["Piezas"])) for row in sales_diarias}
    
        accum_venta_sin_iva = 0.0
        accum_piezas = 0
    
        days_in_month = calendar.monthrange(current_year[0], current_month[0])[1]
        daily_accum_map = {}
    
        for d in range(1, days_in_month + 1):
            d_con, d_sin, d_pzs = sales_map.get(d, (0.0, 0.0, 0))
            accum_venta_sin_iva += d_sin
            accum_piezas += d_pzs
            daily_accum_map[d] = (d_sin, d_pzs, accum_venta_sin_iva, accum_piezas)
    
        if meta_v_sin_iva > 0:
            v_ratio = accum_venta_sin_iva / meta_v_sin_iva
            progress_bar_venta.value = min(1.0, v_ratio)
            progress_bar_venta.color = "#FF4B4B" if v_ratio < 0.5 else ("#FFCC00" if v_ratio < 1.0 else "#00FF7F")
            progress_text_venta.value = f"Ventas: {v_ratio*100:.1f}% (${accum_venta_sin_iva:,.2f} / ${meta_v_sin_iva:,.2f} sin IVA)"
        else:
            progress_bar_venta.value = 0.0
            progress_bar_venta.color = "#FF4B4B"
            progress_text_venta.value = f"Ventas: Meta no definida (${accum_venta_sin_iva:,.2f} sin IVA)"
    
        if meta_p > 0:
            p_ratio = accum_piezas / meta_p
            progress_bar_piezas.value = min(1.0, p_ratio)
            progress_bar_piezas.color = "#FF4B4B" if p_ratio < 0.5 else ("#FFCC00" if p_ratio < 1.0 else "#00FF7F")
            progress_text_piezas.value = f"Piezas: {p_ratio*100:.1f}% ({accum_piezas} / {meta_p} pzs)"
        else:
            progress_bar_piezas.value = 0.0
            progress_bar_piezas.color = "#FF4B4B"
            progress_text_piezas.value = f"Piezas: Meta no definida ({accum_piezas} pzs)"
    
        tienda_title_txt.value = selected_tienda[0].upper() if selected_tienda[0] else "SELECCIONE TIENDA"
        zona_title_txt.value = f"Nº Tienda: {txt_num_tienda.value}" if txt_num_tienda.value else ""
        period_title_txt.value = f"{meses_nombres[current_month[0]-1].upper()} {current_year[0]}"
    
        render_meses_logrados()
        render_calendar(daily_accum_map)
        try:
            page.update()
        except Exception:
            pass
    
    def guardar_metas_click(e):
        tienda_actual = selected_tienda[0]
        mes_actual = current_month[0]
        anio_actual = current_year[0]
        
        if not tienda_actual:
            mostrar_snack("Escribe una tienda primero.", color="red")
            return
        
        try:
            m_venta = float(meta_venta_tf.value.strip() or 0.0)
            m_piezas = int(meta_piezas_tf.value.strip() or 0)
        except ValueError:
            mostrar_snack("Por favor ingresa números válidos para las metas.", color="red")
            return
        
        try:
            db = conectar_db()
            if db:
                cur = db.cursor()
                cur.execute("""
                    INSERT INTO presupuesto_mensual (Tienda, Mes, Anio, Meta_Venta, Meta_Piezas)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        Meta_Venta = %s,
                        Meta_Piezas = %s
                """, (tienda_actual, mes_actual, anio_actual, m_venta, m_piezas, m_venta, m_piezas))
                db.commit()
                db.close()
                mostrar_snack("Metas guardadas exitosamente.", color="#7CFC00")
                refresh_data()
        except Exception as ex:
            print("Error saving month goals:", ex)
            mostrar_snack("Error al guardar metas.", color="red")
    
    def on_period_changed(e):
        current_month[0] = int(dd_mes.value)
        current_year[0] = int(dd_anio.value)
        refresh_data()
    
    def on_tienda_changed(e):
        selected_tienda[0] = txt_tienda.value.strip()
        refresh_data()
    
    dd_mes.on_change = on_period_changed
    dd_anio.on_change = on_period_changed
    
    btn_consultar = ft.ElevatedButton(
        "Consultar 🔍",
        bgcolor="#00FFFF",
        color="black",
        height=45,
        on_click=lambda e: refresh_data()
    )
    
    filters_row = ft.Row([
        txt_tienda,
        txt_num_tienda,
        dd_mes,
        dd_anio,
        btn_consultar
    ], spacing=10, wrap=True)
    
    btn_guardar_metas = ft.ElevatedButton(
        "Guardar Metas Mensuales 💾",
        bgcolor="#9D50BB",
        color="white",
        height=35,
        visible=not es_admin(),
        on_click=guardar_metas_click
    )
    
    btn_guardar_anual = ft.ElevatedButton(
        "Guardar Configuración Anual 💾",
        bgcolor="#6E48AA",
        color="white",
        height=35,
        visible=not es_admin(),
        on_click=guardar_presupuesto_anual_click
    )
    
    left_panel = ft.Column([
        # Card 1: Definir Metas del Mes
        ft.Container(
            content=ft.Column([
                ft.Text("Definir Metas del Mes", size=14, color="#D8B4FE", weight="bold"),
                ft.Row([
                    meta_venta_tf,
                    meta_piezas_tf
                ], spacing=10),
                btn_guardar_metas
            ], spacing=10),
            bgcolor="#0F0F1A",
            padding=15,
            border_radius=8,
            border=ft.Border.all(1, "#333333")
        ),
        
        # Card 2: Avance del Período
        ft.Container(
            content=ft.Column([
                ft.Text("Avance del Período", size=14, color="#D8B4FE", weight="bold"),
                progress_text_venta,
                progress_bar_venta,
                progress_text_piezas,
                progress_bar_piezas
            ], spacing=8),
            bgcolor="#0F0F1A",
            padding=15,
            border_radius=8,
            border=ft.Border.all(1, "#333333")
        ),
        
        # Card 3: Configuración Bouget Anual (Nuevo)
        ft.Container(
            content=ft.Column([
                ft.Text("Configuración de Bouget Anual", size=14, color="#D8B4FE", weight="bold"),
                txt_presupuesto_anual,
                ft.Container(height=5),
                ft.Text("Metas Trimestrales:", size=12, color="#aaaaaa"),
                ft.Row([
                    ft.Column([
                        ft.Text("Q1 (Ene-Mar)", size=10, weight="bold", color="#D8B4FE"),
                        txt_q1,
                        txt_q1_logro,
                        txt_q1_pct
                    ], spacing=4, expand=True),
                    ft.Column([
                        ft.Text("Q2 (Abr-Jun)", size=10, weight="bold", color="#D8B4FE"),
                        txt_q2,
                        txt_q2_logro,
                        txt_q2_pct
                    ], spacing=4, expand=True)
                ], spacing=10),
                ft.Row([
                    ft.Column([
                        ft.Text("Q3 (Jul-Sep)", size=10, weight="bold", color="#D8B4FE"),
                        txt_q3,
                        txt_q3_logro,
                        txt_q3_pct
                    ], spacing=4, expand=True),
                    ft.Column([
                        ft.Text("Q4 (Oct-Dic)", size=10, weight="bold", color="#D8B4FE"),
                        txt_q4,
                        txt_q4_logro,
                        txt_q4_pct
                    ], spacing=4, expand=True)
                ], spacing=10),
                ft.Container(height=5),
                ft.Text("Hitos: Meses logrados", size=12, color="#aaaaaa"),
                ft.Container(
                    content=ft.Row([chk_meses[i] for i in range(12)], wrap=True, spacing=10),
                    padding=5,
                    border_radius=5,
                    bgcolor="#1c1c1c"
                ),
                btn_guardar_anual
            ], spacing=10),
            bgcolor="#0F0F1A",
            padding=15,
            border_radius=8,
            border=ft.Border.all(1, "#333333")
        )
    ], spacing=15)
    
    right_panel = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Column([
                    tienda_title_txt,
                    zona_title_txt
                ], spacing=2),
                ft.Container(expand=True),
                period_title_txt
            ], vertical_alignment="center"),
            padding=ft.Padding(left=10, top=5, right=10, bottom=5)
        ),
        calendar_grid
    ], spacing=10, expand=True)
    
    responsive_layout = ft.ResponsiveRow([
        ft.Container(left_panel, col={"xs": 12, "md": 4}),
        ft.Container(right_panel, col={"xs": 12, "md": 8})
    ], spacing=20)
    
    main_col = ft.Column([
        ft.Row([
            ft.Text("Bouget 📊", size=24, color="#D8B4FE", weight="bold")
        ]),
        ft.Text("Monitorea las metas mensuales de ventas y piezas, y registra la configuración de hitos anuales.", color="#aaaaaa", size=13),
        ft.Divider(height=15, color="#333333"),
        filters_row,
        ft.Container(height=10),
        responsive_layout
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    
    refresh_data()
    return main_col