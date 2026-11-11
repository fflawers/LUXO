# -*- coding: utf-8 -*-
"""
Módulo de Servicio para Digitalización de Bitácora de Conteo de Tienda.
Incluye:
- Catálogo oficial de marcas 2026 (ARMAZONES, OTRAS, ACCESORIOS).
- Importador de Excel MIM (StockSummary).
- Cálculos por turno, colores por número, validación automática OK (✓ / ✗).
- Herencia automática de Exhibición (EXH) y ajuste Matutino -> Vespertino.
- Organización anual en 4 Trimestres (Q1-Q4) x 3 meses con fecha de inicio configurable.
- Persistencia dual (MySQL + SQLite local fallback).
- Generador de PDF vectorial copia fiel del formato físico oficial usando PyMuPDF (fitz).
"""

import os
import re
import json
import copy
import sqlite3
from datetime import datetime, date, timedelta, timezone

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TEMP_PDF_DIR = os.path.join(BASE_PATH, "custom_assets", "temp_pdfs")
SQLITE_DB_PATH = os.path.join(BASE_PATH, "bitacora_conteo_local.db")


def get_now_mexico():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Mexico_City"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-6)))


def conectar_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "los4valtierra"),
            database=os.getenv("DB_NAME", "sgh_portal"),
            port=int(os.getenv("DB_PORT", 3306)),
            connection_timeout=5,
        )
    except Exception:
        return None


# ==============================================================================
# 1. CATÁLOGO OFICIAL DE FILAS DE LA BITÁCORA 2026
# ==============================================================================

ARMAZONES_FILAS = [
    {"key": "RB", "codigo": "RB", "marca": "RAY BAN"},
    {"key": "OO", "codigo": "OO", "marca": "OAKLEY"},
    {"key": "MJ", "codigo": "MJ", "marca": "MAUI JIM"},
    {"key": "CM", "codigo": "CM", "marca": "COSTA DEL MAR"},
    {"key": "AN", "codigo": "AN", "marca": "ARNETTE"},
    {"key": "HU", "codigo": "HU", "marca": "SUNGLASS HUT COLLECTION"},
    {"key": "VO", "codigo": "VO", "marca": "VOGUE"},
    {"key": "AX", "codigo": "AX", "marca": "ARMANI EXCHANGE"},
    {"key": "RA", "codigo": "RA", "marca": "RALPH LAUREN"},
    {"key": "MK", "codigo": "MK", "marca": "MICHAEL KORS"},
    {"key": "HC", "codigo": "HC", "marca": "COACH"},
    {"key": "EA", "codigo": "EA", "marca": "EMPORIO ARMANI"},
    {"key": "PH", "codigo": "PH", "marca": "POLO RALPH LAUREN"},
    {"key": "TY", "codigo": "TY", "marca": "TORY BURCH"},
    {"key": "VE", "codigo": "VE", "marca": "VERSACE"},
    {"key": "BE", "codigo": "BE", "marca": "BURBERRY"},
    {"key": "GC", "codigo": "GC", "marca": "GUCCI"},
    {"key": "PO", "codigo": "PO", "marca": "PERSOL"},
    {"key": "AR", "codigo": "AR", "marca": "GIORGIO ARMANI"},
    {"key": "PS", "codigo": "PS", "marca": "PRADA LINEA ROSSA"},
    {"key": "PR", "codigo": "PR", "marca": "PRADA"},
    {"key": "DR", "codigo": "DR", "marca": "DIOR"},
    {"key": "DG", "codigo": "DG", "marca": "DOLCE & GABBANA"},
    {"key": "VA", "codigo": "VA", "marca": "VALENTINO"},
    {"key": "MU", "codigo": "MU", "marca": "MIU MIU"},
    {"key": "CH", "codigo": "CH", "marca": "CHANEL"},
    {"key": "TF", "codigo": "TF", "marca": "TIFFANY"},
    {"key": "BV", "codigo": "BV", "marca": "BVLGARI"},
    {"key": "CT", "codigo": "CT", "marca": "CARTIER"},
    {"key": "SW", "codigo": "SW", "marca": "SWAROVSKI"},
    {"key": "JC", "codigo": "JC", "marca": "JIMMY CHOO"},
    {"key": "BC", "codigo": "BC", "marca": "BRUNELLO CUCINELLI"},
    {"key": "BB", "codigo": "BB", "marca": "BALENCIAGA"},
    {"key": "YS", "codigo": "YS", "marca": "SAINT LAURENT"},
    {"key": "FE", "codigo": "FE", "marca": "FERRARI"},
    {"key": "DA", "codigo": "DA", "marca": "DITA"},
    {"key": "TFD", "codigo": "TF", "marca": "TOM FORD"},
    {"key": "CS", "codigo": "CS", "marca": "CELINE"},
    {"key": "RJ", "codigo": "RJ", "marca": "RAYBAN JR"},
    {"key": "JB", "codigo": "JB", "marca": "BURBERRY JR"},
    {"key": "DK", "codigo": "DK", "marca": "D&G JR"},
    {"key": "VK", "codigo": "VK", "marca": "VERSACE KIDS"},
    {"key": "ME", "codigo": "ME", "marca": "MONCLER"},
    {"key": "DL", "codigo": "DL", "marca": "DIESEL"},
    {"key": "RW", "codigo": "RW", "marca": "RB META"},
    {"key": "OW", "codigo": "OW", "marca": "OAKLEY META"},
]

OTRAS_FILAS = [
    {"key": "OTRA_1", "codigo": "", "marca": ""},
    {"key": "OTRA_2", "codigo": "", "marca": ""},
    {"key": "OTRA_3", "codigo": "", "marca": ""},
    {"key": "OTRA_4", "codigo": "", "marca": ""},
]

ACCESORIOS_FILAS = [
    {"key": "ACC_FM", "codigo": "", "marca": "FACE MASKS"},
    {"key": "ACC_FC", "codigo": "", "marca": "FRAME CASES"},
    {"key": "ACC_CK", "codigo": "", "marca": "CARE KITS"},
    {"key": "ACC_CL", "codigo": "", "marca": "CLEANERS"},
    {"key": "ACC_ESS", "codigo": "", "marca": "ESS"},
    {"key": "ACC_EX1", "codigo": "", "marca": ""},
    {"key": "ACC_EX2", "codigo": "", "marca": ""},
    {"key": "ACC_EX3", "codigo": "", "marca": ""},
]

ALL_TEMPLATE_ROWS = (
    [dict(r, seccion="ARMAZONES") for r in ARMAZONES_FILAS]
    + [dict(r, seccion="OTRAS") for r in OTRAS_FILAS]
    + [dict(r, seccion="ACCESORIOS") for r in ACCESORIOS_FILAS]
)

CAMPOS_EDITABLES = ["exh", "bod", "gt", "dan", "se", "tr", "mim", "e", "st", "sv"]
CAMPOS_TODOS = ["exh", "bod", "gt", "dan", "se", "tot", "tr", "mim", "ok", "e", "st", "sv", "en"]

# Mapeo por código Merchandise (Col C) y por nombre en MIM (Col B)
MIM_CODE_TO_KEY = {
    "030505005": "ACC_CL",   # Cleaner
    "031005011": "ACC_FM",   # Facemasks
    "030510010": "ACC_FC",   # Frame Cases
    "100510750": "AN",       # Arnette
    "100510095": "BE",       # Burberry
    "100510160": "HC",       # Coach
    "100510165": "CM",       # Costa Del Mar
    "100510487": "DL",       # Diesel
    "100510195": "DG",       # Dolce & Gabbana
    "100510220": "EA",       # Emporio Armani
    "100510265": "GC",       # Gucci
    "100510533": "JC",       # Jimmy Choo
    "100510345": "MJ",       # Maui Jim
    "100510954": "MK",       # Michael Kors
    "100510350": "MU",       # Miu Miu
    "100525004": "OW",       # Oakley Wearables / Meta
    "100510375": "OO",       # Oakley
    "100510426": "OW",       # Oakley Wearables
    "100510390": "PO",       # Persol
    "100510415": "PR",       # Prada
    "100510420": "PS",       # Prada Linea Rossa
    "100510440": "RA",       # Ralph
    "100510450": "RB",       # Ray-Ban
    "100505010": "RJ",       # Ray-Ban Jr
}


def _norm_text(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


MIM_NAME_PATTERNS = [
    ("ray ban jr", "RJ"),
    ("rayban jr", "RJ"),
    ("ray ban meta", "RW"),
    ("rb meta", "RW"),
    ("ray ban wearables", "RW"),
    ("ray ban", "RB"),
    ("oakley wearables", "OW"),
    ("oakley meta", "OW"),
    ("oakley", "OO"),
    ("maui jim", "MJ"),
    ("costa del mar", "CM"),
    ("costa del ma", "CM"),
    ("arnette", "AN"),
    ("sunglass hut", "HU"),
    ("vogue", "VO"),
    ("armani exchange", "AX"),
    ("polo ralph", "PH"),
    ("ralph lauren", "RA"),
    ("ralph", "RA"),
    ("michael kors", "MK"),
    ("coach", "HC"),
    ("emporio armani", "EA"),
    ("emporio arman", "EA"),
    ("tory burch", "TY"),
    ("versace kids", "VK"),
    ("versace jr", "VK"),
    ("versace", "VE"),
    ("burberry jr", "JB"),
    ("burberry", "BE"),
    ("gucci", "GC"),
    ("persol", "PO"),
    ("giorgio armani", "AR"),
    ("prada linea rossa", "PS"),
    ("prada linea r", "PS"),
    ("prada", "PR"),
    ("dior", "DR"),
    ("dolce gabbana jr", "DK"),
    ("d g jr", "DK"),
    ("dolce gabbana", "DG"),
    ("dolce gabb", "DG"),
    ("valentino", "VA"),
    ("miu miu", "MU"),
    ("chanel", "CH"),
    ("tiffany", "TF"),
    ("bvlgari", "BV"),
    ("bulgari", "BV"),
    ("cartier", "CT"),
    ("swarovski", "SW"),
    ("jimmy choo", "JC"),
    ("brunello", "BC"),
    ("balenciaga", "BB"),
    ("saint laurent", "YS"),
    ("yves saint", "YS"),
    ("ferrari", "FE"),
    ("dita", "DA"),
    ("tom ford", "TFD"),
    ("celine", "CS"),
    ("moncler", "ME"),
    ("diesel", "DL"),
    ("facemasks", "ACC_FM"),
    ("face masks", "ACC_FM"),
    ("frame cases", "ACC_FC"),
    ("care kits", "ACC_CK"),
    ("care kit", "ACC_CK"),
    ("cleaner", "ACC_CL"),
    ("cleaners", "ACC_CL"),
    ("ess", "ACC_ESS"),
]


def _match_mim_brand(brand_name, merch_code=""):
    code_clean = re.sub(r"\D", "", str(merch_code or ""))
    if code_clean in MIM_CODE_TO_KEY:
        return MIM_CODE_TO_KEY[code_clean]
    bn = _norm_text(brand_name)
    if not bn:
        return None
    for pattern, key in MIM_NAME_PATTERNS:
        if bn == pattern or bn.startswith(pattern) or pattern in bn:
            return key
    return None


def parse_int_or_none(val):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s == "-":
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def fmt_val(val):
    return "" if val is None else str(int(val))


def empty_shift_row():
    return {k: "" for k in CAMPOS_EDITABLES}


def crear_estado_inicial(fecha_str=None, tienda="", exh_previos=None):
    if not fecha_str:
        fecha_str = get_now_mexico().strftime("%Y-%m-%d")
    exh_previos = exh_previos or {}
    filas = {}
    for tpl in ALL_TEMPLATE_ROWS:
        k = tpl["key"]
        m_row = empty_shift_row()
        v_row = empty_shift_row()
        if k in exh_previos and str(exh_previos[k]).strip() != "":
            m_row["exh"] = str(exh_previos[k]).strip()
        filas[k] = {
            "codigo": tpl["codigo"],
            "marca": tpl["marca"],
            "seccion": tpl["seccion"],
            "matutino": m_row,
            "vespertino": v_row,
            "in_store_expected": None,
        }
    return {
        "fecha": fecha_str,
        "tienda": tienda,
        "caja_chica_1": "",
        "caja_chica_2": "",
        "caja_chica_3": "",
        "recibi_mat": "",
        "entrego_mat": "",
        "recibi_ves": "",
        "entrego_ves": "",
        "filas": filas,
    }


def calcular_fila_turno(row_data, in_store_expected=None):
    """
    Calcula los valores automáticos de un turno para una fila:
    - TOT = EXH + BOD + GT + DAÑ + S/E
    - OK  = True (palomita verde) si TOT + TR == MIM (o TOT == in_store_expected), False (tache rojo) si difiere, None si no hay MIM
    - DIFF = (TOT + TR) - MIM
    - EN  = TOT + E - ST - SV
    """
    exh = parse_int_or_none(row_data.get("exh"))
    bod = parse_int_or_none(row_data.get("bod"))
    gt = parse_int_or_none(row_data.get("gt"))
    dan = parse_int_or_none(row_data.get("dan"))
    se = parse_int_or_none(row_data.get("se"))
    tr = parse_int_or_none(row_data.get("tr"))
    mim = parse_int_or_none(row_data.get("mim"))
    e = parse_int_or_none(row_data.get("e"))
    st = parse_int_or_none(row_data.get("st"))
    sv = parse_int_or_none(row_data.get("sv"))

    tiene_conteo = any(v is not None for v in (exh, bod, gt, dan, se))
    tiene_movs = any(v is not None for v in (e, st, sv))
    tiene_algo = tiene_conteo or tiene_movs or (tr is not None) or (mim is not None)

    if not tiene_algo:
        return {
            "tot": None,
            "ok": None,
            "diff": None,
            "en": None,
            "activo": False,
        }

    tot = (exh or 0) + (bod or 0) + (gt or 0) + (dan or 0) + (se or 0) if tiene_conteo else None

    ok = None
    diff = None
    if tot is not None and mim is not None:
        total_con_tr = tot + (tr or 0)
        diff = total_con_tr - mim
        ok = (diff == 0)
    elif tot is not None and in_store_expected is not None:
        diff = tot - in_store_expected
        ok = (diff == 0)

    en = None
    if tot is not None:
        en = tot + (e or 0) - (st or 0) - (sv or 0)

    return {
        "tot": tot,
        "ok": ok,
        "diff": diff,
        "en": en,
        "activo": True,
    }


def calcular_totales_globales(estado):
    """Calcula la fila TOTAL vertical para ambos turnos."""
    cols_sum = ["exh", "bod", "gt", "dan", "se", "tot", "tr", "mim", "e", "st", "sv", "en"]
    tot_mat = {c: 0 for c in cols_sum}
    tot_ves = {c: 0 for c in cols_sum}
    ok_mat_count = 0
    bad_mat_count = 0
    ok_ves_count = 0
    bad_ves_count = 0

    filas = estado.get("filas", {})
    for tpl in ALL_TEMPLATE_ROWS:
        k = tpl["key"]
        f_obj = filas.get(k, {})
        exp = f_obj.get("in_store_expected")
        for turno_key, acc_dict, is_mat in [("matutino", tot_mat, True), ("vespertino", tot_ves, False)]:
            raw = f_obj.get(turno_key, {})
            calc = calcular_fila_turno(raw, exp)
            for c in ["exh", "bod", "gt", "dan", "se", "tr", "mim", "e", "st", "sv"]:
                v = parse_int_or_none(raw.get(c))
                if v is not None:
                    acc_dict[c] += v
            if calc["tot"] is not None:
                acc_dict["tot"] += calc["tot"]
            if calc["en"] is not None:
                acc_dict["en"] += calc["en"]
            if calc["ok"] is True:
                if is_mat:
                    ok_mat_count += 1
                else:
                    ok_ves_count += 1
            elif calc["ok"] is False:
                if is_mat:
                    bad_mat_count += 1
                else:
                    bad_ves_count += 1

    return {
        "matutino": tot_mat,
        "vespertino": tot_ves,
        "ok_mat": ok_mat_count,
        "bad_mat": bad_mat_count,
        "ok_ves": ok_ves_count,
        "bad_ves": bad_ves_count,
    }


def aplicar_ajuste_fila_a_vespertino(estado, row_key):
    """
    Calcula y copia el ajuste Matutino -> Vespertino de una sola fila (E, ST, SV -> delta en BOD/EXH/MIM).
    Retorna True si la fila quedó activa y ajustada, False si está vacía.
    """
    filas = estado.get("filas", {})
    f_obj = filas.get(row_key)
    if not f_obj:
        return False
    mat = f_obj.get("matutino", {})
    calc = calcular_fila_turno(mat, f_obj.get("in_store_expected"))
    if not calc["activo"]:
        return False

    exh = parse_int_or_none(mat.get("exh"))
    bod = parse_int_or_none(mat.get("bod"))
    gt = parse_int_or_none(mat.get("gt"))
    dan = parse_int_or_none(mat.get("dan"))
    se = parse_int_or_none(mat.get("se"))
    tr = parse_int_or_none(mat.get("tr"))
    mim = parse_int_or_none(mat.get("mim"))
    e = parse_int_or_none(mat.get("e")) or 0
    st = parse_int_or_none(mat.get("st")) or 0
    sv = parse_int_or_none(mat.get("sv")) or 0

    delta = e - st - sv
    new_bod = bod
    new_exh = exh

    if delta != 0:
        bod_curr = bod or 0
        exh_curr = exh or 0
        cand_bod = bod_curr + delta
        if cand_bod >= 0:
            new_bod = cand_bod
        else:
            new_bod = 0
            new_exh = max(0, exh_curr + cand_bod)

    # Ajustar también MIM esperado si hubo movimientos en tienda (E - ST - SV)
    new_mim = mim
    if mim is not None and delta != 0:
        new_mim = max(0, mim + delta)

    ves = f_obj.setdefault("vespertino", empty_shift_row())
    ves["exh"] = fmt_val(new_exh)
    ves["bod"] = fmt_val(new_bod)
    ves["gt"] = fmt_val(gt)
    ves["dan"] = fmt_val(dan)
    ves["se"] = fmt_val(se)
    ves["tr"] = fmt_val(tr)
    ves["mim"] = fmt_val(new_mim)
    return True


def aplicar_ajuste_matutino_a_vespertino(estado, skip_keys=None, reset_movimientos=False):
    """
    Pasa los valores del Turno Matutino al Turno Vespertino aplicando
    automáticamente los movimientos de las columnas 12-14 (E, ST, SV):
      delta = E - ST - SV
    Se suma/resta a BOD (y si BOD no alcanza, el remanente se ajusta de EXH).
    Todos los campos del Vespertino quedan completamente editables.
    """
    skip = skip_keys or set()
    ajustadas = 0
    for tpl in ALL_TEMPLATE_ROWS:
        k = tpl["key"]
        if k in skip:
            continue
        if aplicar_ajuste_fila_a_vespertino(estado, k):
            if reset_movimientos:
                ves = estado["filas"][k]["vespertino"]
                ves["e"] = ""
                ves["st"] = ""
                ves["sv"] = ""
            ajustadas += 1
    return ajustadas


# ==============================================================================
# 2. IMPORTADOR DE EXCEL MIM (StockSummary_Headers.xlsx)
# ==============================================================================

def importar_excel_mim(ruta_xlsx, estado, aplicar_a_vespertino=False):
    """
    Lee el Excel descargado de MIM ignorando la columna A:
    - Col B: Product Brand
    - Col C: Merchandise (código)
    - Col D: Total Quantity -> rellena MIM
    - Col E: Unconfirmed    -> rellena TR
    - Col F: In-Store Qty   -> referencia física esperada
    Si una marca no existe en el Excel, sus celdas quedan vacías (sin ceros).
    """
    if not ruta_xlsx or not os.path.exists(ruta_xlsx):
        return False, "Archivo no encontrado", {}

    import openpyxl
    wb = openpyxl.load_workbook(ruta_xlsx, data_only=True)
    ws = wb.active

    # Detectar fila de encabezados
    header_row_idx = 1
    col_brand = 2
    col_merch = 3
    col_total = 4
    col_unconf = 5
    col_instore = 6

    for r_idx in range(1, min(10, ws.max_row + 1)):
        row_vals = [str(ws.cell(r_idx, c).value or "").strip().lower() for c in range(1, min(12, ws.max_column + 1))]
        if any("brand" in v for v in row_vals) or any("merchandise" in v for v in row_vals):
            header_row_idx = r_idx
            for c_i, val in enumerate(row_vals, start=1):
                if "brand" in val:
                    col_brand = c_i
                elif "merchandise" in val:
                    col_merch = c_i
                elif "total quant" in val or val == "total":
                    col_total = c_i
                elif "unconfirmed" in val:
                    col_unconf = c_i
                elif "in-store" in val or "in store" in val:
                    col_instore = c_i
            break

    agregado = {}
    no_mapeadas = []

    for r_idx in range(header_row_idx + 1, ws.max_row + 1):
        b_val = ws.cell(r_idx, col_brand).value
        c_val = ws.cell(r_idx, col_merch).value
        d_val = parse_int_or_none(ws.cell(r_idx, col_total).value)
        e_val = parse_int_or_none(ws.cell(r_idx, col_unconf).value)
        f_val = parse_int_or_none(ws.cell(r_idx, col_instore).value)

        if b_val is None and c_val is None:
            continue
        b_str = str(b_val or "").strip()
        if not b_str or b_str.lower() in ("total", "grand total"):
            continue

        key = _match_mim_brand(b_str, c_val)
        if not key:
            no_mapeadas.append((b_str, d_val or 0, e_val or 0))
            continue

        if key not in agregado:
            agregado[key] = {"mim": 0, "tr": 0, "instore": 0}
        agregado[key]["mim"] += (d_val or 0)
        agregado[key]["tr"] += (e_val or 0)
        agregado[key]["instore"] += (f_val if f_val is not None else max(0, (d_val or 0) - (e_val or 0)))

    # Si hay marcas no mapeadas (ej. extras en OTRAS), asignarlas en OTRAS_1..4
    otras_keys = [r["key"] for r in OTRAS_FILAS]
    otra_idx = 0
    for b_str, d_v, e_v in no_mapeadas:
        if otra_idx < len(otras_keys):
            ok_key = otras_keys[otra_idx]
            estado["filas"][ok_key]["marca"] = b_str.upper()[:22]
            agregado[ok_key] = {"mim": d_v, "tr": e_v, "instore": max(0, d_v - e_v)}
            otra_idx += 1

    filas = estado.get("filas", {})
    actualizadas = 0
    for tpl in ALL_TEMPLATE_ROWS:
        k = tpl["key"]
        f_obj = filas.get(k)
        if not f_obj:
            continue
        if k in agregado:
            info = agregado[k]
            f_obj["matutino"]["tr"] = str(info["tr"])
            f_obj["matutino"]["mim"] = str(info["mim"])
            f_obj["in_store_expected"] = info["instore"]
            if aplicar_a_vespertino:
                f_obj["vespertino"]["tr"] = str(info["tr"])
                f_obj["vespertino"]["mim"] = str(info["mim"])
            actualizadas += 1
        else:
            # Si no viene en MIM, dejar TR y MIM en blanco (no llenar con ceros)
            f_obj["matutino"]["tr"] = ""
            f_obj["matutino"]["mim"] = ""
            f_obj["in_store_expected"] = None
            if aplicar_a_vespertino:
                f_obj["vespertino"]["tr"] = ""
                f_obj["vespertino"]["mim"] = ""

    return True, f"MIM importado: {actualizadas} marcas actualizadas", {
        "actualizadas": actualizadas,
        "extras": len(no_mapeadas),
        "active_keys": sorted(agregado.keys()),
    }


# ==============================================================================
# 3. ORGANIZACIÓN ANUAL EN 4Q (Q1, Q2, Q3, Q4) x 3 MESES + SEMANAS
# ==============================================================================

MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def _default_q_starts(anio):
    """Fechas de inicio por defecto (domingo de Semana 1 del año fiscal, 13 sem por Q)."""
    q1_dom = _domingo_de_fecha(date(anio, 1, 4))
    return generar_q_starts_desde_q1(q1_dom)


def generar_q_starts_desde_q1(q1_start_date):
    """
    A partir del día que indique el usuario en el calendario como inicio de Semana 1 del Q1,
    calcula Q1..Q4 en bloques de 13 semanas (91 días cada Q -> 3 meses operativos por Q).
    """
    return {
        "Q1": q1_start_date,
        "Q2": q1_start_date + timedelta(weeks=13),
        "Q3": q1_start_date + timedelta(weeks=26),
        "Q4": q1_start_date + timedelta(weeks=39),
    }


def _domingo_de_fecha(d_obj):
    """Retorna el domingo de inicio de semana (Domingo a Sábado) para una fecha dada."""
    return d_obj - timedelta(days=(d_obj.weekday() + 1) % 7)


def listar_semanas_de_q(anio, q_name, q_starts=None):
    """Retorna lista de (sem_anual, ini_dom, fin_sab) para Q1(1-13), Q2(14-26), Q3(27-39), Q4(40-52)."""
    if not q_starts:
        q_starts = _default_q_starts(int(anio))
    q1_dom = _domingo_de_fecha(q_starts.get("Q1", _default_q_starts(int(anio))["Q1"]))
    offsets = {"Q1": (1, 13), "Q2": (14, 26), "Q3": (27, 39), "Q4": (40, 52)}
    s_ini, s_fin = offsets.get(q_name, (1, 13))
    res = []
    for sn in range(s_ini, s_fin + 1):
        d_dom = q1_dom + timedelta(weeks=sn - 1)
        res.append((sn, d_dom, d_dom + timedelta(days=6)))
    return res


def obtener_rango_semana_dom_sab(fecha_obj=None, q_starts=None, semana_num=None, q_name=None):
    """
    Calcula el rango (domingo, sabado, info_q) de 7 días de Domingo a Sábado.
    semana_num es el número de semana del año (Q1:1-13, Q2:14-26, Q3:27-39, Q4:40-52).
    """
    if fecha_obj is None:
        fecha_obj = get_now_mexico().date()
    elif isinstance(fecha_obj, str):
        fecha_obj = datetime.strptime(fecha_obj[:10], "%Y-%m-%d").date()
    elif isinstance(fecha_obj, datetime):
        fecha_obj = fecha_obj.date()

    if not q_starts:
        q_starts = _default_q_starts(fecha_obj.year)

    if semana_num is not None:
        q1_dom = _domingo_de_fecha(q_starts.get("Q1", _default_q_starts(fecha_obj.year)["Q1"]))
        ini_dom = q1_dom + timedelta(weeks=max(1, int(semana_num)) - 1)
        fin_sab = ini_dom + timedelta(days=6)
        return ini_dom, fin_sab, calcular_info_q_fecha(ini_dom, q_starts)

    ini_dom = _domingo_de_fecha(fecha_obj)
    fin_sab = ini_dom + timedelta(days=6)
    return ini_dom, fin_sab, calcular_info_q_fecha(fecha_obj, q_starts)


def calcular_info_q_fecha(fecha_obj, q_starts=None):
    """Determina a qué Q (Q1-Q4), Mes del Q (1-3) y Semana del año (1-52, Dom-Sáb) pertenece una fecha."""
    if isinstance(fecha_obj, str):
        fecha_obj = datetime.strptime(fecha_obj, "%Y-%m-%d").date()
    elif isinstance(fecha_obj, datetime):
        fecha_obj = fecha_obj.date()

    if not q_starts:
        q_starts = _default_q_starts(fecha_obj.year)

    ordered = sorted(q_starts.items(), key=lambda kv: kv[1])
    q_name, q_start = ordered[0]
    for q_k, q_d in ordered:
        if fecha_obj >= q_d:
            q_name, q_start = q_k, q_d

    q1_dom = _domingo_de_fecha(q_starts.get("Q1", q_start))
    q_dom = _domingo_de_fecha(q_start)
    f_dom = _domingo_de_fecha(fecha_obj)

    dias_desde_q1 = (f_dom - q1_dom).days
    semana_anual = 1 if dias_desde_q1 < 0 else (dias_desde_q1 // 7) + 1

    dias_desde_q = (f_dom - q_dom).days
    if dias_desde_q < 0:
        mes_en_q = 1
    else:
        semana_en_q = (dias_desde_q // 7) + 1
        # Cada Q tiene 3 meses operativos (~4-5 semanas: 4+4+5 semanas = 13 semanas)
        if semana_en_q <= 4:
            mes_en_q = 1
        elif semana_en_q <= 8:
            mes_en_q = 2
        else:
            mes_en_q = 3

    mes_calendario = MESES_ES[fecha_obj.month]
    return {
        "anio": fecha_obj.year,
        "q": q_name,
        "semana": semana_anual,
        "mes_en_q": mes_en_q,
        "mes_nombre": mes_calendario,
        "q_start": q_start.strftime("%Y-%m-%d"),
        "carpeta": f"{fecha_obj.year} / {q_name} / Mes {mes_en_q} ({mes_calendario}) / Sem {semana_anual}",
    }


# ==============================================================================
# 4. PERSISTENCIA DUAL (MYSQL + SQLITE FALLBACK)
# ==============================================================================

def _init_sqlite():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_conteo_diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tienda VARCHAR(50) NOT NULL,
            fecha VARCHAR(20) NOT NULL,
            anio INT NOT NULL,
            quarter VARCHAR(5) NOT NULL,
            mes_q INT NOT NULL,
            semana INT NOT NULL,
            datos_json TEXT NOT NULL,
            exh_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tienda, fecha)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_conteo_config_q (
            tienda VARCHAR(50) NOT NULL,
            anio INT NOT NULL,
            q1_start VARCHAR(20) NOT NULL,
            q2_start VARCHAR(20) NOT NULL,
            q3_start VARCHAR(20) NOT NULL,
            q4_start VARCHAR(20) NOT NULL,
            PRIMARY KEY(tienda, anio)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_conteo_marcas_tienda (
            tienda VARCHAR(50) PRIMARY KEY,
            marcas_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


_MYSQL_TABLES_OK = False


def _init_mysql(db):
    global _MYSQL_TABLES_OK
    if _MYSQL_TABLES_OK:
        return
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_conteo_diario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tienda VARCHAR(50) NOT NULL,
            fecha DATE NOT NULL,
            anio INT NOT NULL,
            quarter VARCHAR(5) NOT NULL,
            mes_q INT NOT NULL,
            semana INT NOT NULL,
            datos_json LONGTEXT NOT NULL,
            exh_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_tienda_fecha (tienda, fecha)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_conteo_config_q (
            tienda VARCHAR(50) NOT NULL,
            anio INT NOT NULL,
            q1_start DATE NOT NULL,
            q2_start DATE NOT NULL,
            q3_start DATE NOT NULL,
            q4_start DATE NOT NULL,
            PRIMARY KEY(tienda, anio)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_conteo_marcas_tienda (
            tienda VARCHAR(50) PRIMARY KEY,
            marcas_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    db.commit()
    cur.close()
    _MYSQL_TABLES_OK = True


_CONFIG_Q_CACHE = {}


def obtener_config_q(tienda, anio):
    t_str = str(tienda or "GENERAL").strip()
    cache_key = (t_str, int(anio))
    if cache_key in _CONFIG_Q_CACHE:
        return dict(_CONFIG_Q_CACHE[cache_key])

    res_cfg = None
    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT q1_start, q2_start, q3_start, q4_start FROM bitacora_conteo_config_q WHERE tienda=%s AND anio=%s", (t_str, int(anio)))
            row = cur.fetchone()
            cur.close()
            db.close()
            if row:
                res_cfg = {
                    k: (v if isinstance(v, date) else datetime.strptime(str(v)[:10], "%Y-%m-%d").date())
                    for k, v in [("Q1", row["q1_start"]), ("Q2", row["q2_start"]), ("Q3", row["q3_start"]), ("Q4", row["q4_start"])]
                }
        except Exception:
            try:
                db.close()
            except Exception:
                pass

    if res_cfg is None:
        try:
            sq = _init_sqlite()
            cur = sq.cursor()
            cur.execute("SELECT q1_start, q2_start, q3_start, q4_start FROM bitacora_conteo_config_q WHERE tienda=? AND anio=?", (t_str, int(anio)))
            row = cur.fetchone()
            sq.close()
            if row:
                res_cfg = {
                    "Q1": datetime.strptime(row[0], "%Y-%m-%d").date(),
                    "Q2": datetime.strptime(row[1], "%Y-%m-%d").date(),
                    "Q3": datetime.strptime(row[2], "%Y-%m-%d").date(),
                    "Q4": datetime.strptime(row[3], "%Y-%m-%d").date(),
                }
        except Exception:
            pass

    if res_cfg is None:
        res_cfg = _default_q_starts(int(anio))
    _CONFIG_Q_CACHE[cache_key] = dict(res_cfg)
    return dict(res_cfg)


def guardar_config_q(tienda, anio, q_starts):
    t_str = str(tienda or "GENERAL").strip()
    _CONFIG_Q_CACHE[(t_str, int(anio))] = dict(q_starts)
    vals = tuple(q_starts[q].strftime("%Y-%m-%d") for q in ("Q1", "Q2", "Q3", "Q4"))
    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO bitacora_conteo_config_q (tienda, anio, q1_start, q2_start, q3_start, q4_start)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (t_str, int(anio), *vals))
        sq.commit()
        sq.close()
    except Exception as ex:
        print("Notice sqlite config_q:", ex)

    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor()
            cur.execute("""
                INSERT INTO bitacora_conteo_config_q (tienda, anio, q1_start, q2_start, q3_start, q4_start)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE q1_start=VALUES(q1_start), q2_start=VALUES(q2_start), q3_start=VALUES(q3_start), q4_start=VALUES(q4_start)
            """, (t_str, int(anio), *vals))
            db.commit()
            cur.close()
            db.close()
        except Exception as ex:
            print("Notice mysql config_q:", ex)
            try:
                db.close()
            except Exception:
                pass


_TIENDA_MARCAS_CACHE = {}


def obtener_marcas_tienda(tienda):
    """Obtiene la lista de llaves de marca activas grabadas para esta tienda (SQLite/MySQL con caché)."""
    t_str = str(tienda or "GENERAL").strip()
    if t_str in _TIENDA_MARCAS_CACHE:
        return list(_TIENDA_MARCAS_CACHE[t_str])

    # SQLite primero para respuesta inmediata
    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("SELECT marcas_json FROM bitacora_conteo_marcas_tienda WHERE tienda=?", (t_str,))
        row = cur.fetchone()
        sq.close()
        if row and row[0]:
            res = json.loads(row[0])
            _TIENDA_MARCAS_CACHE[t_str] = list(res)
            return list(res)
    except Exception:
        pass

    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT marcas_json FROM bitacora_conteo_marcas_tienda WHERE tienda=%s", (t_str,))
            row = cur.fetchone()
            cur.close()
            db.close()
            if row and row.get("marcas_json"):
                res = json.loads(row["marcas_json"])
                _TIENDA_MARCAS_CACHE[t_str] = list(res)
                # Replicar en SQLite local para próximas aperturas instantáneas
                try:
                    sq = _init_sqlite()
                    sq.cursor().execute(
                        "INSERT OR REPLACE INTO bitacora_conteo_marcas_tienda (tienda, marcas_json) VALUES (?, ?)",
                        (t_str, json.dumps(res, ensure_ascii=False)),
                    )
                    sq.commit()
                    sq.close()
                except Exception:
                    pass
                return list(res)
        except Exception:
            try:
                db.close()
            except Exception:
                pass

    _TIENDA_MARCAS_CACHE[t_str] = []
    return []


def guardar_marcas_tienda(tienda, keys_list):
    """Guarda el catálogo de marcas activas de una tienda (en caché, SQLite y MySQL en segundo plano)."""
    t_str = str(tienda or "GENERAL").strip()
    clean_keys = sorted(set(str(k) for k in (keys_list or []) if k))
    _TIENDA_MARCAS_CACHE[t_str] = list(clean_keys)
    payload = json.dumps(clean_keys, ensure_ascii=False)
    try:
        sq = _init_sqlite()
        sq.cursor().execute(
            "INSERT OR REPLACE INTO bitacora_conteo_marcas_tienda (tienda, marcas_json, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (t_str, payload),
        )
        sq.commit()
        sq.close()
    except Exception:
        pass

    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor()
            cur.execute("""
                INSERT INTO bitacora_conteo_marcas_tienda (tienda, marcas_json)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE marcas_json=VALUES(marcas_json)
            """, (t_str, payload))
            db.commit()
            cur.close()
            db.close()
        except Exception:
            try:
                db.close()
            except Exception:
                pass
    return clean_keys


def _extraer_exh_para_herencia(estado):
    exh_map = {}
    for k, f_obj in estado.get("filas", {}).items():
        # Prioriza la exhibición del último turno (vespertino si existe, sino matutino)
        v_exh = str(f_obj.get("vespertino", {}).get("exh", "") or "").strip()
        m_exh = str(f_obj.get("matutino", {}).get("exh", "") or "").strip()
        val = v_exh if v_exh != "" else m_exh
        if val != "":
            exh_map[k] = val
    return exh_map


def guardar_bitacora_dia(tienda, fecha_str, estado):
    t_str = str(tienda or "GENERAL").strip()
    f_date = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    q_starts = obtener_config_q(t_str, f_date.year)
    info_q = calcular_info_q_fecha(f_date, q_starts)
    datos_json = json.dumps(estado, ensure_ascii=False)
    exh_json = json.dumps(_extraer_exh_para_herencia(estado), ensure_ascii=False)

    saved_ok = False
    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO bitacora_conteo_diario
            (tienda, fecha, anio, quarter, mes_q, semana, datos_json, exh_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (t_str, fecha_str, info_q["anio"], info_q["q"], info_q["mes_en_q"], info_q["semana"], datos_json, exh_json))
        sq.commit()
        sq.close()
        saved_ok = True
    except Exception as ex:
        print("Error sqlite guardar_bitacora_dia:", ex)

    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor()
            cur.execute("""
                INSERT INTO bitacora_conteo_diario
                (tienda, fecha, anio, quarter, mes_q, semana, datos_json, exh_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  anio=VALUES(anio), quarter=VALUES(quarter), mes_q=VALUES(mes_q),
                  semana=VALUES(semana), datos_json=VALUES(datos_json), exh_json=VALUES(exh_json)
            """, (t_str, fecha_str, info_q["anio"], info_q["q"], info_q["mes_en_q"], info_q["semana"], datos_json, exh_json))
            db.commit()
            cur.close()
            db.close()
            saved_ok = True
        except Exception as ex:
            print("Notice mysql guardar_bitacora_dia:", ex)
            try:
                db.close()
            except Exception:
                pass
    return saved_ok


def obtener_exh_anterior(tienda, fecha_str, db=None):
    """Obtiene el mapa de EXH del conteo guardado más reciente anterior a fecha_str."""
    t_str = str(tienda or "GENERAL").strip()
    own_db = False
    if db is None:
        db = conectar_db()
        own_db = True
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor(dictionary=True)
            cur.execute("""
                SELECT exh_json FROM bitacora_conteo_diario
                WHERE tienda=%s AND fecha < %s AND exh_json IS NOT NULL
                ORDER BY fecha DESC LIMIT 1
            """, (t_str, fecha_str))
            row = cur.fetchone()
            cur.close()
            if own_db:
                db.close()
            if row and row.get("exh_json"):
                return json.loads(row["exh_json"])
        except Exception:
            if own_db:
                try:
                    db.close()
                except Exception:
                    pass

    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("""
            SELECT exh_json FROM bitacora_conteo_diario
            WHERE tienda=? AND fecha < ? AND exh_json IS NOT NULL
            ORDER BY fecha DESC LIMIT 1
        """, (t_str, fecha_str))
        row = cur.fetchone()
        sq.close()
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        pass
    return {}


def cargar_bitacora_dia(tienda, fecha_str):
    """Carga una bitácora existente o crea una nueva heredando EXH del día anterior usando una sola conexión."""
    t_str = str(tienda or "GENERAL").strip()
    exh_prev = {}
    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT datos_json FROM bitacora_conteo_diario WHERE tienda=%s AND fecha=%s", (t_str, fecha_str))
            row = cur.fetchone()
            cur.close()
            if row and row.get("datos_json"):
                db.close()
                return json.loads(row["datos_json"]), True
            # Reutilizar esta misma conexión para buscar EXH anterior
            exh_prev = obtener_exh_anterior(t_str, fecha_str, db=db)
            db.close()
        except Exception:
            try:
                db.close()
            except Exception:
                pass

    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("SELECT datos_json FROM bitacora_conteo_diario WHERE tienda=? AND fecha=?", (t_str, fecha_str))
        row = cur.fetchone()
        sq.close()
        if row and row[0]:
            return json.loads(row[0]), True
    except Exception:
        pass

    if not exh_prev:
        exh_prev = obtener_exh_anterior(t_str, fecha_str, db=False)
    return crear_estado_inicial(fecha_str=fecha_str, tienda=t_str, exh_previos=exh_prev), False


def listar_dias_por_q(tienda, anio, quarter):
    """Lista las bitácoras guardadas dentro de una carpeta Q (Q1-Q4) para el navegador."""
    t_str = str(tienda or "GENERAL").strip()
    resultados = {}
    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("""
            SELECT fecha, mes_q, semana FROM bitacora_conteo_diario
            WHERE tienda=? AND anio=? AND quarter=? ORDER BY fecha DESC
        """, (t_str, int(anio), quarter))
        for f, mq, sem in cur.fetchall():
            resultados[str(f)] = {"fecha": str(f), "mes_q": mq, "semana": sem}
        sq.close()
    except Exception:
        pass

    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor(dictionary=True)
            cur.execute("""
                SELECT fecha, mes_q, semana FROM bitacora_conteo_diario
                WHERE tienda=%s AND anio=%s AND quarter=%s ORDER BY fecha DESC
            """, (t_str, int(anio), quarter))
            for r in cur.fetchall():
                f_s = str(r["fecha"])[:10]
                resultados[f_s] = {"fecha": f_s, "mes_q": r["mes_q"], "semana": r["semana"]}
            cur.close()
            db.close()
        except Exception:
            try:
                db.close()
            except Exception:
                pass

    return sorted(resultados.values(), key=lambda x: x["fecha"], reverse=True)


DIAS_CORTO_ES = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]


def cargar_rango_bitacora(tienda, fecha_inicio, fecha_fin):
    """
    Carga todas las bitácoras entre fecha_inicio y fecha_fin (inclusive) desde MySQL / SQLite.
    Retorna lista de tuplas (fecha_str, estado_dict, existe_en_bd).
    """
    t_str = str(tienda or "GENERAL").strip()
    if isinstance(fecha_inicio, str):
        d_ini = datetime.strptime(fecha_inicio[:10], "%Y-%m-%d").date()
    elif isinstance(fecha_inicio, datetime):
        d_ini = fecha_inicio.date()
    else:
        d_ini = fecha_inicio

    if isinstance(fecha_fin, str):
        d_fin = datetime.strptime(fecha_fin[:10], "%Y-%m-%d").date()
    elif isinstance(fecha_fin, datetime):
        d_fin = fecha_fin.date()
    else:
        d_fin = fecha_fin

    if d_fin < d_ini:
        d_ini, d_fin = d_fin, d_ini

    s_ini = d_ini.strftime("%Y-%m-%d")
    s_fin = d_fin.strftime("%Y-%m-%d")
    por_fecha = {}

    try:
        sq = _init_sqlite()
        cur = sq.cursor()
        cur.execute("""
            SELECT fecha, datos_json FROM bitacora_conteo_diario
            WHERE tienda=? AND fecha >= ? AND fecha <= ?
        """, (t_str, s_ini, s_fin))
        for f_s, dj in cur.fetchall():
            if dj:
                por_fecha[str(f_s)[:10]] = json.loads(dj)
        sq.close()
    except Exception:
        pass

    db = conectar_db()
    if db:
        try:
            _init_mysql(db)
            cur = db.cursor(dictionary=True)
            cur.execute("""
                SELECT fecha, datos_json FROM bitacora_conteo_diario
                WHERE tienda=%s AND fecha >= %s AND fecha <= %s
            """, (t_str, s_ini, s_fin))
            for r in cur.fetchall():
                if r.get("datos_json"):
                    por_fecha[str(r["fecha"])[:10]] = json.loads(r["datos_json"])
            cur.close()
            db.close()
        except Exception:
            try:
                db.close()
            except Exception:
                pass

    resultados = []
    d_cur = d_ini
    while d_cur <= d_fin:
        fs = d_cur.strftime("%Y-%m-%d")
        if fs in por_fecha:
            est = por_fecha[fs]
            aplicar_ajuste_matutino_a_vespertino(est)
            resultados.append((fs, est, True))
        else:
            resultados.append((fs, crear_estado_inicial(fecha_str=fs, tienda=t_str), False))
        d_cur += timedelta(days=1)
    return resultados


def generar_excel_semanal_bitacora(tienda, fecha_inicio, fecha_fin, filename_out=None):
    """
    Genera un archivo Excel (.xlsx) con 1 hoja por cada día del rango (ej. 7 días Dom-Sáb),
    manteniendo los colores de números (Negro, Azul, Rojo y Verde en OK) y totales de ambos turnos.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    import time as _t_xl

    os.makedirs(TEMP_PDF_DIR, exist_ok=True)
    t_str = str(tienda or "GENERAL").strip()
    dias_lista = cargar_rango_bitacora(t_str, fecha_inicio, fecha_fin)
    s_ini = dias_lista[0][0]
    s_fin = dias_lista[-1][0]
    tienda_clean = re.sub(r"[^A-Za-z0-9_-]", "", t_str) or "TIENDA"

    if not filename_out:
        filename_out = f"Bitacora_Semanal_{tienda_clean}_{s_ini}_al_{s_fin}_{int(_t_xl.time() * 1000)}.xlsx"
    xlsx_path = os.path.join(TEMP_PDF_DIR, filename_out)

    wb = openpyxl.Workbook()
    # Remover hoja por defecto al final tras crear las hojas reales
    default_ws = wb.active

    thin_side = Side(border_style="thin", color="475569")
    med_side = Side(border_style="medium", color="111827")
    border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_hdr = Border(left=thin_side, right=thin_side, top=med_side, bottom=med_side)

    f_title = Font(name="Calibri", size=12, bold=True, color="111827")
    f_meta = Font(name="Calibri", size=9, bold=True, color="334155")
    f_hdr_white = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    f_hdr_dark = Font(name="Calibri", size=9, bold=True, color="111827")
    f_negro = Font(name="Calibri", size=9, bold=False, color="111827")
    f_negro_b = Font(name="Calibri", size=9, bold=True, color="111827")
    f_azul = Font(name="Calibri", size=9, bold=False, color="0B41C7")
    f_azul_b = Font(name="Calibri", size=9, bold=True, color="0B41C7")
    f_rojo = Font(name="Calibri", size=9, bold=False, color="D11414")
    f_rojo_b = Font(name="Calibri", size=9, bold=True, color="D11414")
    f_verde_b = Font(name="Calibri", size=9, bold=True, color="0A942E")

    fill_arm = PatternFill("solid", fgColor="374151")
    fill_mat = PatternFill("solid", fgColor="1E3A8A")
    fill_ves = PatternFill("solid", fgColor="581C87")
    fill_subhdr = PatternFill("solid", fgColor="D1D5DB")
    fill_cod = PatternFill("solid", fgColor="E5E7EB")
    fill_mar = PatternFill("solid", fgColor="F3F4F6")
    fill_calc = PatternFill("solid", fgColor="F1F5F9")
    fill_sec = PatternFill("solid", fgColor="9CA3AF")
    fill_tot = PatternFill("solid", fgColor="E5E7EB")

    align_c = Alignment(horizontal="center", vertical="center")
    align_l = Alignment(horizontal="left", vertical="center")

    cols_headers = ["EXH", "BOD", "GT", "DAÑ", "S/E", "TOT", "TR", "MIM", "OK", "E", "ST", "SV", "EN"]
    cols_keys = ["exh", "bod", "gt", "dan", "se", "tot", "tr", "mim", "ok", "e", "st", "sv", "en"]
    font_map = {
        "exh": f_negro, "bod": f_azul, "gt": f_rojo, "dan": f_rojo, "se": f_rojo,
        "tot": f_negro_b, "tr": f_azul, "mim": f_azul,
        "e": f_rojo, "st": f_rojo, "sv": f_rojo, "en": f_negro_b,
    }
    tot_font_map = {
        "exh": f_negro_b, "bod": f_azul_b, "gt": f_rojo_b, "dan": f_rojo_b, "se": f_rojo_b,
        "tot": f_negro_b, "tr": f_azul_b, "mim": f_azul_b,
        "e": f_rojo_b, "st": f_rojo_b, "sv": f_rojo_b, "en": f_negro_b,
    }

    for f_str, est, existe in dias_lista:
        dt_d = datetime.strptime(f_str, "%Y-%m-%d").date()
        dia_nom = DIAS_CORTO_ES[dt_d.weekday()]
        sh_name = f"{dia_nom} {dt_d.strftime('%d-%m')}"[:31]
        ws = wb.create_sheet(title=sh_name)
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:AC1")
        ws["A1"] = f"BITÁCORA DE CONTEO DE TIENDA ({t_str}) - {dia_nom.upper()} {dt_d.strftime('%d-%m-%Y')}" + ("" if existe else " [SIN GUARDAR]")
        ws["A1"].font = f_title
        ws["A1"].alignment = align_l

        ws.merge_cells("A2:AC2")
        ws["A2"] = (
            f"CAJA CHICA: {est.get('caja_chica_1', '')} | {est.get('caja_chica_2', '')} | {est.get('caja_chica_3', '')}    •    "
            f"MATUTINO Recibí: {est.get('recibi_mat', '')} / Entregó: {est.get('entrego_mat', '')}    •    "
            f"VESPERTINO Recibí: {est.get('recibi_ves', '')} / Entregó: {est.get('entrego_ves', '')}"
        )
        ws["A2"].font = f_meta

        # Fila 4: encabezados de bloque (A-B Armazones, C-O Matutino, P Gap, Q-AC Vespertino)
        ws.merge_cells("A4:B4")
        ws["A4"] = "ARMAZONES"
        ws["A4"].font = f_hdr_white
        ws["A4"].fill = fill_arm
        ws["A4"].alignment = align_c

        ws.merge_cells("C4:O4")
        ws["C4"] = "TURNO MATUTINO"
        ws["C4"].font = f_hdr_white
        ws["C4"].fill = fill_mat
        ws["C4"].alignment = align_c

        ws.merge_cells("Q4:AC4")
        ws["Q4"] = "TURNO VESPERTINO"
        ws["Q4"].font = f_hdr_white
        ws["Q4"].fill = fill_ves
        ws["Q4"].alignment = align_c

        # Fila 5: sub-encabezados de columna
        ws.cell(5, 1, "CÓD").font = f_hdr_dark
        ws.cell(5, 1).fill = fill_subhdr
        ws.cell(5, 1).alignment = align_c
        ws.cell(5, 1).border = border_hdr
        ws.cell(5, 2, "MARCA").font = f_hdr_dark
        ws.cell(5, 2).fill = fill_subhdr
        ws.cell(5, 2).alignment = align_c
        ws.cell(5, 2).border = border_hdr

        for base_col in (3, 17):
            for idx, lbl in enumerate(cols_headers):
                c_cell = ws.cell(5, base_col + idx, lbl)
                c_cell.font = f_hdr_dark
                c_cell.fill = fill_subhdr
                c_cell.alignment = align_c
                c_cell.border = border_hdr

        filas_d = est.get("filas", {})
        cur_r = 6

        def _write_rows(tpl_list):
            nonlocal cur_r
            for tpl in tpl_list:
                k = tpl["key"]
                f_obj = filas_d.get(k, {})
                exp_val = f_obj.get("in_store_expected")

                c_cod = ws.cell(cur_r, 1, f_obj.get("codigo", tpl["codigo"]))
                c_cod.font = f_negro_b
                c_cod.fill = fill_cod
                c_cod.alignment = align_c
                c_cod.border = border_cell

                c_mar = ws.cell(cur_r, 2, f_obj.get("marca", tpl["marca"]))
                c_mar.font = f_negro
                c_mar.fill = fill_mar
                c_mar.alignment = align_l
                c_mar.border = border_cell

                for base_col, t_name in ((3, "matutino"), (17, "vespertino")):
                    raw_t = f_obj.get(t_name, {})
                    calc = calcular_fila_turno(raw_t, exp_val)
                    for idx, ck in enumerate(cols_keys):
                        cell = ws.cell(cur_r, base_col + idx)
                        cell.border = border_cell
                        cell.alignment = align_c
                        if ck in ("tot", "ok", "en"):
                            cell.fill = fill_calc
                        if not calc["activo"]:
                            continue

                        if ck == "ok":
                            if calc["ok"] is True:
                                cell.value = "✓"
                                cell.font = f_verde_b
                            elif calc["ok"] is False:
                                d_val = calc.get("diff") if calc.get("diff") is not None else 0
                                cell.value = abs(d_val)
                                cell.font = f_verde_b if d_val > 0 else f_rojo_b
                            continue

                        if ck == "tot":
                            val_num = calc["tot"]
                        elif ck == "en":
                            val_num = calc["en"]
                        else:
                            val_num = parse_int_or_none(raw_t.get(ck))

                        if val_num is not None:
                            cell.value = val_num
                            if ck == "mim" and calc["ok"] is False:
                                cell.font = f_rojo_b
                            else:
                                cell.font = font_map.get(ck, f_negro)
                cur_r += 1

        def _write_sec(label):
            nonlocal cur_r
            ws.merge_cells(start_row=cur_r, start_column=1, end_row=cur_r, end_column=2)
            c_lbl = ws.cell(cur_r, 1, label)
            c_lbl.font = f_hdr_dark
            c_lbl.fill = fill_sec
            c_lbl.alignment = align_c
            c_lbl.border = border_cell
            for ci in range(3, 30):
                if ci == 16:
                    continue
                c_e = ws.cell(cur_r, ci)
                c_e.fill = fill_subhdr
                c_e.border = border_cell
            cur_r += 1

        _write_rows(ARMAZONES_FILAS)
        _write_sec("OTRAS")
        _write_rows(OTRAS_FILAS)
        _write_sec("ACCESORIOS")
        _write_rows(ACCESORIOS_FILAS)

        # Fila TOTAL
        totales = calcular_totales_globales(est)
        ws.merge_cells(start_row=cur_r, start_column=1, end_row=cur_r, end_column=2)
        c_t = ws.cell(cur_r, 1, "TOTAL")
        c_t.font = f_negro_b
        c_t.fill = fill_tot
        c_t.alignment = align_l
        c_t.border = border_hdr
        ws.cell(cur_r, 2).border = border_hdr

        for base_col, t_name in ((3, "matutino"), (17, "vespertino")):
            t_dict = totales[t_name]
            bad_c = totales["bad_mat"] if t_name == "matutino" else totales["bad_ves"]
            ok_c = totales["ok_mat"] if t_name == "matutino" else totales["ok_ves"]
            for idx, ck in enumerate(cols_keys):
                cell = ws.cell(cur_r, base_col + idx)
                cell.fill = fill_tot
                cell.border = border_hdr
                cell.alignment = align_c
                if ck == "ok":
                    if bad_c > 0:
                        net_d = (t_dict.get("tot", 0) + t_dict.get("tr", 0)) - t_dict.get("mim", 0)
                        if net_d != 0:
                            cell.value = abs(net_d)
                            cell.font = f_verde_b if net_d > 0 else f_rojo_b
                        else:
                            cell.value = bad_c
                            cell.font = f_rojo_b
                    elif ok_c > 0:
                        cell.value = "✓"
                        cell.font = f_verde_b
                else:
                    v_sum = t_dict.get(ck, 0)
                    if v_sum != 0 or ck in ("tot", "en"):
                        cell.value = v_sum
                        cell.font = tot_font_map.get(ck, f_negro_b)

        # Anchos de columna cómodos
        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 22
        ws.column_dimensions["P"].width = 2.5
        for base_col in (3, 17):
            for idx in range(13):
                ws.column_dimensions[get_column_letter(base_col + idx)].width = 6.2
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    if default_ws in wb.worksheets and len(wb.worksheets) > 1:
        wb.remove(default_ws)

    wb.save(xlsx_path)
    return xlsx_path, filename_out


# ==============================================================================
# 5. GENERADOR PDF VECTORIAL COPIA EXACTA DE LA BITÁCORA OFICIAL (PyMuPDF)
# ==============================================================================

COLOR_NEGRO = (0.05, 0.05, 0.05)
COLOR_AZUL = (0.05, 0.25, 0.78)
COLOR_ROJO = (0.82, 0.08, 0.08)
COLOR_VERDE = (0.04, 0.58, 0.18)
COLOR_GRIS_HEADER = (0.84, 0.84, 0.84)
COLOR_GRIS_SECCION = (0.76, 0.76, 0.76)
COLOR_GRIS_TEXTO = (0.35, 0.35, 0.35)


def _draw_checkmark(page_pdf, cx, cy, size=4.0):
    """Dibuja una palomita verde vectorial limpia."""
    p1 = fitz.Point(cx - size * 0.75, cy + size * 0.05)
    p2 = fitz.Point(cx - size * 0.15, cy + size * 0.65)
    p3 = fitz.Point(cx + size * 0.85, cy - size * 0.65)
    shape = page_pdf.new_shape()
    shape.draw_line(p1, p2)
    shape.draw_line(p2, p3)
    shape.finish(color=COLOR_VERDE, width=1.15, lineCap=1, lineJoin=1)
    shape.commit()


def _draw_cross(page_pdf, cx, cy, size=3.4):
    """Dibuja un tache rojo vectorial limpio."""
    shape = page_pdf.new_shape()
    shape.draw_line(fitz.Point(cx - size * 0.65, cy - size * 0.65), fitz.Point(cx + size * 0.65, cy + size * 0.65))
    shape.draw_line(fitz.Point(cx - size * 0.65, cy + size * 0.65), fitz.Point(cx + size * 0.65, cy - size * 0.65))
    shape.finish(color=COLOR_ROJO, width=1.15, lineCap=1)
    shape.commit()


def _text_writer_append_center(tw, font_obj, rect, text, fontsize=6.5, min_fs=4.2):
    if text is None or str(text) == "":
        return
    import fitz
    s = str(text)
    fs = fontsize
    max_w = rect.width - 1.5
    while fs > min_fs and font_obj.text_length(s, fontsize=fs) > max_w:
        fs -= 0.4
    tw_len = font_obj.text_length(s, fontsize=fs)
    tx = rect.x0 + (rect.width - tw_len) / 2.0
    ty = rect.y0 + (rect.height + fs * 0.72) / 2.0
    tw.append(fitz.Point(tx, ty), s, font=font_obj, fontsize=fs)


def _text_writer_append_left(tw, font_obj, rect, text, fontsize=5.8, pad=2.5):
    if text is None or str(text) == "":
        return
    import fitz
    s = str(text)
    fs = fontsize
    max_w = rect.width - pad * 2
    while fs > 3.8 and font_obj.text_length(s, fontsize=fs) > max_w:
        fs -= 0.3
    ty = rect.y0 + (rect.height + fs * 0.72) / 2.0
    tw.append(fitz.Point(rect.x0 + pad, ty), s, font=font_obj, fontsize=fs)


def generar_pdf_bitacora(estado, filename_out=None):
    """
    Genera el PDF Carta Vertical (612 x 792 pt) copia fiel de la Bitácora de Conteo 2026.
    Guarda el archivo en custom_assets/temp_pdfs/ para descarga e impresión inmediata.
    Usa un solo Shape y TextWriters por color para renderizado vectorial en <50 ms.
    """
    import fitz
    os.makedirs(TEMP_PDF_DIR, exist_ok=True)
    fecha_str = estado.get("fecha") or get_now_mexico().strftime("%Y-%m-%d")
    tienda_str = re.sub(r"[^A-Za-z0-9_-]", "", str(estado.get("tienda") or "TIENDA"))
    if not filename_out:
        import time as _t_pdf
        filename_out = f"Bitacora_Conteo_{tienda_str}_{fecha_str}_{int(_t_pdf.time() * 1000)}.pdf"
    pdf_path = os.path.join(TEMP_PDF_DIR, filename_out)

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    font_reg = fitz.Font("helv")
    font_bold = fitz.Font("hebo")
    tw_by_color = {}

    def _get_tw(col):
        tw = tw_by_color.get(col)
        if tw is None:
            tw = fitz.TextWriter(page.rect)
            tw_by_color[col] = tw
        return tw

    def _txt_pt(x, y, s, fontsize=6.5, color=COLOR_NEGRO, bold=False):
        if s is None or str(s) == "":
            return
        _get_tw(color).append(fitz.Point(x, y), str(s), font=(font_bold if bold else font_reg), fontsize=fontsize)

    def _txt_center(rect, s, fontsize=6.5, color=COLOR_NEGRO, bold=False, min_fs=4.2):
        _text_writer_append_center(_get_tw(color), font_bold if bold else font_reg, rect, s, fontsize=fontsize, min_fs=min_fs)

    def _txt_left(rect, s, fontsize=5.8, color=COLOR_NEGRO, bold=False, pad=2.5):
        _text_writer_append_left(_get_tw(color), font_bold if bold else font_reg, rect, s, fontsize=fontsize, pad=pad)

    shp = page.new_shape()
    margin_x = 18.0
    table_w = 612.0 - 2 * margin_x  # 576 pt

    # 1. TÍTULO PRINCIPAL Y CAJA CHICA
    _txt_pt(margin_x, 22, "BITÁCORA DE CONTEO DE TIENDA", fontsize=12.5, color=COLOR_NEGRO, bold=True)
    tienda_lbl = str(estado.get("tienda") or "").strip()
    if tienda_lbl:
        _txt_pt(430, 22, f"TIENDA: {tienda_lbl}", fontsize=8.5, color=COLOR_GRIS_TEXTO, bold=True)

    try:
        dt_f = datetime.strptime(fecha_str, "%Y-%m-%d")
        fecha_fmt = dt_f.strftime("%d-%m-%y")
    except Exception:
        fecha_fmt = fecha_str

    y_meta = 37.0
    cch1 = estado.get("caja_chica_1", "")
    rec_m = estado.get("recibi_mat", "")
    ent_m = estado.get("entrego_mat", "")
    rec_v = estado.get("recibi_ves", "")
    ent_v = estado.get("entrego_ves", "")

    _txt_pt(margin_x, y_meta, f"FECHA: {fecha_fmt}", fontsize=7.5, color=COLOR_NEGRO, bold=True)
    _txt_pt(116, y_meta, f"CAJA CHICA: {cch1}", fontsize=6.5, color=COLOR_NEGRO)
    _txt_pt(212, y_meta, f"RECIBÍ: {rec_m}", fontsize=6.5, color=COLOR_NEGRO)
    _txt_pt(300, y_meta, f"ENTREGÓ: {ent_m}", fontsize=6.5, color=COLOR_NEGRO)
    _txt_pt(404, y_meta, f"RECIBÍ: {rec_v}", fontsize=6.5, color=COLOR_NEGRO)
    _txt_pt(498, y_meta, f"ENTREGÓ: {ent_v}", fontsize=6.5, color=COLOR_NEGRO)

    shp.draw_line(fitz.Point(margin_x + 32, y_meta + 2), fitz.Point(margin_x + 88, y_meta + 2))
    shp.draw_line(fitz.Point(158, y_meta + 2), fitz.Point(205, y_meta + 2))
    shp.draw_line(fitz.Point(238, y_meta + 2), fitz.Point(295, y_meta + 2))
    shp.draw_line(fitz.Point(335, y_meta + 2), fitz.Point(392, y_meta + 2))
    shp.draw_line(fitz.Point(430, y_meta + 2), fitz.Point(492, y_meta + 2))
    shp.draw_line(fitz.Point(534, y_meta + 2), fitz.Point(margin_x + table_w, y_meta + 2))
    shp.finish(color=COLOR_NEGRO, width=0.55)

    # 2. GEOMETRÍA DE COLUMNAS
    w_cod = 22.0
    w_mar = 84.0
    w_arm = w_cod + w_mar  # 106
    gap1 = 4.0
    gap2 = 6.0
    w_turno = (table_w - w_arm - gap1 - gap2) / 2.0  # 230.0 pt cada turno
    w_col = w_turno / 13.0

    x_arm = margin_x
    x_mat = x_arm + w_arm + gap1
    x_ves = x_mat + w_turno + gap2

    cols_headers = ["EXH", "BOD", "GT", "DAÑ", "S/E", "TOT", "TR", "MIM", "OK", "E", "ST", "SV", "EN"]
    cols_keys = ["exh", "bod", "gt", "dan", "se", "tot", "tr", "mim", "ok", "e", "st", "sv", "en"]

    col_colors = {
        "exh": COLOR_NEGRO,
        "bod": COLOR_AZUL,
        "gt": COLOR_ROJO,
        "dan": COLOR_ROJO,
        "se": COLOR_ROJO,
        "tot": COLOR_NEGRO,
        "tr": COLOR_AZUL,
        "mim": COLOR_AZUL,
        "e": COLOR_ROJO,
        "st": COLOR_ROJO,
        "sv": COLOR_ROJO,
        "en": COLOR_NEGRO,
    }

    # 3. ENCABEZADOS PRINCIPALES DE TABLA
    y_top = 45.0
    h_hdr1 = 12.0
    h_hdr2 = 11.0

    r_arm_top = fitz.Rect(x_arm, y_top, x_arm + w_arm, y_top + h_hdr1)
    shp.draw_rect(r_arm_top)
    shp.finish(color=COLOR_NEGRO, fill=COLOR_GRIS_SECCION, width=0.8)
    _txt_center(r_arm_top, "ARMAZONES", fontsize=6.5, bold=True)

    r_cod_hdr = fitz.Rect(x_arm, y_top + h_hdr1, x_arm + w_cod, y_top + h_hdr1 + h_hdr2)
    r_mar_hdr = fitz.Rect(x_arm + w_cod, y_top + h_hdr1, x_arm + w_arm, y_top + h_hdr1 + h_hdr2)
    shp.draw_rect(r_cod_hdr)
    shp.draw_rect(r_mar_hdr)
    _txt_center(r_cod_hdr, "CÓD.", fontsize=5.2, bold=True)
    _txt_center(r_mar_hdr, "MARCA", fontsize=5.5, bold=True)

    for x_t, titulo_t in [(x_mat, "TURNO MATUTINO"), (x_ves, "TURNO VESPERTINO")]:
        r_t_top = fitz.Rect(x_t, y_top, x_t + w_turno, y_top + h_hdr1)
        shp.draw_rect(r_t_top)
        shp.finish(color=COLOR_NEGRO, fill=(1, 1, 1), width=0.8)
        _txt_center(r_t_top, titulo_t, fontsize=6.5, bold=True)
        for idx, c_lbl in enumerate(cols_headers):
            cx0 = x_t + idx * w_col
            rc = fitz.Rect(cx0, y_top + h_hdr1, cx0 + w_col, y_top + h_hdr1 + h_hdr2)
            shp.draw_rect(rc)
            _txt_center(rc, c_lbl, fontsize=5.2, bold=True)
    shp.finish(color=COLOR_NEGRO, fill=COLOR_GRIS_HEADER, width=0.6)

    # 4. FILAS DE DATOS (46 Armazones + 4 Otras + 8 Accesorios + TOTAL)
    y_curr = y_top + h_hdr1 + h_hdr2
    h_row = 10.7
    h_sec_hdr = 11.0
    filas_dict = estado.get("filas", {})

    check_marks = []  # (cx, cy, size)
    cross_marks = []  # (cx, cy, size)

    def _draw_section_block(tpl_list, y_start):
        n = len(tpl_list)
        if n == 0:
            return y_start
        y_end = y_start + n * h_row

        # Fondos gris claro para CÓD y MARCA en lote
        shp.draw_rect(fitz.Rect(x_arm, y_start, x_arm + w_cod, y_end))
        shp.finish(color=None, fill=COLOR_GRIS_HEADER, width=0)
        shp.draw_rect(fitz.Rect(x_arm + w_cod, y_start, x_arm + w_arm, y_end))
        shp.finish(color=None, fill=(0.95, 0.95, 0.95), width=0)

        # Cuadrícula de CÓD + MARCA
        shp.draw_rect(fitz.Rect(x_arm, y_start, x_arm + w_arm, y_end))
        shp.draw_line(fitz.Point(x_arm + w_cod, y_start), fitz.Point(x_arm + w_cod, y_end))
        for i in range(1, n):
            yi = y_start + i * h_row
            shp.draw_line(fitz.Point(x_arm, yi), fitz.Point(x_arm + w_arm, yi))
        shp.finish(color=COLOR_NEGRO, width=0.45)

        # Cuadrícula de Matutino y Vespertino
        for x_t in (x_mat, x_ves):
            shp.draw_rect(fitz.Rect(x_t, y_start, x_t + w_turno, y_end))
            for idx in range(1, 13):
                xi = x_t + idx * w_col
                shp.draw_line(fitz.Point(xi, y_start), fitz.Point(xi, y_end))
            for i in range(1, n):
                yi = y_start + i * h_row
                shp.draw_line(fitz.Point(x_t, yi), fitz.Point(x_t + w_turno, yi))
        shp.finish(color=(0.35, 0.35, 0.35), width=0.35)

        # Textos y palomitas/taches de cada fila
        y_r = y_start
        for row_tpl in tpl_list:
            k = row_tpl["key"]
            f_obj = filas_dict.get(k, {})
            cod_txt = f_obj.get("codigo", row_tpl["codigo"])
            mar_txt = f_obj.get("marca", row_tpl["marca"])
            exp_val = f_obj.get("in_store_expected")

            _txt_center(fitz.Rect(x_arm, y_r, x_arm + w_cod, y_r + h_row), cod_txt, fontsize=5.2)
            _txt_center(fitz.Rect(x_arm + w_cod, y_r, x_arm + w_arm, y_r + h_row), mar_txt, fontsize=5.0)

            for x_t, turno_name in [(x_mat, "matutino"), (x_ves, "vespertino")]:
                raw = f_obj.get(turno_name, {})
                calc = calcular_fila_turno(raw, exp_val)
                if not calc["activo"]:
                    continue
                for idx, ck in enumerate(cols_keys):
                    cx0 = x_t + idx * w_col
                    rc = fitz.Rect(cx0, y_r, cx0 + w_col, y_r + h_row)
                    if ck == "ok":
                        if calc["ok"] is True:
                            check_marks.append((rc.x0 + rc.width / 2.0, rc.y0 + rc.height / 2.0, 3.4))
                        elif calc["ok"] is False:
                            d_val = calc.get("diff") if calc.get("diff") is not None else 0
                            c_diff = COLOR_VERDE if d_val > 0 else COLOR_ROJO
                            _txt_center(rc, str(abs(d_val)), fontsize=5.8, color=c_diff, bold=True)
                        continue

                    if ck == "tot":
                        val_str = "" if calc["tot"] is None else str(calc["tot"])
                    elif ck == "en":
                        val_str = "" if calc["en"] is None else str(calc["en"])
                    else:
                        v_n = parse_int_or_none(raw.get(ck))
                        val_str = "" if v_n is None else str(v_n)

                    if val_str != "":
                        c_txt = col_colors.get(ck, COLOR_NEGRO)
                        if ck == "mim" and calc["ok"] is False:
                            c_txt = COLOR_ROJO
                        _txt_center(rc, val_str, fontsize=5.8, color=c_txt, bold=(ck in ("tot", "en")))
            y_r += h_row
        return y_end

    # Sección 1: ARMAZONES (46 filas)
    y_curr = _draw_section_block(ARMAZONES_FILAS, y_curr)

    # Separador OTRAS
    y_curr += 4.0
    r_otr_h = fitz.Rect(x_arm, y_curr, x_arm + w_arm, y_curr + h_sec_hdr)
    shp.draw_rect(r_otr_h)
    for x_t in (x_mat, x_ves):
        shp.draw_rect(fitz.Rect(x_t, y_curr, x_t + w_turno, y_curr + h_sec_hdr))
    shp.finish(color=COLOR_NEGRO, fill=COLOR_GRIS_SECCION, width=0.7)
    _txt_center(r_otr_h, "OTRAS", fontsize=6.0, bold=True)
    y_curr += h_sec_hdr
    y_curr = _draw_section_block(OTRAS_FILAS, y_curr)

    # Separador ACCESORIOS
    y_curr += 4.0
    r_acc_h = fitz.Rect(x_arm, y_curr, x_arm + w_arm, y_curr + h_sec_hdr)
    shp.draw_rect(r_acc_h)
    for x_t in (x_mat, x_ves):
        shp.draw_rect(fitz.Rect(x_t, y_curr, x_t + w_turno, y_curr + h_sec_hdr))
    shp.finish(color=COLOR_NEGRO, fill=COLOR_GRIS_SECCION, width=0.7)
    _txt_center(r_acc_h, "ACCESORIOS", fontsize=6.0, bold=True)
    y_curr += h_sec_hdr
    y_curr = _draw_section_block(ACCESORIOS_FILAS, y_curr)

    # Fila TOTAL
    y_curr += 5.0
    h_tot = 14.0
    totales = calcular_totales_globales(estado)
    r_tot_lbl = fitz.Rect(x_arm, y_curr, x_arm + w_arm, y_curr + h_tot)
    shp.draw_rect(r_tot_lbl)
    shp.finish(color=COLOR_NEGRO, fill=COLOR_GRIS_SECCION, width=0.8)
    _txt_left(r_tot_lbl, "TOTAL", fontsize=7.0, bold=True, pad=6.0)

    for x_t, turno_k in [(x_mat, "matutino"), (x_ves, "vespertino")]:
        t_dict = totales[turno_k]
        for idx, ck in enumerate(cols_keys):
            cx0 = x_t + idx * w_col
            rc = fitz.Rect(cx0, y_curr, cx0 + w_col, y_curr + h_tot)
            shp.draw_rect(rc)
            if ck == "ok":
                bad_c = totales["bad_mat"] if turno_k == "matutino" else totales["bad_ves"]
                ok_c = totales["ok_mat"] if turno_k == "matutino" else totales["ok_ves"]
                if bad_c > 0:
                    net_diff = (t_dict.get("tot", 0) + t_dict.get("tr", 0)) - t_dict.get("mim", 0)
                    if net_diff != 0:
                        _txt_center(rc, str(abs(net_diff)), fontsize=5.8, color=(COLOR_VERDE if net_diff > 0 else COLOR_ROJO), bold=True)
                    else:
                        _txt_center(rc, str(bad_c), fontsize=5.8, color=COLOR_ROJO, bold=True)
                elif ok_c > 0:
                    check_marks.append((rc.x0 + rc.width / 2.0, rc.y0 + rc.height / 2.0, 3.7))
            else:
                v_sum = t_dict.get(ck, 0)
                if v_sum != 0 or ck in ("tot", "en"):
                    c_txt = col_colors.get(ck, COLOR_NEGRO)
                    _txt_center(rc, str(v_sum), fontsize=5.8, color=c_txt, bold=True)
    shp.finish(color=COLOR_NEGRO, fill=(0.94, 0.94, 0.94), width=0.6)

    # Palomitas verdes y taches rojos en lote
    if check_marks:
        for cx, cy, sz in check_marks:
            shp.draw_line(fitz.Point(cx - sz * 0.75, cy + sz * 0.05), fitz.Point(cx - sz * 0.15, cy + sz * 0.65))
            shp.draw_line(fitz.Point(cx - sz * 0.15, cy + sz * 0.65), fitz.Point(cx + sz * 0.85, cy - sz * 0.65))
        shp.finish(color=COLOR_VERDE, width=1.15, lineCap=1, lineJoin=1)
    if cross_marks:
        for cx, cy, sz in cross_marks:
            shp.draw_line(fitz.Point(cx - sz * 0.65, cy - sz * 0.65), fitz.Point(cx + sz * 0.65, cy + sz * 0.65))
            shp.draw_line(fitz.Point(cx - sz * 0.65, cy + sz * 0.65), fitz.Point(cx + sz * 0.65, cy - sz * 0.65))
        shp.finish(color=COLOR_ROJO, width=1.15, lineCap=1)

    # 5. PIE DE PÁGINA CON ABREVIATURAS OFICIALES
    y_foot = y_curr + h_tot + 6.0
    r_foot = fitz.Rect(margin_x, y_foot, margin_x + table_w, 780.0)
    shp.draw_rect(r_foot)
    shp.finish(color=COLOR_NEGRO, fill=(0.96, 0.96, 0.96), width=0.7)

    shp.commit()

    l1 = "EXH: EXHIBICIÓN    BOD: BODEGA    GT: GARANTÍAS    DAÑ: DAÑADOS    S/E: SIN ETIQUETA    TOT: TOTAL    TR: MERCANCÍA EN TRÁNSITO"
    l2 = "MIM: TOTAL RESUMEN EN INVENTARIO    E: ENTRADAS    ST: SALIDAS POR TRANSFERENCIA    SV: SALIDAS POR VENTA    EN: TOTAL ENTREGADO EN TURNO"
    _txt_center(fitz.Rect(margin_x, y_foot + 2, margin_x + table_w, y_foot + 13), l1, fontsize=5.4, bold=True)
    _txt_center(fitz.Rect(margin_x, y_foot + 13, margin_x + table_w, y_foot + 24), l2, fontsize=5.4, bold=True)

    for col, tw in tw_by_color.items():
        tw.write_text(page, color=col)

    pdf_bytes = doc.tobytes()
    doc.close()
    try:
        with open(pdf_path, "wb") as f_pdf:
            f_pdf.write(pdf_bytes)
    except PermissionError:
        import time as _t_pdf2
        base_n, ext_n = os.path.splitext(filename_out)
        filename_out = f"{base_n}_{int(_t_pdf2.time() * 1000)}{ext_n}"
        pdf_path = os.path.join(TEMP_PDF_DIR, filename_out)
        with open(pdf_path, "wb") as f_pdf:
            f_pdf.write(pdf_bytes)
    return pdf_path, filename_out
