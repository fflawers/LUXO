# -*- coding: utf-8 -*-
"""
Vista Flet para Digitalización de Bitácora de Conteo de Tienda.
Diseño tipo hoja oficial (fondo claro de alta legibilidad para respetar los
colores exactos de los números: Negro, Azul, Rojo y Palomita Verde / Tache Rojo).
"""

import os
import asyncio
import calendar
import threading
import urllib.parse
from datetime import datetime, timedelta, date
import flet as ft

import bitacora_conteo_service as bcs

HEX_NEGRO = "#111827"
HEX_AZUL = "#0B41C7"
HEX_ROJO = "#D11414"
HEX_VERDE = "#0A942E"

FIELD_TEXT_COLOR = {
    "exh": HEX_NEGRO,
    "bod": HEX_AZUL,
    "gt": HEX_ROJO,
    "dan": HEX_ROJO,
    "se": HEX_ROJO,
    "tr": HEX_AZUL,
    "mim": HEX_AZUL,
    "e": HEX_ROJO,
    "st": HEX_ROJO,
    "sv": HEX_ROJO,
}


def _seleccionar_excel_nativo(titulo="Seleccionar Excel MIM"):
    try:
        import subprocess
        ps_cmd = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $f = New-Object System.Windows.Forms.OpenFileDialog
        $f.InitialDirectory = [System.IO.Path]::Combine($env:USERPROFILE, 'Downloads')
        $f.Filter = "Archivos Excel (*.xlsx;*.xls)|*.xlsx;*.xls|Todos los archivos (*.*)|*.*"
        $f.Title = "{titulo}"
        $f.TopMost = $true
        $result = $f.ShowDialog()
        if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
            Write-Output $f.FileName
        }}
        '''
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=120
        )
        sel = proc.stdout.strip()
        if sel and os.path.exists(sel):
            return sel
    except Exception:
        pass
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        sel = filedialog.askopenfilename(
            title=titulo,
            initialdir=os.path.expanduser("~/Downloads"),
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")]
        )
        root.destroy()
        if sel and os.path.exists(sel):
            return sel
    except Exception:
        pass
    return ""


def build_bitacora_conteo_view(
    page: ft.Page,
    store_code="A540",
    store_name="Tienda",
    user_info=None,
    seleccionar_archivo_async=None,
    mostrar_snack_fn=None,
):
    if user_info is None:
        user_info = {}

    tienda_key = str(store_code or user_info.get("tienda") or "GENERAL").strip()
    hoy = bcs.get_now_mexico().date()
    fecha_actual = [hoy]
    turno_activo = ["matutino"]  # "matutino" o "vespertino"
    q_seleccionado = [None]
    estado_ref = {"data": None}
    solo_con_stock = [False]
    filtro_texto = [""]
    vespertino_manual_keys = set()
    marcas_tienda_set = set(bcs.obtener_marcas_tienda(tienda_key))
    cell_grid = []        # list of dicts: {col_key: cell_meta}
    cell_col_order = []   # list of lists of (col_key, cell_meta) per row
    row_y_offsets = []    # y offset in px for each visible row
    active_cell_pos = [None]  # (r_idx, col_key) or None
    cell_fresh_edit = [True]
    shift_held = [False]
    scroll_win_top = [0]
    body_scroll_col_ref = [None]
    body_height_ref = [460]
    total_row_ref = [None]
    kb_listener_ref = [None]
    EDIT_COLS_ORDER = ["cod", "mar", "exh", "bod", "gt", "dan", "se", "tr", "mim", "e", "st", "sv"]

    def notify(msg, color="#065F46"):
        if mostrar_snack_fn:
            try:
                mostrar_snack_fn(msg, color=color)
                return
            except Exception:
                pass
        try:
            snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color, duration=3000)
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception:
            pass

    # Cargar estado inicial del día actual
    estado_init, existe_en_bd = bcs.cargar_bitacora_dia(tienda_key, fecha_actual[0].strftime("%Y-%m-%d"))
    estado_ref["data"] = estado_init

    # Referencias de controles por fila para actualización rápida sin reconstruir toda la tabla
    row_widgets = {}  # (turno, row_key) -> {"inputs": {campo: TextField}, "tot": Text, "ok": Control, "diff": Text, "en": Text}
    total_widgets = {}  # turno -> {col: Text}
    brand_inputs = {}   # row_key -> {"codigo": TextField, "marca": TextField}

    lbl_fecha = ft.Text("", size=15, weight="bold", color="#00FFFF")
    lbl_carpeta_q = ft.Text("", size=12, weight="bold", color="#D8B4FE")
    lbl_estado_guardado = ft.Text(
        "📂 Registro guardado" if existe_en_bd else "✨ Nuevo día (EXH autorellenado)",
        size=11, color="#7CFC00" if existe_en_bd else "#FBBF24", weight="bold"
    )
    lbl_resumen_banner = ft.Text("", size=12, color="white", weight="bold")

    # Campos de cabecera física (Caja Chica, Recibí, Entregó)
    def _make_header_tf(label, width, key_estado):
        tf = ft.TextField(
            label=label,
            value=str(estado_ref["data"].get(key_estado, "") or ""),
            width=width,
            height=30,
            text_size=11,
            label_style=ft.TextStyle(size=10),
            color="white",
            border_color="#475569",
            focused_border_color="#00FFFF",
            content_padding=ft.padding.Padding(6, 2, 6, 2),
        )
        def _on_ch(e):
            estado_ref["data"][key_estado] = e.control.value or ""
        def _on_hdr_focus(e):
            active_cell_pos[0] = None
        tf.on_change = _on_ch
        tf.on_focus = _on_hdr_focus
        return tf

    tf_cch1 = _make_header_tf("Caja Chica 1", 92, "caja_chica_1")
    tf_cch2 = _make_header_tf("Caja Chica 2", 92, "caja_chica_2")
    tf_cch3 = _make_header_tf("Caja Chica 3", 92, "caja_chica_3")
    tf_rec_m = _make_header_tf("Recibí (Matutino)", 124, "recibi_mat")
    tf_ent_m = _make_header_tf("Entregó (Matutino)", 124, "entrego_mat")
    tf_rec_v = _make_header_tf("Recibí (Vespertino)", 124, "recibi_ves")
    tf_ent_v = _make_header_tf("Entregó (Vespertino)", 124, "entrego_ves")

    def _sync_header_fields_from_state():
        d = estado_ref["data"]
        tf_cch1.value = d.get("caja_chica_1", "")
        tf_cch2.value = d.get("caja_chica_2", "")
        tf_cch3.value = d.get("caja_chica_3", "")
        tf_rec_m.value = d.get("recibi_mat", "")
        tf_ent_m.value = d.get("entrego_mat", "")
        tf_rec_v.value = d.get("recibi_ves", "")
        tf_ent_v.value = d.get("entrego_ves", "")

    def _actualizar_badges_fecha_q():
        d_cur = fecha_actual[0]
        q_starts = bcs.obtener_config_q(tienda_key, d_cur.year)
        info_q = bcs.calcular_info_q_fecha(d_cur, q_starts)
        q_seleccionado[0] = info_q["q"]
        lbl_fecha.value = f"📅 {d_cur.strftime('%d-%m-%Y')}"
        lbl_carpeta_q.value = f"📁 Carpeta: {info_q['carpeta']}"

    def _recalcular_y_pintar_totales(turno):
        totales = bcs.calcular_totales_globales(estado_ref["data"])
        t_dict = totales[turno]
        tw = total_widgets.get(turno, {})
        for col_k, txt_ctrl in tw.items():
            if col_k == "ok":
                bad_c = totales["bad_mat"] if turno == "matutino" else totales["bad_ves"]
                ok_c = totales["ok_mat"] if turno == "matutino" else totales["ok_ves"]
                if bad_c > 0:
                    net_diff = (t_dict.get("tot", 0) + t_dict.get("tr", 0)) - t_dict.get("mim", 0)
                    if net_diff != 0:
                        txt_ctrl.value = str(abs(net_diff))
                        txt_ctrl.color = HEX_VERDE if net_diff > 0 else HEX_ROJO
                    else:
                        txt_ctrl.value = str(bad_c)
                        txt_ctrl.color = HEX_ROJO
                elif ok_c > 0:
                    txt_ctrl.value = "✓"
                    txt_ctrl.color = HEX_VERDE
                else:
                    txt_ctrl.value = ""
            else:
                v = t_dict.get(col_k, 0)
                txt_ctrl.value = str(v) if (v != 0 or col_k in ("tot", "en")) else "0"

    def _actualizar_celdas_calculadas_fila(turno, row_key):
        f_obj = estado_ref["data"]["filas"].get(row_key, {})
        raw = f_obj.get(turno, {})
        calc = bcs.calcular_fila_turno(raw, f_obj.get("in_store_expected"))
        w = row_widgets.get((turno, row_key))
        if not w:
            return

        mim_txt = w["texts"].get("mim")
        if not calc["activo"]:
            w["tot"].value = ""
            w["ok"].value = ""
            w["diff"].value = ""
            w["en"].value = ""
            if mim_txt:
                mim_txt.color = HEX_AZUL
        else:
            w["tot"].value = "" if calc["tot"] is None else str(calc["tot"])
            w["en"].value = "" if calc["en"] is None else str(calc["en"])
            if calc["ok"] is True:
                w["ok"].value = "✓"
                w["ok"].color = HEX_VERDE
                w["diff"].value = ""
                if mim_txt:
                    mim_txt.color = HEX_AZUL
            elif calc["ok"] is False:
                d_val = calc["diff"] if calc["diff"] is not None else 0
                w["ok"].value = str(abs(d_val))
                w["ok"].color = HEX_VERDE if d_val > 0 else HEX_ROJO
                w["diff"].value = ""
                if mim_txt:
                    mim_txt.color = HEX_ROJO
            else:
                w["ok"].value = ""
                w["diff"].value = ""
                if mim_txt:
                    mim_txt.color = HEX_AZUL

        _recalcular_y_pintar_totales(turno)

    tabla_host = ft.Column(spacing=0)

    def _dlg_width(ideal_w):
        pw = getattr(page, "width", None) or ideal_w
        try:
            return min(ideal_w, max(280, int(pw) - 48))
        except Exception:
            return ideal_w

    pw_init = getattr(page, "width", None) or 1200
    modo_tactil = [bool(pw_init < 950)]

    lbl_celda_activa = ft.Text("Haz clic en una celda (↑ ↓ ← →, Tab, Enter)", size=12, weight="bold", color="#00FFFF")
    tf_editor_rapido = ft.TextField(
        hint_text="Valor celda activa",
        width=145 if pw_init < 680 else 170,
        height=34,
        dense=True,
        text_size=13,
        color="white",
        bgcolor="#1E293B",
        border_color="#38BDF8",
        focused_border_color="#00FFFF",
        keyboard_type=ft.KeyboardType.NUMBER,
        content_padding=ft.padding.Padding(8, 4, 8, 4),
    )

    def _fila_tiene_datos(f_obj, rk=None):
        if not f_obj:
            return False
        if rk and rk in marcas_tienda_set:
            return True
        if f_obj.get("in_store_expected") is not None:
            return True
        for t_k in ("matutino", "vespertino"):
            t_d = f_obj.get(t_k, {})
            for ck in ("exh", "bod", "gt", "dan", "se", "tr", "mim", "e", "st", "sv"):
                if str(t_d.get(ck, "") or "").strip() != "":
                    return True
        if f_obj.get("seccion") in ("OTRAS", "ACCESORIOS") and not f_obj.get("codigo") and not f_obj.get("marca"):
            return False
        if f_obj.get("seccion") == "OTRAS" and (str(f_obj.get("codigo", "")).strip() or str(f_obj.get("marca", "")).strip()):
            return True
        return False

    def _extraer_marcas_con_mim(est):
        keys = set()
        for k, f_obj in (est or {}).get("filas", {}).items():
            mat_mim = str(f_obj.get("matutino", {}).get("mim", "") or "").strip()
            ves_mim = str(f_obj.get("vespertino", {}).get("mim", "") or "").strip()
            if f_obj.get("in_store_expected") is not None or mat_mim != "" or ves_mim != "":
                keys.add(k)
        return keys

    def _auto_activar_filtro_si_hay_marcas():
        est_act = estado_ref["data"]
        if not marcas_tienda_set and est_act:
            en_dia = _extraer_marcas_con_mim(est_act)
            if en_dia:
                marcas_tienda_set.update(en_dia)
                threading.Thread(
                    target=bcs.guardar_marcas_tienda,
                    args=(tienda_key, list(marcas_tienda_set)),
                    daemon=True,
                ).start()
        if marcas_tienda_set or any(_fila_tiene_datos(f, k) for k, f in (est_act or {}).get("filas", {}).items()):
            solo_con_stock[0] = True
            _actualizar_btn_filtro()

    async def _focus_ctrl_async(ctrl, scroll_off=None, from_tab=False):
        try:
            if scroll_off is not None and body_scroll_col_ref[0] is not None:
                await body_scroll_col_ref[0].scroll_to(offset=scroll_off, duration=50)
        except Exception:
            pass
        try:
            if ctrl is not None:
                await ctrl.focus()
                if from_tab:
                    await asyncio.sleep(0.025)
                    await ctrl.focus()
        except Exception:
            pass

    def _get_cell_value(rk, ck):
        f_obj = estado_ref["data"]["filas"].get(rk, {})
        if ck == "cod":
            return str(f_obj.get("codigo", "") or "")
        if ck == "mar":
            return str(f_obj.get("marca", "") or "")
        return str(f_obj.get(turno_activo[0], {}).get(ck, "") or "")

    def _set_cell_value(rk, ck, raw_val, update_editor=True):
        turno = turno_activo[0]
        f_obj = estado_ref["data"]["filas"][rk]
        if ck == "cod":
            val_s = str(raw_val or "")[:10]
            f_obj["codigo"] = val_s
        elif ck == "mar":
            val_s = str(raw_val or "")[:30]
            f_obj["marca"] = val_s
        else:
            val_s = "".join(ch for ch in str(raw_val or "") if ch.isdigit())
            f_obj[turno][ck] = val_s
            if turno == "vespertino":
                vespertino_manual_keys.add(rk)
            elif rk not in vespertino_manual_keys:
                bcs.aplicar_ajuste_fila_a_vespertino(estado_ref["data"], rk)

        upd_ctrls = []
        w = row_widgets.get((turno, rk))
        if w:
            txt_c = w["texts"].get(ck)
            if txt_c is not None:
                txt_c.value = val_s
            if ck not in ("cod", "mar"):
                _actualizar_celdas_calculadas_fila(turno, rk)
                upd_ctrls.append(w["row"])
            elif w.get("left_row") is not None:
                upd_ctrls.append(w["left_row"])
            else:
                upd_ctrls.append(w["row"])
        if ck not in ("cod", "mar"):
            if total_row_ref[0] is not None:
                upd_ctrls.append(total_row_ref[0])
        if update_editor:
            tf_editor_rapido.value = val_s
            upd_ctrls.append(tf_editor_rapido)
        if upd_ctrls:
            try:
                page.update(*upd_ctrls)
            except Exception:
                pass

    def _select_cell(nr, nck, from_tab=False, from_arrow=False, focus_editor=False):
        if not cell_grid or nr < 0 or nr >= len(cell_grid) or nck not in cell_grid[nr]:
            return
        upd_ctrls = []
        prev = active_cell_pos[0]
        if prev is not None and prev != (nr, nck):
            pr, pck = prev
            if 0 <= pr < len(cell_grid) and pck in cell_grid[pr]:
                p_meta = cell_grid[pr][pck]
                p_meta["cont"].border = ft.Border.all(0.5, p_meta["base_border"])
                p_meta["cont"].bgcolor = p_meta["base_bg"]
                upd_ctrls.append(p_meta["cont"])

        active_cell_pos[0] = (nr, nck)
        cell_fresh_edit[0] = True
        meta = cell_grid[nr][nck]
        meta["cont"].border = ft.Border.all(2.2, "#0284C7")
        meta["cont"].bgcolor = "#DBEAFE"
        upd_ctrls.append(meta["cont"])

        rk = meta["rk"]
        f_obj = estado_ref["data"]["filas"].get(rk, {})
        marca_lbl = f_obj.get("marca") or rk
        lbl_celda_activa.value = f"{marca_lbl} • {nck.upper()}"
        tf_editor_rapido.value = _get_cell_value(rk, nck)
        tf_editor_rapido.keyboard_type = ft.KeyboardType.TEXT if meta["editable_text"] else ft.KeyboardType.NUMBER
        upd_ctrls.extend([lbl_celda_activa, tf_editor_rapido])
        try:
            page.update(*upd_ctrls)
        except Exception:
            pass

        # Scroll vertical solo si la fila sale del área visible
        scroll_off = None
        if nr < len(row_y_offsets):
            y_pos = row_y_offsets[nr]
            vis_h = body_height_ref[0]
            if y_pos < scroll_win_top[0]:
                scroll_win_top[0] = max(0, y_pos - 36)
                scroll_off = scroll_win_top[0]
            elif (y_pos + 38) > (scroll_win_top[0] + vis_h):
                scroll_win_top[0] = max(0, y_pos - vis_h + 72)
                scroll_off = scroll_win_top[0]

        abrir_tactil = focus_editor or meta["editable_text"] or (modo_tactil[0] and not from_arrow and not from_tab)
        need_focus = abrir_tactil or (not from_arrow) or from_tab
        target_focus = tf_editor_rapido if abrir_tactil else kb_listener_ref[0]
        if (need_focus and target_focus is not None) or scroll_off is not None:
            try:
                page.run_task(_focus_ctrl_async, target_focus if need_focus else None, scroll_off, from_tab)
            except Exception:
                pass

    def _move_grid_focus(dr, dc, wrap_tab=False, reverse_tab=False, from_tab=False, from_arrow=False):
        if not cell_grid:
            return
        pos_act = active_cell_pos[0]
        if not pos_act:
            first_k = cell_col_order[0][0][0]
            _select_cell(0, first_k, from_tab=from_tab, from_arrow=from_arrow)
            return
        r, ck = pos_act
        if r < 0 or r >= len(cell_grid) or not cell_col_order[r]:
            return
        cols_r = [k for k, _ in cell_col_order[r]]
        pos = cols_r.index(ck) if ck in cols_r else 0

        if wrap_tab:
            if reverse_tab:
                if pos > 0:
                    nr, nck = r, cols_r[pos - 1]
                else:
                    nr = (r - 1) % len(cell_grid)
                    nck = cell_col_order[nr][-1][0]
            else:
                if pos + 1 < len(cols_r):
                    nr, nck = r, cols_r[pos + 1]
                else:
                    nr = (r + 1) % len(cell_grid)
                    nck = cell_col_order[nr][0][0]
        elif dr != 0:
            nr = max(0, min(len(cell_grid) - 1, r + dr))
            if ck in cell_grid[nr]:
                nck = ck
            elif "exh" in cell_grid[nr]:
                nck = "exh"
            else:
                nck = cell_col_order[nr][0][0]
        else:
            npos = pos + dc
            if npos < 0:
                if r > 0:
                    nr = r - 1
                    nck = cell_col_order[nr][-1][0]
                else:
                    nr, nck = 0, cols_r[0]
            elif npos >= len(cols_r):
                if r + 1 < len(cell_grid):
                    nr = r + 1
                    nck = cell_col_order[nr][0][0]
                else:
                    nr, nck = r, cols_r[-1]
            else:
                nr, nck = r, cols_r[npos]

        _select_cell(nr, nck, from_tab=from_tab, from_arrow=from_arrow)

    def _extraer_digito(key_str):
        ks = (key_str or "").strip()
        if len(ks) == 1 and ks.isdigit():
            return ks
        low = ks.lower().replace(" ", "")
        for pref in ("numpad", "digit"):
            if low.startswith(pref) and len(low) == len(pref) + 1 and low[-1].isdigit():
                return low[-1]
        return None

    def _on_grid_key_down(e):
        k_raw = getattr(e, "key", "") or ""
        k_norm = k_raw.replace(" ", "").lower()
        if k_norm in ("shiftleft", "shiftright", "shift"):
            shift_held[0] = True
            return
        if not cell_grid:
            return
        if active_cell_pos[0] is None:
            _select_cell(0, cell_col_order[0][0][0])
            return

        if k_norm == "arrowup":
            _move_grid_focus(-1, 0, from_arrow=True)
            return
        if k_norm in ("arrowdown", "enter", "numpadenter"):
            _move_grid_focus(1, 0, from_arrow=True)
            return
        if k_norm == "arrowleft":
            _move_grid_focus(0, -1, from_arrow=True)
            return
        if k_norm == "arrowright":
            _move_grid_focus(0, 1, from_arrow=True)
            return
        if k_norm == "tab":
            _move_grid_focus(0, 0, wrap_tab=True, reverse_tab=shift_held[0], from_tab=True)
            return
        if k_norm == "f2":
            r, ck = active_cell_pos[0]
            _select_cell(r, ck, focus_editor=True)
            return

        r, ck = active_cell_pos[0]
        meta = cell_grid[r][ck]
        rk = meta["rk"]

        if k_norm == "delete":
            cell_fresh_edit[0] = False
            _set_cell_value(rk, ck, "")
            return
        if k_norm == "backspace":
            cur_v = _get_cell_value(rk, ck)
            cell_fresh_edit[0] = False
            _set_cell_value(rk, ck, cur_v[:-1])
            return

        dig = _extraer_digito(k_raw)
        if dig is not None and not meta["editable_text"]:
            cur_v = _get_cell_value(rk, ck)
            new_v = dig if cell_fresh_edit[0] else (cur_v + dig)
            cell_fresh_edit[0] = False
            _set_cell_value(rk, ck, new_v)

    def _on_grid_key_up(e):
        k_norm = (getattr(e, "key", "") or "").replace(" ", "").lower()
        if k_norm in ("shiftleft", "shiftright", "shift"):
            shift_held[0] = False

    def _on_editor_change(e):
        pos = active_cell_pos[0]
        if not pos:
            return
        r, ck = pos
        if 0 <= r < len(cell_grid) and ck in cell_grid[r]:
            rk = cell_grid[r][ck]["rk"]
            cell_fresh_edit[0] = False
            _set_cell_value(rk, ck, e.control.value, update_editor=False)

    def _on_editor_submit(e):
        _move_grid_focus(1, 0)

    tf_editor_rapido.on_change = _on_editor_change
    tf_editor_rapido.on_submit = _on_editor_submit

    kb_listener = ft.KeyboardListener(
        content=tabla_host,
        autofocus=True,
        on_key_down=_on_grid_key_down,
        on_key_up=_on_grid_key_up,
    )
    kb_listener_ref[0] = kb_listener

    def _construir_tabla_turno():
        turno = turno_activo[0]
        row_widgets.clear()
        total_widgets.clear()
        brand_inputs.clear()
        cell_grid.clear()
        cell_col_order.clear()
        row_y_offsets.clear()
        active_cell_pos[0] = None
        scroll_win_top[0] = 0

        es_movil = (getattr(page, "width", None) or 1200) < 680
        W_COD = 38 if es_movil else 48
        W_MAR = 122 if es_movil else 180
        W_NUM = 44 if es_movil else 52
        W_OK = 48 if es_movil else 56
        H_ROW = 36 if es_movil else 34

        def _hdr_cell(txt, width, bg="#D1D5DB", color="#111827"):
            return ft.Container(
                content=ft.Text(txt, size=11, weight="bold", color=color, text_align=ft.TextAlign.CENTER),
                width=width,
                height=30,
                bgcolor=bg,
                border=ft.Border.all(0.5, "#6B7280"),
                alignment=ft.alignment.Alignment(0, 0),
            )

        titulo_turno = "TURNO MATUTINO" if turno == "matutino" else "TURNO VESPERTINO"
        bg_turno = "#1E3A8A" if turno == "matutino" else "#581C87"

        W_LEFT = W_COD + W_MAR
        W_RIGHT = W_NUM * 12 + W_OK

        hdr_left_top = ft.Container(
            content=ft.Text("ARMAZONES", size=11, weight="bold", color="white"),
            width=W_LEFT,
            height=26,
            bgcolor="#374151",
            border=ft.Border.all(0.5, "#111827"),
            alignment=ft.alignment.Alignment(0, 0),
        )
        hdr_left_cols = ft.Row([
            _hdr_cell("CÓD", W_COD),
            _hdr_cell("MARCA", W_MAR),
        ], spacing=0)

        hdr_right_top = ft.Container(
            content=ft.Text(titulo_turno, size=12, weight="bold", color="white"),
            width=W_RIGHT,
            height=26,
            bgcolor=bg_turno,
            border=ft.Border.all(0.5, "#111827"),
            alignment=ft.alignment.Alignment(0, 0),
        )
        hdr_right_cols = ft.Row([
            _hdr_cell("EXH", W_NUM, color=HEX_NEGRO),
            _hdr_cell("BOD", W_NUM, color=HEX_AZUL),
            _hdr_cell("GT", W_NUM, color=HEX_ROJO),
            _hdr_cell("DAÑ", W_NUM, color=HEX_ROJO),
            _hdr_cell("S/E", W_NUM, color=HEX_ROJO),
            _hdr_cell("TOT", W_NUM, bg="#E5E7EB", color=HEX_NEGRO),
            _hdr_cell("TR", W_NUM, color=HEX_AZUL),
            _hdr_cell("MIM", W_NUM, color=HEX_AZUL),
            _hdr_cell("OK", W_OK, bg="#E5E7EB", color=HEX_VERDE),
            _hdr_cell("E", W_NUM, color=HEX_ROJO),
            _hdr_cell("ST", W_NUM, color=HEX_ROJO),
            _hdr_cell("SV", W_NUM, color=HEX_ROJO),
            _hdr_cell("EN", W_NUM, bg="#E5E7EB", color=HEX_NEGRO),
        ], spacing=0)

        left_rows = []
        right_rows = []
        y_cursor = [0]
        filas_data = estado_ref["data"]["filas"]
        q_busq = filtro_texto[0].strip().lower()

        def _make_section_bars(label):
            l_bar = ft.Container(
                content=ft.Text(label, size=11, weight="bold", color="#111827"),
                width=W_LEFT,
                height=22,
                bgcolor="#9CA3AF",
                border=ft.Border.all(0.5, "#374151"),
                alignment=ft.alignment.Alignment(0, 0),
            )
            r_bar = ft.Container(
                width=W_RIGHT,
                height=22,
                bgcolor="#D1D5DB",
                border=ft.Border.all(0.5, "#374151"),
            )
            return l_bar, r_bar

        def _build_light_cell(row_key, campo_key, val_init, r_idx, width_c, base_bg="#FFFFFF", base_border="#CBD5E1", align_left=False, editable_text=False, txt_size=13, color_override=None):
            t_color = color_override or FIELD_TEXT_COLOR.get(campo_key, HEX_NEGRO)
            txt = ft.Text(
                str(val_init or ""),
                size=txt_size,
                weight=ft.FontWeight.W_600,
                color=t_color,
                text_align=ft.TextAlign.LEFT if align_left else ft.TextAlign.CENTER,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
            cont = ft.Container(
                content=txt,
                width=width_c,
                height=H_ROW,
                bgcolor=base_bg,
                border=ft.Border.all(0.5, base_border),
                padding=ft.padding.Padding(5, 0, 2, 0) if align_left else None,
                alignment=ft.alignment.Alignment(-1, 0) if align_left else ft.alignment.Alignment(0, 0),
                on_click=lambda e, rr=r_idx, cc=campo_key: _select_cell(rr, cc),
            )
            meta = {
                "rk": row_key,
                "cont": cont,
                "txt": txt,
                "base_bg": base_bg,
                "base_border": base_border,
                "editable_text": editable_text,
            }
            return txt, cont, meta

        def _add_template_rows(tpl_list, editable_brand=False, section_label=None):
            rendered_any = False
            for tpl in tpl_list:
                rk = tpl["key"]
                f_obj = filas_data.setdefault(rk, {
                    "codigo": tpl["codigo"],
                    "marca": tpl["marca"],
                    "seccion": tpl.get("seccion", "ARMAZONES"),
                    "matutino": bcs.empty_shift_row(),
                    "vespertino": bcs.empty_shift_row(),
                    "in_store_expected": None,
                })
                if solo_con_stock[0] and not _fila_tiene_datos(f_obj, rk):
                    continue
                if q_busq:
                    c_s = str(f_obj.get("codigo", "")).lower()
                    m_s = str(f_obj.get("marca", "")).lower()
                    if q_busq not in c_s and q_busq not in m_s:
                        continue

                if section_label and not rendered_any:
                    sb_l, sb_r = _make_section_bars(section_label)
                    left_rows.append(sb_l)
                    right_rows.append(sb_r)
                    y_cursor[0] += 22
                rendered_any = True

                raw_t = f_obj.setdefault(turno, bcs.empty_shift_row())
                r_idx = len(cell_grid)
                row_map = {}
                row_order = []
                texts_map = {}

                if editable_brand:
                    t_cod, cell_cod, m_cod = _build_light_cell(
                        rk, "cod", f_obj.get("codigo", ""), r_idx, W_COD,
                        base_bg="#E5E7EB", base_border="#9CA3AF", editable_text=True, txt_size=10, color_override=HEX_NEGRO,
                    )
                    t_mar, cell_mar, m_mar = _build_light_cell(
                        rk, "mar", f_obj.get("marca", ""), r_idx, W_MAR,
                        base_bg="#F3F4F6", base_border="#9CA3AF", align_left=True, editable_text=True, txt_size=10, color_override=HEX_NEGRO,
                    )
                    texts_map["cod"] = t_cod
                    texts_map["mar"] = t_mar
                    row_map["cod"] = m_cod
                    row_map["mar"] = m_mar
                    row_order.extend([("cod", m_cod), ("mar", m_mar)])
                else:
                    cell_cod = ft.Container(
                        content=ft.Text(f_obj.get("codigo", tpl["codigo"]), size=10, weight="bold", color=HEX_NEGRO),
                        width=W_COD, height=H_ROW, bgcolor="#E5E7EB", border=ft.Border.all(0.5, "#9CA3AF"),
                        alignment=ft.alignment.Alignment(0, 0),
                    )
                    cell_mar = ft.Container(
                        content=ft.Text(f_obj.get("marca", tpl["marca"]), size=10, weight="bold", color=HEX_NEGRO),
                        width=W_MAR, height=H_ROW, bgcolor="#F3F4F6", border=ft.Border.all(0.5, "#9CA3AF"),
                        padding=ft.padding.Padding(5, 0, 2, 0),
                        alignment=ft.alignment.Alignment(-1, 0),
                    )

                left_row = ft.Row([cell_cod, cell_mar], spacing=0)
                num_cells = []

                for ck in ["exh", "bod", "gt", "dan", "se"]:
                    t_c, cont_c, m_c = _build_light_cell(rk, ck, raw_t.get(ck, ""), r_idx, W_NUM)
                    texts_map[ck] = t_c
                    row_map[ck] = m_c
                    row_order.append((ck, m_c))
                    num_cells.append(cont_c)

                txt_tot = ft.Text("", size=12, weight="bold", color=HEX_NEGRO)
                num_cells.append(ft.Container(content=txt_tot, width=W_NUM, height=H_ROW, bgcolor="#F1F5F9", border=ft.Border.all(0.5, "#9CA3AF"), alignment=ft.alignment.Alignment(0, 0)))

                for ck in ["tr", "mim"]:
                    t_ro = ft.Text(
                        str(raw_t.get(ck, "") or ""),
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=FIELD_TEXT_COLOR.get(ck, HEX_AZUL),
                        text_align=ft.TextAlign.CENTER,
                    )
                    texts_map[ck] = t_ro
                    num_cells.append(ft.Container(
                        content=t_ro,
                        width=W_NUM,
                        height=H_ROW,
                        bgcolor="#F8FAFC",
                        border=ft.Border.all(0.5, "#CBD5E1"),
                        alignment=ft.alignment.Alignment(0, 0),
                    ))

                txt_ok = ft.Text("", size=14, weight="bold", color=HEX_VERDE)
                txt_diff = ft.Text("", size=9, weight="bold", color=HEX_ROJO)
                num_cells.append(ft.Container(
                    content=ft.Row([txt_ok, txt_diff], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    width=W_OK, height=H_ROW, bgcolor="#F1F5F9", border=ft.Border.all(0.5, "#9CA3AF"),
                    alignment=ft.alignment.Alignment(0, 0),
                ))

                for ck in ["e", "st", "sv"]:
                    t_c, cont_c, m_c = _build_light_cell(rk, ck, raw_t.get(ck, ""), r_idx, W_NUM)
                    texts_map[ck] = t_c
                    row_map[ck] = m_c
                    row_order.append((ck, m_c))
                    num_cells.append(cont_c)

                txt_en = ft.Text("", size=12, weight="bold", color=HEX_NEGRO)
                num_cells.append(ft.Container(content=txt_en, width=W_NUM, height=H_ROW, bgcolor="#F1F5F9", border=ft.Border.all(0.5, "#9CA3AF"), alignment=ft.alignment.Alignment(0, 0)))

                row_ctrl = ft.Row(num_cells, spacing=0)
                cell_grid.append(row_map)
                cell_col_order.append(row_order)
                row_y_offsets.append(y_cursor[0])
                y_cursor[0] += H_ROW

                row_widgets[(turno, rk)] = {
                    "row": row_ctrl,
                    "left_row": left_row,
                    "texts": texts_map,
                    "tot": txt_tot,
                    "ok": txt_ok,
                    "diff": txt_diff,
                    "en": txt_en,
                }
                left_rows.append(left_row)
                right_rows.append(row_ctrl)
                _actualizar_celdas_calculadas_fila(turno, rk)

        _add_template_rows(bcs.ARMAZONES_FILAS, editable_brand=False)
        _add_template_rows(bcs.OTRAS_FILAS, editable_brand=True, section_label="OTRAS")
        _add_template_rows(bcs.ACCESORIOS_FILAS[:5], editable_brand=False, section_label="ACCESORIOS")
        _add_template_rows(bcs.ACCESORIOS_FILAS[5:], editable_brand=True)

        if not right_rows:
            left_rows.append(ft.Container(width=W_LEFT, height=70, bgcolor="#F8FAFC"))
            right_rows.append(
                ft.Container(
                    content=ft.Text(
                        "Sin marcas visibles con ese filtro. Limpia la búsqueda o pulsa 'Todas las marcas'.",
                        size=12, color="#475569", weight="bold"
                    ),
                    width=W_RIGHT,
                    height=70,
                    bgcolor="#F8FAFC",
                    alignment=ft.alignment.Alignment(0, 0),
                )
            )
            y_cursor[0] += 70

        # Fila TOTAL (fija debajo de las filas visibles)
        tot_map = {}
        tot_left_cell = ft.Container(
            content=ft.Text("TOTAL", size=12, weight="bold", color=HEX_NEGRO),
            width=W_LEFT, height=32, bgcolor="#D1D5DB", border=ft.Border.all(0.8, "#111827"),
            padding=ft.padding.Padding(8, 0, 0, 0), alignment=ft.alignment.Alignment(-1, 0),
        )
        tot_cells = []
        for ck in ["exh", "bod", "gt", "dan", "se", "tot", "tr", "mim", "ok", "e", "st", "sv", "en"]:
            c_w = W_OK if ck == "ok" else W_NUM
            c_col = bcs.FIELD_TEXT_COLOR.get(ck, HEX_NEGRO) if hasattr(bcs, "FIELD_TEXT_COLOR") else FIELD_TEXT_COLOR.get(ck, HEX_NEGRO)
            t_ctrl = ft.Text("0", size=11, weight="bold", color=c_col)
            tot_map[ck] = t_ctrl
            tot_cells.append(ft.Container(
                content=t_ctrl, width=c_w, height=32, bgcolor="#E5E7EB",
                border=ft.Border.all(0.8, "#111827"), alignment=ft.alignment.Alignment(0, 0),
            ))
        total_widgets[turno] = tot_map
        total_row = ft.Row(tot_cells, spacing=0)
        total_row_ref[0] = total_row

        _recalcular_y_pintar_totales(turno)

        pw_cur = getattr(page, "width", None) or 1200
        ph_cur = getattr(page, "height", None) or 760
        try:
            ph_cur = int(ph_cur)
        except Exception:
            ph_cur = 760
        vis_h = max(280, min(520, ph_cur - (310 if es_movil else 330)))
        body_height_ref[0] = vis_h

        hdr_right_scroll = ft.Row(
            [ft.Column([hdr_right_top, hdr_right_cols], spacing=0)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        body_right_scroll = ft.Row(
            [ft.Column(right_rows, spacing=0)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        tot_right_scroll = ft.Row(
            [total_row],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        h_scrollers = (hdr_right_scroll, body_right_scroll, tot_right_scroll)
        h_sync_lock = [False]
        h_last_off = [-1.0]

        async def _sync_h_async(src_idx, off):
            if h_sync_lock[0]:
                return
            h_sync_lock[0] = True
            try:
                h_last_off[0] = off
                for i, sc in enumerate(h_scrollers):
                    if i != src_idx:
                        try:
                            await sc.scroll_to(offset=off, duration=0)
                        except Exception:
                            pass
            finally:
                h_sync_lock[0] = False

        def _make_h_handler(src_idx):
            def _on_hs(e):
                if h_sync_lock[0]:
                    return
                off = float(getattr(e, "extent_before", 0.0) or 0.0)
                if abs(off - h_last_off[0]) < 1.5:
                    return
                try:
                    page.run_task(_sync_h_async, src_idx, off)
                except Exception:
                    pass
            return _on_hs

        hdr_right_scroll.on_scroll = _make_h_handler(0)
        body_right_scroll.on_scroll = _make_h_handler(1)
        tot_right_scroll.on_scroll = _make_h_handler(2)

        left_body_col = ft.Column(left_rows, spacing=0, width=W_LEFT)
        body_vscroll = ft.Column(
            [
                ft.Row(
                    [left_body_col, body_right_scroll],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            height=vis_h,
            on_scroll=lambda e: scroll_win_top.__setitem__(0, float(getattr(e, "extent_before", 0.0) or 0.0)),
        )
        body_scroll_col_ref[0] = body_vscroll

        total_table_w = W_LEFT + W_RIGHT
        tbl_w = (total_table_w + 3) if (pw_cur - 270) >= (total_table_w + 3) else None

        tabla_host.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([hdr_left_top, hdr_left_cols], spacing=0, width=W_LEFT),
                        hdr_right_scroll,
                    ], spacing=0),
                    body_vscroll,
                    ft.Row([tot_left_cell, tot_right_scroll], spacing=0),
                ], spacing=0),
                width=tbl_w,
                bgcolor="#FFFFFF",
                border=ft.Border.all(1.5, "#111827"),
                border_radius=6,
            )
        ]

    # ==========================================================================
    # ACCIONES PRINCIPALES (Fecha, Q1-Q4, MIM Excel, Ajuste Vespertino, Guardar, PDF)
    # ==========================================================================

    def _cargar_fecha(nueva_fecha):
        fecha_actual[0] = nueva_fecha
        f_str = nueva_fecha.strftime("%Y-%m-%d")
        nuevo_est, existe = bcs.cargar_bitacora_dia(tienda_key, f_str)
        estado_ref["data"] = nuevo_est
        vespertino_manual_keys.clear()
        bcs.aplicar_ajuste_matutino_a_vespertino(estado_ref["data"], skip_keys=vespertino_manual_keys)
        _auto_activar_filtro_si_hay_marcas()
        lbl_estado_guardado.value = "📂 Registro guardado" if existe else "✨ Nuevo día (EXH autorellenado)"
        lbl_estado_guardado.color = "#7CFC00" if existe else "#FBBF24"
        _sync_header_fields_from_state()
        _actualizar_badges_fecha_q()
        _construir_tabla_turno()
        try:
            page.update()
        except Exception:
            pass

    DIAS_SEMANA_CORTO = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    DIAS_SEMANA_LARGO = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    def _abrir_calendario_es(titulo, fecha_inicial, on_select_cb):
        cal_obj = calendar.Calendar(firstweekday=6)  # Domingo primero
        nav = [fecha_inicial.year, fecha_inicial.month]
        hoy_mx = bcs.get_now_mexico().date()

        lbl_mes_anio = ft.Text("", size=14, weight="bold", color="#00FFFF", expand=True, text_align=ft.TextAlign.CENTER)
        lbl_fecha_sub = ft.Text(
            f"{DIAS_SEMANA_LARGO[fecha_inicial.weekday()]}, {fecha_inicial.day} de {bcs.MESES_ES[fecha_inicial.month]} de {fecha_inicial.year}",
            size=12, color="#94A3B8"
        )
        grid_col = ft.Column(spacing=4)

        def _render_mes():
            y, m = nav[0], nav[1]
            lbl_mes_anio.value = f"{bcs.MESES_ES[m]} {y}"
            rows_c = [
                ft.Row([
                    ft.Container(
                        content=ft.Text(d_lbl, size=11, weight="bold", color="#94A3B8", text_align=ft.TextAlign.CENTER),
                        width=40, height=24, alignment=ft.alignment.Alignment(0, 0),
                    )
                    for d_lbl in DIAS_SEMANA_CORTO
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
            ]
            for week in cal_obj.monthdayscalendar(y, m):
                w_cells = []
                for day_num in week:
                    if day_num == 0:
                        w_cells.append(ft.Container(width=40, height=34))
                    else:
                        d_cell = date(y, m, day_num)
                        es_sel = (d_cell == fecha_inicial)
                        es_hoy = (d_cell == hoy_mx)
                        bg_c = "#2563EB" if es_sel else ("#1E293B" if es_hoy else "#0B1120")
                        brd_c = "#00FFFF" if es_hoy else ("#60A5FA" if es_sel else "#1E293B")
                        w_cells.append(
                            ft.Container(
                                content=ft.Text(str(day_num), size=12, weight="bold" if (es_sel or es_hoy) else "normal", color="white"),
                                width=40, height=34,
                                bgcolor=bg_c,
                                border=ft.Border.all(1.2 if (es_sel or es_hoy) else 0.5, brd_c),
                                border_radius=17,
                                alignment=ft.alignment.Alignment(0, 0),
                                ink=True,
                                on_click=lambda ev, dc=d_cell: (page.pop_dialog(), on_select_cb(dc)),
                            )
                        )
                rows_c.append(ft.Row(w_cells, spacing=4, alignment=ft.MainAxisAlignment.CENTER))
            grid_col.controls = rows_c

        def _cambiar_mes(delta_m):
            m_new = nav[1] + delta_m
            y_new = nav[0]
            if m_new < 1:
                m_new = 12
                y_new -= 1
            elif m_new > 12:
                m_new = 1
                y_new += 1
            if 2024 <= y_new <= 2032:
                nav[0], nav[1] = y_new, m_new
                _render_mes()
                try:
                    page.update(lbl_mes_anio, grid_col)
                except Exception:
                    pass

        def _cambiar_anio(delta_y):
            y_new = nav[0] + delta_y
            if 2024 <= y_new <= 2032:
                nav[0] = y_new
                _render_mes()
                try:
                    page.update(lbl_mes_anio, grid_col)
                except Exception:
                    pass

        _render_mes()
        dlg_cal = ft.AlertDialog(
            title=ft.Column([
                ft.Text(titulo, size=16, weight="bold", color="#00FFFF"),
                lbl_fecha_sub,
            ], spacing=2),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.IconButton(ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT, icon_color="#94A3B8", tooltip="Año anterior", on_click=lambda ev: _cambiar_anio(-1)),
                        ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color="#00FFFF", tooltip="Mes anterior", on_click=lambda ev: _cambiar_mes(-1)),
                        lbl_mes_anio,
                        ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color="#00FFFF", tooltip="Mes siguiente", on_click=lambda ev: _cambiar_mes(1)),
                        ft.IconButton(ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT, icon_color="#94A3B8", tooltip="Año siguiente", on_click=lambda ev: _cambiar_anio(1)),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    grid_col,
                ], spacing=8, tight=True),
                width=_dlg_width(330),
            ),
            actions=[
                ft.TextButton("Hoy", on_click=lambda ev: (page.pop_dialog(), on_select_cb(hoy_mx))),
                ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
            ],
            bgcolor="#0F172A",
        )
        page.show_dialog(dlg_cal)

    def abrir_calendario(e):
        _abrir_calendario_es("📅 Seleccionar fecha", fecha_actual[0], _cargar_fecha)

    # Configuración de inicio de Q1 en el calendario
    def _aplicar_q1_start(d_q1):
        q_starts = bcs.generar_q_starts_desde_q1(d_q1)
        bcs.guardar_config_q(tienda_key, d_q1.year, q_starts)
        _actualizar_badges_fecha_q()
        notify(f"📅 Inicio de Q1 ({d_q1.year}) fijado el {d_q1.strftime('%d-%m-%Y')}. Q1–Q4 actualizados.", "#065F46")
        try:
            page.update()
        except Exception:
            pass

    def abrir_config_q(e):
        anio_c = fecha_actual[0].year
        q_curr = bcs.obtener_config_q(tienda_key, anio_c)
        _abrir_calendario_es(f"⚙️ Inicio Semana 1 de Q1 ({anio_c})", q_curr["Q1"], _aplicar_q1_start)

    def abrir_carpetas_q(e):
        anio_c = fecha_actual[0].year
        q_starts = bcs.obtener_config_q(tienda_key, anio_c)
        info_curr = bcs.calcular_info_q_fecha(fecha_actual[0], q_starts)
        q_act = [info_curr["q"]]
        lista_dias_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=320)

        def _poblar_q(q_name):
            q_act[0] = q_name
            q_ini = q_starts[q_name]
            dias = bcs.listar_dias_por_q(tienda_key, anio_c, q_name)
            items = [
                ft.Text(f"📁 {q_name} ({anio_c}) • Inicia: {q_ini.strftime('%d-%m-%Y')} (3 meses / 13 sem)", color="#00FFFF", weight="bold", size=13)
            ]
            for m_idx in (1, 2, 3):
                dias_mes = [d for d in dias if int(d.get("mes_q", 1)) == m_idx]
                q_base = {"Q1": 0, "Q2": 13, "Q3": 26, "Q4": 39}.get(q_name, 0)
                if m_idx == 1:
                    sem_rango = f"Sem {q_base + 1}–{q_base + 4}"
                elif m_idx == 2:
                    sem_rango = f"Sem {q_base + 5}–{q_base + 8}"
                else:
                    sem_rango = f"Sem {q_base + 9}–{q_base + 13}"
                sub_btns = []
                for dm in dias_mes:
                    f_s = dm["fecha"]
                    def _go_day(ev, fs=f_s):
                        try:
                            page.pop_dialog()
                        except Exception:
                            pass
                        _cargar_fecha(datetime.strptime(fs, "%Y-%m-%d").date())
                    sub_btns.append(
                        ft.ElevatedButton(
                            f"📄 {f_s} (Sem {dm['semana']})",
                            on_click=_go_day,
                            bgcolor="#1E293B",
                            color="#00FFFF",
                            height=32,
                        )
                    )
                if not sub_btns:
                    sub_btns.append(ft.Text("Sin bitácoras guardadas aún en este mes.", size=11, color="#9CA3AF", italic=True))
                items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"📂 Mes {m_idx} de {q_name} ({sem_rango})", color="#D8B4FE", weight="bold", size=12),
                            ft.Row(sub_btns, wrap=True, spacing=6)
                        ], spacing=4),
                        padding=8, bgcolor="#141424", border=ft.Border.all(1, "#334155"), border_radius=8
                    )
                )
            lista_dias_col.controls = items
            try:
                lista_dias_col.update()
            except Exception:
                pass

        q_btns = []
        for qn in ("Q1", "Q2", "Q3", "Q4"):
            q_btns.append(
                ft.ElevatedButton(
                    qn,
                    bgcolor="#7C3AED" if qn == q_act[0] else "#1E293B",
                    color="white",
                    on_click=lambda ev, qq=qn: _poblar_q(qq)
                )
            )
        _poblar_q(q_act[0])

        dlg = ft.AlertDialog(
            title=ft.Text(f"🗂️ Carpetas Anuales {anio_c} (4Q x 3 Meses)", color="#00FFFF", weight="bold"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row(q_btns, spacing=8),
                    lista_dias_col,
                ], spacing=10),
                width=_dlg_width(540),
            ),
            actions=[
                ft.TextButton("⚙️ Cambiar inicio Q1", on_click=lambda ev: (page.pop_dialog(), abrir_config_q(ev)), visible=False),
                ft.TextButton("Cerrar", on_click=lambda ev: page.pop_dialog()),
            ],
            bgcolor="#0F172A",
        )
        page.show_dialog(dlg)

    def _actualizar_btn_filtro():
        pass

    def subir_mim_click(e):
        def _procesar_ruta(ruta):
            if not ruta:
                return
            ok, msg, info = bcs.importar_excel_mim(ruta, estado_ref["data"], aplicar_a_vespertino=True)
            if ok:
                bcs.aplicar_ajuste_matutino_a_vespertino(estado_ref["data"], skip_keys=vespertino_manual_keys)
                new_mim_keys = set(info.get("active_keys") or [])
                if not new_mim_keys:
                    new_mim_keys = _extraer_marcas_con_mim(estado_ref["data"])

                rendered_keys = {m["rk"] for r in cell_grid for m in r.values() if "rk" in m}
                perfil_cambio = (new_mim_keys != marcas_tienda_set)

                if perfil_cambio or not marcas_tienda_set:
                    marcas_tienda_set.clear()
                    marcas_tienda_set.update(new_mim_keys)
                    threading.Thread(
                        target=bcs.guardar_marcas_tienda,
                        args=(tienda_key, list(marcas_tienda_set)),
                        daemon=True,
                    ).start()

                turno = turno_activo[0]
                if solo_con_stock[0] and not perfil_cambio and new_mim_keys.issubset(rendered_keys) and rendered_keys:
                    # Actualización en sitio sin reconstruir toda la tabla
                    filas_d = estado_ref["data"]["filas"]
                    for rk in rendered_keys:
                        w = row_widgets.get((turno, rk))
                        if not w:
                            continue
                        raw_t = filas_d.get(rk, {}).get(turno, {})
                        for ck in ("exh", "bod", "tr", "mim", "e", "st", "sv"):
                            if ck in w["texts"]:
                                w["texts"][ck].value = str(raw_t.get(ck, "") or "")
                        _actualizar_celdas_calculadas_fila(turno, rk)
                    try:
                        page.update(tabla_host)
                    except Exception:
                        pass
                    notify(f"✅ {msg} (Actualizado directo sin reconstruir tabla)", "#065F46")
                else:
                    solo_con_stock[0] = True
                    _construir_tabla_turno()
                    try:
                        page.update(tabla_host)
                    except Exception:
                        pass
                    notify(f"✅ {msg} (Catálogo de marcas actualizado)", "#065F46")
            else:
                notify(f"❌ {msg}", "#991B1B")
                try:
                    page.update()
                except Exception:
                    pass

        if seleccionar_archivo_async:
            seleccionar_archivo_async(
                "Seleccionar Excel MIM (StockSummary)",
                [("Excel files", "*.xlsx *.xls"), ("Todos", "*.*")],
                _procesar_ruta
            )
        else:
            r = _seleccionar_excel_nativo("Seleccionar Excel MIM (StockSummary)")
            _procesar_ruta(r)

    def pasar_ajuste_vespertino_click(e):
        vespertino_manual_keys.clear()
        cant = bcs.aplicar_ajuste_matutino_a_vespertino(estado_ref["data"], reset_movimientos=True)
        turno_activo[0] = "vespertino"
        _actualizar_botones_turno()
        _construir_tabla_turno()
        threading.Thread(
            target=bcs.guardar_bitacora_dia,
            args=(tienda_key, fecha_actual[0].strftime("%Y-%m-%d"), estado_ref["data"]),
            daemon=True,
        ).start()
        lbl_estado_guardado.value = "💾 Guardado automáticamente"
        lbl_estado_guardado.color = "#7CFC00"
        notify(f"➡️ Ajuste (E, ST, SV) re-aplicado a {cant} marcas en Turno Vespertino. Puedes editar cualquier número.", "#1D4ED8")
        try:
            page.update()
        except Exception:
            pass

    def guardar_click(e):
        lbl_estado_guardado.value = "⏳ Guardando..."
        lbl_estado_guardado.color = "#FBBF24"
        try:
            lbl_estado_guardado.update()
        except Exception:
            pass

        def _bg_save():
            ok = bcs.guardar_bitacora_dia(tienda_key, fecha_actual[0].strftime("%Y-%m-%d"), estado_ref["data"])
            if ok:
                lbl_estado_guardado.value = "💾 Guardado correctamente"
                lbl_estado_guardado.color = "#7CFC00"
                notify("✅ Bitácora guardada y Exhibición (EXH) actualizada para el siguiente día.", "#065F46")
            else:
                lbl_estado_guardado.value = "⚠️ Error al guardar"
                lbl_estado_guardado.color = "#F87171"
                notify("⚠️ No se pudo guardar en base de datos.", "#991B1B")
            try:
                page.update()
            except Exception:
                pass

        threading.Thread(target=_bg_save, daemon=True).start()

    def _lanzar_descarga_url(url, local_path=None, inline=0):
        async def _launch():
            target_win = "_blank" if inline == 1 else "_self"
            try:
                res = page.launch_url(url, web_popup_window_name=target_win)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                try:
                    res2 = page.launch_url(url)
                    if asyncio.iscoroutine(res2):
                        await res2
                except Exception:
                    pass
        try:
            page.run_task(_launch)
        except Exception:
            try:
                if local_path and os.path.exists(local_path) and hasattr(os, "startfile"):
                    os.startfile(local_path)
            except Exception:
                pass

    def _generar_y_abrir_pdf(inline=0):
        try:
            bcs.aplicar_ajuste_matutino_a_vespertino(estado_ref["data"], skip_keys=vespertino_manual_keys)
            pdf_path, fname = bcs.generar_pdf_bitacora(estado_ref["data"])
            display_name = f"Bitacora_Conteo_{tienda_key}_{fecha_actual[0].strftime('%Y-%m-%d')}.pdf"
            url = f"/dl?file={urllib.parse.quote(fname)}&original={urllib.parse.quote(display_name)}&inline={inline}"
            _lanzar_descarga_url(url, local_path=pdf_path, inline=inline)

            snapshot_estado = dict(estado_ref["data"])
            fecha_s = fecha_actual[0].strftime("%Y-%m-%d")
            def _bg_persist():
                try:
                    dl_dir = os.path.expanduser("~/Downloads")
                    if os.path.isdir(dl_dir) and inline == 0:
                        import shutil
                        shutil.copy2(pdf_path, os.path.join(dl_dir, display_name))
                except Exception:
                    pass
                try:
                    bcs.guardar_bitacora_dia(tienda_key, fecha_s, snapshot_estado)
                except Exception:
                    pass
            threading.Thread(target=_bg_persist, daemon=True).start()

            notify(f"📄 {'Abriendo' if inline == 1 else 'Descargando'} {display_name}", "#065F46")
        except Exception as ex_pdf:
            notify(f"❌ Error generando PDF: {ex_pdf}", "#991B1B")

    def abrir_descarga_semanal(e):
        q_starts = bcs.obtener_config_q(tienda_key, fecha_actual[0].year)
        ini_dom, fin_sab, info_q = bcs.obtener_rango_semana_dom_sab(fecha_actual[0], q_starts)
        rango_ref = {"ini": ini_dom, "fin": fin_sab, "q": info_q["q"], "sem": info_q["semana"]}

        lbl_rango_info = ft.Text("", size=12, color="#7CFC00", weight="bold")
        btn_desde = ft.ElevatedButton("", bgcolor="#1E293B", color="#00FFFF")
        btn_hasta = ft.ElevatedButton("", bgcolor="#1E293B", color="#00FFFF")

        def _opts_semanas(qn):
            sems = bcs.listar_semanas_de_q(fecha_actual[0].year, qn, q_starts)
            return [
                ft.dropdown.Option(str(sn), f"Semana {sn} ({d1.strftime('%d/%m')}–{d2.strftime('%d/%m')})")
                for sn, d1, d2 in sems
            ]

        dd_q = ft.Dropdown(
            label="Trimestre",
            width=105,
            value=rango_ref["q"],
            options=[ft.dropdown.Option(q) for q in ("Q1", "Q2", "Q3", "Q4")],
            text_size=13,
            color="white",
            border_color="#475569",
        )
        init_opts = _opts_semanas(rango_ref["q"])
        init_vals = {o.key for o in init_opts}
        sem_val_init = str(rango_ref["sem"]) if str(rango_ref["sem"]) in init_vals else init_opts[0].key
        dd_sem = ft.Dropdown(
            label="Semana (Dom-Sáb)",
            width=235,
            value=sem_val_init,
            options=init_opts,
            text_size=13,
            color="white",
            border_color="#475569",
        )

        def _sync_labels():
            d1, d2 = rango_ref["ini"], rango_ref["fin"]
            if d2 < d1:
                d1, d2 = d2, d1
                rango_ref["ini"], rango_ref["fin"] = d1, d2
            dias_cnt = (d2 - d1).days + 1
            btn_desde.content = f"Desde: {d1.strftime('%d-%m-%Y')}"
            btn_hasta.content = f"Hasta: {d2.strftime('%d-%m-%Y')}"
            lbl_rango_info.value = f"📆 Rango Dom–Sáb: {d1.strftime('%d/%m/%Y')} al {d2.strftime('%d/%m/%Y')} ({dias_cnt} día{'s' if dias_cnt != 1 else ''})"

        def _on_q_change(ev):
            qn = dd_q.value or "Q1"
            new_opts = _opts_semanas(qn)
            dd_sem.options = new_opts
            dd_sem.value = new_opts[0].key
            sn = int(dd_sem.value)
            d1, d2, _ = bcs.obtener_rango_semana_dom_sab(fecha_actual[0], q_starts, semana_num=sn, q_name=qn)
            rango_ref["ini"], rango_ref["fin"] = d1, d2
            _sync_labels()
            try:
                page.update(dd_sem, btn_desde, btn_hasta, lbl_rango_info)
            except Exception:
                pass

        def _on_sem_change(ev):
            qn = dd_q.value or "Q1"
            sn = int(dd_sem.value or "1")
            d1, d2, _ = bcs.obtener_rango_semana_dom_sab(fecha_actual[0], q_starts, semana_num=sn, q_name=qn)
            rango_ref["ini"], rango_ref["fin"] = d1, d2
            _sync_labels()
            try:
                page.update(btn_desde, btn_hasta, lbl_rango_info)
            except Exception:
                pass

        dd_q.on_change = _on_q_change
        dd_sem.on_change = _on_sem_change

        def _pick_desde(ev):
            def _set_d(picked):
                rango_ref["ini"] = picked
                _sync_labels()
                abrir_descarga_semanal_reopen()
            page.pop_dialog()
            _abrir_calendario_es("📅 Fecha inicial (Desde)", rango_ref["ini"], _set_d)

        def _pick_hasta(ev):
            def _set_h(picked):
                rango_ref["fin"] = picked
                _sync_labels()
                abrir_descarga_semanal_reopen()
            page.pop_dialog()
            _abrir_calendario_es("📅 Fecha final (Hasta)", rango_ref["fin"], _set_h)

        btn_desde.on_click = _pick_desde
        btn_hasta.on_click = _pick_hasta
        _sync_labels()

        def _ejecutar_descarga_excel(ev):
            d1, d2 = rango_ref["ini"], rango_ref["fin"]
            if (d2 - d1).days > 31:
                notify("⚠️ El rango máximo por Excel es 31 días.", "#B45309")
                return
            try:
                page.pop_dialog()
            except Exception:
                pass
            notify("⏳ Generando Excel semanal...", "#1D4ED8")
            try:
                xlsx_path, fname = bcs.generar_excel_semanal_bitacora(tienda_key, d1, d2)
                disp = f"Bitacora_Semanal_{tienda_key}_{d1.strftime('%Y-%m-%d')}_al_{d2.strftime('%Y-%m-%d')}.xlsx"
                url = f"/dl?file={urllib.parse.quote(fname)}&original={urllib.parse.quote(disp)}&inline=0"
                _lanzar_descarga_url(url, local_path=xlsx_path, inline=0)
                try:
                    dl_dir = os.path.expanduser("~/Downloads")
                    if os.path.isdir(dl_dir):
                        import shutil
                        shutil.copy2(xlsx_path, os.path.join(dl_dir, disp))
                except Exception:
                    pass
                notify(f"📊 Excel descargado: {disp}", "#065F46")
            except Exception as ex_xl:
                notify(f"❌ Error generando Excel: {ex_xl}", "#991B1B")

        dlg_sem = ft.AlertDialog(
            title=ft.Text("📊 Descargar Bitácora Semanal (Excel)", color="#00FFFF", weight="bold", size=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Elige por Semana del Q (Domingo a Sábado) o ajusta tus fechas:", size=12, color="#CBD5E1"),
                    ft.Row([dd_q, dd_sem], spacing=10),
                    ft.Row([btn_desde, btn_hasta], spacing=10, wrap=True),
                    lbl_rango_info,
                ], spacing=12, tight=True),
                width=_dlg_width(420),
            ),
            actions=[
                ft.ElevatedButton("⬇️ Descargar Excel", on_click=_ejecutar_descarga_excel, bgcolor="#059669", color="white"),
                ft.TextButton("Cancelar", on_click=lambda ev: page.pop_dialog()),
            ],
            bgcolor="#0F172A",
        )

        def abrir_descarga_semanal_reopen():
            _sync_labels()
            page.show_dialog(dlg_sem)

        page.show_dialog(dlg_sem)

    btn_tab_mat = ft.ElevatedButton("☀️ Turno Matutino", bgcolor="#1E3A8A", color="white")
    btn_tab_ves = ft.ElevatedButton("🌙 Turno Vespertino", bgcolor="#1E293B", color="white")

    def _actualizar_botones_turno():
        if turno_activo[0] == "matutino":
            btn_tab_mat.bgcolor = "#1E3A8A"
            btn_tab_ves.bgcolor = "#1E293B"
        else:
            btn_tab_mat.bgcolor = "#1E293B"
            btn_tab_ves.bgcolor = "#581C87"

    def switch_turno(t_name):
        if t_name == "vespertino":
            bcs.aplicar_ajuste_matutino_a_vespertino(estado_ref["data"], skip_keys=vespertino_manual_keys)
        turno_activo[0] = t_name
        _actualizar_botones_turno()
        _construir_tabla_turno()
        try:
            page.update()
        except Exception:
            pass

    btn_tab_mat.on_click = lambda e: switch_turno("matutino")
    btn_tab_ves.on_click = lambda e: switch_turno("vespertino")

    bcs.aplicar_ajuste_matutino_a_vespertino(estado_ref["data"], skip_keys=vespertino_manual_keys)
    _auto_activar_filtro_si_hay_marcas()
    _actualizar_badges_fecha_q()
    _construir_tabla_turno()

    barra_fecha_q = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color="#00FFFF", on_click=lambda e: _cargar_fecha(fecha_actual[0] - timedelta(days=1)), tooltip="Día anterior"),
                lbl_fecha,
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color="#00FFFF", on_click=lambda e: _cargar_fecha(fecha_actual[0] + timedelta(days=1)), tooltip="Día siguiente"),
                ft.ElevatedButton("📅 Calendario", on_click=abrir_calendario, bgcolor="#1E293B", color="#00FFFF", height=34),
                ft.ElevatedButton("🗂️ Carpetas Q1-Q4", on_click=abrir_carpetas_q, bgcolor="#1E293B", color="#D8B4FE", height=34),
                ft.ElevatedButton("⚙️ Inicio Q1", on_click=abrir_config_q, bgcolor="#1E293B", color="#FBBF24", height=34, visible=False),
            ], wrap=True, spacing=6),
            ft.Column([lbl_carpeta_q, lbl_estado_guardado], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        padding=10,
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#334155"),
        border_radius=10,
    )

    MIM_PORTAL_URL = "https://mim.luxotticaretail.com/sap/bc/ui5_ui5/ui2/ushell/shells/abap/FioriLaunchpad.html?sap-client=500&sap-language=ES#Shell-home"

    es_movil_ipad = (getattr(page, "width", None) or 1200) < 1050

    btn_mim = ft.ElevatedButton("🌐 MIM", on_click=lambda e: _lanzar_descarga_url(MIM_PORTAL_URL, inline=1), bgcolor="#0369A1", color="white", tooltip="Abrir portal MIM para descargar inventario")
    btn_subir_mim = ft.ElevatedButton("📥 Subir Excel" if es_movil_ipad else "📥 Subir Excel MIM", on_click=subir_mim_click, bgcolor="#0284C7", color="white")
    btn_ajuste_ves = ft.ElevatedButton("➡️ Aplicar Ajuste a Vespertino", on_click=pasar_ajuste_vespertino_click, bgcolor="#7C3AED", color="white")
    btn_guardar = ft.ElevatedButton("💾 Guardar", on_click=guardar_click, bgcolor="#059669", color="white")
    btn_dl_pdf = ft.ElevatedButton("📄 PDF" if es_movil_ipad else "📄 Descargar PDF", on_click=lambda e: _generar_y_abrir_pdf(0), bgcolor="#DC2626", color="white")
    btn_ver_pdf = ft.ElevatedButton("🖨️ Ver / Imprimir", on_click=lambda e: _generar_y_abrir_pdf(1), bgcolor="#334155", color="white")
    btn_excel_sem = ft.ElevatedButton("📊 Descargar Semana (Excel)", on_click=abrir_descarga_semanal, bgcolor="#0D9488", color="white")

    if es_movil_ipad:
        for _b in (btn_subir_mim, btn_guardar, btn_dl_pdf):
            _b.height = 34
            _b.style = ft.ButtonStyle(padding=ft.padding.Padding(10, 0, 10, 0))

        menu_movil_panel = ft.Container(
            visible=False,
            bgcolor="#0F172A",
            border=ft.Border.all(1, "#334155"),
            border_radius=8,
            padding=8,
        )

        def _toggle_menu_movil(e):
            menu_movil_panel.visible = not menu_movil_panel.visible
            try:
                menu_movil_panel.update()
            except Exception:
                pass

        def _wrap_cierra_menu(fn):
            def _wrapped(ev):
                menu_movil_panel.visible = False
                try:
                    menu_movil_panel.update()
                except Exception:
                    pass
                if fn:
                    fn(ev)
            return _wrapped

        for _mb in (btn_tab_mat, btn_tab_ves, btn_mim, btn_ajuste_ves, btn_ver_pdf, btn_excel_sem):
            _mb.on_click = _wrap_cierra_menu(_mb.on_click)

        menu_movil_panel.content = ft.Row([
            btn_tab_mat,
            btn_tab_ves,
            btn_mim,
            btn_ajuste_ves,
            btn_ver_pdf,
            btn_excel_sem,
        ], wrap=True, spacing=6)

        btn_menu_hamb = ft.ElevatedButton(
            "☰",
            on_click=_toggle_menu_movil,
            bgcolor="#1E293B",
            color="#00FFFF",
            height=34,
            width=44,
            tooltip="Más opciones de Conteo",
            style=ft.ButtonStyle(padding=ft.padding.Padding(0, 0, 0, 0)),
        )

        barra_acciones = ft.Column([
            ft.Row([btn_menu_hamb, btn_subir_mim, btn_guardar, btn_dl_pdf], wrap=True, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            menu_movil_panel,
        ], spacing=6)
    else:
        barra_acciones = ft.Row([
            btn_tab_mat,
            btn_tab_ves,
            btn_mim,
            btn_subir_mim,
            btn_ajuste_ves,
            btn_guardar,
            btn_dl_pdf,
            btn_ver_pdf,
            btn_excel_sem,
        ], wrap=True, spacing=8)

    cabecera_fisica = ft.Container(
        content=ft.Row([
            tf_cch1, tf_cch2, tf_cch3, tf_rec_m, tf_ent_m, tf_rec_v, tf_ent_v
        ], wrap=True, spacing=5),
        padding=6,
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#1E293B"),
        border_radius=8,
    )

    def _on_buscar_marca(e):
        filtro_texto[0] = e.control.value or ""
        _construir_tabla_turno()
        try:
            tabla_host.update()
        except Exception:
            pass

    tf_buscar_marca = ft.TextField(
        hint_text="🔍 Buscar marca...",
        width=185,
        height=34,
        dense=True,
        text_size=12,
        color="white",
        bgcolor="#0F172A",
        border_color="#475569",
        focused_border_color="#00FFFF",
        content_padding=ft.padding.Padding(8, 4, 8, 4),
        on_change=_on_buscar_marca,
    )

    btn_modo_tactil = ft.ElevatedButton(
        "📱 Táctil: ON" if modo_tactil[0] else "📱 Táctil: OFF",
        on_click=None,
        bgcolor="#0D9488" if modo_tactil[0] else "#1E293B",
        color="white",
        height=32,
        tooltip="Abre teclado numérico al tocar cada celda en iPad / Celular",
    )

    def _toggle_modo_tactil(e):
        modo_tactil[0] = not modo_tactil[0]
        btn_modo_tactil.content = "📱 Táctil: ON" if modo_tactil[0] else "📱 Táctil: OFF"
        btn_modo_tactil.bgcolor = "#0D9488" if modo_tactil[0] else "#1E293B"
        try:
            page.update(btn_modo_tactil)
        except Exception:
            pass

    btn_modo_tactil.on_click = _toggle_modo_tactil

    barra_editor_rapido = ft.Container(
        content=ft.Row([
            lbl_celda_activa,
            tf_editor_rapido,
            tf_buscar_marca,
        ], wrap=True, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.Padding(10, 6, 10, 6),
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#334155"),
        border_radius=8,
    )

    leyenda_colores = ft.Container(
        content=ft.Row([
            ft.Text("Colores:", size=11, weight="bold", color="#94A3B8"),
            ft.Text("● Negro: EXH, TOT, EN", size=11, color="#E2E8F0"),
            ft.Text("● Azul: BOD, TR, MIM", size=11, color="#60A5FA"),
            ft.Text("● Rojo: GT, DAÑ, S/E, E, ST, SV y errores", size=11, color="#F87171"),
            ft.Text("✓ Cuadra / Rojo: faltan / Verde: sobran", size=11, color="#4ADE80"),
            ft.Text("⌨️ Clic en celda + números directo, ↑ ↓ ← →, Enter, Tab (F2 para editar texto)", size=11, color="#00FFFF"),
        ], wrap=True, spacing=12),
        padding=ft.padding.Padding(8, 4, 8, 4),
        bgcolor="#0B1120",
        border_radius=6,
    )

    outer_scroll_col = ft.Column(
        controls=[
            ft.Row([
                ft.Text("📊 BITÁCORA DE CONTEO DE TIENDA", size=20, weight="bold", color="#00FFFF"),
                ft.Text(f"({store_name} - {tienda_key})", size=13, color="#94A3B8"),
            ], wrap=True, spacing=10),
            barra_fecha_q,
            barra_acciones,
            cabecera_fisica,
            barra_editor_rapido,
            kb_listener,
        ],
        spacing=10,
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
    )

    return ft.Container(
        content=outer_scroll_col,
        expand=True,
        padding=ft.padding.Padding(6, 6, 16, 24),
    )
