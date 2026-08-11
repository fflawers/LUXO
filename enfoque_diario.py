# -*- coding: utf-8 -*-
"""
MÓDULO ENFOQUE DIARIO 2026 - SUNGLASS HUT (SGH)
Sistema LUXO - Replicación fiel del Excel Oficial 2026 SGH ENFOQUE DIARIO.

Este módulo es 100% independiente y modular.
No modifica ninguna función existente del sistema.
"""

import os
import math
import datetime
import flet as ft

# Intentar importar reportlab para generación de PDF
try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

BASE_PATH = os.path.dirname(__file__)


# --- ESTADO GLOBAL Y MATRIZ DE DATOS ---
DIAS = ["DOMINGO", "LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"]
COLOR_TABS = {
    "SEMANAL": "#7C3AED",
    "DOMINGO": "#10B981",
    "PLAN.ACCIÓN_D": "#F59E0B",
    "LUNES": "#EF4444",
    "PLAN.ACCIÓN_L": "#F59E0B",
    "MARTES": "#EC4899",
    "PLAN.ACCIÓN_MA": "#F59E0B",
    "MIÉRCOLES": "#8B5CF6",
    "PLAN.ACCIÓN_MI": "#F59E0B",
    "JUEVES": "#3B82F6",
    "PLAN.ACCIÓN_J": "#F59E0B",
    "VIERNES": "#06B6D4",
    "PLAN.ACCIÓN_V": "#F59E0B",
    "SÁBADO": "#10B981",
    "PLAN.ACCIÓN_S": "#F59E0B"
}

# --- MATRIZ OFICIAL DE TIENDAS Y NÚMEROS REALES SGH ---
MAPEO_TIENDAS_SGH = {
    "3502": "Interlomas",
    "9277": "Ampliación Interlomas",
    "3019": "Toreo",
    "3645": "Vallejo",
    "3488": "Atizapán",
    "3586": "Punta Norte 1",
    "5256": "Punta Norte 2",
    "3583": "Satélite",
    "3507": "Lindavista",
    "8839": "Fortuna",
    "c964": "Explanada Pachuca",
    "q382": "Parque Tepeyac",
    "3542": "Galerías Pachuca",
    "3519": "Santa Fe",
    "9539": "Town Square Metepec",
    "108024": "Plaza Satélite"
}
MAPEO_NOMBRE_A_NUMERO_SGH = {v.upper(): k for k, v in MAPEO_TIENDAS_SGH.items()}

global_meta = {
    "semana": "30",
    "tienda": "Vallejo",
    "num_tienda": "3645"
}

# Inicialización de estado diario por tienda y semana
store_state = {}
for d in DIAS:
    store_state[d] = {
        "meta_diaria": 4758.0,
        "trafico_esperado": 8,
        "conversion_target": 0.13,
        "vta_ly": 4758.0,
        "wearables_pct": 0.15,
        "kids_pct": 0.05,
        "carekits_pct": 0.30,
        "atv_dia": 3620.0,
        "aur_dia": 3620.0,
        "atv_mtd": 7597.0,
        "aur_mtd": 3362.0,
        "estrellas_logro": 5,
        "trafico_bloques": [4, 2, 2, 0, 0],
        "colaboradores": [
            {"nombre": "VIVIANA", "horas": 10.0},
            {"nombre": "moises", "horas": 8.0},
            {"nombre": "diego", "horas": 8.0},
            {"nombre": "", "horas": 0.0},
            {"nombre": "", "horas": 0.0},
            {"nombre": "", "horas": 0.0},
            {"nombre": "", "horas": 0.0},
            {"nombre": "", "horas": 0.0}
        ],
        "enfoque_hoy": "Enfocar el 100% del equipo en ofrecer la solución limpiadora y bandeja de opciones para maximizar venta múltiple.",
        "logros_hoy": "Excelente retención de clientes y venta cruzada.",
        "plan_accion": [
            {"colaborador": "VIVIANA", "compromiso": "Asegurar 1 Wearable y 1 Carekit en el turno de Apertura."},
            {"colaborador": "moises", "compromiso": "Abordar el 100% del tráfico en hora pico (3pm-5pm)."},
            {"colaborador": "diego", "compromiso": "Ofrecer limpiadores en cada cierre de venta."}
        ]
    }

active_tab = ["DOMINGO"]

# Histórico de semanas guardadas (Semanas 1-52)
historico_semanal_state = {}

import json

STATE_FILE = os.path.join(BASE_PATH, "enfoque_diario_state.json")

def guardar_estado_persistente():
    try:
        payload = {
            "global_meta": global_meta,
            "store_state": store_state,
            "historico_semanal_state": historico_semanal_state
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
    except Exception as ex:
        print("Error al guardar estado de enfoque diario:", ex)

def cargar_estado_persistente():
    global store_state, global_meta, historico_semanal_state
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
                if "store_state" in payload:
                    store_state.update(payload["store_state"])
                if "global_meta" in payload:
                    global_meta.update(payload["global_meta"])
                if "historico_semanal_state" in payload:
                    historico_semanal_state.update(payload["historico_semanal_state"])
        else:
            guardar_estado_persistente()
    except Exception as ex:
        print("Error al cargar estado de enfoque diario:", ex)

# Cargar al importar
cargar_estado_persistente()

def guardar_semana_historico():
    key = f"S{global_meta['semana']}_{global_meta['num_tienda']}_{global_meta['tienda']}"
    import copy
    historico_semanal_state[key] = copy.deepcopy(store_state)
    guardar_estado_persistente()

def cargar_semana_historico(num_semana):
    global_meta["semana"] = str(num_semana)
    key = f"S{num_semana}_{global_meta['num_tienda']}_{global_meta['tienda']}"
    if key in historico_semanal_state:
        import copy
        global store_state
        store_state.clear()
        store_state.update(copy.deepcopy(historico_semanal_state[key]))
    guardar_estado_persistente()

def sincronizar_colaboradores_db(user_info=None, tienda_name=None):
    """Consulta los colaboradores registrados en la base de datos de Configuración de Tienda y los auto-llena en Enfoque Diario 2026."""
    db_names = []
    try:
        target_t = tienda_name or global_meta.get("tienda", "Vallejo")
        from main import conectar_db
        db = conectar_db()
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT v.Nombre_Completo 
                FROM vendedores v
                JOIN usuarios u ON v.ID_Usuario_Tienda = u.ID_Usuario
                WHERE LOWER(u.Tienda) = LOWER(%s) AND v.Activo = 1
                ORDER BY v.ID_Vendedor ASC
            """, (target_t,))
            rows = cursor.fetchall()
            if not rows and isinstance(user_info, dict):
                user_id = user_info.get("id", 1)
                cursor.execute("""
                    SELECT Nombre_Completo FROM vendedores
                    WHERE (ID_Usuario_Tienda = %s OR ID_Usuario_Tienda = 1) AND Activo = 1
                    ORDER BY ID_Vendedor ASC
                """, (user_id,))
                rows = cursor.fetchall()
            db.close()
            db_names = [r["Nombre_Completo"] for r in rows if r.get("Nombre_Completo")]
    except Exception as ex:
        print("Error sincronizando colaboradores DB:", ex)

    if db_names:
        for d in DIAS:
            for i in range(8):
                if i < len(db_names):
                    store_state[d]["colaboradores"][i]["nombre"] = db_names[i]
                    if store_state[d]["colaboradores"][i]["horas"] <= 0:
                        store_state[d]["colaboradores"][i]["horas"] = 10.0 if i == 0 else 8.0
                else:
                    store_state[d]["colaboradores"][i]["nombre"] = ""
                    store_state[d]["colaboradores"][i]["horas"] = 0.0
        guardar_estado_persistente()

# --- FUNCIONES MATEMÁTICAS EXPORTADAS AL MÓDULO ---
def calcular_dia(d_name):
    data = store_state[d_name]
    m_diaria = data["meta_diaria"]
    analogos = m_diaria * 0.85
    wearables = m_diaria * 0.15
    
    trafico = data["trafico_esperado"]
    conv = data["conversion_target"]
    transacciones = math.ceil(trafico * conv) if trafico > 0 else 0
    meta_ideal = m_diaria * 1.10
    total_unidades = max(transacciones, 1)

    vta_neta_prod = (m_diaria / total_unidades) if total_unidades > 0 else 0.0
    vta_ly = data["vta_ly"]

    b_trafico = data["trafico_bloques"]
    tot_trafico_b = sum(b_trafico)
    b_pesos = [(t / tot_trafico_b) if tot_trafico_b > 0 else 0.0 for t in b_trafico]
    b_metas = [p * m_diaria for p in b_pesos]

    colabs = data["colaboradores"]
    tot_horas = sum(c["horas"] for c in colabs if c["nombre"].strip() and c["horas"] > 0)
    u_prod = round(total_unidades / tot_horas, 2) if tot_horas > 0 else 0.0

    colab_rows = []
    for c in colabs:
        nom = c["nombre"].strip()
        hrs = c["horas"]
        if hrs > 0 and tot_horas > 0:
            m_vta = (m_diaria / tot_horas) * hrs
            m_ana = max(math.ceil((analogos / tot_horas) * hrs), 1)
            m_wea = max(math.ceil((wearables / tot_horas) * hrs), 1)
            m_kid = max(math.ceil(((data["kids_pct"] * m_diaria) / tot_horas) * hrs), 1)
            m_ck = max(math.ceil(((data["carekits_pct"] * m_diaria) / tot_horas) * hrs), 1)
        else:
            m_vta = 0.0
            m_ana = 0
            m_wea = 0
            m_kid = 0
            m_ck = 0
        
        colab_rows.append({
            "nombre": nom,
            "horas": hrs,
            "meta_vta": m_vta,
            "meta_ana": m_ana,
            "meta_wea": m_wea,
            "meta_kid": m_kid,
            "meta_ck": m_ck
        })

    return {
        "meta_diaria": m_diaria,
        "analogos": analogos,
        "wearables": wearables,
        "total_unidades": total_unidades,
        "transacciones": transacciones,
        "meta_ideal": meta_ideal,
        "vta_neta_prod": vta_neta_prod,
        "u_prod": u_prod,
        "vta_ly": vta_ly,
        "tot_trafico_b": tot_trafico_b,
        "b_pesos": b_pesos,
        "b_metas": b_metas,
        "tot_horas": tot_horas,
        "colab_rows": colab_rows
    }

# --- GENERADOR DE EXCEL OFICIAL SGH (.xlsx) ---
def generar_excel_enfoque(d_name, page=None):
    try:
        import openpyxl
        calc = calcular_dia(d_name)
        data = store_state[d_name]

        template_path = os.path.join(BASE_PATH, "2026 SGH ENFOQUE DIARIO- Nuestra meta y plan de accion FINAL.xlsx")
        if not os.path.exists(template_path):
            template_path = os.path.join(BASE_PATH, "plantilla_sgh_2026.xlsx")
        if not os.path.exists(template_path):
            downloads_template = os.path.join(os.path.expanduser("~"), "Downloads", "2026 SGH ENFOQUE DIARIO- Nuestra meta y plan de accion FINAL.xlsx")
            if os.path.exists(downloads_template):
                template_path = downloads_template

        if os.path.exists(template_path):
            wb = openpyxl.load_workbook(template_path)
            for d in DIAS:
                if d in wb.sheetnames:
                    ws = wb[d]
                    d_data = store_state[d]

                    ws['I1'] = int(global_meta['semana']) if str(global_meta['semana']).isdigit() else global_meta['semana']
                    ws['K1'] = datetime.datetime.now()
                    ws['M1'] = global_meta['tienda']

                    ws['C5'] = d_data['meta_diaria']
                    ws['F5'] = d_data['trafico_esperado']
                    ws['F6'] = d_data['conversion_target']
                    ws['E9'] = d_data['vta_ly']
                    ws['I5'] = d_data['wearables_pct']
                    ws['I6'] = d_data['kids_pct']
                    ws['I7'] = d_data['carekits_pct']

                    for i, val in enumerate(d_data['trafico_bloques']):
                        col_letter = ['C', 'D', 'E', 'F', 'G'][i]
                        ws[f'{col_letter}12'] = val

                    ws['P7'] = d_data.get('atv_dia', 7500.0)
                    ws['P9'] = d_data.get('aur_dia', 4617.0)
                    ws['P13'] = d_data.get('atv_mtd', 6578.0)
                    ws['P15'] = d_data.get('aur_mtd', 4312.0)

                    for i, c in enumerate(d_data['colaboradores']):
                        r_idx = 17 + i
                        if r_idx <= 24:
                            ws[f'B{r_idx}'] = c['nombre']
                            ws[f'D{r_idx}'] = c['horas']
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = f"Enfoque {d_name}"
            ws['A1'] = "SUNGLASS HUT (SGH) - ENFOQUE DIARIO 2026"
            ws['A2'] = f"DÍA: {d_name} | SEMANA: {global_meta['semana']} | TIENDA: {global_meta['tienda']}"
            ws['A4'] = f"Meta Diaria: ${calc['meta_diaria']:,.2f}"

        excel_filename = f"Enfoque_Diario_{d_name}_SGH_2026.xlsx"
        uploads_dir = os.path.join(BASE_PATH, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        web_excel_path = os.path.join(uploads_dir, excel_filename)
        temp_saved_path = web_excel_path + ".tmp"
        wb.save(temp_saved_path)
        try:
            wb.close()
        except Exception:
            pass

        # Realizar el cosido (stitching) para preservar las relaciones de dibujo originales y evitar duplicación de imágenes
        if os.path.exists(template_path) and os.path.exists(temp_saved_path):
            import zipfile
            import re
            try:
                with zipfile.ZipFile(template_path, 'r') as z_orig, \
                     zipfile.ZipFile(temp_saved_path, 'r') as z_temp, \
                     zipfile.ZipFile(web_excel_path, 'w', zipfile.ZIP_DEFLATED) as z_final:
                    
                    orig_names = z_orig.namelist()
                    temp_names = z_temp.namelist()
                    
                    copied_from_temp = [
                        "xl/styles.xml",
                        "xl/sharedStrings.xml",
                        "xl/workbook.xml"
                    ]
                    
                    for name in orig_names:
                        is_worksheet = re.match(r"^xl/worksheets/sheet\d+\.xml$", name)
                        if is_worksheet:
                            if name in temp_names:
                                z_final.writestr(name, z_temp.read(name))
                            else:
                                z_final.writestr(name, z_orig.read(name))
                        elif name in copied_from_temp:
                            if name in temp_names:
                                z_final.writestr(name, z_temp.read(name))
                            else:
                                z_final.writestr(name, z_orig.read(name))
                        else:
                            z_final.writestr(name, z_orig.read(name))
                
                if os.path.exists(temp_saved_path):
                    os.remove(temp_saved_path)
            except Exception as e_stitch:
                print("Error durante el stitching del Excel:", e_stitch)
                if os.path.exists(temp_saved_path):
                    if os.path.exists(web_excel_path):
                        os.remove(web_excel_path)
                    os.rename(temp_saved_path, web_excel_path)
        else:
            if os.path.exists(temp_saved_path):
                if os.path.exists(web_excel_path):
                    os.remove(web_excel_path)
                os.rename(temp_saved_path, web_excel_path)

        home_dir = os.path.expanduser("~")
        possible_desktops = [
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "OneDrive", "Desktop")
        ]
        primary_desk = None
        for d_path in possible_desktops:
            if os.path.exists(d_path):
                target_file = os.path.join(d_path, excel_filename)
                try:
                    import shutil
                    shutil.copy2(web_excel_path, target_file)
                    if not primary_desk:
                        primary_desk = target_file
                except Exception:
                    pass

        if primary_desk and os.path.exists(primary_desk):
            try:
                os.startfile(primary_desk)
            except Exception:
                pass

        if page:
            snack = ft.SnackBar(ft.Text(f"📊 Excel oficial generado y guardado en tu Escritorio: {excel_filename}", color="white"), bgcolor="#10B981")
            page.overlay.append(snack)
            snack.open = True
            page.update()

        return web_excel_path

    except Exception as ex_excel:
        print("Error generando Excel Enfoque Diario:", ex_excel)
        if page:
            snack = ft.SnackBar(ft.Text(f"❌ Error generando Excel: {ex_excel}", color="white"), bgcolor="red")
            page.overlay.append(snack)
            snack.open = True
            page.update()
        return None

# --- GENERADOR DE REPORTES EN PDF ---
def generar_pdf_enfoque_file(d_name):
    if not REPORTLAB_AVAILABLE:
        return None
    try:
        calc = calcular_dia(d_name)
        data = store_state[d_name]

        pdf_filename = f"Enfoque_Diario_{d_name}_SGH_2026.pdf"

        uploads_dir = os.path.join(BASE_PATH, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        web_pdf_path = os.path.join(uploads_dir, pdf_filename)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Heading1'], fontSize=16,
            textColor=colors.HexColor('#000000'), fontName='Helvetica-Bold', spaceAfter=4
        )
        sub_title_style = ParagraphStyle(
            'SubTitleStyle', parent=styles['Normal'], fontSize=10,
            textColor=colors.HexColor('#333333'), fontName='Helvetica-Bold', spaceAfter=8
        )
        h2_style = ParagraphStyle(
            'H2Style', parent=styles['Heading2'], fontSize=11,
            textColor=colors.HexColor('#000000'), fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'NormalStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#111111')
        )
        black_hdr_style = ParagraphStyle(
            'BlackHdrStyle', parent=styles['Normal'], fontSize=8,
            textColor=colors.HexColor('#FFFFFF'), fontName='Helvetica-Bold'
        )

        story = []
        story.append(Paragraph(f"<b>SUNGLASS HUT (SGH) - ENFOQUE DIARIO 2026</b>", title_style))
        story.append(Paragraph(f"<b>DÍA:</b> {d_name} | <b>SEMANA:</b> {global_meta['semana']} | <b>TIENDA:</b> {global_meta['tienda']} | <b>FECHA EMISIÓN:</b> {datetime.date.today().strftime('%d/%m/%Y')}", sub_title_style))
        story.append(Spacer(1, 6))

        story.append(Paragraph("<b>1. META DEL DÍA Y NO NEGOCIABLES (RESUMEN OPERATIVO)</b>", h2_style))
        meta_data_table = [
            [
                Paragraph("<b>META DEL DÍA</b>", black_hdr_style),
                Paragraph("<b>CONVERSIÓN</b>", black_hdr_style),
                Paragraph("<b>NO NEGOCIABLES</b>", black_hdr_style),
                Paragraph("<b>PRODUCTIVIDAD</b>", black_hdr_style)
            ],
            [
                f"Meta Diaria: ${calc['meta_diaria']:,.2f}\nAnálogos (85%): ${calc['analogos']:,.2f}\nWearables (15%): ${calc['wearables']:,.2f}\nTotal Unidades: {calc['total_unidades']}\nEvaluación: {'⭐' * data['estrellas_logro']}",
                f"Tráfico Esperado: {data['trafico_esperado']}\nConversión LY+1: {int(data['conversion_target']*100)}%\nTransacciones Target: {calc['transacciones']}\nMeta Ideal (110%): ${calc['meta_ideal']:,.2f}",
                f"Wearables: 15% (Min 1)\nKids: 5% (Min 1)\nCarekits: 30% (Min 1)",
                f"Vta Neta: ${calc['vta_neta_prod']:,.2f}\nU.Prod: {calc['u_prod']}\nVta LY: ${calc['vta_ly']:,.2f}"
            ]
        ]
        t_meta = Table(meta_data_table, colWidths=[135, 135, 135, 135])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#999999')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F3F4F6')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>2. DESGLOSE HORARIO DE VENTA</b>", h2_style))
        bloques_names = ["Apertura-1pm", "1pm - 3pm", "3pm - 5pm", "5pm - 7pm", "7pm - Cierre", "TOTAL"]
        hdr_b = [Paragraph(f"<b>{b}</b>", black_hdr_style) for b in bloques_names]
        hdr_b.insert(0, Paragraph("<b>BLOQUE / INDICADOR</b>", black_hdr_style))

        row_trafico = ["Tráfico (⚪)"] + [str(b) for b in data["trafico_bloques"]] + [str(calc["tot_trafico_b"])]
        row_peso = ["Peso % (🟩)"] + [f"{p*100:.1f}%" for p in calc["b_pesos"]] + ["100%"]
        row_meta = ["Meta $ (🟩)"] + [f"${m:,.0f}" for m in calc["b_metas"]] + [f"${calc['meta_diaria']:,.0f}"]

        t_bloques = Table([hdr_b, row_trafico, row_peso, row_meta], colWidths=[115, 70, 70, 70, 70, 75, 70])
        t_bloques.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#999999')),
            ('BACKGROUND', (1,2), (-1,3), colors.HexColor('#E6F4EA')),
            ('PADDING', (0,0), (-1,-1), 5)
        ]))
        story.append(t_bloques)
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>3. ASIGNACIÓN POR COLABORADOR</b>", h2_style))
        colab_hdr = [Paragraph(h, black_hdr_style) for h in ["COLABORADOR", "HORAS", "META VENTA", "ANÁLOGOS", "WEARABLES", "KIDS", "CAREKITS"]]
        colab_table_data = [colab_hdr]

        for r in calc["colab_rows"]:
            if r["nombre"]:
                colab_table_data.append([
                    r["nombre"], f"{r['horas']:.1f}", f"${r['meta_vta']:,.2f}",
                    str(r["meta_ana"]), str(r["meta_wea"]), str(r["meta_kid"]), str(r["meta_ck"])
                ])

        colab_table_data.append([
            "TOTAL TIENDA", f"{calc['tot_horas']:.1f}", f"${calc['meta_diaria']:,.2f}",
            str(sum(r["meta_ana"] for r in calc["colab_rows"])),
            str(sum(r["meta_wea"] for r in calc["colab_rows"])),
            str(sum(r["meta_kid"] for r in calc["colab_rows"])),
            str(sum(r["meta_ck"] for r in calc["colab_rows"]))
        ])

        t_colab = Table(colab_table_data, colWidths=[120, 55, 95, 65, 70, 65, 70])
        t_colab.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#000000')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#999999')),
            ('BACKGROUND', (2,1), (-1,-2), colors.HexColor('#E6F4EA')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D1D5DB')),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('PADDING', (0,0), (-1,-1), 5)
        ]))
        story.append(t_colab)
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>4. PLAN DE ACCIÓN, LOS 5 SECRETOS Y CUSTOMER JOURNEY</b>", h2_style))
        story.append(Paragraph(f"<b>Los 5 Secretos:</b> 1. Pulir es poder | 2. Póntelos | 3. Diviértete más | 4. Cuídalos | 5. Ajuste perfecto", normal_style))
        story.append(Paragraph(f"<b>Customer Journey:</b> 1. Empieza una relación | 2. Gánate su confianza | 3. Interactúa y relaciona | 4. Descubre y aprende | 5. Ve más allá", normal_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Tu Enfoque Para Hoy:</b> {data['enfoque_hoy'] or 'Seguimiento continuo al 100% de la Meta Diaria.'}", normal_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Logros y Oportunidades:</b> {data['logros_hoy'] or 'Mantener la disciplina en el Customer Journey y Los 5 Secretos.'}", normal_style))

        doc = SimpleDocTemplate(
            web_pdf_path, pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        doc.build(story)

        home_dir = os.path.expanduser("~")
        possible_desktops = [
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "OneDrive", "Desktop")
        ]
        for d_path in possible_desktops:
            if os.path.exists(d_path):
                try:
                    import shutil
                    shutil.copy2(web_pdf_path, os.path.join(d_path, pdf_filename))
                except Exception:
                    pass

        return web_pdf_path
    except Exception as ex_gen:
        print("Error en generar_pdf_enfoque_file:", ex_gen)
        return None


def build_enfoque_diario_view(page: ft.Page, session_user: dict = None):
    """
    Construye la vista principal del Módulo Enfoque Diario 2026 SGH
    con navegación por pestañas (Resumen Semanal, Días y Planes de Acción).
    """
    sincronizar_colaboradores_db(session_user)

    def generar_pdf_enfoque(target_day=None):
        if not REPORTLAB_AVAILABLE:
            snack = ft.SnackBar(ft.Text("❌ La librería ReportLab no está instalada para generar PDF.", color="white"), bgcolor="red")
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return

        try:
            if target_day:
                d_name = target_day
            else:
                curr_tab = active_tab[0]
                d_name = curr_tab.replace("PLAN.ACCIÓN_", "")
                code_map = {"D": "DOMINGO", "L": "LUNES", "MA": "MARTES", "MI": "MIÉRCOLES", "J": "JUEVES", "V": "VIERNES", "S": "SÁBADO"}
                d_name = code_map.get(d_name, d_name if d_name in DIAS else "DOMINGO")

            pdf_path = generar_pdf_enfoque_file(d_name)
            pdf_filename = f"Enfoque_Diario_{d_name}_SGH_2026.pdf"
            pdf_url = f"/uploads/{pdf_filename}"

            def cerrar_dialogo(e):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color="#10B981", size=24),
                    ft.Text(f"Reporte PDF ({d_name}) Listo 📄", color="white", weight="bold", size=16)
                ], spacing=8),
                content=ft.Column([
                    ft.Text("Tu reporte ha sido generado y guardado en tu Escritorio de Windows:", color="#CCCCCC", size=12),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FOLDER_ROUNDED, color="#FFD700", size=18),
                            ft.Text(pdf_filename, color="#00FFFF", weight="bold", size=12)
                        ], spacing=6),
                        bgcolor="#111827", padding=12, border_radius=8, border=ft.Border.all(1, "#374151")
                    ),
                    ft.Text("Haz clic en el botón de abajo para abrir o descargar el PDF directamente en tu navegador:", color="#AAAAAA", size=11),
                ], spacing=12, main_axis_alignment="center", tight=True),
                actions=[
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, color="white", size=16),
                            ft.Text("⬇️ Abrir / Descargar PDF en Navegador", color="white", weight="bold", size=12)
                        ], spacing=6),
                        style=ft.ButtonStyle(bgcolor="#10B981", shape=ft.RoundedRectangleBorder(radius=8)),
                        url=pdf_url,
                        on_click=cerrar_dialogo
                    ),
                    ft.TextButton("Cerrar", on_click=cerrar_dialogo)
                ],
                actions_alignment="end",
                bgcolor="#06070B",
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.startfile(pdf_path)
                except Exception:
                    pass

        except Exception as ex:
            print("Error en generar_pdf_enfoque:", ex)

    # --- COMPONENTES VISUALES ---

    # Re-renderizador del contenedor activo
    def update_active_view():
        curr_tab = active_tab[0]
        if curr_tab == "SEMANAL":
            tab_content_container.content = build_semanal_ui()
        elif curr_tab.startswith("PLAN.ACCIÓN_"):
            d_code = curr_tab.replace("PLAN.ACCIÓN_", "")
            code_map = {"D": "DOMINGO", "L": "LUNES", "MA": "MARTES", "MI": "MIÉRCOLES", "J": "JUEVES", "V": "VIERNES", "S": "SÁBADO"}
            d_real = code_map.get(d_code, "DOMINGO")
            tab_content_container.content = build_plan_accion_ui(d_real)
        else:
            tab_content_container.content = build_sheet_ui(curr_tab)
            
        try:
            d_name = curr_tab
            if d_name.startswith("PLAN.ACCIÓN_"):
                d_code = d_name.replace("PLAN.ACCIÓN_", "")
                code_map = {"D": "DOMINGO", "L": "LUNES", "MA": "MARTES", "MI": "MIÉRCOLES", "J": "JUEVES", "V": "VIERNES", "S": "SÁBADO"}
                d_name = code_map.get(d_code, "DOMINGO")
            elif d_name == "SEMANAL":
                d_name = "DOMINGO"

            btn_download_excel.url = f"/api/download_excel/{d_name}"
            btn_download_pdf.url = f"/print_enfoque/{d_name}"
            btn_download_excel.update()
            btn_download_pdf.update()
        except Exception:
            pass
            
        page.update()

    # Callback al modificar celdas globales de Semana/Tienda
    def on_global_header_change(e):
        if e.control.data == "semana":
            global_meta["semana"] = e.control.value
        elif e.control.data == "tienda":
            global_meta["tienda"] = e.control.value
        guardar_estado_persistente()

    # --- CONSTRUCCIÓN DE INTERFAZ GRÁFICA DE HOJA DIARIA ---
    def build_sheet_ui(d_name):
        calc = calcular_dia(d_name)
        data = store_state[d_name]
        try:
            generar_pdf_enfoque_file(d_name)
        except Exception:
            pass

        green_txts = {}

        def make_green_calc(key, val_str, width=120):
            t_obj = ft.Text(val_str, size=12, weight="bold", color="#00FF88")
            green_txts[key] = t_obj
            return ft.Container(
                content=t_obj,
                bgcolor="#052C1E",
                border=ft.Border.all(1, "#10B981"),
                border_radius=6,
                padding=8,
                alignment=ft.alignment.Alignment(0, 0),
                width=width
            )

        def sync_green_cells():
            c = calcular_dia(d_name)
            if "analogos" in green_txts: green_txts["analogos"].value = f"${c['analogos']:,.2f}"
            if "wearables" in green_txts: green_txts["wearables"].value = f"${c['wearables']:,.2f}"
            if "total_unidades" in green_txts: green_txts["total_unidades"].value = f"{c['total_unidades']} Pza"
            if "transacciones" in green_txts: green_txts["transacciones"].value = f"{c['transacciones']} Transac."
            if "meta_ideal" in green_txts: green_txts["meta_ideal"].value = f"${c['meta_ideal']:,.2f}"
            if "vta_neta_prod" in green_txts: green_txts["vta_neta_prod"].value = f"${c['vta_neta_prod']:,.2f}"
            if "u_prod" in green_txts: green_txts["u_prod"].value = f"{c['u_prod']}"
            if "tot_trafico_b" in green_txts: green_txts["tot_trafico_b"].value = str(c["tot_trafico_b"])
            
            for idx, p in enumerate(c["b_pesos"]):
                if f"b_peso_{idx}" in green_txts: green_txts[f"b_peso_{idx}"].value = f"{p*100:.1f}%"
            for idx, m in enumerate(c["b_metas"]):
                if f"b_meta_{idx}" in green_txts: green_txts[f"b_meta_{idx}"].value = f"${m:,.0f}"
            if "b_meta_tot" in green_txts: green_txts["b_meta_tot"].value = f"${c['meta_diaria']:,.0f}"

            for idx, r in enumerate(c["colab_rows"]):
                if f"colab_vta_{idx}" in green_txts: green_txts[f"colab_vta_{idx}"].value = f"${r['meta_vta']:,.2f}"
                if f"colab_ana_{idx}" in green_txts: green_txts[f"colab_ana_{idx}"].value = str(r['meta_ana'])
                if f"colab_wea_{idx}" in green_txts: green_txts[f"colab_wea_{idx}"].value = str(r['meta_wea'])
                if f"colab_kid_{idx}" in green_txts: green_txts[f"colab_kid_{idx}"].value = str(r['meta_kid'])
                if f"colab_ck_{idx}" in green_txts: green_txts[f"colab_ck_{idx}"].value = str(r['meta_ck'])

            if "tot_colab_hrs" in green_txts: green_txts["tot_colab_hrs"].value = f"{c['tot_horas']:.1f} hrs"
            if "tot_colab_vta" in green_txts: green_txts["tot_colab_vta"].value = f"${c['meta_diaria']:,.2f}"
            if "tot_colab_ana" in green_txts: green_txts["tot_colab_ana"].value = str(sum(r["meta_ana"] for r in c["colab_rows"]))
            if "tot_colab_wea" in green_txts: green_txts["tot_colab_wea"].value = str(sum(r["meta_wea"] for r in c["colab_rows"]))
            if "tot_colab_kid" in green_txts: green_txts["tot_colab_kid"].value = str(sum(r["meta_kid"] for r in c["colab_rows"]))
            if "tot_colab_ck" in green_txts: green_txts["tot_colab_ck"].value = str(sum(r["meta_ck"] for r in c["colab_rows"]))

        def on_white_cell_change(e):
            try:
                v = e.control.value or ""
                if e.control.data == "meta_diaria":
                    data["meta_diaria"] = float(v) if v else 0.0
                elif e.control.data == "trafico_esperado":
                    data["trafico_esperado"] = int(v) if v else 0
                elif e.control.data == "conversion_target":
                    data["conversion_target"] = (float(v) / 100.0) if v else 0.0
                elif e.control.data == "vta_ly":
                    data["vta_ly"] = float(v) if v else 0.0
                elif e.control.data == "atv_dia":
                    data["atv_dia"] = float(v) if v else 0.0
                elif e.control.data == "aur_dia":
                    data["aur_dia"] = float(v) if v else 0.0
                elif e.control.data == "atv_mtd":
                    data["atv_mtd"] = float(v) if v else 0.0
                elif e.control.data == "aur_mtd":
                    data["aur_mtd"] = float(v) if v else 0.0
                elif e.control.data.startswith("trafico_b_"):
                    idx = int(e.control.data.split("_")[-1])
                    data["trafico_bloques"][idx] = int(v) if v else 0
                elif e.control.data.startswith("colab_nom_"):
                    idx = int(e.control.data.split("_")[-1])
                    data["colaboradores"][idx]["nombre"] = v
                elif e.control.data.startswith("colab_hrs_"):
                    idx = int(e.control.data.split("_")[-1])
                    data["colaboradores"][idx]["horas"] = float(v) if v else 0.0
            except Exception:
                pass
            
            sync_green_cells()
            guardar_estado_persistente()
            try: page.update()
            except Exception: pass

        # Componente Celda Blanca (Entrada editable ⚪)
        def make_white_input(val, data_id, width=110, suffix=""):
            return ft.Container(
                content=ft.TextField(
                    value=str(val),
                    data=data_id,
                    on_change=on_white_cell_change,
                    text_size=12,
                    text_style=ft.TextStyle(weight="bold", color="#FFFFFF"),
                    bgcolor="#1F2937",
                    border_color="#374151",
                    focused_border_color="#00FFFF",
                    content_padding=8,
                    suffix=ft.Text(suffix, color="#AAAAAA", size=11) if suffix else None
                ),
                width=width
            )

        # Render Estrellas ⭐
        def set_stars(num):
            data["estrellas_logro"] = num
            update_active_view()

        star_row = ft.Row([
            ft.IconButton(
                icon=ft.Icons.STAR_ROUNDED if i <= data["estrellas_logro"] else ft.Icons.STAR_OUTLINE_ROUNDED,
                icon_color="#FFD700" if i <= data["estrellas_logro"] else "#555555",
                icon_size=20,
                on_click=lambda e, idx=i: set_stars(idx),
                padding=0
            ) for i in range(1, 6)
        ], spacing=0)

        # 1. TARJETA CABECERA DE METAS GENERATION (OFICIAL SGH)
        card_metas = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FLAG_ROUNDED, color="#00FFFF", size=18),
                    ft.Text(f"META DEL DÍA ({d_name}) Y NO NEGOCIABLES", color="white", weight="bold", size=13),
                    ft.Container(expand=True),
                    ft.Text("Evaluación:", color="#AAAAAA", size=11),
                    star_row
                ], spacing=6, vertical_alignment="center"),
                ft.Divider(height=8, color="#374151"),
                ft.Row([
                    # Columna 1: Meta del Día (Negro / Cian)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("META DEL DÍA (NEGRO)", color="#00FFFF", weight="bold", size=11),
                            ft.Text("Meta Diaria (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data["meta_diaria"], "meta_diaria", width=130, suffix="$"),
                            ft.Text("Análogos 85% (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("analogos", f"${calc['analogos']:,.2f}", width=130),
                            ft.Text("Wearables 15% (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("wearables", f"${calc['wearables']:,.2f}", width=130),
                            ft.Text("Total Unidades (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("total_unidades", f"{calc['total_unidades']} Pza", width=130),
                        ], spacing=4),
                        bgcolor="#111827", padding=10, border_radius=8, border=ft.Border.all(1, "#374151"), width=220
                    ),
                    # Columna 2: Conversión (No Negociable)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("CONVERSIÓN (NO NEGOCIABLE)", color="#F59E0B", weight="bold", size=11),
                            ft.Text("Tráfico Esperado (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data["trafico_esperado"], "trafico_esperado", width=130),
                            ft.Text("Conversión LY+1 (Manual)", color="#AAAAAA", size=10),
                            make_white_input(int(data["conversion_target"]*100), "conversion_target", width=130, suffix="%"),
                            ft.Text("Transacciones (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("transacciones", f"{calc['transacciones']} Transac.", width=130),
                            ft.Text("Meta Ideal 110% (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("meta_ideal", f"${calc['meta_ideal']:,.2f}", width=130),
                        ], spacing=4),
                        bgcolor="#111827", padding=10, border_radius=8, border=ft.Border.all(1, "#374151"), width=220
                    ),
                    # Columna 3: Otros No Negociables
                    ft.Container(
                        content=ft.Column([
                            ft.Text("OTROS NO NEGOCIABLES", color="#E040FB", weight="bold", size=11),
                            ft.Text("Wearables: 15% (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("fix_wea", f"15% (Min 1)", width=130),
                            ft.Text("Kids: 5% (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("fix_kid", f"5% (Min 1)", width=130),
                            ft.Text("Carekits: 30% (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("fix_ck", f"30% (Min 1)", width=130),
                        ], spacing=4),
                        bgcolor="#111827", padding=10, border_radius=8, border=ft.Border.all(1, "#374151"), width=220
                    ),
                    # Columna 4: Productividad & COMP LY
                    ft.Container(
                        content=ft.Column([
                            ft.Text("PRODUCTIVIDAD & COMP LY", color="#10B981", weight="bold", size=11),
                            ft.Text("Vta Neta / Prod (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("vta_neta_prod", f"${calc['vta_neta_prod']:,.2f}", width=130),
                            ft.Text("U.Prod (U/Hr) (Auto)", color="#AAAAAA", size=10),
                            make_green_calc("u_prod", f"{calc['u_prod']}", width=130),
                            ft.Text("COMP LY - Vta LY (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data["vta_ly"], "vta_ly", width=130, suffix="$"),
                        ], spacing=4),
                        bgcolor="#111827", padding=10, border_radius=8, border=ft.Border.all(1, "#374151"), width=220
                    ),
                    # Columna 5: CAPTURA DÍA COMP & MTD (ATV / AUR)
                    ft.Container(
                        content=ft.Column([
                            ft.Text("VALORES DÍA COMP & MTD", color="#FFD700", weight="bold", size=11),
                            ft.Text("ATV Día Comp (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data.get("atv_dia", 3620.0), "atv_dia", width=130, suffix="$"),
                            ft.Text("AUR Día Comp (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data.get("aur_dia", 3620.0), "aur_dia", width=130, suffix="$"),
                            ft.Text("ATV MTD (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data.get("atv_mtd", 7597.0), "atv_mtd", width=130, suffix="$"),
                            ft.Text("AUR MTD (Manual)", color="#AAAAAA", size=10),
                            make_white_input(data.get("aur_mtd", 3362.0), "aur_mtd", width=130, suffix="$"),
                        ], spacing=4),
                        bgcolor="#111827", padding=10, border_radius=8, border=ft.Border.all(1, "#374151"), width=220
                    ),
                ], spacing=10, wrap=True)
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#00FFFF"),
            shadow=[ft.BoxShadow(color="#2000FFFF", blur_radius=10, spread_radius=1)]
        )

        # 2. TARJETA DESGLOSE HORARIO POR BLOQUE
        is_mobile_w = (page.width < 800) if (page and page.width) else False
        w_lbl = 90 if is_mobile_w else 120
        w_cell = 75 if is_mobile_w else 95

        b_names = ["Apertura-1pm", "1pm - 3pm", "3pm - 5pm", "5pm - 7pm", "7pm - Cierre"]
        row_b_headers = [ft.Container(ft.Text("INDICADOR", weight="bold", color="#00FFFF", size=11), width=w_lbl)]
        for bn in b_names:
            row_b_headers.append(ft.Container(ft.Text(bn, weight="bold", color="white", size=11), width=w_cell, alignment=ft.alignment.Alignment(0, 0)))
        row_b_headers.append(ft.Container(ft.Text("TOTAL", weight="bold", color="#00FF88", size=11), width=w_cell, alignment=ft.alignment.Alignment(0, 0)))

        # Fila Tráfico (⚪)
        row_b_trafico = [ft.Container(ft.Text("Tráfico (⚪)", color="#AAAAAA", size=11), width=w_lbl)]
        for idx, tv in enumerate(data["trafico_bloques"]):
            row_b_trafico.append(make_white_input(tv, f"trafico_b_{idx}", width=w_cell))
        row_b_trafico.append(make_green_calc("tot_trafico_b", str(calc["tot_trafico_b"]), width=w_cell))

        # Fila Peso % (🟩)
        row_b_peso = [ft.Container(ft.Text("Peso % (🟩)", color="#AAAAAA", size=11), width=w_lbl)]
        for idx, p in enumerate(calc["b_pesos"]):
            row_b_peso.append(make_green_calc(f"b_peso_{idx}", f"{p*100:.1f}%", width=w_cell))
        row_b_peso.append(make_green_calc("b_peso_tot", "100%", width=w_cell))

        # Fila Meta $ (🟩)
        row_b_meta = [ft.Container(ft.Text("Meta $ (🟩)", color="#AAAAAA", size=11), width=w_lbl)]
        for idx, m in enumerate(calc["b_metas"]):
            row_b_meta.append(make_green_calc(f"b_meta_{idx}", f"${m:,.0f}", width=w_cell))
        row_b_meta.append(make_green_calc("b_meta_tot", f"${calc['meta_diaria']:,.0f}", width=w_cell))

        scrollable_horarios_table = ft.Row([
            ft.Column([
                ft.Row(row_b_headers, spacing=6),
                ft.Row(row_b_trafico, spacing=6),
                ft.Row(row_b_peso, spacing=6),
                ft.Row(row_b_meta, spacing=6)
            ], spacing=6)
        ], scroll=ft.ScrollMode.AUTO)

        card_horarios = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, color="#E040FB", size=18),
                    ft.Text("DESGLOSE HORARIO DE VENTA DE TIENDA", color="white", weight="bold", size=13)
                ], spacing=6),
                ft.Divider(height=8, color="#374151"),
                scrollable_horarios_table
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#E040FB"),
            shadow=[ft.BoxShadow(color="#20E040FB", blur_radius=10, spread_radius=1)]
        )

        # Componente Celda Bloqueada / Solo Lectura (🔒)
        def make_readonly_input(val, width=140):
            return ft.Container(
                content=ft.TextField(
                    value=str(val),
                    read_only=True,
                    text_size=12,
                    text_style=ft.TextStyle(weight="bold", color="#00FFFF"),
                    bgcolor="#111827",
                    border_color="#374151",
                    content_padding=8
                ),
                width=width
            )

        # 3. TABLA ASIGNACIÓN POR COLABORADOR
        w_colab_name = 100 if is_mobile_w else 140
        w_colab_hrs = 65 if is_mobile_w else 80
        w_colab_vta = 90 if is_mobile_w else 110
        w_colab_ana = 75 if is_mobile_w else 90
        w_colab_wea = 75 if is_mobile_w else 90
        w_colab_kid = 65 if is_mobile_w else 80
        w_colab_ck = 65 if is_mobile_w else 80

        colab_hdr_ui = ft.Row([
            ft.Container(ft.Text("COLABORADOR (🔒)", weight="bold", color="#00FFFF", size=11), width=w_colab_name),
            ft.Container(ft.Text("HORAS (⚪)", weight="bold", color="#00FFFF", size=11), width=w_colab_hrs),
            ft.Container(ft.Text("META VTA (🟩)", weight="bold", color="#00FF88", size=11), width=w_colab_vta),
            ft.Container(ft.Text("ANÁLOGOS (🟩)", weight="bold", color="#00FF88", size=11), width=w_colab_ana),
            ft.Container(ft.Text("WEARABLES (🟩)", weight="bold", color="#00FF88", size=11), width=w_colab_wea),
            ft.Container(ft.Text("KIDS (🟩)", weight="bold", color="#00FF88", size=11), width=w_colab_kid),
            ft.Container(ft.Text("CAREKITS (🟩)", weight="bold", color="#00FF88", size=11), width=w_colab_ck),
        ], spacing=6)

        colab_rows_ui = [colab_hdr_ui]
        for idx, c in enumerate(data["colaboradores"]):
            r_calc = calc["colab_rows"][idx]
            colab_rows_ui.append(
                ft.Row([
                    make_readonly_input(c["nombre"], width=w_colab_name),
                    make_white_input(c["horas"], f"colab_hrs_{idx}", width=w_colab_hrs),
                    make_green_calc(f"colab_vta_{idx}", f"${r_calc['meta_vta']:,.2f}", width=w_colab_vta),
                    make_green_calc(f"colab_ana_{idx}", str(r_calc['meta_ana']), width=w_colab_ana),
                    make_green_calc(f"colab_wea_{idx}", str(r_calc['meta_wea']), width=w_colab_wea),
                    make_green_calc(f"colab_kid_{idx}", str(r_calc['meta_kid']), width=w_colab_kid),
                    make_green_calc(f"colab_ck_{idx}", str(r_calc['meta_ck']), width=w_colab_ck),
                ], spacing=6)
            )

        # Fila Totales Colaboradores
        colab_rows_ui.append(
            ft.Row([
                ft.Container(ft.Text("TOTALES TIENDA", weight="bold", color="white", size=11), width=w_colab_name),
                make_green_calc("tot_colab_hrs", f"{calc['tot_horas']:.1f} hrs", width=w_colab_hrs),
                make_green_calc("tot_colab_vta", f"${calc['meta_diaria']:,.2f}", width=w_colab_vta),
                make_green_calc("tot_colab_ana", str(sum(r["meta_ana"] for r in calc["colab_rows"])), width=w_colab_ana),
                make_green_calc("tot_colab_wea", str(sum(r["meta_wea"] for r in calc["colab_rows"])), width=w_colab_wea),
                make_green_calc("tot_colab_kid", str(sum(r["meta_kid"] for r in calc["colab_rows"])), width=w_colab_kid),
                make_green_calc("tot_colab_ck", str(sum(r["meta_ck"] for r in calc["colab_rows"])), width=w_colab_ck),
            ], spacing=6)
        )

        scrollable_colabs_table = ft.Row([
            ft.Column(colab_rows_ui, spacing=5)
        ], scroll=ft.ScrollMode.AUTO)

        card_colabs = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE_ROUNDED, color="#00FFFF", size=18),
                    ft.Text("ASIGNACIÓN Y DISTRIBUCIÓN POR PERSONAL", color="white", weight="bold", size=13)
                ], spacing=6),
                ft.Text("💡 Celdas blancas (⚪) son editables. Las celdas verdes (🟩) calculan metas en tiempo real.", color="#AAAAAA", size=10),
                ft.Divider(height=8, color="#374151"),
                scrollable_colabs_table
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#00FFFF"),
            shadow=[ft.BoxShadow(color="#2000FFFF", blur_radius=10, spread_radius=1)]
        )

        return ft.Column([
            card_metas,
            ft.Container(height=8),
            card_horarios,
            ft.Container(height=8),
            card_colabs
        ], scroll=ft.ScrollMode.AUTO)

    # --- INTERFAZ PLAN DE ACCIÓN ---
    def build_plan_accion_ui(d_name):
        data = store_state[d_name]

        def on_enfoque_change(e):
            data["enfoque_hoy"] = e.control.value
            guardar_estado_persistente()

        def on_logros_change(e):
            data["logros_hoy"] = e.control.value
            guardar_estado_persistente()

        # Tarjetas de Los 5 Secretos (Brandies SGH)
        card_secretos = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color="#FFD700", size=18),
                    ft.Text(f"LOS 5 SECRETOS Y PLAN DE ACCIÓN ({d_name}) - OFICIAL SGH", color="white", weight="bold", size=13),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.TABLE_CHART_ROUNDED, color="white", size=15),
                            ft.Text(f"📊 Exportar Excel Plan ({d_name})", color="white", weight="bold", size=11)
                        ], spacing=4),
                        style=ft.ButtonStyle(bgcolor="#059669", shape=ft.RoundedRectangleBorder(radius=6)),
                        url=f"/api/download_excel/{d_name}"
                    ),
                    ft.Container(width=6),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PRINT_ROUNDED, color="white", size=15),
                            ft.Text(f"📄 Descargar PDF Plan ({d_name})", color="white", weight="bold", size=11)
                        ], spacing=4),
                        style=ft.ButtonStyle(bgcolor="#10B981", shape=ft.RoundedRectangleBorder(radius=6)),
                        on_click=lambda e, day=d_name: generar_pdf_enfoque(day)
                    )
                ], spacing=6, vertical_alignment="center"),
                ft.Divider(height=8, color="#374151"),
                ft.Row([
                    ft.Container(ft.Column([ft.Text("✨ 1. PULIR ES PODER", weight="bold", color="#00FFFF", size=11), ft.Text("Ofrece limpiar sus lentes al iniciar la conversación.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("🕶️ 2. PÓNTELOS", weight="bold", color="#E040FB", size=11), ft.Text("Invítalo a probar diferentes modelos en la bandeja.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("🎉 3. DIVIÉRTETE MÁS", weight="bold", color="#FFD700", size=11), ft.Text("Muestra 3 o 4 opciones adicionales para venta múltiple.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("🧼 4. CUÍDALOS", weight="bold", color="#10B981", size=11), ft.Text("Ofrece estuche, solución limpiadora y carekits.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("📐 5. AJUSTE PERFECTO", weight="bold", color="#3B82F6", size=11), ft.Text("Ajusta los armazones a la medida exacta del cliente.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                ], wrap=True, spacing=8)
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#FFD700")
        )

        # Tarjetas del Customer Journey
        card_journey = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MAP_ROUNDED, color="#00FFFF", size=18),
                    ft.Text("CUSTOMER JOURNEY (EXPERIENCIA DEL CLIENTE)", color="white", weight="bold", size=13)
                ], spacing=6),
                ft.Divider(height=8, color="#374151"),
                ft.Row([
                    ft.Container(ft.Column([ft.Text("🤝 1. Empieza una relación", weight="bold", color="#00FFFF", size=11), ft.Text("Bienvenida cálida e idéntica a los estándares SGH.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("🛡️ 2. Gánate su confianza", weight="bold", color="#E040FB", size=11), ft.Text("Escucha activa y conocimiento de producto.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("💬 3. Interactúa y relaciona", weight="bold", color="#FFD700", size=11), ft.Text("Conecta necesidades con beneficios clave.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("🔍 4. Descubre y aprende", weight="bold", color="#10B981", size=11), ft.Text("Preguntas abiertas sobre estilo de vida.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                    ft.Container(ft.Column([ft.Text("🚀 5. Ve más allá", weight="bold", color="#3B82F6", size=11), ft.Text("Cierre perfecto, garantía y despedida memorable.", color="#CCCCCC", size=10)]), bgcolor="#111827", padding=8, border_radius=8, width=190),
                ], wrap=True, spacing=8)
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#00FFFF")
        )

        card_enfoque_texto = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EDIT_NOTE_ROUNDED, color="#00FFFF", size=18),
                    ft.Text("📝 TU ENFOQUE PARA HOY", color="#00FFFF", weight="bold", size=13)
                ], spacing=6),
                ft.TextField(
                    value=data["enfoque_hoy"],
                    on_change=on_enfoque_change,
                    hint_text="Escribe aquí las acciones clave y estrategia del día...",
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    bgcolor="#111827",
                    border_color="#374151",
                    color="white",
                    text_size=12
                )
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#00FFFF")
        )

        # Evaluador de 5 estrellas para logros
        def set_stars(num):
            data["estrellas_logro"] = num
            update_active_view()

        star_row_logros = ft.Row([
            ft.Text("Calificación del día: ", color="white", weight="bold", size=12),
            *[
                ft.IconButton(
                    icon=ft.Icons.STAR_ROUNDED if i <= data["estrellas_logro"] else ft.Icons.STAR_OUTLINE_ROUNDED,
                    icon_color="#FFD700" if i <= data["estrellas_logro"] else "#555555",
                    icon_size=24,
                    on_click=lambda e, idx=i: set_stars(idx),
                    padding=0
                ) for i in range(1, 6)
            ]
        ], spacing=4, vertical_alignment="center")

        card_logros_texto = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, color="#E040FB", size=18),
                    ft.Text("🏆 LOGROS DE HOY Y OPORTUNIDADES PARA MAÑANA", color="#E040FB", weight="bold", size=13),
                    ft.Container(expand=True),
                    star_row_logros
                ], spacing=6),
                ft.TextField(
                    value=data["logros_hoy"],
                    on_change=on_logros_change,
                    hint_text="Resumen del cierre del día, compromisos y áreas de oportunidad...",
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    bgcolor="#111827",
                    border_color="#374151",
                    color="white",
                    text_size=12
                )
            ]),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#E040FB")
        )

        return ft.Column([
            card_secretos,
            ft.Container(height=8),
            card_journey,
            ft.Container(height=8),
            card_enfoque_texto,
            ft.Container(height=8),
            card_logros_texto
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    # --- INTERFAZ RESUMEN SEMANAL ---
    def build_semanal_ui():
        rows_sem = []
        tot_meta = sum(store_state[d]["meta_diaria"] for d in DIAS)
        tot_ana = tot_meta * 0.85
        tot_wea = tot_meta * 0.15
        tot_horas_sem = 0.0
        tot_transac_sem = 0

        for d in DIAS:
            c = calcular_dia(d)
            tot_horas_sem += c["tot_horas"]
            tot_transac_sem += c["transacciones"]
            rows_sem.append(
                ft.Row([
                    ft.Container(ft.Text(d, weight="bold", color="white", size=11), width=110),
                    ft.Container(ft.Text(f"${c['meta_diaria']:,.2f}", color="#00FF88", size=11, weight="bold"), width=120),
                    ft.Container(ft.Text(f"${c['analogos']:,.2f}", color="#00FF88", size=11), width=120),
                    ft.Container(ft.Text(f"${c['wearables']:,.2f}", color="#00FF88", size=11), width=120),
                    ft.Container(ft.Text(str(c['transacciones']), color="white", size=11), width=100),
                    ft.Container(ft.Text(f"{c['tot_horas']:.1f} hrs", color="white", size=11), width=100),
                ], spacing=8)
            )

        card_sem = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TABLE_CHART_ROUNDED, color="#7C3AED", size=18),
                    ft.Text(f"CONSOLIDADO DE ENFOQUE SEMANAL - SEMANA {global_meta['semana']} ({global_meta['tienda']})", color="white", weight="bold", size=13)
                ], spacing=6),
                ft.Divider(height=8, color="#374151"),
                ft.Row([
                    ft.Container(ft.Text("DÍA", weight="bold", color="#7C3AED", size=11), width=110),
                    ft.Container(ft.Text("META DIARIA", weight="bold", color="#00FF88", size=11), width=120),
                    ft.Container(ft.Text("ANÁLOGOS", weight="bold", color="#00FF88", size=11), width=120),
                    ft.Container(ft.Text("WEARABLES", weight="bold", color="#00FF88", size=11), width=120),
                    ft.Container(ft.Text("TRANSAC.", weight="bold", color="white", size=11), width=100),
                    ft.Container(ft.Text("HORAS", weight="bold", color="white", size=11), width=100),
                ], spacing=8),
                ft.Column(rows_sem, spacing=6),
                ft.Divider(height=8, color="#374151"),
                ft.Row([
                    ft.Container(ft.Text("TOTAL SEMANAL", weight="bold", color="white", size=12), width=110),
                    ft.Container(ft.Text(f"${tot_meta:,.2f}", weight="bold", color="#00FF88", size=12), width=120),
                    ft.Container(ft.Text(f"${tot_ana:,.2f}", weight="bold", color="#00FF88", size=12), width=120),
                    ft.Container(ft.Text(f"${tot_wea:,.2f}", weight="bold", color="#00FF88", size=12), width=120),
                    ft.Container(ft.Text(str(tot_transac_sem), weight="bold", color="white", size=12), width=100),
                    ft.Container(ft.Text(f"{tot_horas_sem:.1f} hrs", weight="bold", color="white", size=12), width=100),
                ], spacing=8)
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="#0B0E17",
            padding=14,
            border_radius=12,
            border=ft.Border.all(1.5, "#7C3AED")
        )

        return card_sem

    # --- NAVEGACIÓN Y CAMBIO DE PESTAÑAS ---
    tab_content_container = ft.Container(content=build_sheet_ui("DOMINGO"))

    def select_tab(tab_name):
        active_tab[0] = tab_name
        for btn, t_id in tab_buttons:
            is_sel = (t_id == tab_name)
            col_base = COLOR_TABS.get(t_id, "#00FFFF")
            btn.content.color = "white" if is_sel else "#CCCCCC"
            btn.bgcolor = col_base if is_sel else "#111827"
            btn.border = ft.Border.all(1.5, col_base if is_sel else "#374151")

        update_active_view()

    # Construcción de botones de pestañas
    TABS_LIST = [
        ("📊 SEMANAL", "SEMANAL"),
        ("☀️ DOMINGO", "DOMINGO"),
        ("📋 PLAN DOMINGO", "PLAN.ACCIÓN_D"),
        ("🌙 LUNES", "LUNES"),
        ("📋 PLAN LUNES", "PLAN.ACCIÓN_L"),
        ("🔥 MARTES", "MARTES"),
        ("📋 PLAN MARTES", "PLAN.ACCIÓN_MA"),
        ("⚡ MIÉRCOLES", "MIÉRCOLES"),
        ("📋 PLAN MIÉRCOLES", "PLAN.ACCIÓN_MI"),
        ("🚀 JUEVES", "JUEVES"),
        ("📋 PLAN JUEVES", "PLAN.ACCIÓN_J"),
        ("💎 VIERNES", "VIERNES"),
        ("📋 PLAN VIERNES", "PLAN.ACCIÓN_V"),
        ("👑 SÁBADO", "SÁBADO"),
        ("📋 PLAN SÁBADO", "PLAN.ACCIÓN_S")
    ]

    tab_buttons = []
    tab_row_controls = []
    for label, t_id in TABS_LIST:
        is_sel = (t_id == active_tab[0])
        col_base = COLOR_TABS.get(t_id, "#00FFFF")
        btn = ft.Container(
            content=ft.Text(label, color="white" if is_sel else "#CCCCCC", size=11, weight="bold"),
            bgcolor=col_base if is_sel else "#111827",
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=8,
            border=ft.Border.all(1.5, col_base if is_sel else "#374151"),
            on_click=lambda e, tid=t_id: select_tab(tid),
            ink=True
        )
        tab_buttons.append((btn, t_id))
        tab_row_controls.append(btn)

    tab_navigation_bar = ft.Row(tab_row_controls, scroll=ft.ScrollMode.AUTO, spacing=6)

    # --- BARRA SUPERIOR CON BOTÓN PDF Y CAMPOS DE ENCABEZADO ---
    # --- VERIFICACIÓN DE ROL Y USUARIO ---
    es_admin = False
    if session_user and isinstance(session_user, dict):
        u_rol = str(session_user.get("rol", "")).lower()
        u_name = str(session_user.get("user", "")).lower()
        if u_rol in ["admin", "administrador"] or u_name in ["mx204562", "clorio", "ricardo", "gerry", "cesar", "manuel"]:
            es_admin = True

    if not es_admin and session_user and isinstance(session_user, dict):
        u_tienda = session_user.get("tienda") or session_user.get("Tienda")
        u_user = session_user.get("usuario") or session_user.get("Usuario") or ""
        num_code = u_user.lower().replace("sgh", "").strip()
        if u_tienda and u_tienda != "Tienda Luxo":
            global_meta["tienda"] = u_tienda
            if num_code in MAPEO_TIENDAS_SGH:
                global_meta["num_tienda"] = num_code
            elif u_tienda.upper() in MAPEO_NOMBRE_A_NUMERO_SGH:
                global_meta["num_tienda"] = MAPEO_NOMBRE_A_NUMERO_SGH[u_tienda.upper()]

    # Sincronizar colaboradores iniciales
    sincronizar_colaboradores_db(session_user, global_meta["tienda"])

    # 0. Selector de Año (2025, 2026, 2027, 2028)
    global_meta.setdefault("anio", "2026")

    def on_anio_change(e):
        global_meta["anio"] = e.control.value
        guardar_estado_persistente()
        update_active_view()

    dd_anio = ft.Dropdown(
        value=str(global_meta["anio"]),
        options=[ft.dropdown.Option(str(y)) for y in [2026, 2025, 2027, 2028]],
        width=80,
        content_padding=6,
        text_size=11,
        text_style=ft.TextStyle(weight="bold", color="#FFFFFF"),
        bgcolor="#1F2937",
        border_color="#374151",
        border_radius=6
    )
    dd_anio.on_change = on_anio_change

    # 1. Selector de Semana (1 a 52)
    def on_semana_change(e):
        guardar_semana_historico()
        n_sem = e.control.value
        cargar_semana_historico(n_sem)
        guardar_estado_persistente()
        update_active_view()
        if page:
            snack = ft.SnackBar(ft.Text(f"📅 Semana {n_sem} cargada.", color="white"), bgcolor="#059669")
            page.overlay.append(snack)
            snack.open = True
            page.update()

    dd_semana = ft.Dropdown(
        value=str(global_meta["semana"]),
        options=[ft.dropdown.Option(str(w)) for w in range(1, 53)],
        width=75,
        content_padding=6,
        text_size=11,
        text_style=ft.TextStyle(weight="bold", color="#FFFFFF"),
        bgcolor="#1F2937",
        border_color="#374151",
        border_radius=6
    )
    dd_semana.on_change = on_semana_change

    # 2. Campo # TIENDA (Número de Tienda SGH)
    def on_num_tienda_change(e):
        val = e.control.value.strip()
        global_meta["num_tienda"] = val
        if val in MAPEO_TIENDAS_SGH:
            t_matched = MAPEO_TIENDAS_SGH[val]
            global_meta["tienda"] = t_matched
            dd_tienda.value = t_matched
            sincronizar_colaboradores_db(session_user, t_matched)
            guardar_estado_persistente()
            update_active_view()

    txt_num_tienda = ft.TextField(
        value=global_meta["num_tienda"],
        read_only=not es_admin,
        width=85,
        text_size=11,
        text_style=ft.TextStyle(weight="bold", color="#00FFFF" if es_admin else "#00FF88"),
        bgcolor="#111827" if es_admin else "#1F2937",
        border_color="#00FFFF" if es_admin else "#374151",
        content_padding=6,
        on_change=on_num_tienda_change if es_admin else None,
        tooltip="Número de Tienda SGH (🔒 Fijo para Gerentes)" if not es_admin else "Ingrese número de tienda"
    )

    # 3. Desplegable NOMBRE DE TIENDA (16 Tiendas Oficiales)
    options_tiendas = [ft.dropdown.Option(v) for v in MAPEO_TIENDAS_SGH.values()]

    def on_store_select_change(e):
        selected_tienda = e.control.value
        global_meta["tienda"] = selected_tienda
        if selected_tienda.upper() in MAPEO_NOMBRE_A_NUMERO_SGH:
            num_code = MAPEO_NOMBRE_A_NUMERO_SGH[selected_tienda.upper()]
            global_meta["num_tienda"] = num_code
            txt_num_tienda.value = num_code

        sincronizar_colaboradores_db(session_user, selected_tienda)
        guardar_estado_persistente()
        update_active_view()
        if page:
            snack = ft.SnackBar(ft.Text(f"🏢 Tienda cambiada a {selected_tienda} (# {global_meta['num_tienda']}).", color="white"), bgcolor="#059669")
            page.overlay.append(snack)
            snack.open = True
            page.update()

    dd_tienda = ft.Dropdown(
        value=global_meta["tienda"],
        options=options_tiendas,
        disabled=not es_admin,
        width=150,
        content_padding=6,
        text_size=11,
        text_style=ft.TextStyle(weight="bold", color="#00FFFF" if es_admin else "#00FF88"),
        bgcolor="#111827" if es_admin else "#1F2937",
        border_color="#00FFFF" if es_admin else "#374151",
        border_radius=6
    )
    if es_admin:
        dd_tienda.on_change = on_store_select_change

    btn_download_excel = ft.ElevatedButton(
        content=ft.Text("📊 Exportar Excel SGH", color="white", weight="bold", size=11),
        style=ft.ButtonStyle(
            bgcolor="#059669",
            shape=ft.RoundedRectangleBorder(radius=8)
        ),
        url="/api/download_excel/DOMINGO",
        on_click=lambda e: generar_excel_enfoque(active_tab[0] if active_tab[0] in DIAS else "DOMINGO")
    )

    btn_download_pdf = ft.ElevatedButton(
        content=ft.Text("🖨️ PDF / Imprimir Día", color="white", weight="bold", size=11),
        style=ft.ButtonStyle(
            bgcolor="#10B981",
            shape=ft.RoundedRectangleBorder(radius=8)
        ),
        url="/print_enfoque/DOMINGO"
    )

    # Master Refresh Button 🔄 (Flat Neon Green Outline Style)
    def on_master_refresh_click(e):
        curr_tab = active_tab[0]
        d_name = curr_tab.replace("PLAN.ACCIÓN_", "")
        code_map = {"D": "DOMINGO", "L": "LUNES", "MA": "MARTES", "MI": "MIÉRCOLES", "J": "JUEVES", "V": "VIERNES", "S": "SÁBADO"}
        d_name = code_map.get(d_name, d_name if d_name in DIAS else "DOMINGO")
        
        calcular_dia(d_name)
        update_active_view()

        if page:
            snack = ft.SnackBar(
                content=ft.Text(f"🔄 LUXO: Datos de {d_name} ({global_meta['tienda']} #{global_meta['num_tienda']}) Sincronizados", color="white", weight="bold", size=12),
                bgcolor="#064E3B",
                duration=2000
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()

    btn_refresh_master = ft.Container(
        content=ft.Text("🔄 Recalcular Todo", color="#00FF88", weight="bold", size=11),
        border=ft.Border.all(1.5, "#00FF88"),
        border_radius=6,
        padding=8,
        bgcolor="transparent",
        ink=True,
        on_click=on_master_refresh_click,
        tooltip="Sincronizar y recalcular todas las celdas y fórmulas"
    )

    header_module = ft.Container(
        content=ft.Column([
            # Fila 1: Título Principal + Botones de Acción de Exportación y Recálculo
            ft.Row([
                ft.Text("🎯 ENFOQUE DIARIO - SUNGLASS HUT", size=14, weight="bold", color="#00FFFF"),
                ft.Row([
                    btn_refresh_master,
                    btn_download_excel,
                    btn_download_pdf
                ], vertical_alignment="center", spacing=6, wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
            ft.Divider(height=4, color="#1F2937"),
            # Fila 2: Subtítulo + Filtros de Año, Semana, # Tienda y Nombre Tienda
            ft.Row([
                ft.Text("Replicación fiel del Excel Oficial SGH (Celdas blancas ⚪ = Entrada | Celdas verdes 🟩 = Cálculo automático).", size=10, color="#AAAAAA"),
                ft.Row([
                    ft.Text("AÑO:", color="white", weight="bold", size=11),
                    dd_anio,
                    ft.Container(width=2),
                    ft.Text("SEMANA:", color="white", weight="bold", size=11),
                    dd_semana,
                    ft.Container(width=2),
                    ft.Text("# TIENDA:", color="white", weight="bold", size=11),
                    txt_num_tienda,
                    ft.Container(width=2),
                    ft.Text("TIENDA:", color="white", weight="bold", size=11),
                    dd_tienda
                ], vertical_alignment="center", spacing=4, wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True)
        ], spacing=6),
        bgcolor="#0B0E17",
        padding=10,
        border_radius=10,
        border=ft.Border.all(1.5, "#1F2937")
    )

    return ft.Column([
        header_module,
        ft.Divider(height=8, color="#374151"),
        tab_navigation_bar,
        ft.Container(height=6),
        tab_content_container
    ], scroll=ft.ScrollMode.AUTO)
