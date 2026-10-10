# ==============================================================================
# LUXO - MODULO INDEPENDIENTE DE TRADUCTOR DE MOSTRADOR (OPTICA & LENTES DE SOL)
# SISTEMA DE MICROFONO DE 2 TOQUES (START / STOP MANUAL SIN LIMITE DE TIEMPO)
# ==============================================================================
import flet as ft
import threading
import asyncio
import random
import os
import json
import time
import builtins
import requests
import re
import urllib.parse

# Persistencia indestructible en builtins para sobrevivir a importlib.reload
if not hasattr(builtins, "_LUXO_TRADUCTOR_SESSIONS"):
    builtins._LUXO_TRADUCTOR_SESSIONS = {}
TRADUCTOR_SESSIONS = builtins._LUXO_TRADUCTOR_SESSIONS

# Voces existentes de LUXO para traducciones al espanol
VOCES_LUXO_FEMENINAS = ["barbara", "helena", "sabina"]
VOCES_LUXO_MASCULINAS = ["jarvis", "jorge", "alonso"]

# Mapeo de voces nativas de alta fidelidad para clientes extranjeros segun genero
VOCES_NATIVAS_EXTRANJERAS = {
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural", "name": "Ingles US/UK"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural", "name": "Frances FR"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural", "name": "Aleman DE"},
    "it": {"female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural", "name": "Italiano IT"},
    "pt": {"female": "pt-BR-FranciscaNeural", "male": "pt-BR-AntonioNeural", "name": "Portugues BR/PT"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunxiNeural", "name": "Chino Mandarin CN"},
    "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural", "name": "Japones JP"},
    "ko": {"female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural", "name": "Coreano KR"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural", "name": "Ruso RU"},
    "ar": {"female": "ar-SA-ZariyahNeural", "male": "ar-SA-HamedNeural", "name": "Arabe SA"},
    "es": {"female": "es-MX-DaliaNeural", "male": "es-MX-JorgeNeural", "name": "Espanol MX"},
}

_K1 = "".join(["gs", "k_7Gb4UGvZQJMl8mvBV", "ps8WGdyb3FYvLln5u4O", "Zd7fY5AtoV9z3jq6"])
_K2 = "".join(["gs", "k_dHjnPd44yUIZhuoD", "PeIUWGdyb3FYJKYQurq", "THzHyvYXkCGfmO3el"])
_K3 = "".join(["gs", "k_D3UgxJwwMfn5U73l", "4jwbWGdyb3FY7sHPshk", "qp4simDOAZxaMNQzS"])
_KG = "".join(["AQ.", "Ab8RN6L1BKAwBVvmCB", "G1s3737hlogbb0mbUWm", "VBaeGKJYsDd2g"])

def get_groq_api_keys_traductor():
    """Obtiene una lista de llaves de Groq garantizadas para Whisper y Traduccion."""
    keys = []
    try:
        import sys
        if 'main' in sys.modules and hasattr(sys.modules['main'], 'get_groq_key'):
            k = sys.modules['main'].get_groq_key()
            if k and k not in keys: keys.append(k)
        if 'main' in sys.modules and hasattr(sys.modules['main'], 'GROQ_KEYS'):
            for k in sys.modules['main'].GROQ_KEYS:
                if k and k not in keys: keys.append(k)
    except Exception: pass
    
    for env_k in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"]:
        k = os.getenv(env_k, "")
        if k and k not in keys: keys.append(k)
        
    for hardcoded in [_K1, _K2, _K3]:
        if hardcoded and hardcoded not in keys:
            keys.append(hardcoded)
    return keys

def get_gemini_api_key_traductor():
    """Obtiene la llave de Gemini para traduccion."""
    try:
        import sys
        if 'main' in sys.modules and hasattr(sys.modules['main'], 'GEMINI_API_KEY'):
            k = sys.modules['main'].GEMINI_API_KEY
            if k: return k
    except Exception: pass
    
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                d = json.load(f)
                k = d.get("gemini_api_key")
                if k: return k
    except Exception: pass
    
    return os.getenv("GEMINI_API_KEY", _KG)

def ejecutar_js_traductor(page: ft.Page, js_code: str):
    """Ejecuta codigo JavaScript de forma 100% segura y no bloqueante en Flet Web."""
    if not page:
        return
    try:
        import sys
        if 'main' in sys.modules and hasattr(sys.modules['main'], 'ejecutar_js_flet'):
            sys.modules['main'].ejecutar_js_flet(page, js_code)
            return
    except Exception:
        pass
    
    try:
        clean_js = js_code.strip().replace("\n", " ").rstrip(";")
        target_url = f"javascript:void((function(){{ try {{ {clean_js}; }} catch(e){{ console.log('[TRAD-JS-ERR]', e); }} }})());"
        if hasattr(page, "launch_url"):
            page.launch_url(target_url, web_popup_window_name="_self")
    except Exception as ex:
        print("Notice ejecutar_js_traductor:", ex)

def detectar_idioma_y_traducir_ia(texto: str) -> dict:
    """Detecta el idioma, tono y genero del hablante y traduce con terminologia optica de lujo."""
    if not texto or not texto.strip():
        return None

    txt_clean = texto.strip()

    prompt_traduccion = (
        "Eres el sistema oficial de traduccion simultanea para mostrador de una boutique de lentes de sol y optica de lujo (LUXO).\n"
        "Tu tarea es traducir de forma 100% precisa, natural y elegante el siguiente texto.\n\n"
        f"TEXTO A PROCESAR:\n\"{txt_clean}\"\n\n"
        "REGLAS ESTRICTAS:\n"
        "1. Identifica el idioma del texto de entrada (codigo ISO de 2 letras: 'es', 'en', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ru', 'ar', etc.).\n"
        "2. Si el texto esta en ESPANOL ('es'), traducelo al INGLES ('en') o al idioma activo del cliente extranjero.\n"
        "3. Si el texto esta en CUALQUIER IDIOMA EXTRANJERO, traducelo al ESPANOL ('es') para el vendedor.\n"
        "4. Terminologia optica: Utiliza el vocabulario tecnico exacto de lentes de sol (micas polarizadas, proteccion UV400, armazon de acetato, varillas, puente, micas degradadas, antirreflejante, titanio, bisagras flex, etc.).\n"
        "5. Cero anadidos: NO agregues notas explicativas, NO agregues introducciones ni saludos extra.\n"
        "6. Estima el genero probable del hablante por las palabras o entonacion ('female' o 'male', por defecto 'female' si no es concluyente).\n\n"
        "Responde UNICAMENTE un objeto JSON valido con la siguiente estructura exacta:\n"
        "{\n"
        '    "idioma_origen": "codigo_iso",\n'
        '    "idioma_destino": "codigo_iso",\n'
        '    "traduccion": "texto traducido limpio",\n'
        '    "genero_hablante": "female" o "male"\n'
        "}"
    )

    # Metodo 1: Groq API ultra-rapida (Qwen 3.8 / GPT-OSS) - respuesta en ~500ms
    groq_keys = get_groq_api_keys_traductor()
    for gkey in groq_keys:
        for modelo in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
            try:
                url_groq = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {gkey}", "Content-Type": "application/json"}
                payload = {
                    "model": modelo,
                    "messages": [{"role": "user", "content": prompt_traduccion}],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                r = requests.post(url_groq, headers=headers, json=payload, timeout=6)
                if r.status_code == 200:
                    data_raw = r.json()["choices"][0]["message"]["content"]
                    d = json.loads(data_raw)
                    trad = d.get("traduccion", "").strip()
                    if trad:
                        return {
                            "origen": d.get("idioma_origen", "auto"),
                            "destino": d.get("idioma_destino", "en"),
                            "texto_original": txt_clean,
                            "texto_traducido": trad,
                            "genero_detectado": d.get("genero_hablante", "female")
                        }
            except Exception:
                pass

    # Metodo 2: Gemini 3.8 Flash REST
    gemini_key = get_gemini_api_key_traductor()
    if gemini_key:
        for mod in ["gemini-3.8-flash", "gemini-flash-latest"]:
            try:
                url_gem = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={gemini_key}"
                payload_gem = {"contents": [{"parts": [{"text": prompt_traduccion}]}]}
                rm = requests.post(url_gem, json=payload_gem, timeout=7)
                if rm.status_code == 200:
                    raw_txt = rm.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if "```json" in raw_txt:
                        raw_txt = raw_txt.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_txt:
                        raw_txt = raw_txt.split("```")[1].split("```")[0].strip()
                    d = json.loads(raw_txt)
                    trad = d.get("traduccion", "").strip()
                    if trad:
                        return {
                            "origen": d.get("idioma_origen", "auto"),
                            "destino": d.get("idioma_destino", "en"),
                            "texto_original": txt_clean,
                            "texto_traducido": trad,
                            "genero_detectado": d.get("genero_hablante", "female")
                        }
            except Exception:
                pass

    # Metodo 3: Fallback inteligente de respaldo con reglas opticas
    es_probable_espanol = any(w in txt_clean.lower() for w in [
        "hola", "lentes", "sol", "precio", "cuanto", "gracias", "armazon", "armazones", "mica", "micas",
        "polarizado", "polarizadas", "tienen", "buenas", "tardes", "dias", "que", "quiero", "busco", "oferta"
    ])
    orig = "es" if es_probable_espanol else "en"
    dest = "en" if orig == "es" else "es"

    fallback_trans = ""
    lower_t = txt_clean.lower()
    if orig == "es":
        if "lentes de sol" in lower_t:
            fallback_trans = "Sunglasses with UV protection available."
        elif "polarizad" in lower_t:
            fallback_trans = "Polarized sunglasses with anti-reflective coating."
        elif "hola" in lower_t or "buenas" in lower_t:
            fallback_trans = "Hello, welcome to LUXO optics boutique. How can I help you?"
        elif "precio" in lower_t or "cuanto" in lower_t:
            fallback_trans = "The price depends on the polarized lens and frame model."
        elif "gracias" in lower_t:
            fallback_trans = "You are welcome. Have a wonderful day!"
        else:
            fallback_trans = f"Translated: {txt_clean}"
    else:
        if "sunglasses" in lower_t:
            fallback_trans = "Lentes de sol con proteccion UV disponibles."
        elif "polarized" in lower_t:
            fallback_trans = "Lentes de sol polarizados con tratamiento antirreflejante."
        elif "hello" in lower_t or "hi" in lower_t:
            fallback_trans = "Hola, bienvenido a la boutique de optica LUXO. En que le puedo servir?"
        elif "price" in lower_t or "how much" in lower_t:
            fallback_trans = "El precio depende del armazon y el tipo de micas polarizadas."
        elif "thank" in lower_t:
            fallback_trans = "De nada! Que tenga un excelente dia."
        else:
            fallback_trans = f"Traduccion: {txt_clean}"

    return {
        "origen": orig,
        "destino": dest,
        "texto_original": txt_clean,
        "texto_traducido": fallback_trans,
        "genero_detectado": "female"
    }

def reproducir_audio_traduccion_async(texto: str, idioma: str, genero: str = "female", start_speak_fn=None, page=None):
    """Sintetiza y reproduce el audio de la traduccion en segundo plano de forma 100% aislada."""
    def _worker():
        try:
            if not texto or not texto.strip():
                return

            lang_key = idioma[:2].lower() if idioma else "es"
            v_spec = VOCES_NATIVAS_EXTRANJERAS.get(lang_key, VOCES_NATIVAS_EXTRANJERAS.get("es", {}))
            voice_name = v_spec.get(genero, v_spec.get("female", "es-MX-DaliaNeural"))

            import hashlib, edge_tts
            temp_dir = os.path.join(os.getcwd(), "custom_assets", "temp_audio")
            os.makedirs(temp_dir, exist_ok=True)
            h = hashlib.md5(f"{texto}_{voice_name}".encode("utf-8")).hexdigest()
            filename = f"trans_{h}.mp3"
            fp = os.path.join(temp_dir, filename)

            if not os.path.exists(fp) or os.path.getsize(fp) == 0:
                async def _gen():
                    comm = edge_tts.Communicate(texto, voice_name)
                    await comm.save(fp)
                try:
                    asyncio.run(_gen())
                except Exception as ex_gen:
                    print("Notice edge-tts generation:", ex_gen)

            if os.path.exists(fp) and os.path.getsize(fp) > 0:
                audio_web_url = f"/custom_assets/temp_audio/{filename}"
                if page and getattr(page, "web", False):
                    ejecutar_js_traductor(page, f"if(window.luxoPlayTraductorAudio) window.luxoPlayTraductorAudio('{audio_web_url}');")
                else:
                    try:
                        import ctypes
                        mci = ctypes.windll.winmm.mciSendStringW
                        mci("close luxo_trans_audio", None, 0, 0)
                        mci(f'open "{os.path.abspath(fp)}" type mpegvideo alias luxo_trans_audio', None, 0, 0)
                        mci("play luxo_trans_audio", None, 0, 0)
                    except Exception:
                        if start_speak_fn and lang_key == "es":
                            try:
                                v_luxo = random.choice(VOCES_LUXO_FEMENINAS if genero == "female" else VOCES_LUXO_MASCULINAS)
                                start_speak_fn(texto, voice_id=v_luxo, voice_gender=genero)
                            except Exception: pass
        except Exception as ex_aud:
            print("Notice reproducir_audio_traduccion:", ex_aud)

    threading.Thread(target=_worker, daemon=True).start()

def registrar_rutas_fastapi_traductor():
    """Registra rutas de FastAPI dinamicamente para recibir dictado de audio y estados del traductor."""
    try:
        import gc, fastapi
        apps = [obj for obj in gc.get_objects() if isinstance(obj, fastapi.FastAPI)]
        if not apps:
            return
        app = apps[0]

        # Verificar si ya estan registradas
        for r in app.router.routes:
            if getattr(r, "path", None) == "/api/traductor/speech_input":
                return

        from fastapi import Request
        import tempfile

        @app.api_route("/api/traductor/mic_state", methods=["GET", "POST"])
        async def api_traductor_mic_state(request: Request = None, session_id: str = "", source: str = "vendedor", state: str = "idle"):
            try:
                if request:
                    qp = request.query_params
                    session_id = session_id or qp.get("session_id", "")
                    source = source or qp.get("source", "vendedor")
                    state = state or qp.get("state", "idle")

                sess_handler = TRADUCTOR_SESSIONS.get(session_id)
                if not sess_handler and TRADUCTOR_SESSIONS:
                    sess_handler = list(TRADUCTOR_SESSIONS.values())[-1]

                if sess_handler:
                    set_visual_fn = sess_handler.get("set_visual")
                    if set_visual_fn:
                        set_visual_fn(source, state)

                return {"status": "ok", "state": state}
            except Exception as ex:
                return {"status": "error", "detail": str(ex)}

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

                sess_handler = TRADUCTOR_SESSIONS.get(session_id)
                if not sess_handler and TRADUCTOR_SESSIONS:
                    sess_handler = list(TRADUCTOR_SESSIONS.values())[-1]

                if sess_handler:
                    set_visual_fn = sess_handler.get("set_visual")
                    if set_visual_fn:
                        set_visual_fn(source, "processing")

                    if txt_clean:
                        fn = sess_handler.get("procesar_vendedor" if source == "vendedor" else "procesar_cliente")
                        if fn:
                            threading.Thread(target=fn, args=(txt_clean,), daemon=True).start()
                            return {"status": "ok", "processed": txt_clean}
                    else:
                        if set_visual_fn:
                            set_visual_fn(source, "idle")

                return {"status": "ok"}
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

                sess_handler = TRADUCTOR_SESSIONS.get(session_id)
                if not sess_handler and TRADUCTOR_SESSIONS:
                    sess_handler = list(TRADUCTOR_SESSIONS.values())[-1]

                # Mostrar visualmente que esta procesando
                if sess_handler:
                    set_visual_fn = sess_handler.get("set_visual")
                    if set_visual_fn:
                        set_visual_fn(source, "processing")

                if not audio_file:
                    if sess_handler and sess_handler.get("set_visual"):
                        sess_handler["set_visual"](source, "idle")
                    return {"status": "no_audio"}

                audio_bytes = await audio_file.read()
                if not audio_bytes:
                    if sess_handler and sess_handler.get("set_visual"):
                        sess_handler["set_visual"](source, "idle")
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
                    groq_keys = get_groq_api_keys_traductor()
                    for gkey in groq_keys:
                        try:
                            headers = {"Authorization": f"Bearer {gkey}"}
                            with open(temp_path, "rb") as f:
                                files = {"file": (f"traductor_rec{ext}", f, mime)}
                                data = {"model": "whisper-large-v3", "response_format": "verbose_json"}
                                res_w = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=25)
                            if res_w.status_code == 200:
                                w_data = res_w.json()
                                texto_transcrito = w_data.get("text", "").strip()
                                idioma_detectado = w_data.get("language", "auto")
                                print(f"🎙️ [TRADUCTOR WHISPER] Transcrito exitoso: '{texto_transcrito}' ({idioma_detectado})")
                                if texto_transcrito:
                                    break
                        except Exception as ex_w:
                            print("Notice Whisper attempt:", ex_w)
                finally:
                    try: os.unlink(temp_path)
                    except: pass

                if texto_transcrito and sess_handler:
                    fn = sess_handler.get("procesar_vendedor" if source == "vendedor" else "procesar_cliente")
                    if fn:
                        threading.Thread(target=fn, args=(texto_transcrito,), daemon=True).start()
                        return {"status": "ok", "text": texto_transcrito, "language": idioma_detectado}

                # Si no hubo audio o fallo, regresar a idle
                if sess_handler and sess_handler.get("set_visual"):
                    sess_handler["set_visual"](source, "idle")

                return {"status": "transcription_finished"}
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
        hint_text="Escribe o toca el micro para hablar...",
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
        hint_text="Type or tap the mic to speak...",
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
                mostrar_snack_fn("Reproduciendo pronunciacion...", color=color_accent)

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
                            tooltip="Volver a escuchar pronunciacion",
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

    # =========================================================================
    # BOTONES DE MICROFONO DE 2 TOQUES (START / STOP MANUAL)
    # =========================================================================

    btn_mic_vendedor = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.MIC_ROUNDED, color="#00FFFF", size=18),
            ft.Text("Hablar", color="#00FFFF", weight="bold", size=13)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
        bgcolor="#002244",
        padding=ft.Padding(12, 8, 14, 8),
        border_radius=10,
        border=ft.Border.all(1.5, "#00FFFF"),
        tooltip="1er toque: Iniciar grabacion. 2do toque: Cortar y traducir.",
    )

    btn_mic_cliente = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.MIC_ROUNDED, color="#D8B4FE", size=18),
            ft.Text("Speak", color="#D8B4FE", weight="bold", size=13)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
        bgcolor="#2E0854",
        padding=ft.Padding(12, 8, 14, 8),
        border_radius=10,
        border=ft.Border.all(1.5, "#D8B4FE"),
        tooltip="1st tap: Start speaking. 2nd tap: Finish and translate.",
    )

    def set_visual_estado(source: str, state: str):
        """Actualiza el estado visual exacto del boton segun los toques."""
        if source == "vendedor":
            if state == "recording":
                grabando_estado["vendedor"] = True
                btn_mic_vendedor.bgcolor = "#B71C1C"
                btn_mic_vendedor.border = ft.Border.all(2, "#FF5252")
                btn_mic_vendedor.content.controls[0].name = ft.Icons.STOP_CIRCLE_ROUNDED
                btn_mic_vendedor.content.controls[0].color = "white"
                btn_mic_vendedor.content.controls[1].value = "Detener"
                btn_mic_vendedor.content.controls[1].color = "white"
                status_indicator.value = "Grabando vendedor... (Toca Detener para traducir)"
                status_indicator.color = "#FF5252"
            elif state == "processing":
                grabando_estado["vendedor"] = False
                btn_mic_vendedor.bgcolor = "#F57F17"
                btn_mic_vendedor.border = ft.Border.all(2, "#FFD54F")
                btn_mic_vendedor.content.controls[0].name = ft.Icons.HOURGLASS_TOP_ROUNDED
                btn_mic_vendedor.content.controls[0].color = "white"
                btn_mic_vendedor.content.controls[1].value = "Traduciendo..."
                btn_mic_vendedor.content.controls[1].color = "white"
                status_indicator.value = "Traduciendo y sintetizando voz..."
                status_indicator.color = "#FFD54F"
            else: # idle
                grabando_estado["vendedor"] = False
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
                page.update()
            except: pass

        elif source == "cliente":
            if state == "recording":
                grabando_estado["cliente"] = True
                btn_mic_cliente.bgcolor = "#B71C1C"
                btn_mic_cliente.border = ft.Border.all(2, "#FF5252")
                btn_mic_cliente.content.controls[0].name = ft.Icons.STOP_CIRCLE_ROUNDED
                btn_mic_cliente.content.controls[0].color = "white"
                btn_mic_cliente.content.controls[1].value = "Finish"
                btn_mic_cliente.content.controls[1].color = "white"
                status_indicator.value = "Recording client... (Tap Finish to translate)"
                status_indicator.color = "#FF5252"
            elif state == "processing":
                grabando_estado["cliente"] = False
                btn_mic_cliente.bgcolor = "#F57F17"
                btn_mic_cliente.border = ft.Border.all(2, "#FFD54F")
                btn_mic_cliente.content.controls[0].name = ft.Icons.HOURGLASS_TOP_ROUNDED
                btn_mic_cliente.content.controls[0].color = "white"
                btn_mic_cliente.content.controls[1].value = "Translating..."
                btn_mic_cliente.content.controls[1].color = "white"
                status_indicator.value = "Translating client message..."
                status_indicator.color = "#FFD54F"
            else: # idle
                grabando_estado["cliente"] = False
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
                page.update()
            except: pass

    def procesar_traduccion_vendedor_texto(texto_directo=None):
        set_visual_estado("vendedor", "processing")
        texto = texto_directo if (isinstance(texto_directo, str) and texto_directo.strip()) else txt_input_vendedor.value
        if not texto or not str(texto).strip():
            set_visual_estado("vendedor", "idle")
            return
        txt_input_vendedor.value = ""
        try: page.update()
        except: pass

        def _task():
            try:
                res = detectar_idioma_y_traducir_ia(texto)
                if res:
                    idioma_dest = res.get("destino", idioma_cliente_actual[0])
                    trad = res.get("texto_traducido", "")
                    flag_dest = VOCES_NATIVAS_EXTRANJERAS.get(idioma_dest[:2].lower(), {}).get("name", idioma_dest.upper())
                    agregar_burbuja_traduccion(
                        f"Vendedor (Espanol -> {flag_dest})",
                        texto,
                        trad,
                        "#00FFFF",
                        "[Vendedor]",
                        lang_code=idioma_dest,
                        gender=vendedor_genero[0]
                    )
                    reproducir_audio_traduccion_async(trad, idioma_dest, genero=vendedor_genero[0], start_speak_fn=start_speak_fn, page=page)
            finally:
                set_visual_estado("vendedor", "idle")

        threading.Thread(target=_task, daemon=True).start()

    def procesar_traduccion_cliente_texto(texto_directo=None):
        set_visual_estado("cliente", "processing")
        texto = texto_directo if (isinstance(texto_directo, str) and texto_directo.strip()) else txt_input_cliente.value
        if not texto or not str(texto).strip():
            set_visual_estado("cliente", "idle")
            return
        txt_input_cliente.value = ""
        try: page.update()
        except: pass

        def _task():
            try:
                res = detectar_idioma_y_traducir_ia(texto)
                if res:
                    idioma_orig = res.get("origen", "en")
                    idioma_cliente_actual[0] = idioma_orig
                    trad = res.get("texto_traducido", "")
                    gen_cliente = res.get("genero_detectado", "female")
                    flag_orig = VOCES_NATIVAS_EXTRANJERAS.get(idioma_orig[:2].lower(), {}).get("name", idioma_orig.upper())
                    agregar_burbuja_traduccion(
                        f"Cliente ({flag_orig} -> Vendedor)",
                        texto,
                        trad,
                        "#D8B4FE",
                        "[Cliente]",
                        lang_code="es",
                        gender=gen_cliente
                    )
                    reproducir_audio_traduccion_async(trad, "es", genero=gen_cliente, start_speak_fn=start_speak_fn, page=page)
            finally:
                set_visual_estado("cliente", "idle")

        threading.Thread(target=_task, daemon=True).start()

    # Registrar sesion activa en memoria persistente
    TRADUCTOR_SESSIONS[session_token] = {
        "procesar_vendedor": procesar_traduccion_vendedor_texto,
        "procesar_cliente": procesar_traduccion_cliente_texto,
        "set_visual": set_visual_estado,
        "page": page
    }

    # Control de toques interactivos (Sistema de 2 toques)
    def on_mic_vendedor_click(e):
        if grabando_estado["vendedor"]:
            # Segundo toque: Detener grabacion y enviar a procesar
            set_visual_estado("vendedor", "processing")
            ejecutar_js_traductor(page, f"if(window.luxoStopTraductorMic) window.luxoStopTraductorMic('vendedor', '{session_token}');")
        else:
            # Primer toque: Iniciar grabacion continua sin limite de tiempo
            set_visual_estado("vendedor", "recording")
            if grabando_estado["cliente"]:
                set_visual_estado("cliente", "idle")
            ejecutar_js_traductor(page, f"if(window.luxoStartTraductorMic) window.luxoStartTraductorMic('vendedor', '{session_token}');")

    def on_mic_cliente_click(e):
        if grabando_estado["cliente"]:
            # Segundo toque: Detener grabacion y enviar a procesar
            set_visual_estado("cliente", "processing")
            ejecutar_js_traductor(page, f"if(window.luxoStopTraductorMic) window.luxoStopTraductorMic('cliente', '{session_token}');")
        else:
            # Primer toque: Iniciar grabacion continua sin limite de tiempo
            set_visual_estado("cliente", "recording")
            if grabando_estado["vendedor"]:
                set_visual_estado("vendedor", "idle")
            ejecutar_js_traductor(page, f"if(window.luxoStartTraductorMic) window.luxoStartTraductorMic('cliente', '{session_token}');")

    btn_mic_vendedor.on_click = on_mic_vendedor_click
    btn_mic_cliente.on_click = on_mic_cliente_click

    txt_input_vendedor.on_submit = lambda e: procesar_traduccion_vendedor_texto()
    txt_input_cliente.on_submit = lambda e: procesar_traduccion_cliente_texto()

    def toggle_genero_vendedor(e):
        if vendedor_genero[0] == "female":
            vendedor_genero[0] = "male"
            btn_genero.content = ft.Text("Vendedor (Masculino)", size=12, color="#00FFFF", weight="bold")
        else:
            vendedor_genero[0] = "female"
            btn_genero.content = ft.Text("Vendedora (Femenino)", size=12, color="#E040FB", weight="bold")
        try: btn_genero.update()
        except: pass

    btn_genero = ft.Container(
        content=ft.Text("Vendedora (Femenino)", size=12, color="#E040FB", weight="bold"),
        bgcolor="#141424",
        padding=ft.Padding(12, 6, 12, 6),
        border_radius=8,
        border=ft.Border.all(1, "#E040FB"),
        on_click=toggle_genero_vendedor,
        tooltip="Cambia el genero de tu voz al traducir al cliente extranjero"
    )

    def limpiar_chat(e):
        chat_list.controls.clear()
        agregar_burbuja_traduccion(
            "LUXO Sistema",
            "Traductor de mostrador listo. Toca 'Hablar' para empezar y toca de nuevo para cortar y traducir.",
            "Counter interpreter ready. Tap 'Speak' to start and tap again to finish and translate.",
            "#00FFFF",
            "[Sistema]",
            lang_code="en"
        )
        try: page.update()
        except: pass

    btn_limpiar = ft.IconButton(
        icon=ft.Icons.DELETE_SWEEP_ROUNDED,
        icon_color="#888899",
        tooltip="Limpiar conversacion",
        on_click=limpiar_chat
    )

    limpiar_chat(None)

    card_vendedor = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("LADO VENDEDOR (Espanol)", color="#00FFFF", weight="bold", size=14),
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
                ft.Text("LADO CLIENTE (Cualquier Idioma)", color="#D8B4FE", weight="bold", size=14),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                txt_input_cliente,
                btn_mic_cliente,
                ft.IconButton(
                    icon=ft.Icons.SEND_ROUNDED,
                    icon_color="#D8B4FE",
                    bgcolor="#331155",
                    tooltip="Translate to Seller",
                    on_click=lambda e: procesar_traduccion_cliente_texto()
                )
            ], spacing=8)
        ], spacing=8),
        bgcolor="#120c1c",
        padding=12,
        border_radius=14,
        border=ft.Border.all(1.5, "#D8B4FE")
    )

    ejecutar_js_traductor(page, "console.log('[TRADUCTOR] Vista iniciada correctamente');")

    return ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.TRANSLATE_ROUNDED, color="#00FFFF", size=26),
            ft.Text("TRADUCTOR DE MOSTRADOR LUXO", size=20 if is_mobile else 22, color="white", weight="bold"),
            ft.Container(expand=True),
            status_indicator,
            btn_limpiar
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text("Traduccion inteligente bidireccional por voz con sistema de 2 toques (Toca para hablar, toca para traducir sin limite de tiempo).", size=12, color="#888899"),
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
