# ==============================================================================
# LUXO - MÓDULO INDEPENDIENTE DE TRADUCTOR DE MOSTRADOR (ÓPTICA & LENTES DE SOL)
# ==============================================================================
import flet as ft
import threading
import asyncio
import random
import os
import json
import time
import urllib.parse

# Voces existentes de LUXO para traducciones al español
VOCES_LUXO_FEMENINAS = ["barbara", "helena", "sabina"]
VOCES_LUXO_MASCULINAS = ["jarvis", "jorge", "alonso"]

# Mapeo de voces nativas para clientes extranjeros según género
VOCES_NATIVAS_EXTRANJERAS = {
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural", "name": "Inglés 🇺🇸/🇬🇧"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural", "name": "Francés 🇫🇷"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural", "name": "Alemán 🇩🇪"},
    "it": {"female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural", "name": "Italiano 🇮🇹"},
    "pt": {"female": "pt-BR-FranciscaNeural", "male": "pt-BR-AntonioNeural", "name": "Portugués 🇧🇷/🇵🇹"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunxiNeural", "name": "Chino Mandarín 🇨🇳"},
    "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural", "name": "Japonés 🇯🇵"},
    "ko": {"female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural", "name": "Coreano 🇰🇷"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural", "name": "Ruso 🇷🇺"},
    "ar": {"female": "ar-SA-ZariyahNeural", "male": "ar-SA-HamedNeural", "name": "Árabe 🇸🇦"},
}

# Sesiones activas del traductor para puente bidireccional Web/FastAPI
TRADUCTOR_SESSIONS = {}

def get_groq_api_key_traductor():
    """Obtiene una llave de Groq para Whisper sin alterar el core."""
    for env_k in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"]:
        k = os.getenv(env_k, "")
        if k: return k
    return ""

def detectar_idioma_y_traducir_ia(texto: str) -> dict:
    """Detecta el idioma, tono y género del hablante y traduce con terminología óptica."""
    if not texto or not texto.strip():
        return None

    txt_clean = texto.strip()

    prompt_traduccion = f'''Eres el sistema oficial de traducción simultánea para mostrador de una boutique de lentes de sol y óptica (LUXO).
Tu tarea es traducir de forma 100% precisa, natural y elegante el siguiente texto.

TEXTO A PROCESAR:
"{txt_clean}"

REGLAS ESTRICTAS:
1. Identifica el idioma del texto de entrada (código ISO de 2 letras: 'es', 'en', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ru', 'ar', etc.).
2. Si el texto está en ESPAÑOL ('es'), tradúcelo al INGLÉS ('en') o al idioma activo del cliente extranjero.
3. Si el texto está en CUALQUIER IDIOMA EXTRANJERO, tradúcelo al ESPAÑOL ('es') para el vendedor.
4. Terminología óptica: Utiliza el vocabulario técnico exacto de lentes de sol (micas polarizadas, protección UV400, armazón de acetato, varillas, puente, micas degradadas, antirreflejante, titanio, bisagras flex, etc.).
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

    es_probable_espanol = any(w in txt_clean.lower() for w in ["hola", "lentes", "sol", "precio", "cuanto", "gracias", "armazon", "mica", "polarizado", "tienen", "buenas", "que"])
    orig = "es" if es_probable_espanol else "en"
    dest = "en" if orig == "es" else "es"

    return {
        "origen": orig,
        "destino": dest,
        "texto_original": txt_clean,
        "texto_traducido": f"{txt_clean}",
        "genero_detectado": "female"
    }

def reproducir_audio_traduccion_async(texto: str, idioma: str, genero: str = "female", start_speak_fn=None, page=None):
    """Sintetiza y reproduce el audio de la traducción en segundo plano de forma 100% aislada."""
    def _worker():
        try:
            if not texto or not texto.strip():
                return

            # Caso 1: Traducción al ESPAÑOL (para el Vendedor) -> Usar voces LUXO
            if idioma == "es":
                if genero == "female":
                    v_luxo = random.choice(VOCES_LUXO_FEMENINAS)
                else:
                    v_luxo = random.choice(VOCES_LUXO_MASCULINAS)

                if start_speak_fn:
                    start_speak_fn(texto, voice_id=v_luxo, voice_gender=genero)
                return

            # Caso 2: Traducción al IDIOMA EXTRANJERO (para el Cliente) -> Voz nativa de ese país
            lang_key = idioma[:2].lower()
            v_spec = VOCES_NATIVAS_EXTRANJERAS.get(lang_key, VOCES_NATIVAS_EXTRANJERAS["en"])
            voice_name = v_spec.get(genero, v_spec["female"])

            import hashlib, edge_tts
            temp_dir = os.path.join(os.getcwd(), "custom_assets", "temp_audio")
            os.makedirs(temp_dir, exist_ok=True)
            h = hashlib.md5(f"{texto}_{voice_name}".encode("utf-8")).hexdigest()
            filename = f"trans_{h}.mp3"
            fp = os.path.join(temp_dir, filename)

            if not os.path.exists(fp):
                async def _gen():
                    comm = edge_tts.Communicate(texto, voice_name)
                    await comm.save(fp)
                asyncio.run(_gen())

            if os.path.exists(fp) and os.path.getsize(fp) > 0:
                audio_web_url = f"/custom_assets/temp_audio/{filename}"
                if page and getattr(page, "web", False):
                    try:
                        js_play = f"""
                        (function() {{
                            try {{
                                let a = new Audio('{audio_web_url}');
                                a.play().catch(function(e){{ console.log('[TRADUCTOR TTS] Autoplay:', e); }});
                            }} catch(e){{}}
                        }})();
                        """
                        if hasattr(page, "launch_url"):
                            page.launch_url(f"javascript:{js_play}")
                    except Exception as ex_p:
                        print("Notice audio web play:", ex_p)
                else:
                    try:
                        import ctypes
                        mci = ctypes.windll.winmm.mciSendStringW
                        mci("close luxo_trans_audio", None, 0, 0)
                        mci(f'open "{os.path.abspath(fp)}" type mpegvideo alias luxo_trans_audio', None, 0, 0)
                        mci("play luxo_trans_audio", None, 0, 0)
                    except Exception:
                        pass
        except Exception as ex_aud:
            print("Notice reproducir_audio_traduccion:", ex_aud)

    threading.Thread(target=_worker, daemon=True).start()

def registrar_rutas_fastapi_traductor():
    """Registra rutas de FastAPI dinámicamente para recibir dictado de audio y texto del traductor."""
    try:
        import gc, fastapi
        apps = [obj for obj in gc.get_objects() if isinstance(obj, fastapi.FastAPI)]
        if not apps:
            return
        app = apps[0]

        for r in app.router.routes:
            if getattr(r, "path", None) == "/api/traductor/speech_input":
                return

        from fastapi import Request
        import tempfile, requests

        @app.api_route("/api/traductor/speech_input", methods=["GET", "POST"])
        async def api_traductor_speech_input(request: Request = None, session_id: str = "", source: str = "vendedor", text: str = ""):
            try:
                if request:
                    qp = request.query_params
                    session_id = session_id or qp.get("session_id", "")
                    source = source or qp.get("source", "vendedor")
                    text = text or qp.get("text", "")
                    if not text:
                        try:
                            body = await request.json()
                            session_id = session_id or body.get("session_id", "")
                            source = source or body.get("source", "vendedor")
                            text = text or body.get("text", "")
                        except Exception: pass

                txt_clean = (text or "").strip()
                if not txt_clean:
                    return {"status": "empty"}

                sess_handler = TRADUCTOR_SESSIONS.get(session_id)
                if not sess_handler and TRADUCTOR_SESSIONS:
                    sess_handler = list(TRADUCTOR_SESSIONS.values())[-1]

                if sess_handler:
                    fn = sess_handler.get("procesar_vendedor" if source == "vendedor" else "procesar_cliente")
                    if fn:
                        fn(txt_clean)
                        return {"status": "ok", "processed": txt_clean}

                return {"status": "no_session"}
            except Exception as e:
                print("Error en /api/traductor/speech_input:", e)
                return {"status": "error", "detail": str(e)}

        @app.post("/api/traductor/audio_upload")
        async def api_traductor_audio_upload(request: Request):
            try:
                form = await request.form()
                session_id = form.get("session_id") or ""
                source = form.get("source") or "cliente"
                audio_file = form.get("file")

                if not audio_file:
                    return {"status": "no_audio"}

                audio_bytes = await audio_file.read()
                if not audio_bytes:
                    return {"status": "empty_audio"}

                is_webm = audio_bytes.startswith(b"\x1a\x45\xdf\xa3") or b"webm" in audio_bytes[:100]
                ext = ".webm" if is_webm else ".wav"
                mime = "audio/webm" if is_webm else "audio/wav"

                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(audio_bytes)
                    temp_path = tmp.name

                texto_transcrito = ""
                idioma_detectado = "auto"
                try:
                    gkey = get_groq_api_key_traductor()
                    if gkey:
                        headers = {"Authorization": f"Bearer {gkey}"}
                        with open(temp_path, "rb") as f:
                            files = {"file": (f"traductor_rec{ext}", f, mime)}
                            data = {"model": "whisper-large-v3", "response_format": "verbose_json"}
                            res_w = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=15)
                        if res_w.status_code == 200:
                            w_data = res_w.json()
                            texto_transcrito = w_data.get("text", "").strip()
                            idioma_detectado = w_data.get("language", "auto")
                finally:
                    try: os.unlink(temp_path)
                    except: pass

                if texto_transcrito:
                    sess_handler = TRADUCTOR_SESSIONS.get(session_id)
                    if not sess_handler and TRADUCTOR_SESSIONS:
                        sess_handler = list(TRADUCTOR_SESSIONS.values())[-1]

                    if sess_handler:
                        fn = sess_handler.get("procesar_vendedor" if source == "vendedor" else "procesar_cliente")
                        if fn:
                            fn(texto_transcrito)
                            return {"status": "ok", "text": texto_transcrito, "language": idioma_detectado}

                return {"status": "transcription_failed"}
            except Exception as e_aud:
                print("Error en /api/traductor/audio_upload:", e_aud)
                return {"status": "error", "detail": str(e_aud)}

    except Exception as ex_reg:
        print("Notice registrar_rutas_fastapi_traductor:", ex_reg)

def build_traductor_view(page: ft.Page, user_info=None, conectar_db_fn=None, mostrar_snack_fn=None, start_speak_fn=None):
    """Construye la vista interactiva y aislada del Traductor de Mostrador."""
    registrar_rutas_fastapi_traductor()

    is_mobile = (page.width < 768) if (page.width and page.width > 0) else False
    session_token = getattr(page, "_luxo_token", None) or getattr(page, "session_id", None) or str(time.time())

    vendedor_genero = ["female"]
    idioma_cliente_actual = ["en"]
    grabando_estado = {"vendedor": False, "cliente": False}

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

    def agregar_burbuja_traduccion(origen_lbl, texto_orig, texto_trad, color_accent, icono, lang_code="es", gender="female"):
        def re_escuchar(e):
            reproducir_audio_traduccion_async(texto_trad, lang_code, genero=gender, start_speak_fn=start_speak_fn, page=page)
            if mostrar_snack_fn:
                mostrar_snack_fn("🔊 Reproduciendo audio...", color=color_accent)

        chat_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Text(icono, size=16),
                            ft.Text(origen_lbl, color=color_accent, weight="bold", size=13),
                        ], spacing=6),
                        ft.IconButton(
                            icon=ft.Icons.VOLUME_UP_ROUNDED,
                            icon_color=color_accent,
                            icon_size=18,
                            tooltip="Volver a escuchar pronunciación",
                            on_click=re_escuchar
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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

    def procesar_traduccion_vendedor_texto(texto_directo=None):
        texto = texto_directo if (isinstance(texto_directo, str) and texto_directo.strip()) else txt_input_vendedor.value
        if not texto or not str(texto).strip():
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
                flag_dest = VOCES_NATIVAS_EXTRANJERAS.get(idioma_dest[:2].lower(), {}).get("name", idioma_dest.upper())
                agregar_burbuja_traduccion(
                    f"Vendedor (🇲🇽 Español ➔ {flag_dest})",
                    texto,
                    trad,
                    "#00FFFF",
                    "👤",
                    lang_code=idioma_dest,
                    gender=vendedor_genero[0]
                )
                reproducir_audio_traduccion_async(trad, idioma_dest, genero=vendedor_genero[0], start_speak_fn=start_speak_fn, page=page)
            status_indicator.value = "Listo para traducir"
            status_indicator.color = "#00FFFF"
            try: page.update()
            except: pass

        threading.Thread(target=_task, daemon=True).start()

    def procesar_traduccion_cliente_texto(texto_directo=None):
        texto = texto_directo if (isinstance(texto_directo, str) and texto_directo.strip()) else txt_input_cliente.value
        if not texto or not str(texto).strip():
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
                flag_orig = VOCES_NATIVAS_EXTRANJERAS.get(idioma_orig[:2].lower(), {}).get("name", idioma_orig.upper())
                agregar_burbuja_traduccion(
                    f"Cliente ({flag_orig} ➔ 🇲🇽 Vendedor)",
                    texto,
                    trad,
                    "#D8B4FE",
                    "🕶️",
                    lang_code="es",
                    gender=gen_cliente
                )
                reproducir_audio_traduccion_async(trad, "es", genero=gen_cliente, start_speak_fn=start_speak_fn, page=page)
            status_indicator.value = "Listo para traducir"
            status_indicator.color = "#00FFFF"
            try: page.update()
            except: pass

        threading.Thread(target=_task, daemon=True).start()

    TRADUCTOR_SESSIONS[session_token] = {
        "procesar_vendedor": procesar_traduccion_vendedor_texto,
        "procesar_cliente": procesar_traduccion_cliente_texto,
        "page": page
    }

    # =========================================================================
    # BOTONES DE MICRÓFONO
    # =========================================================================

    btn_mic_vendedor = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.MIC_ROUNDED, color="#00FFFF", size=18),
            ft.Text("Hablar", color="#00FFFF", weight="bold", size=13)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
        bgcolor="#002244",
        padding=ft.Padding(10, 8, 12, 8),
        border_radius=10,
        border=ft.Border.all(1.5, "#00FFFF"),
        tooltip="Presiona para hablar en español por el micrófono",
    )

    btn_mic_cliente = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.MIC_ROUNDED, color="#D8B4FE", size=18),
            ft.Text("Speak", color="#D8B4FE", weight="bold", size=13)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
        bgcolor="#2E0854",
        padding=ft.Padding(10, 8, 12, 8),
        border_radius=10,
        border=ft.Border.all(1.5, "#D8B4FE"),
        tooltip="Click to speak in your native language",
    )

    def set_mic_vendedor_visual(activo: bool):
        grabando_estado["vendedor"] = activo
        if activo:
            btn_mic_vendedor.bgcolor = "#B71C1C"
            btn_mic_vendedor.border = ft.Border.all(2, "#FF5252")
            btn_mic_vendedor.content.controls[0].name = ft.Icons.MIC_EXTERNAL_ON_ROUNDED
            btn_mic_vendedor.content.controls[0].color = "white"
            btn_mic_vendedor.content.controls[1].value = "Escuchando..."
            btn_mic_vendedor.content.controls[1].color = "white"
            status_indicator.value = "🎙️ Escuchando vendedor en español..."
            status_indicator.color = "#FF5252"
        else:
            btn_mic_vendedor.bgcolor = "#002244"
            btn_mic_vendedor.border = ft.Border.all(1.5, "#00FFFF")
            btn_mic_vendedor.content.controls[0].name = ft.Icons.MIC_ROUNDED
            btn_mic_vendedor.content.controls[0].color = "#00FFFF"
            btn_mic_vendedor.content.controls[1].value = "Hablar"
            btn_mic_vendedor.content.controls[1].color = "#00FFFF"
            status_indicator.value = "Listo para traducir"
            status_indicator.color = "#00FFFF"
        try:
            btn_mic_vendedor.update()
            status_indicator.update()
        except: pass

    def set_mic_cliente_visual(activo: bool):
        grabando_estado["cliente"] = activo
        if activo:
            btn_mic_cliente.bgcolor = "#B71C1C"
            btn_mic_cliente.border = ft.Border.all(2, "#FF5252")
            btn_mic_cliente.content.controls[0].name = ft.Icons.MIC_EXTERNAL_ON_ROUNDED
            btn_mic_cliente.content.controls[0].color = "white"
            btn_mic_cliente.content.controls[1].value = "Listening..."
            btn_mic_cliente.content.controls[1].color = "white"
            status_indicator.value = "🎙️ Listening to client voice..."
            status_indicator.color = "#FF5252"
        else:
            btn_mic_cliente.bgcolor = "#2E0854"
            btn_mic_cliente.border = ft.Border.all(1.5, "#D8B4FE")
            btn_mic_cliente.content.controls[0].name = ft.Icons.MIC_ROUNDED
            btn_mic_cliente.content.controls[0].color = "#D8B4FE"
            btn_mic_cliente.content.controls[1].value = "Speak"
            btn_mic_cliente.content.controls[1].color = "#D8B4FE"
            status_indicator.value = "Listo para traducir"
            status_indicator.color = "#00FFFF"
        try:
            btn_mic_cliente.update()
            status_indicator.update()
        except: pass

    def on_mic_vendedor_click(e):
        if grabando_estado["vendedor"]:
            set_mic_vendedor_visual(False)
            if getattr(page, "web", False):
                try:
                    page.launch_url("javascript:if(window.luxoStopTraductorMic) window.luxoStopTraductorMic(); void(0);")
                except: pass
            return

        set_mic_vendedor_visual(True)

        if getattr(page, "web", False):
            js_call = f"""
            (function() {{
                if (window.luxoStartTraductorMic) {{
                    window.luxoStartTraductorMic('vendedor', '{session_token}');
                }}
            }})();
            """
            try:
                page.launch_url(f"javascript:{js_call}")
            except Exception as ex_m:
                print("Notice launch mic vendedor:", ex_m)
        else:
            def _local_speech_vendedor():
                try:
                    import speech_recognition as sr
                    r = sr.Recognizer()
                    r.pause_threshold = 1.0
                    with sr.Microphone() as source:
                        r.adjust_for_ambient_noise(source, duration=0.6)
                        audio = r.listen(source, timeout=6, phrase_time_limit=15)
                        txt = r.recognize_google(audio, language="es-MX")
                        if txt:
                            procesar_traduccion_vendedor_texto(txt)
                except Exception as ex_sr:
                    print("Notice mic local vendedor:", ex_sr)
                finally:
                    set_mic_vendedor_visual(False)

            threading.Thread(target=_local_speech_vendedor, daemon=True).start()

    def on_mic_cliente_click(e):
        if grabando_estado["cliente"]:
            set_mic_cliente_visual(False)
            if getattr(page, "web", False):
                try:
                    page.launch_url("javascript:if(window.luxoStopTraductorMic) window.luxoStopTraductorMic(); void(0);")
                except: pass
            return

        set_mic_cliente_visual(True)

        if getattr(page, "web", False):
            js_call = f"""
            (function() {{
                if (window.luxoStartTraductorMic) {{
                    window.luxoStartTraductorMic('cliente', '{session_token}');
                }}
            }})();
            """
            try:
                page.launch_url(f"javascript:{js_call}")
            except Exception as ex_mc:
                print("Notice launch mic cliente:", ex_mc)
        else:
            def _local_speech_cliente():
                try:
                    import speech_recognition as sr
                    r = sr.Recognizer()
                    r.pause_threshold = 1.2
                    with sr.Microphone() as source:
                        r.adjust_for_ambient_noise(source, duration=0.6)
                        audio = r.listen(source, timeout=6, phrase_time_limit=15)
                        txt = r.recognize_google(audio, language=idioma_cliente_actual[0])
                        if txt:
                            procesar_traduccion_cliente_texto(txt)
                except Exception as ex_cl:
                    print("Notice mic local cliente:", ex_cl)
                finally:
                    set_mic_cliente_visual(False)

            threading.Thread(target=_local_speech_cliente, daemon=True).start()

    btn_mic_vendedor.on_click = on_mic_vendedor_click
    btn_mic_cliente.on_click = on_mic_cliente_click

    txt_input_vendedor.on_submit = lambda e: procesar_traduccion_vendedor_texto()
    txt_input_cliente.on_submit = lambda e: procesar_traduccion_cliente_texto()

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
            "Traductor de mostrador listo. Puedes hablar o escribir.",
            "Counter interpreter ready. You can speak or type in any language.",
            "#00FFFF",
            "✨",
            lang_code="en"
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
                btn_mic_vendedor,
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    icon_color="#00FFFF",
                    bgcolor="#003366",
                    tooltip="Traducir al Cliente",
                    on_click=lambda e: procesar_traduccion_vendedor_texto()
                )
            ], spacing=8)
        ], spacing=8),
        bgcolor="#0c0c1a",
        padding=12,
        border_radius=14,
        border=ft.Border.all(1.5, "#00FFFF")
    )

    card_cliente = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("🌍 LADO CLIENTE (Cualquier Idioma)", color="#D8B4FE", weight="bold", size=14),
                ft.Text("✨ Auto-Detección de Idioma y Tono", size=11, color="#aaaaaa")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                txt_input_cliente,
                btn_mic_cliente,
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    icon_color="#D8B4FE",
                    bgcolor="#4A0072",
                    tooltip="Translate to Spanish",
                    on_click=lambda e: procesar_traduccion_cliente_texto()
                )
            ], spacing=8)
        ], spacing=8),
        bgcolor="#0c0c1a",
        padding=12,
        border_radius=14,
        border=ft.Border.all(1.5, "#D8B4FE")
    )

    js_init_traductor_audio = """
    (function() {
        if (window._luxoTraductorInjected) return;
        window._luxoTraductorInjected = true;

        let _tradMediaRecorder = null;
        let _tradAudioChunks = [];
        let _tradAudioStream = null;
        let _tradActiveSource = null;
        let _tradActiveSession = null;
        let _tradTimer = null;

        window.luxoStartTraductorMic = function(source, sessionId) {
            _tradActiveSource = source || 'vendedor';
            _tradActiveSession = sessionId || '';

            let SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (source === 'vendedor' && SR) {
                try {
                    let rec = new SR();
                    rec.lang = 'es-MX';
                    rec.interimResults = false;
                    rec.continuous = false;
                    rec.onresult = function(ev) {
                        let txt = ev.results && ev.results[0] && ev.results[0][0] ? ev.results[0][0].transcript : '';
                        if (txt) {
                            fetch('/api/traductor/speech_input?source=vendedor&session_id=' + encodeURIComponent(_tradActiveSession) + '&text=' + encodeURIComponent(txt), { method: 'POST' });
                        }
                    };
                    rec.onerror = function() {
                        iniciarMediaRecorderTraductor(source, sessionId);
                    };
                    rec.start();
                    return;
                } catch(e) {}
            }

            iniciarMediaRecorderTraductor(source, sessionId);
        };

        function iniciarMediaRecorderTraductor(source, sessionId) {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert('⚠️ Micrófono no soportado en este navegador.');
                return;
            }

            navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
                _tradAudioStream = stream;
                _tradAudioChunks = [];
                let mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported('audio/webm')) {
                    mimeType = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '';
                }

                _tradMediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType: mimeType }) : new MediaRecorder(stream);
                _tradMediaRecorder.ondataavailable = function(e) {
                    if (e.data && e.data.size > 0) _tradAudioChunks.push(e.data);
                };

                _tradMediaRecorder.onstop = function() {
                    if (_tradAudioStream) {
                        _tradAudioStream.getTracks().forEach(function(t) { t.stop(); });
                        _tradAudioStream = null;
                    }
                    if (_tradAudioChunks.length > 0) {
                        const blob = new Blob(_tradAudioChunks, { type: mimeType || 'audio/webm' });
                        const fd = new FormData();
                        fd.append('file', blob, 'traductor_rec.webm');
                        fd.append('source', _tradActiveSource || 'cliente');
                        fd.append('session_id', _tradActiveSession || '');

                        fetch('/api/traductor/audio_upload', {
                            method: 'POST',
                            body: fd
                        }).catch(function(err) { console.log('[TRADUCTOR UPLOAD ERR]', err); });
                    }
                };

                _tradMediaRecorder.start();

                if (_tradTimer) clearTimeout(_tradTimer);
                _tradTimer = setTimeout(function() {
                    window.luxoStopTraductorMic();
                }, 7000);

            }).catch(function(err) {
                console.log('[TRADUCTOR MIC ERR]', err);
                if (err.name === 'NotAllowedError') {
                    alert('⚠️ Permite el acceso al micrófono en tu navegador para usar el traductor.');
                }
            });
        }

        window.luxoStopTraductorMic = function() {
            if (_tradTimer) clearTimeout(_tradTimer);
            if (_tradMediaRecorder && _tradMediaRecorder.state === 'recording') {
                try { _tradMediaRecorder.stop(); } catch(e){}
            }
        };
    })();
    """

    if getattr(page, "web", False):
        try:
            page.launch_url(f"javascript:{js_init_traductor_audio}")
        except: pass

    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.TRANSLATE_ROUNDED, color="#00FFFF", size=26),
            ft.Text("TRADUCTOR DE MOSTRADOR LUXO", size=20 if is_mobile else 22, color="white", weight="bold"),
            ft.Container(expand=True),
            status_indicator,
            btn_limpiar
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("Traducción inteligente bidireccional por voz y texto con auto-detección de idioma y pronunciación nativa.", size=12, color="#888899"),
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
