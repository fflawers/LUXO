# ==============================================================================
# LUXO - MÓDULO INDEPENDIENTE DE TRADUCTOR DE MOSTRADOR (ÓPTICA & LENTES DE SOL)
# ==============================================================================
import flet as ft
import threading
import asyncio
import random
import os
import json

# Voces existentes de LUXO para traducciones al español
VOCES_LUXO_FEMENINAS = ["barbara", "helena", "sabina"]
VOCES_LUXO_MASCULINAS = ["jarvis", "jorge", "alonso"]

# Mapeo de voces nativas para clientes extranjeros según género
VOCES_NATIVAS_EXTRANJERAS = {
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural"},
    "it": {"female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural"},
    "pt": {"female": "pt-BR-FranciscaNeural", "male": "pt-BR-AntonioNeural"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunxiNeural"},
    "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"},
}

def detectar_idioma_y_traducir_ia(texto: str) -> dict:
    if not texto or not texto.strip():
        return None

    txt_clean = texto.strip()

    prompt_traduccion = f'''Eres el sistema oficial de traducción simultánea para mostrador de una boutique de lentes de sol y óptica (LUXO).
Tu tarea es traducir de forma 100% precisa, natural y elegante el siguiente texto.

TEXTO A PROCESAR:
"{txt_clean}"

REGLAS ESTRICTAS:
1. Identifica el idioma del texto de entrada (código ISO de 2 letras: 'es', 'en', 'fr', 'de', 'it', 'pt', 'zh', 'ja', etc.).
2. Si el texto está en ESPAÑOL ('es'), tradúcelo al INGLÉS ('en') o al idioma que corresponda para el cliente extranjero.
3. Si el texto está en CUALQUIER IDIOMA EXTRANJERO, tradúcelo al ESPAÑOL ('es') para el vendedor.
4. Terminología óptica: Utiliza el vocabulario técnico exacto de lentes de sol (micas polarizadas, protección UV400, armazón de acetato, varillas, puente, micas degradadas, antirreflejante, etc.).
5. Cero añadidos: NO agregues notas, NO agregues sugerencias de venta ni introducciones.
6. Estima el género probable del hablante por las palabras o entonación ('female' o 'male', por defecto 'female' si no es concluyente).

Responde ÚNICAMENTE un objeto JSON válido con la siguiente estructura exacta:
{{
    "idioma_origen": "código_iso",
    "idioma_destino": "código_iso",
    "traduccion": "texto traducido limpio",
    "genero_hablante": "female" o "male"
}}'''

    try:
        import google.generativeai as genai
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt_traduccion)
        if response and response.text:
            raw = response.text.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            data = json.loads(raw)
            return {
                "origen": data.get("idioma_origen", "auto"),
                "destino": data.get("idioma_destino", "es"),
                "texto_original": txt_clean,
                "texto_traducido": data.get("traduccion", "").strip(),
                "genero_detectado": data.get("genero_hablante", "female")
            }
    except Exception as ex_gem:
        print("Notice traduccion Gemini:", ex_gem)

    es_probable_espanol = any(w in txt_clean.lower() for w in ["hola", "lentes", "sol", "precio", "cuanto", "gracias", "armazon", "mica", "polarizado", "tienen", "buenas"])
    orig = "es" if es_probable_espanol else "en"
    dest = "en" if orig == "es" else "es"

    return {
        "origen": orig,
        "destino": dest,
        "texto_original": txt_clean,
        "texto_traducido": f"{txt_clean}",
        "genero_detectado": "female"
    }

def reproducir_audio_traduccion_async(texto: str, idioma: str, genero: str = "female", start_speak_fn=None):
    def _worker():
        try:
            if not texto or not texto.strip():
                return

            if idioma == "es":
                if genero == "female":
                    v_luxo = random.choice(VOCES_LUXO_FEMENINAS)
                else:
                    v_luxo = random.choice(VOCES_LUXO_MASCULINAS)

                if start_speak_fn:
                    start_speak_fn(texto, voice_id=v_luxo, voice_gender=genero)
                return

            lang_key = idioma[:2].lower()
            v_spec = VOCES_NATIVAS_EXTRANJERAS.get(lang_key, VOCES_NATIVAS_EXTRANJERAS["en"])
            voice_name = v_spec.get(genero, v_spec["female"])

            import hashlib, edge_tts
            temp_dir = os.path.join(os.getcwd(), "custom_assets", "temp_audio")
            os.makedirs(temp_dir, exist_ok=True)
            h = hashlib.md5(f"{texto}_{voice_name}".encode("utf-8")).hexdigest()
            fp = os.path.join(temp_dir, f"trans_{h}.mp3")

            if not os.path.exists(fp):
                async def _gen():
                    comm = edge_tts.Communicate(texto, voice_name)
                    await comm.save(fp)
                asyncio.run(_gen())

            if os.path.exists(fp) and os.path.getsize(fp) > 0:
                try:
                    import ctypes
                    mci = ctypes.windll.winmm.mciSendStringW
                    mci("close luxo_translator_audio", None, 0, 0)
                    mci(f'open "{os.path.abspath(fp)}" type mpegvideo alias luxo_translator_audio', None, 0, 0)
                    mci("play luxo_translator_audio", None, 0, 0)
                except Exception:
                    pass
        except Exception as ex_aud:
            print("Notice reproducir_audio_traduccion:", ex_aud)

    threading.Thread(target=_worker, daemon=True).start()

def build_traductor_view(page: ft.Page, user_info=None, conectar_db_fn=None, mostrar_snack_fn=None, start_speak_fn=None):
    is_mobile = (page.width < 768) if (page.width and page.width > 0) else False

    vendedor_genero = ["female"]
    idioma_cliente_actual = ["en"]

    chat_list = ft.ListView(
        expand=True,
        spacing=12,
        padding=ft.Padding(12, 12, 12, 12),
        auto_scroll=True
    )

    status_indicator = ft.Text("Listo para traducir", color="#00FFFF", size=13, weight="bold")

    txt_input_vendedor = ft.TextField(
        hint_text="Escribe o habla en español...",
        hint_style=ft.TextStyle(color="#666677", size=13),
        color="white",
        bgcolor="#0e0e18",
        border_color="#00FFFF",
        focused_border_color="#D8B4FE",
        border_radius=12,
        expand=True,
        content_padding=12,
    )

    txt_input_cliente = ft.TextField(
        hint_text="Type or speak in any foreign language...",
        hint_style=ft.TextStyle(color="#666677", size=13),
        color="white",
        bgcolor="#0e0e18",
        border_color="#D8B4FE",
        focused_border_color="#00FFFF",
        border_radius=12,
        expand=True,
        content_padding=12,
    )

    def agregar_burbuja_traduccion(origen_lbl, texto_orig, texto_trad, color_accent, icono):
        chat_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(icono, size=16),
                        ft.Text(origen_lbl, color=color_accent, weight="bold", size=13),
                    ], spacing=6),
                    ft.Text(f'"{texto_orig}"', color="#cccccc", size=14, italic=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.TRANSLATE_ROUNDED, color="#00FFFF", size=16),
                            ft.Text(texto_trad, color="white", weight="bold", size=15, expand=True)
                        ], spacing=8),
                        bgcolor="#16162a",
                        padding=10,
                        border_radius=8,
                        border=ft.Border.all(1, color_accent)
                    )
                ], spacing=6),
                bgcolor="#0a0a14",
                padding=14,
                border_radius=12,
                border=ft.Border.all(1.5, color_accent),
                shadow=[ft.BoxShadow(color=f"{color_accent}22", blur_radius=10, spread_radius=1)]
            )
        )
        try: page.update()
        except: pass

    def procesar_traduccion_vendedor(e=None):
        texto = txt_input_vendedor.value
        if not texto or not texto.strip():
            return
        txt_input_vendedor.value = ""
        status_indicator.value = "Traduciendo al cliente..."
        status_indicator.color = "#FFD700"
        try: page.update()
        except: pass

        def _task():
            res = detectar_idioma_y_traducir_ia(texto)
            if res:
                idioma_dest = res.get("destino", idioma_cliente_actual[0])
                trad = res.get("texto_traducido", "")
                agregar_burbuja_traduccion(
                    "Vendedor (Español 🇲🇽 ➔ Cliente)",
                    texto,
                    trad,
                    "#00FFFF",
                    "👤"
                )
                reproducir_audio_traduccion_async(trad, idioma_dest, genero=vendedor_genero[0], start_speak_fn=start_speak_fn)
            status_indicator.value = "Listo para traducir"
            status_indicator.color = "#00FFFF"
            try: page.update()
            except: pass

        threading.Thread(target=_task, daemon=True).start()

    def procesar_traduccion_cliente(e=None):
        texto = txt_input_cliente.value
        if not texto or not texto.strip():
            return
        txt_input_cliente.value = ""
        status_indicator.value = "Traduciendo al español..."
        status_indicator.color = "#FFD700"
        try: page.update()
        except: pass

        def _task():
            res = detectar_idioma_y_traducir_ia(texto)
            if res:
                idioma_orig = res.get("origen", "en")
                idioma_cliente_actual[0] = idioma_orig
                trad = res.get("texto_traducido", "")
                gen_cliente = res.get("genero_detectado", "female")
                agregar_burbuja_traduccion(
                    f"Cliente ({idioma_orig.upper()} 🌍 ➔ Vendedor)",
                    texto,
                    trad,
                    "#D8B4FE",
                    "🕶️"
                )
                reproducir_audio_traduccion_async(trad, "es", genero=gen_cliente, start_speak_fn=start_speak_fn)
            status_indicator.value = "Listo para traducir"
            status_indicator.color = "#00FFFF"
            try: page.update()
            except: pass

        threading.Thread(target=_task, daemon=True).start()

    txt_input_vendedor.on_submit = procesar_traduccion_vendedor
    txt_input_cliente.on_submit = procesar_traduccion_cliente

    def toggle_genero_vendedor(e):
        if vendedor_genero[0] == "female":
            vendedor_genero[0] = "male"
            btn_genero.content = ft.Text("👨 Vendedor (Masculino)", size=12, color="#00FFFF", weight="bold")
        else:
            vendedor_genero[0] = "female"
            btn_genero.content = ft.Text("👩 Vendedora (Femenino)", size=12, color="#E040FB", weight="bold")
        try: btn_genero.update()
        except: pass

    btn_genero = ft.Container(
        content=ft.Text("👩 Vendedora (Femenino)", size=12, color="#E040FB", weight="bold"),
        bgcolor="#141424",
        padding=ft.Padding(12, 6, 12, 6),
        border_radius=8,
        border=ft.Border.all(1, "#E040FB"),
        on_click=toggle_genero_vendedor,
        tooltip="Cambia el género de tu voz al traducir al cliente extranjero"
    )

    def limpiar_chat(e):
        chat_list.controls.clear()
        agregar_burbuja_traduccion(
            "LUXO Sistema",
            "Traductor listo para atención en mostrador",
            "Ready for sunglasses & optical translation",
            "#00FFFF",
            "✨"
        )
        try: page.update()
        except: pass

    btn_limpiar = ft.IconButton(
        icon=ft.Icons.DELETE_SWEEP_ROUNDED,
        icon_color="#888899",
        tooltip="Limpiar conversación",
        on_click=limpiar_chat
    )

    limpiar_chat(None)

    card_vendedor = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("🇲🇽 LADO VENDEDOR (Español)", color="#00FFFF", weight="bold", size=14),
                btn_genero
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                txt_input_vendedor,
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    icon_color="#00FFFF",
                    bgcolor="#003366",
                    tooltip="Traducir al Cliente",
                    on_click=procesar_traduccion_vendedor
                )
            ])
        ], spacing=8),
        bgcolor="#0c0c1a",
        padding=12,
        border_radius=14,
        border=ft.Border.all(1.5, "#00FFFF")
    )

    card_cliente = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("🌍 LADO CLIENTE (Idioma Extranjero)", color="#D8B4FE", weight="bold", size=14),
                ft.Text("✨ Auto-Detección", size=11, color="#aaaaaa")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                txt_input_cliente,
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    icon_color="#D8B4FE",
                    bgcolor="#4A0072",
                    tooltip="Translate to Spanish",
                    on_click=procesar_traduccion_cliente
                )
            ])
        ], spacing=8),
        bgcolor="#0c0c1a",
        padding=12,
        border_radius=14,
        border=ft.Border.all(1.5, "#D8B4FE")
    )

    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.TRANSLATE_ROUNDED, color="#00FFFF", size=26),
            ft.Text("TRADUCTOR DE MOSTRADOR LUXO", size=20 if is_mobile else 22, color="white", weight="bold"),
            ft.Container(expand=True),
            status_indicator,
            btn_limpiar
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("Traducción inteligente bidireccional en tiempo real con detección automática de idioma para óptica y lentes de sol.", size=12, color="#888899"),
        ft.Divider(height=10, color="#222233"),
        ft.Container(
            content=chat_list,
            expand=True,
            bgcolor="#04040a",
            border_radius=12,
            border=ft.Border.all(1, "#181828")
        ),
        ft.Divider(height=8, color="transparent"),
        ft.Column([
            card_vendedor,
            card_cliente
        ], spacing=10)
    ], expand=True)
