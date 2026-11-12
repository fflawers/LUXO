import inspect
import json
import threading
import uuid
from urllib.parse import quote

import flet as ft
import cotizador_service as cs


TAG_OPTIONS = [
    ("REGULAR", "Regular", "#64748B", "#1E293B"),
    ("AZUL_20", "🔵 Azul 20%", "#38BDF8", "#0C2D48"),
    ("VERDE_30", "🟢 Verde 30%", "#10B981", "#063628"),
    ("ROJO_30_50", "🔴 Roja 30→50%", "#F43F5E", "#3F0D1D"),
    ("OUTLET_60", "🟣 Outlet 60%", "#C084FC", "#2E1065"),
    ("OUTLET_70", "🟡 Outlet 70%", "#FACC15", "#3B2804"),
]
TAG_META = {k: (lbl, fg, bg) for k, lbl, fg, bg in TAG_OPTIONS}


def build_cotizador_view(
    page: ft.Page,
    store_code: str = "A540",
    store_name: str = "Tienda",
    user_info: dict = None,
    user_role: str = "tienda",
    seleccionar_archivo_async=None,
    mostrar_snack_fn=None,
):
    """
    Cotizador / Calculadora Inteligente POS LUXO (hasta 200+ piezas):
    - Soporta reglas Tienda Línea (Parejas Desc, Extremos, Manual, Azul/Verde/Roja + comparativa) y Outlet (30/40/50 + 60/70).
    - Panel Admin Promo Especial (ej. Buen Fin 20% con exclusiones) + Carga Excel Precios MIM.
    - Lectura limpia de descuentos_semanales + exportación Excel.
    - Argumento de cierre persuasivo con MSI (3/6/9/12) y costo diario equivalente.
    - Cotizaciones guardadas en MySQL con Editar/Reabrir, Borrar y PDF vectorial multipágina.
    """
    user_info = user_info or {}
    es_admin = str(user_role or "").lower() == "admin"
    store_code = str(store_code or "A540").strip().upper()
    store_name = str(store_name or f"Tienda {store_code}").strip()
    is_mobile = bool(getattr(page, "width", 1200) and getattr(page, "width", 1200) < 920)

    # ---------------- ESTADO DEL COTIZADOR ----------------
    state = {
        "active_tab": "cotizador",  # "cotizador" | "guardadas"
        "items": [],  # lista de dicts {uid, upc, marca, tipo_producto, descripcion, precio, tag, cantidad, manual_group}
        "tipo_tienda": cs.obtener_modo_tienda(store_code, store_name),
        "modo_agrupacion": "PAREJAS_DESC",  # "PAREJAS_DESC" | "EXTREMOS" | "MANUAL"
        "preferencia_mixta": "AUTO",  # "AUTO" | "ROJA_50" | "PAR_40"
        "promo_especial": cs.obtener_promo_especial(),
        "editing_id": None,
        "editing_folio": None,
        "last_calc": cs.calcular_cotizacion([]),
        "catalogo_count": cs.obtener_conteo_catalogo(),
        "saved_list": [],
    }

    def _snack(msg: str, color: str = "#00FFAA"):
        if callable(mostrar_snack_fn):
            try:
                mostrar_snack_fn(msg, color)
                return
            except Exception:
                pass
        try:
            sb = ft.SnackBar(
                content=ft.Text(str(msg), color="#0F172A", weight="bold"),
                bgcolor=color,
                duration=3500,
            )
            page.overlay.append(sb)
            sb.open = True
            page.update()
        except Exception as ex:
            print("Snack error:", ex)

    def _show_dlg(dlg: ft.AlertDialog):
        try:
            page.show_dialog(dlg)
        except Exception:
            try:
                page.dialog = dlg
                dlg.open = True
                page.update()
            except Exception as ex:
                print("Dialog open error:", ex)

    def _close_dlg(dlg: ft.AlertDialog = None):
        try:
            page.pop_dialog()
        except Exception:
            try:
                if dlg:
                    dlg.open = False
                page.update()
            except Exception:
                pass

    def _lanzar_dl(fname: str, inline: bool = False):
        url_dl = f"/dl?file={quote(fname)}&original={quote(fname)}&inline={'1' if inline else '0'}"
        target = "_blank" if inline else "_self"

        async def _go():
            try:
                res = page.launch_url(url_dl, web_popup_window_name=target)
                if inspect.isawaitable(res):
                    await res
            except TypeError:
                try:
                    res2 = page.launch_url(url_dl)
                    if inspect.isawaitable(res2):
                        await res2
                except Exception as ex2:
                    print("Launch URL fallback error:", ex2)
            except Exception as ex:
                print("Launch URL error:", ex)

        try:
            page.run_task(_go)
        except Exception:
            try:
                page.launch_url(url_dl)
            except Exception:
                pass

    # ---------------- CONTROLES PRINCIPALES ----------------
    txt_catalogo_badge = ft.Text(
        f"📦 {state['catalogo_count']:,} UPCs con precio",
        size=11,
        color="#38BDF8",
        weight="bold",
    )

    banner_promo_holder = ft.Container(visible=False)
    banner_editing_holder = ft.Container(visible=False)

    tf_cliente = ft.TextField(
        label="Nombre del cliente (opcional, sale en PDF)",
        hint_text="Cliente Mostrador",
        height=44,
        text_size=13,
        bgcolor="#0F172A",
        border_color="#334155",
        focused_border_color="#00FFFF",
        color="white",
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=6),
    )

    tf_scanner = ft.TextField(
        label="Escanear UPC / Buscar modelo o marca (Ej. 8056597... o 2*8056597...)",
        hint_text="Escanea código de barras y presiona Enter, o escribe marca/modelo...",
        autofocus=True,
        height=48,
        text_size=13,
        bgcolor="#0B1120",
        border_color="#00FFFF",
        focused_border_color="#00FFAA",
        color="white",
        prefix_icon=ft.Icons.QR_CODE_SCANNER,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
    )

    search_results_col = ft.Column(spacing=4, visible=False)
    search_results_box = ft.Container(
        content=search_results_col,
        visible=False,
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#334155"),
        border_radius=10,
        padding=8,
    )

    progress_upload_bar = ft.ProgressBar(value=0, color="#00FFAA", bgcolor="#1E293B", visible=False)
    progress_upload_txt = ft.Text("", size=11, color="#38BDF8", visible=False)

    # Selectores de reglas de tienda y agrupación
    btn_mode_linea = ft.Container()
    btn_mode_outlet = ft.Container()

    linea_options_row = ft.Container()
    dd_agrupacion = ft.Dropdown(
        label="Agrupación Línea (2+ pzs regulares)",
        value=state["modo_agrupacion"],
        width=260,
        text_size=12,
        bgcolor="#0F172A",
        border_color="#334155",
        color="white",
        options=[
            ft.dropdown.Option("PAREJAS_DESC", "Modo 2: Pares Mayor → Menor"),
            ft.dropdown.Option("EXTREMOS", "Modo 1: Cara + Barata (Extremos)"),
            ft.dropdown.Option("MANUAL", "Modo 3: Agrupación Manual (Par #)"),
        ],
    )

    dd_mixta = ft.Dropdown(
        label="Estrategia si hay 🔴 Roja (30→50%)",
        value=state["preferencia_mixta"],
        width=250,
        text_size=12,
        bgcolor="#0F172A",
        border_color="#334155",
        color="white",
        options=[
            ft.dropdown.Option("AUTO", "⚡ Automático (Mayor ahorro)"),
            ft.dropdown.Option("ROJA_50", "🔴 Priorizar Roja al 50%"),
            ft.dropdown.Option("PAR_40", "🏷️ 2da al 40% en menor valor"),
        ],
    )

    cart_items_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
    cart_count_txt = ft.Text("0 / 200+ piezas", size=12, color="#94A3B8", weight="bold")
    summary_panel_col = ft.Column(spacing=10)

    saved_search_tf = ft.TextField(
        label="Buscar en cotizaciones guardadas (folio, cliente o tienda)",
        height=42,
        text_size=12,
        bgcolor="#0F172A",
        border_color="#334155",
        color="white",
        prefix_icon=ft.Icons.SEARCH,
    )
    saved_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

    # ---------------- LÓGICA DE RENDER Y RECÁLCULO ----------------
    def _refresh_promo_banner():
        p = state["promo_especial"] or {}
        if p.get("activa") and float(p.get("descuento_pct") or 0) > 0:
            aplica_aqui = cs._promo_especial_aplica_tienda(p, state["tipo_tienda"], store_code, store_name)
            excl = p.get("exclusiones") or "Sin exclusiones"
            msg_alc = f"Aplica aquí ({p.get('alcance', 'TODAS')})" if aplica_aqui else f"No aplica en este modo/tienda ({p.get('alcance')})"
            banner_promo_holder.visible = True
            banner_promo_holder.content = ft.Container(
                bgcolor="#2E1065" if aplica_aqui else "#1E293B",
                border=ft.Border.all(1, "#C084FC" if aplica_aqui else "#475569"),
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                content=ft.Row(
                    [
                        ft.Text("🔥", size=18),
                        ft.Column(
                            [
                                ft.Text(
                                    f"PROMO ESPECIAL ACTIVA: {p.get('nombre', 'Campaña')} — {int(float(p.get('descuento_pct') or 0))}% OFF ({msg_alc})",
                                    size=12,
                                    weight="bold",
                                    color="#FDE047" if aplica_aqui else "#CBD5E1",
                                ),
                                ft.Text(
                                    f"Excluye: {excl}  •  Nunca aplica descuento sobre descuento (siempre toma el mayor beneficio).",
                                    size=11,
                                    color="#E2E8F0",
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        else:
            banner_promo_holder.visible = False
            banner_promo_holder.content = None

    def _refresh_editing_banner():
        if state["editing_id"]:
            banner_editing_holder.visible = True
            banner_editing_holder.content = ft.Container(
                bgcolor="#064E3B",
                border=ft.Border.all(1, "#10B981"),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                content=ft.Row(
                    [
                        ft.Text(
                            f"✏️ Editando cotización guardada #{state['editing_id']} ({state['editing_folio'] or ''}) — Al guardar se actualizará este folio.",
                            size=12,
                            color="#A7F3D0",
                            weight="bold",
                            expand=True,
                        ),
                        ft.TextButton(
                            "🆕 Nueva Cotización",
                            style=ft.ButtonStyle(color="#FDE047"),
                            on_click=lambda e: _nueva_cotizacion(),
                        ),
                    ]
                ),
            )
        else:
            banner_editing_holder.visible = False
            banner_editing_holder.content = None

    def _style_mode_buttons():
        is_lin = state["tipo_tienda"] == "LINEA"
        btn_mode_linea.bgcolor = "#0284C7" if is_lin else "#1E293B"
        btn_mode_linea.border = ft.Border.all(1.5, "#38BDF8" if is_lin else "#334155")
        btn_mode_outlet.bgcolor = "#7C3AED" if not is_lin else "#1E293B"
        btn_mode_outlet.border = ft.Border.all(1.5, "#C084FC" if not is_lin else "#334155")
        linea_options_row.visible = is_lin

    def _recalcular_y_render(update_ui: bool = True):
        calc = cs.calcular_cotizacion(
            state["items"],
            tipo_tienda=state["tipo_tienda"],
            modo_agrupacion=state["modo_agrupacion"],
            preferencia_mixta=state["preferencia_mixta"],
            promo_especial=state["promo_especial"],
            codigo_tienda=store_code,
            nombre_tienda=store_name,
        )
        state["last_calc"] = calc
        _refresh_promo_banner()
        _refresh_editing_banner()
        _style_mode_buttons()
        _render_cart_items(calc)
        _render_summary(calc)
        if update_ui:
            try:
                page.update()
            except Exception:
                pass

    def _render_cart_items(calc: dict):
        desglose = calc.get("desglose") or []
        total_pz = calc.get("total_piezas", 0)
        cart_count_txt.value = f"{total_pz} / 200+ piezas"
        cart_count_txt.color = "#FACC15" if total_pz > 200 else ("#00FFAA" if total_pz > 0 else "#94A3B8")

        cart_items_col.controls.clear()
        if not state["items"]:
            cart_items_col.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    bgcolor="#0F172A",
                    border=ft.Border.all(1, "#1E293B"),
                    border_radius=12,
                    content=ft.Column(
                        [
                            ft.Text("🕶️ Escanea un código UPC o busca un modelo arriba", size=15, weight="bold", color="#CBD5E1"),
                            ft.Text(
                                "Soporta hasta 200+ piezas. Puedes escribir '2*UPC' para agregar varias piezas rápido o usar '+ Pieza Manual'.",
                                size=12,
                                color="#64748B",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                )
            )
            return

        # Mapear asignaciones por uid desde el desglose calculado
        desg_by_uid = {}
        for d in desglose:
            base_uid = str(d.get("uid", "")).split("_")[0]
            desg_by_uid.setdefault(base_uid, []).append(d)

        is_manual_mode = state["tipo_tienda"] == "LINEA" and state["modo_agrupacion"] == "MANUAL"

        for idx, item in enumerate(state["items"], start=1):
            uid = item["uid"]
            unit_rows = desg_by_uid.get(uid, [])
            cant = int(item.get("cantidad") or 1)
            p_orig_unit = float(item.get("precio") or 0.0)
            tot_orig_item = round(p_orig_unit * cant, 2)
            tot_final_item = round(sum(r.get("precio_final", p_orig_unit) for r in unit_rows), 2) if unit_rows else tot_orig_item
            motivos = list(dict.fromkeys(r.get("motivo", "") for r in unit_rows if r.get("motivo")))
            pcts = list(dict.fromkeys(int(round(r.get("descuento_pct", 0))) for r in unit_rows))
            pct_str = "/".join(f"{p}%" for p in pcts) if pcts else "0%"

            tag_val = item.get("tag", "REGULAR")
            tag_lbl, tag_fg, tag_bg = TAG_META.get(tag_val, TAG_META["REGULAR"])

            def _make_tag_change(target_uid):
                def _on_chg(e):
                    for it in state["items"]:
                        if it["uid"] == target_uid:
                            it["tag"] = e.control.value
                            break
                    _recalcular_y_render()
                return _on_chg

            def _make_qty_delta(target_uid, delta):
                def _click(e):
                    for pos, it in enumerate(state["items"]):
                        if it["uid"] == target_uid:
                            nc = int(it.get("cantidad") or 1) + delta
                            if nc <= 0:
                                state["items"].pop(pos)
                            else:
                                it["cantidad"] = nc
                            break
                    _recalcular_y_render()
                return _click

            def _make_remove(target_uid):
                def _click(e):
                    state["items"] = [it for it in state["items"] if it["uid"] != target_uid]
                    _recalcular_y_render()
                return _click

            def _make_manual_group_change(target_uid):
                def _chg(e):
                    for it in state["items"]:
                        if it["uid"] == target_uid:
                            it["manual_group"] = str(e.control.value or "").strip()
                            break
                    _recalcular_y_render()
                return _chg

            dd_tag = ft.Dropdown(
                value=tag_val,
                width=124,
                dense=True,
                text_size=11,
                bgcolor=tag_bg,
                border_color=tag_fg,
                color="white",
                content_padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                options=[ft.dropdown.Option(k, lbl) for k, lbl, _, _ in TAG_OPTIONS],
                on_select=_make_tag_change(uid),
            )

            manual_tf = (
                ft.TextField(
                    value=str(item.get("manual_group") or ""),
                    hint_text="Par #",
                    width=56,
                    height=32,
                    text_size=11,
                    bgcolor="#0B1120",
                    border_color="#38BDF8",
                    color="white",
                    content_padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    on_change=_make_manual_group_change(uid),
                )
                if is_manual_mode
                else None
            )

            qty_box = ft.Container(
                width=86,
                height=32,
                bgcolor="#0B1120",
                border=ft.Border.all(1, "#334155"),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=2, vertical=0),
                alignment=ft.Alignment.CENTER,
                content=ft.Row(
                    [
                        ft.IconButton(ft.Icons.REMOVE, icon_size=14, width=26, height=26, padding=0, icon_color="#CBD5E1", on_click=_make_qty_delta(uid, -1)),
                        ft.Text(f"{cant}", size=12, weight="bold", color="white"),
                        ft.IconButton(ft.Icons.ADD, icon_size=14, width=26, height=26, padding=0, icon_color="#00FFAA", on_click=_make_qty_delta(uid, 1)),
                    ],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            btn_del = ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_size=16,
                width=28,
                height=28,
                padding=0,
                icon_color="#F87171",
                tooltip="Quitar pieza",
                on_click=_make_remove(uid),
            )

            has_desc = any(p > 0 for p in pcts)
            precio_col = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                f"${tot_orig_item:,.2f}",
                                size=10,
                                color="#94A3B8",
                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                            ) if has_desc else ft.Container(),
                            ft.Text(f"${tot_final_item:,.2f}", size=13, weight="bold", color="#00FFAA" if has_desc else "white"),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Container(
                        bgcolor="#064E3B" if has_desc else "#1E293B",
                        border_radius=5,
                        padding=ft.Padding.symmetric(horizontal=5, vertical=1),
                        content=ft.Text(
                            f"-{pct_str}" if has_desc else "Regular",
                            size=9.5,
                            weight="bold",
                            color="#34D399" if has_desc else "#94A3B8",
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.END,
                spacing=2,
            )

            num_badge = ft.Container(
                width=22,
                height=22,
                border_radius=11,
                bgcolor="#1E293B",
                alignment=ft.Alignment.CENTER,
                content=ft.Text(str(idx), size=10, weight="bold", color="#38BDF8"),
            )
            info_col = ft.Column(
                [
                    ft.Text(
                        f"{item.get('marca') or 'SUNGLASS HUT'} • {item.get('descripcion') or item.get('upc')}",
                        size=12,
                        weight="bold",
                        color="white",
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"UPC: {item.get('upc') or 'MANUAL'}  |  {' • '.join(motivos) if motivos else 'Precio regular'}",
                        size=10,
                        color="#94A3B8",
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=1,
                expand=True,
            )

            if is_mobile:
                ctrl_row_items = [dd_tag]
                if manual_tf:
                    ctrl_row_items.append(manual_tf)
                ctrl_row_items.extend([qty_box, btn_del])
                row_content = ft.Column(
                    [
                        ft.Row([num_badge, info_col, precio_col], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row(ctrl_row_items, spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ],
                    spacing=5,
                )
            else:
                desktop_row_items = [num_badge, info_col, dd_tag]
                if manual_tf:
                    desktop_row_items.append(manual_tf)
                desktop_row_items.extend([qty_box, precio_col, btn_del])
                row_content = ft.Row(
                    desktop_row_items,
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )

            row_card = ft.Container(
                bgcolor="#0F172A",
                border=ft.Border.all(1, "#1E293B"),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                content=row_content,
            )
            cart_items_col.controls.append(row_card)

    def _render_summary(calc: dict):
        summary_panel_col.controls.clear()

        alertas = calc.get("alertas") or []
        for al in alertas:
            summary_panel_col.controls.append(
                ft.Container(
                    bgcolor="#451A03" if "⚠️" in al else "#0C4A6E",
                    border=ft.Border.all(1, "#F59E0B" if "⚠️" in al else "#38BDF8"),
                    border_radius=8,
                    padding=8,
                    content=ft.Text(al, size=11, color="#FEF3C7" if "⚠️" in al else "#E0F2FE", weight="bold"),
                )
            )

        comp = calc.get("comparativa")
        if comp:
            summary_panel_col.controls.append(
                ft.Container(
                    bgcolor="#1E1B4B",
                    border=ft.Border.all(1, "#818CF8"),
                    border_radius=8,
                    padding=8,
                    content=ft.Column(
                        [
                            ft.Text("⚖️ Comparativa automática (Pieza Roja vs 2da al 40%)", size=11, weight="bold", color="#C7D2FE"),
                            ft.Text(
                                f"• Con Roja al 50%: ${comp['total_roja_50']:,.2f}   |   • Con 2da al 40%: ${comp['total_par_40']:,.2f}",
                                size=11,
                                color="white",
                            ),
                        ],
                        spacing=2,
                    ),
                )
            )

        tot_orig = calc.get("total_original", 0.0)
        tot_ahorro = calc.get("total_ahorro", 0.0)
        tot_final = calc.get("total_final", 0.0)
        ahorro_pct = calc.get("ahorro_pct", 0.0)
        tot_pz = calc.get("total_piezas", 0)

        # Tarjeta Financiera Principal
        summary_panel_col.controls.append(
            ft.Container(
                bgcolor="#0B1120",
                border=ft.Border.all(1.5, "#00FFFF"),
                border_radius=12,
                padding=14,
                content=ft.Column(
                    [
                        ft.Row([ft.Text("RESUMEN DE COTIZACIÓN", size=12, weight="bold", color="#00FFFF"), ft.Text(f"{tot_pz} pzs ({state['tipo_tienda']})", size=11, color="#94A3B8")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1, color="#1E293B"),
                        ft.Row([ft.Text("Precio Total Regular:", size=13, color="#CBD5E1"), ft.Text(f"${tot_orig:,.2f}", size=13, color="#94A3B8", style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if tot_ahorro > 0 else None)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text(f"Te Estás Ahorrando ({ahorro_pct:.1f}%):", size=13, color="#34D399", weight="bold"), ft.Text(f"-${tot_ahorro:,.2f}", size=14, color="#34D399", weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1, color="#1E293B"),
                        ft.Row([ft.Text("TOTAL CON DESCUENTO:", size=15, color="white", weight="bold"), ft.Text(f"${tot_final:,.2f}", size=22, color="#FACC15", weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                    spacing=6,
                ),
            )
        )

        # Tarjeta Persuasiva de Meses Sin Intereses (MSI)
        msi = calc.get("msi") or {}
        if tot_final > 0:
            if msi.get("elegible"):
                mejor = msi["mejor_opcion"]
                pills = []
                for op in msi.get("opciones", []):
                    is_best = op["meses"] == mejor["meses"]
                    pills.append(
                        ft.Container(
                            bgcolor="#065F46" if is_best else "#1E293B",
                            border=ft.Border.all(1, "#34D399" if is_best else "#334155"),
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                            content=ft.Column(
                                [
                                    ft.Text(f"{op['meses']} MSI", size=11, weight="bold", color="#6EE7B7" if is_best else "#CBD5E1"),
                                    ft.Text(f"${op['mensualidad']:,.2f}/mes", size=11, weight="bold", color="white"),
                                ],
                                spacing=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        )
                    )
                summary_panel_col.controls.append(
                    ft.Container(
                        bgcolor="#06281E",
                        border=ft.Border.all(1, "#10B981"),
                        border_radius=12,
                        padding=12,
                        content=ft.Column(
                            [
                                ft.Text("💳 MESES SIN INTERESES (Tarjetas participantes)", size=11, weight="bold", color="#34D399"),
                                ft.Row(pills, wrap=True, spacing=6),
                                ft.Container(
                                    bgcolor="#042018",
                                    border_radius=8,
                                    padding=8,
                                    content=ft.Text(
                                        f"✨ Argumento de cierre: \"Con tu descuento pagas solo ${tot_final:,.2f} (ahorras ${tot_ahorro:,.2f}). A {mejor['meses']} MSI son ${mejor['mensualidad']:,.2f}/mes — ¡menos de ${mejor['diario']:,.2f} al día, más barato que un café!\"",
                                        size=11.5,
                                        color="#ECFDF5",
                                        weight="bold",
                                    ),
                                ),
                            ],
                            spacing=8,
                        ),
                    )
                )
            else:
                falt = msi.get("faltante_3msi", 0.0)
                summary_panel_col.controls.append(
                    ft.Container(
                        bgcolor="#1E293B",
                        border=ft.Border.all(1, "#475569"),
                        border_radius=10,
                        padding=10,
                        content=ft.Text(
                            f"💳 Compra mínima para 3 MSI es $3,000.00 (faltan ${falt:,.2f} para desbloquear Meses Sin Intereses).",
                            size=11,
                            color="#CBD5E1",
                        ),
                    )
                )

        # Botonera de Acciones
        btn_save = ft.ElevatedButton(
            "💾 Actualizar Cotización" if state["editing_id"] else "💾 Guardar Cotización",
            bgcolor="#10B981",
            color="#06281E",
            height=42,
            expand=True,
            on_click=_on_guardar_click,
        )
        btn_pdf = ft.ElevatedButton(
            "📄 Descargar PDF",
            bgcolor="#0284C7",
            color="white",
            height=42,
            expand=True,
            on_click=lambda e: _on_generar_pdf_click(inline=False),
        )
        btn_print = ft.ElevatedButton(
            "🖨️ Ver / Imprimir",
            bgcolor="#7C3AED",
            color="white",
            height=42,
            expand=True,
            on_click=lambda e: _on_generar_pdf_click(inline=True),
        )
        btn_clear = ft.OutlinedButton(
            "🧹 Limpiar",
            height=40,
            on_click=lambda e: _nueva_cotizacion(),
        )

        summary_panel_col.controls.append(
            ft.Column(
                [
                    ft.Row([btn_save, btn_clear], spacing=8),
                    ft.Row([btn_pdf, btn_print], spacing=8),
                ],
                spacing=8,
            )
        )

    # ---------------- ACCIONES DEL CARRITO Y ESCÁNER ----------------
    def _agregar_producto_al_carrito(prod: dict, cant: int = 1):
        upc = str(prod.get("upc") or "").strip()
        tag = str(prod.get("tag") or "REGULAR").upper()
        precio = float(prod.get("precio") or 0.0)
        if precio <= 0:
            _abrir_dialogo_precio_manual(upc or "", prod.get("marca") or "", prod.get("descripcion") or "", tag, cant)
            return

        # Si ya existe mismo UPC + mismo tag + no manual_group, suma cantidad para mantener orden
        merged = False
        if upc:
            for it in state["items"]:
                if it.get("upc") == upc and it.get("tag") == tag and float(it.get("precio") or 0) == precio:
                    it["cantidad"] = int(it.get("cantidad") or 1) + cant
                    merged = True
                    break
        if not merged:
            state["items"].append({
                "uid": uuid.uuid4().hex[:10],
                "upc": upc or "MANUAL",
                "marca": str(prod.get("marca") or "").strip(),
                "tipo_producto": str(prod.get("tipo_producto") or "").strip(),
                "descripcion": str(prod.get("descripcion") or "").strip(),
                "precio": precio,
                "tag": tag,
                "cantidad": cant,
                "manual_group": "",
            })
        search_results_box.visible = False
        search_results_col.visible = False
        tf_scanner.value = ""
        try:
            tf_scanner.focus()
        except Exception:
            pass
        _recalcular_y_render()
        total_pz = state["last_calc"].get("total_piezas", 0)
        if total_pz > 200:
            _snack(f"Agregado ({total_pz} piezas acumuladas en cotización)", "#38BDF8")

    def _abrir_dialogo_precio_manual(upc_init: str = "", marca_init: str = "", desc_init: str = "", tag_init: str = "REGULAR", cant_init: int = 1, guardar_en_catalogo: bool = True):
        tf_u = ft.TextField(label="UPC / Código (opcional si es libre)", value=upc_init, text_size=12, bgcolor="#0F172A", color="white")
        tf_m = ft.TextField(label="Marca (ej. RAY BAN, OAKLEY, PRADA)", value=marca_init, text_size=12, bgcolor="#0F172A", color="white")
        tf_d = ft.TextField(label="Descripción / Modelo", value=desc_init, text_size=12, bgcolor="#0F172A", color="white")
        tf_p = ft.TextField(label="Precio regular ($ MXN) *", value="", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER, text_size=13, bgcolor="#0F172A", color="white")
        tf_c = ft.TextField(label="Cantidad", value=str(cant_init), keyboard_type=ft.KeyboardType.NUMBER, text_size=12, width=100, bgcolor="#0F172A", color="white")
        dd_t = ft.Dropdown(
            label="Etiqueta / Promo",
            value=tag_init,
            width=180,
            text_size=12,
            bgcolor="#0F172A",
            color="white",
            options=[ft.dropdown.Option(k, lbl) for k, lbl, _, _ in TAG_OPTIONS],
        )
        chk_save = ft.Checkbox(label="Guardar precio en catálogo para futuros escaneos", value=bool(upc_init and guardar_en_catalogo))

        def _confirmar(e):
            p_val = cs._parse_precio(tf_p.value)
            if p_val <= 0:
                _snack("Ingresa un precio válido mayor a 0.", "#F59E0B")
                return
            try:
                cant_v = max(1, int(tf_c.value or 1))
            except Exception:
                cant_v = 1
            u_v = cs.normalizar_upc(tf_u.value)
            m_v = str(tf_m.value or "SUNGLASS HUT").strip()
            d_v = str(tf_d.value or m_v or "Armazón / Lente").strip()
            t_v = dd_t.value or "REGULAR"
            out_pct = 60 if t_v == "OUTLET_60" else (70 if t_v == "OUTLET_70" else None)

            if chk_save.value and u_v:
                cs.guardar_precio_manual_upc(u_v, m_v, d_v, p_val, outlet_pct=out_pct)
                state["catalogo_count"] = cs.obtener_conteo_catalogo()
                txt_catalogo_badge.value = f"📦 {state['catalogo_count']:,} UPCs con precio"

            _close_dlg(dlg)
            _agregar_producto_al_carrito(
                {"upc": u_v or "MANUAL", "marca": m_v, "descripcion": d_v, "precio": p_val, "tag": t_v},
                cant=cant_v,
            )

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor="#1E293B",
            title=ft.Text("💲 Capturar Pieza / Precio" if not upc_init else f"💲 Precio no registrado ({upc_init})", color="white", weight="bold", size=15),
            content=ft.Container(
                width=420,
                content=ft.Column([tf_u, tf_m, tf_d, ft.Row([tf_p, tf_c], spacing=8), dd_t, chk_save], tight=True, spacing=8),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: _close_dlg(dlg)),
                ft.ElevatedButton("Agregar a Cotización", bgcolor="#00FFAA", color="#0F172A", on_click=_confirmar),
            ],
        )
        _show_dlg(dlg)

    def _parse_qty_and_query(raw_txt: str):
        raw = str(raw_txt or "").strip()
        cant = 1
        if "*" in raw:
            parts = raw.split("*", 1)
            if parts[0].strip().isdigit():
                cant = max(1, int(parts[0].strip()))
                raw = parts[1].strip()
        return cant, raw

    def _render_search_hits(hits: list, cant: int):
        search_results_col.controls.clear()
        if not hits:
            search_results_box.visible = False
            search_results_col.visible = False
            page.update()
            return
        for prod in hits[:8]:
            t_lbl, t_fg, _ = TAG_META.get(prod.get("tag", "REGULAR"), TAG_META["REGULAR"])
            p_num = float(prod.get("precio") or 0)
            p_str = f"${p_num:,.2f}" if p_num > 0 else "Sin precio (capturar)"

            def _make_pick(item_dict):
                return lambda e: _agregar_producto_al_carrito(item_dict, cant=cant)

            search_results_col.controls.append(
                ft.Container(
                    bgcolor="#1E293B",
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    ink=True,
                    on_click=_make_pick(prod),
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(f"{prod.get('marca') or 'SGH'} — {prod.get('descripcion') or prod.get('upc')}", size=12, weight="bold", color="white", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"UPC: {prod.get('upc')}  |  {t_lbl}", size=10, color=t_fg),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Text(p_str, size=12, weight="bold", color="#00FFAA" if p_num > 0 else "#FACC15"),
                        ]
                    ),
                )
            )
        search_results_box.visible = True
        search_results_col.visible = True
        page.update()

    def _on_scanner_change(e):
        cant, q = _parse_qty_and_query(e.control.value)
        if len(q) < 2:
            search_results_box.visible = False
            search_results_col.visible = False
            page.update()
            return
        hits = cs.buscar_producto_completo(q, store_code=store_code, store_name=store_name)
        _render_search_hits(hits, cant)

    def _on_scanner_submit(e):
        cant, q = _parse_qty_and_query(tf_scanner.value)
        if not q:
            return
        hits = cs.buscar_producto_completo(q, store_code=store_code, store_name=store_name)
        if hits:
            # Si hay coincidencia exacta por UPC o un solo resultado, agrégalo directo
            u_norm = cs.normalizar_upc(q)
            exact = next((h for h in hits if cs.normalizar_upc(h.get("upc")) == u_norm), None)
            if exact or len(hits) == 1:
                _agregar_producto_al_carrito(exact or hits[0], cant=cant)
                return
            _render_search_hits(hits, cant)
        else:
            # No encontrado en catálogo -> pedir captura rápida de precio
            u_norm = cs.normalizar_upc(q) if any(ch.isdigit() for ch in q) else ""
            _abrir_dialogo_precio_manual(upc_init=u_norm, desc_init="" if u_norm else q, cant_init=cant)

    tf_scanner.on_change = _on_scanner_change
    tf_scanner.on_submit = _on_scanner_submit

    # ---------------- CAMBIO DE MODO TIENDA / AGRUPACIÓN ----------------
    def _set_tipo_tienda(nuevo_modo: str):
        state["tipo_tienda"] = nuevo_modo
        threading.Thread(target=lambda: cs.guardar_modo_tienda(store_code, nuevo_modo), daemon=True).start()
        _recalcular_y_render()

    btn_mode_linea = ft.Container(
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ink=True,
        on_click=lambda e: _set_tipo_tienda("LINEA"),
        content=ft.Text("🏬 Tienda Línea (2da al 40% / Promo)", size=12, weight="bold", color="white"),
    )
    btn_mode_outlet = ft.Container(
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        ink=True,
        on_click=lambda e: _set_tipo_tienda("OUTLET"),
        content=ft.Text("🏪 Tienda Outlet (30/40/50% + 60/70%)", size=12, weight="bold", color="white"),
    )

    def _on_agrupacion_change(e):
        state["modo_agrupacion"] = e.control.value or "PAREJAS_DESC"
        _recalcular_y_render()

    def _on_mixta_change(e):
        state["preferencia_mixta"] = e.control.value or "AUTO"
        _recalcular_y_render()

    dd_agrupacion.on_select = _on_agrupacion_change
    dd_mixta.on_select = _on_mixta_change

    linea_options_row = ft.Container(
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#1E293B"),
        border_radius=10,
        padding=8,
        content=ft.Row([dd_agrupacion, dd_mixta], wrap=True, spacing=10),
    )

    # ---------------- GUARDAR / EDITAR / PDF / DESCUENTOS ----------------
    def _nueva_cotizacion():
        state["items"] = []
        state["editing_id"] = None
        state["editing_folio"] = None
        tf_cliente.value = ""
        _recalcular_y_render()

    def _on_guardar_click(e):
        if not state["items"]:
            _snack("Agrega al menos 1 producto antes de guardar.", "#F59E0B")
            return
        cli = str(tf_cliente.value or "Cliente Mostrador").strip() or "Cliente Mostrador"
        ok, cid, msg = cs.guardar_cotizacion(
            store_code,
            store_name,
            cli,
            state["tipo_tienda"],
            state["modo_agrupacion"],
            state["items"],
            state["last_calc"],
            cotizacion_id=state["editing_id"],
        )
        if ok:
            state["editing_id"] = cid
            _recalcular_y_render()
            _snack(msg, "#00FFAA")
        else:
            _snack(msg, "#EF4444")

    def _on_generar_pdf_click(inline: bool = False):
        if not state["items"]:
            _snack("Agrega al menos 1 producto para generar el PDF.", "#F59E0B")
            return
        try:
            cli = str(tf_cliente.value or "Cliente Mostrador").strip() or "Cliente Mostrador"
            folio = state["editing_folio"] or state["editing_id"]
            _, fname = cs.generar_pdf_cotizacion(
                state["last_calc"],
                tienda_label=f"{store_code} {store_name}",
                cliente_nombre=cli,
                tipo_tienda=state["tipo_tienda"],
                folio=folio,
            )
            _lanzar_dl(fname, inline=inline)
            _snack(f"📄 PDF generado: {fname}", "#38BDF8")
        except Exception as ex:
            _snack(f"Error generando PDF: {ex}", "#EF4444")

    def _on_ver_descargar_descuentos(e):
        rows = cs.obtener_descuentos_tienda_readonly(store_code, store_name, limit=60)

        def _dl_excel(ev):
            try:
                _, fname, cnt = cs.exportar_descuentos_tienda_excel(store_code, store_name)
                _close_dlg(dlg)
                _lanzar_dl(fname, inline=False)
                _snack(f"📥 Excel de descuentos generado ({cnt:,} registros)", "#00FFAA")
            except Exception as ex:
                _snack(f"Error exportando descuentos: {ex}", "#EF4444")

        preview_items = []
        for r in rows[:30]:
            t_s = str(r.get("tipo_descuento") or "")
            c_s = "#F43F5E" if "50" in t_s else ("#10B981" if "30" in t_s else "#38BDF8")
            preview_items.append(
                ft.Container(
                    bgcolor="#0F172A",
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                    content=ft.Row(
                        [
                            ft.Text(f"{r.get('upc')} • {r.get('marca', '')}", size=11, color="white", expand=True),
                            ft.Text(t_s, size=11, weight="bold", color=c_s),
                        ]
                    ),
                )
            )
        if not preview_items:
            preview_items.append(ft.Text(f"No se encontraron descuentos semanales activos para {store_code}.", size=12, color="#94A3B8"))

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor="#1E293B",
            title=ft.Text(f"🏷️ Descuentos Activos — {store_code}", color="white", weight="bold", size=15),
            content=ft.Container(
                width=460,
                height=340,
                content=ft.Column(
                    [
                        ft.Text("Lectura en tiempo real desde la pestaña Descuentos (Azul 20%, Verde 30%, Roja 30→50%).", size=11, color="#94A3B8"),
                        ft.Column(preview_items, spacing=4, scroll=ft.ScrollMode.AUTO, expand=True),
                    ],
                    spacing=8,
                ),
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda ev: _close_dlg(dlg)),
                ft.ElevatedButton("📥 Descargar Excel Completo", bgcolor="#00FFAA", color="#0F172A", on_click=_dl_excel),
            ],
        )
        _show_dlg(dlg)

    # ---------------- HERRAMIENTAS EXCLUSIVAS ADMIN ----------------
    def _on_subir_mim_excel(e):
        if not es_admin:
            return

        def _procesar_archivo(ruta: str):
            if not ruta:
                return
            progress_upload_bar.visible = True
            progress_upload_bar.value = 0.05
            progress_upload_txt.visible = True
            progress_upload_txt.value = "Iniciando lectura de Excel MIM..."
            page.update()

            def _cb(pct, msg):
                try:
                    progress_upload_bar.value = max(0.0, min(1.0, float(pct) / 100.0))
                    progress_upload_txt.value = str(msg)
                    page.update()
                except Exception:
                    pass

            def _worker():
                ok, msg, _ = cs.importar_excel_precios_mim(ruta, progress_callback=_cb)
                progress_upload_bar.visible = False
                progress_upload_txt.visible = False
                if ok:
                    state["catalogo_count"] = cs.obtener_conteo_catalogo()
                    txt_catalogo_badge.value = f"📦 {state['catalogo_count']:,} UPCs con precio"
                    _snack(msg, "#00FFAA")
                else:
                    _snack(msg, "#EF4444")
                try:
                    page.update()
                except Exception:
                    pass

            threading.Thread(target=_worker, daemon=True).start()

        if callable(seleccionar_archivo_async):
            seleccionar_archivo_async(
                "Subir archivo Excel de Precios MIM (StockSummary_Details)",
                ["xlsx", "xlsm"],
                lambda paths: _procesar_archivo(paths[0] if isinstance(paths, (list, tuple)) and paths else paths),
                False,
            )
        else:
            _snack("Selector de archivos no disponible en este contexto.", "#F59E0B")

    def _on_promo_especial_admin(e):
        if not es_admin:
            return
        cur_p = cs.obtener_promo_especial()
        sw_act = ft.Switch(label="Activar Promo Especial Global", value=bool(cur_p.get("activa")), active_color="#00FFAA")
        tf_nom = ft.TextField(label="Nombre de campaña (ej. Buen Fin 20%)", value=str(cur_p.get("nombre") or "Buen Fin 20%"), text_size=12, bgcolor="#0F172A", color="white")
        tf_pct = ft.TextField(label="% Descuento (ej. 20)", value=str(int(float(cur_p.get("descuento_pct") or 20))), width=140, keyboard_type=ft.KeyboardType.NUMBER, text_size=12, bgcolor="#0F172A", color="white")
        dd_alc = ft.Dropdown(
            label="Aplica en tiendas",
            value=str(cur_p.get("alcance") or "TODAS"),
            width=210,
            text_size=12,
            bgcolor="#0F172A",
            color="white",
            options=[
                ft.dropdown.Option("TODAS", "TODAS las tiendas"),
                ft.dropdown.Option("LINEA", "Solo Tiendas Línea"),
                ft.dropdown.Option("OUTLET", "Solo Tiendas Outlet"),
                ft.dropdown.Option("CODIGOS", "Solo códigos específicos"),
            ],
        )
        tf_tiendas = ft.TextField(label="Códigos permitidos (si elegiste códigos, sep. por coma)", value=str(cur_p.get("tiendas_permitidas") or ""), hint_text="Ej. A540, S120, C410", text_size=12, bgcolor="#0F172A", color="white")
        tf_excl = ft.TextField(label="Marcas / modelos excluidos (sep. por coma)", value=str(cur_p.get("exclusiones") or "RAY BAN META, OAKLEY META"), hint_text="Ej. RAY BAN META, OAKLEY META", text_size=12, bgcolor="#0F172A", color="white", multiline=True, min_lines=2)

        def _guardar_promo(ev):
            try:
                pct_num = float(str(tf_pct.value or "0").replace("%", "").strip())
            except Exception:
                pct_num = 0.0
            cfg = {
                "activa": bool(sw_act.value),
                "nombre": str(tf_nom.value or "Promo Especial").strip(),
                "descuento_pct": max(0.0, min(95.0, pct_num)),
                "alcance": dd_alc.value or "TODAS",
                "tiendas_permitidas": str(tf_tiendas.value or "").strip(),
                "exclusiones": str(tf_excl.value or "").strip(),
                "actualizado_por": str(user_info.get("nombre") or user_info.get("usuario") or "Admin"),
            }
            if cs.guardar_promo_especial(cfg):
                state["promo_especial"] = cs.obtener_promo_especial()
                _close_dlg(dlg)
                _recalcular_y_render()
                _snack("🔥 Configuración de Promo Especial guardada.", "#00FFAA")
            else:
                _snack("No se pudo guardar la Promo Especial.", "#EF4444")

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor="#1E293B",
            title=ft.Text("🔥 Promo Especial Administrador", color="#FDE047", weight="bold", size=15),
            content=ft.Container(
                width=450,
                content=ft.Column(
                    [
                        sw_act,
                        tf_nom,
                        ft.Row([tf_pct, dd_alc], spacing=8),
                        tf_tiendas,
                        tf_excl,
                        ft.Text("Regla automática: Nunca acumula descuento sobre descuento; aplica el mayor descuento entre promo de pieza o campaña especial.", size=11, color="#94A3B8"),
                    ],
                    tight=True,
                    spacing=8,
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: _close_dlg(dlg)),
                ft.ElevatedButton("Guardar Regla", bgcolor="#00FFAA", color="#0F172A", on_click=_guardar_promo),
            ],
        )
        _show_dlg(dlg)

    # ---------------- PESTAÑA 2: COTIZACIONES GUARDADAS ----------------
    def _cargar_guardadas(update_ui: bool = True):
        state["saved_list"] = cs.listar_cotizaciones(codigo_tienda=store_code, es_admin=es_admin, limit=100)
        _render_guardadas()
        if update_ui:
            try:
                page.update()
            except Exception:
                pass

    def _render_guardadas():
        saved_list_col.controls.clear()
        q = str(saved_search_tf.value or "").strip().lower()
        rows = state["saved_list"] or []
        if q:
            rows = [
                r for r in rows
                if q in str(r.get("folio") or "").lower()
                or q in str(r.get("cliente_nombre") or "").lower()
                or q in str(r.get("codigo_tienda") or "").lower()
                or q in str(r.get("nombre_tienda") or "").lower()
            ]
        if not rows:
            saved_list_col.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    bgcolor="#0F172A",
                    border_radius=12,
                    content=ft.Text("🗂️ No hay cotizaciones guardadas todavía.", size=13, color="#94A3B8"),
                )
            )
            return

        for row in rows:
            cid = row["id"]

            def _make_edit(r_data):
                def _click(ev):
                    try:
                        loaded_items = json.loads(r_data.get("items_json") or "[]")
                    except Exception:
                        loaded_items = []
                    state["items"] = loaded_items
                    state["editing_id"] = r_data["id"]
                    state["editing_folio"] = r_data.get("folio")
                    state["tipo_tienda"] = r_data.get("tipo_tienda") or state["tipo_tienda"]
                    state["modo_agrupacion"] = r_data.get("modo_agrupacion") or "PAREJAS_DESC"
                    dd_agrupacion.value = state["modo_agrupacion"]
                    tf_cliente.value = r_data.get("cliente_nombre") or ""
                    _switch_tab("cotizador")
                    _snack(f"✏️ Cotización {r_data.get('folio')} cargada para editar.", "#38BDF8")
                return _click

            def _make_pdf(r_data, inline=False):
                def _click(ev):
                    try:
                        it_l = json.loads(r_data.get("items_json") or "[]")
                        calc_r = cs.calcular_cotizacion(
                            it_l,
                            tipo_tienda=r_data.get("tipo_tienda") or "LINEA",
                            modo_agrupacion=r_data.get("modo_agrupacion") or "PAREJAS_DESC",
                            promo_especial=state["promo_especial"],
                            codigo_tienda=r_data.get("codigo_tienda") or store_code,
                            nombre_tienda=r_data.get("nombre_tienda") or store_name,
                        )
                        _, fname = cs.generar_pdf_cotizacion(
                            calc_r,
                            tienda_label=f"{r_data.get('codigo_tienda', '')} {r_data.get('nombre_tienda', '')}",
                            cliente_nombre=r_data.get("cliente_nombre") or "Cliente Mostrador",
                            tipo_tienda=r_data.get("tipo_tienda") or "LINEA",
                            folio=r_data.get("folio") or r_data["id"],
                        )
                        _lanzar_dl(fname, inline=inline)
                    except Exception as ex:
                        _snack(f"Error PDF: {ex}", "#EF4444")
                return _click

            def _make_delete(c_id, folio_s):
                def _ask(ev):
                    def _do_del(e2):
                        _close_dlg(dlg_c)
                        if cs.borrar_cotizacion(c_id):
                            if state["editing_id"] == c_id:
                                state["editing_id"] = None
                                state["editing_folio"] = None
                            _cargar_guardadas()
                            _snack(f"🗑️ Cotización {folio_s} eliminada.", "#F87171")
                        else:
                            _snack("No se pudo borrar la cotización.", "#EF4444")

                    dlg_c = ft.AlertDialog(
                        modal=True,
                        bgcolor="#1E293B",
                        title=ft.Text("Confirmar eliminación", color="white", weight="bold"),
                        content=ft.Text(f"¿Seguro deseas borrar {folio_s}? Se liberará espacio y no se podrá deshacer.", color="#CBD5E1"),
                        actions=[
                            ft.TextButton("Cancelar", on_click=lambda e2: _close_dlg(dlg_c)),
                            ft.ElevatedButton("Sí, Borrar", bgcolor="#EF4444", color="white", on_click=_do_del),
                        ],
                    )
                    _show_dlg(dlg_c)
                return _ask

            info_saved = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(str(row.get("folio") or f"#{cid}"), size=13, weight="bold", color="#00FFFF"),
                            ft.Container(
                                bgcolor="#1E293B",
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                content=ft.Text(f"{row.get('tipo_tienda')} • {row.get('total_piezas')} pz", size=10, color="#CBD5E1"),
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Text(f"Cliente: {row.get('cliente_nombre')}  |  Tienda: {row.get('codigo_tienda')} {row.get('nombre_tienda')}", size=11, color="#E2E8F0"),
                    ft.Text(
                        f"Orig: ${float(row.get('total_original') or 0):,.2f}  •  Ahorro: ${float(row.get('total_ahorro') or 0):,.2f}  •  Final: ${float(row.get('total_final') or 0):,.2f}  •  Fecha: {row.get('actualizado_en')}",
                        size=11,
                        color="#34D399",
                        weight="bold",
                    ),
                ],
                spacing=3,
                expand=not is_mobile,
            )
            btns_saved = ft.Row(
                [
                    ft.ElevatedButton("✏️ Editar", bgcolor="#0284C7", color="white", height=34, on_click=_make_edit(row)),
                    ft.IconButton(ft.Icons.PICTURE_AS_PDF, icon_color="#38BDF8", tooltip="Descargar PDF", on_click=_make_pdf(row, inline=False)),
                    ft.IconButton(ft.Icons.PRINT, icon_color="#C084FC", tooltip="Ver / Imprimir", on_click=_make_pdf(row, inline=True)),
                    ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color="#F87171", tooltip="Borrar cotización", on_click=_make_delete(cid, row.get("folio"))),
                ],
                spacing=4,
            )
            card = ft.Container(
                bgcolor="#0F172A",
                border=ft.Border.all(1, "#334155"),
                border_radius=10,
                padding=12,
                content=ft.Column([info_saved, btns_saved], spacing=8) if is_mobile else ft.Row(
                    [info_saved, btns_saved],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )
            saved_list_col.controls.append(card)

    saved_search_tf.on_change = lambda e: (_render_guardadas(), page.update())

    # ---------------- SWITCH DE PESTAÑAS ----------------
    tab1_btn = ft.Container()
    tab2_btn = ft.Container()
    cotizador_tab_body = ft.Container()
    guardadas_tab_body = ft.Container(visible=False)

    def _switch_tab(tab_name: str):
        state["active_tab"] = tab_name
        is_c = tab_name == "cotizador"
        cotizador_tab_body.visible = is_c
        guardadas_tab_body.visible = not is_c
        tab1_btn.bgcolor = "#00FFFF" if is_c else "#1E293B"
        tab1_btn.content.color = "#0F172A" if is_c else "#CBD5E1"
        tab2_btn.bgcolor = "#00FFFF" if not is_c else "#1E293B"
        tab2_btn.content.color = "#0F172A" if not is_c else "#CBD5E1"
        if not is_c:
            _cargar_guardadas(update_ui=False)
        else:
            _recalcular_y_render(update_ui=False)
        try:
            page.update()
        except Exception:
            pass

    tab1_btn = ft.Container(
        bgcolor="#00FFFF",
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        ink=True,
        on_click=lambda e: _switch_tab("cotizador"),
        content=ft.Text("🧮 Cotizador POS", size=12, weight="bold", color="#0F172A"),
    )
    tab2_btn = ft.Container(
        bgcolor="#1E293B",
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        ink=True,
        on_click=lambda e: _switch_tab("guardadas"),
        content=ft.Text("🗂️ Cotizaciones Guardadas", size=12, weight="bold", color="#CBD5E1"),
    )

    # ---------------- HEADER Y ENSAMBLAJE ----------------
    header_actions = [
        ft.ElevatedButton(
            "🏷️ Ver / Descargar Descuentos",
            bgcolor="#1E293B",
            color="#38BDF8",
            height=36,
            on_click=_on_ver_descargar_descuentos,
        )
    ]
    if es_admin:
        header_actions.append(
            ft.ElevatedButton(
                "📥 Subir Precios MIM (Excel)",
                bgcolor="#065F46",
                color="#6EE7B7",
                height=36,
                on_click=_on_subir_mim_excel,
            )
        )
        header_actions.append(
            ft.ElevatedButton(
                "🔥 Promo Especial Admin",
                bgcolor="#7E22CE",
                color="white",
                height=36,
                on_click=_on_promo_especial_admin,
            )
        )

    header_title_col = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("🧮 Calculadora & Cotizador Inteligente", size=18, weight="bold", color="white"),
                    txt_catalogo_badge,
                ],
                wrap=True,
                spacing=10,
            ),
            ft.Text(f"Tienda activa: {store_code} — {store_name}", size=11, color="#94A3B8"),
        ],
        spacing=2,
        expand=not is_mobile,
    )
    header_actions_row = ft.Row(header_actions, wrap=True, spacing=8)

    header_bar = ft.Container(
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#1E293B"),
        border_radius=12,
        padding=12,
        content=ft.Column(
            [
                ft.Column([header_title_col, header_actions_row], spacing=8) if is_mobile else ft.Row(
                    [header_title_col, header_actions_row],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                progress_upload_bar,
                progress_upload_txt,
                ft.Row(
                    [
                        tab1_btn,
                        tab2_btn,
                        ft.Container(width=12),
                        btn_mode_linea,
                        btn_mode_outlet,
                    ],
                    wrap=True,
                    spacing=8,
                ),
                banner_promo_holder,
                banner_editing_holder,
            ],
            spacing=8,
        ),
    )

    btn_manual_item = ft.ElevatedButton(
        "➕ Pieza Manual",
        bgcolor="#1E293B",
        color="#FDE047",
        height=44,
        on_click=lambda e: _abrir_dialogo_precio_manual(guardar_en_catalogo=False),
    )
    cliente_row = (
        ft.Column([tf_cliente, btn_manual_item], spacing=8)
        if is_mobile
        else ft.Row([ft.Container(content=tf_cliente, expand=True), btn_manual_item], spacing=8)
    )

    # Cuerpo de Pestaña 1 (Cotizador)
    left_pane = ft.Column(
        [
            cliente_row,
            tf_scanner,
            search_results_box,
            linea_options_row,
            ft.Row([ft.Text("📦 Artículos en Cotización", size=13, weight="bold", color="#CBD5E1"), cart_count_txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(
                height=500 if not is_mobile else 420,
                bgcolor="#090D16",
                border=ft.Border.all(1, "#1E293B"),
                border_radius=10,
                padding=6,
                content=cart_items_col,
            ),
        ],
        spacing=8,
    )

    right_pane = ft.Container(
        bgcolor="#0F172A",
        border=ft.Border.all(1, "#1E293B"),
        border_radius=12,
        padding=12,
        content=summary_panel_col,
    )

    if is_mobile:
        cotizador_tab_body.content = ft.Column([left_pane, right_pane], spacing=12)
    else:
        cotizador_tab_body.content = ft.Row(
            [
                ft.Container(content=left_pane, expand=7),
                ft.Container(content=right_pane, expand=5),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    # Cuerpo de Pestaña 2 (Cotizaciones Guardadas)
    guardadas_tab_body.content = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(content=saved_search_tf, expand=True),
                    ft.ElevatedButton("🔄 Actualizar Lista", bgcolor="#1E293B", color="#38BDF8", height=42, on_click=lambda e: _cargar_guardadas()),
                ],
                spacing=8,
            ),
            ft.Container(
                height=520,
                content=saved_list_col,
            ),
        ],
        spacing=10,
    )

    _recalcular_y_render(update_ui=False)

    return ft.Container(
        expand=True,
        padding=12,
        bgcolor="#020617",
        content=ft.Column(
            [
                header_bar,
                cotizador_tab_body,
                guardadas_tab_body,
            ],
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
    )
