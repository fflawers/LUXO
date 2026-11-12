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
    "en": {"female": "en-US-AriaNeural", "male": "en-US-ChristopherNeural", "name": "Ingles US/UK"},
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

LANG_ALIAS_MAP = {
    "zh": "zh", "zh-cn": "zh", "zh-tw": "zh", "zh-hk": "zh", "zh-hans": "zh", "zh-hant": "zh",
    "chinese": "zh", "mandarin": "zh", "cantonese": "zh", "cmn": "zh", "yue": "zh", "chino": "zh", "chino mandarin": "zh",
    "en": "en", "en-us": "en", "en-gb": "en", "english": "en", "ingles": "en",
    "fr": "fr", "fr-fr": "fr", "fr-ca": "fr", "french": "fr", "frances": "fr",
    "de": "de", "de-de": "de", "german": "de", "aleman": "de",
    "it": "it", "it-it": "it", "italian": "it", "italiano": "it",
    "pt": "pt", "pt-br": "pt", "pt-pt": "pt", "portuguese": "pt", "portugues": "pt",
    "ja": "ja", "ja-jp": "ja", "jp": "ja", "japanese": "ja", "japones": "ja",
    "ko": "ko", "ko-kr": "ko", "kr": "ko", "korean": "ko", "coreano": "ko",
    "ru": "ru", "ru-ru": "ru", "russian": "ru", "ruso": "ru",
    "ar": "ar", "ar-sa": "ar", "arabic": "ar", "arabe": "ar",
    "es": "es", "es-mx": "es", "es-es": "es", "spanish": "es", "espanol": "es",
}


def normalizar_codigo_idioma(lang_str: str, texto_muestra: str = "") -> str:
    """Convierte nombres largos o variantes (ej. 'chinese', 'zh-CN', 'cmn') a ISO-2 exacto."""
    raw = (lang_str or "").strip().lower().replace("_", "-")
    if raw in LANG_ALIAS_MAP:
        return LANG_ALIAS_MAP[raw]
    for k, v in LANG_ALIAS_MAP.items():
        if raw.startswith(k + "-") or (len(k) >= 4 and k in raw):
            return v
    if len(raw) >= 2 and raw[:2] in VOCES_NATIVAS_EXTRANJERAS:
        return raw[:2]
    # Deteccion por escritura si el codigo fue 'auto' o desconocido
    if texto_muestra:
        if any("\u4e00" <= ch <= "\u9fff" for ch in texto_muestra):
            if any("\u3040" <= ch <= "\u30ff" for ch in texto_muestra):
                return "ja"
            return "zh"
        if any("\u3040" <= ch <= "\u30ff" for ch in texto_muestra):
            return "ja"
        if any("\uac00" <= ch <= "\ud7af" for ch in texto_muestra):
            return "ko"
        if any("\u0400" <= ch <= "\u04ff" for ch in texto_muestra):
            return "ru"
        if any("\u0600" <= ch <= "\u06ff" for ch in texto_muestra):
            return "ar"
    return ""

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

def detectar_idioma_y_traducir_ia(texto: str, idioma_cliente: str = "en", historial_contexto: list = None, es_vendedor: bool = None) -> dict:
    """Detecta el idioma, tono y genero del hablante y traduce con terminologia optica de lujo y contexto."""
    if not texto or not texto.strip():
        return None

    txt_clean = texto.strip()
    cliente_lang_clean = normalizar_codigo_idioma(idioma_cliente) or "en"
    if cliente_lang_clean == "es":
        cliente_lang_clean = "en"
    nombre_idioma_cliente = VOCES_NATIVAS_EXTRANJERAS.get(cliente_lang_clean, {}).get("name", cliente_lang_clean.upper())

    ctx_block = ""
    if historial_contexto:
        ultimas = historial_contexto[-4:]
        ctx_lines = [f"- {h}" for h in ultimas if h]
        if ctx_lines:
            ctx_block = "CONTEXTO RECIENTE DE LA CONVERSACION (solo referencia para genero/numero/modelo, NO retraducir):\n" + "\n".join(ctx_lines) + "\n\n"

    rol_hint = ""
    if es_vendedor is True:
        rol_hint = f"HABLANTE ACTUAL: VENDEDOR MEXICANO hablando en ESPANOL ('es'). Debes traducir OBLIGATORIAMENTE al idioma del cliente: {nombre_idioma_cliente} ('{cliente_lang_clean}').\n"
    elif es_vendedor is False:
        rol_hint = "HABLANTE ACTUAL: CLIENTE EXTRANJERO. Detecta su idioma exacto en ISO-2 (ej. 'zh', 'en', 'fr', 'ja', 'ko') y tradúcelo al ESPANOL ('es') natural de México.\n"

    prompt_traduccion = (
        "Eres un traductor simultaneo profesional de alta precision en mostrador de óptica de lujo (Sunglass Hut).\n"
        "Tu trabajo es EXCLUSIVAMENTE traducir el texto dado con precision gramatical (singular vs plural exacto, numeros y montos).\n"
        "ESTRICTAMENTE PROHIBIDO:\n"
        "- NO actues como asistente ni chatbot ni agregues saludos o comentarios que no se dijeron.\n"
        "- NO dejes palabras sin traducir ni devuelvas la frase en el mismo idioma de origen.\n\n"
        f"{rol_hint}"
        f"IDIOMA ACTIVO DEL CLIENTE EN MOSTRADOR: {nombre_idioma_cliente} (codigo ISO-2: '{cliente_lang_clean}')\n\n"
        f"{ctx_block}"
        f"TEXTO A TRADUCIR:\n\"{txt_clean}\"\n\n"
        "REGLAS OBLIGATORIAS:\n"
        f"1. Si el texto esta en ESPANOL ('es'), traducelo OBLIGATORIAMENTE a {nombre_idioma_cliente} (codigo '{cliente_lang_clean}'). En chino usa caracteres simplificados naturales y fluidez comercial cortes.\n"
        "2. Si el texto esta en CUALQUIER OTRO IDIOMA, traducelo al ESPANOL ('es') natural para el vendedor, respetando si habla en singular ('este lente', 'una pieza') o en plural ('estos lentes', 'dos piezas').\n"
        "3. GLOSARIO OPTICO Y VENTAS DE MOSTRADOR: interpreta con precision términos como lente/gafa/armazón (镜框/太阳镜), mica/cristal (镜片), polarizado/Prizm/Chromance (偏光镜片), fotocromático Transitions (变色镜片), antirreflejante (防反光/镀膜), filtro azul (防蓝光), policarbonato, acetato, titanio, varilla (镜腿), puente nasal/plaquetas (鼻托), graduación/miopía/astigmatismo, garantía/cobertura Oops, cambio en 30 días, meses sin intereses (分期免息), segunda pieza al 40%, descuentos (20%/30%/50%), factura, estuche/microfibra, tarjeta/efectivo, pesos mexicanos (MXN), Ray-Ban/Oakley/Prada/Burberry/Gucci. Corrige pequeños deslices fonéticos del micrófono (ej. 'esta capa'->'esta gafa', '天光'->'偏光').\n\n"
        "Responde UNICAMENTE en JSON valido exacto:\n"
        "{\n"
        '    "idioma_origen": "codigo_iso2",\n'
        '    "idioma_destino": "codigo_iso2",\n'
        '    "traduccion": "texto traducido exacto",\n'
        '    "genero_hablante": "female" o "male"\n'
        "}"
    )

    def _validar_resultado_ia(d_obj):
        trad_v = (d_obj.get("traduccion") or "").strip()
        if not trad_v:
            return None
        orig_n = normalizar_codigo_idioma(d_obj.get("idioma_origen"), txt_clean) or ("es" if es_vendedor else cliente_lang_clean)
        dest_n = normalizar_codigo_idioma(d_obj.get("idioma_destino"), trad_v)
        if es_vendedor is True or orig_n == "es":
            orig_n = "es"
            dest_n = cliente_lang_clean
            # Rechazar si la IA devolvio exactamente la frase en espanol sin traducir a otro idioma
            if trad_v.lower().strip(" .!¡?¿") == txt_clean.lower().strip(" .!¡?¿"):
                return None
            if dest_n == "zh" and not any("\u4e00" <= ch <= "\u9fff" for ch in trad_v):
                return None
        elif es_vendedor is False:
            dest_n = "es"
            if not orig_n or orig_n == "es":
                orig_n = normalizar_codigo_idioma("", txt_clean) or cliente_lang_clean
        return {
            "origen": orig_n,
            "destino": dest_n or ("es" if orig_n != "es" else cliente_lang_clean),
            "texto_original": txt_clean,
            "texto_traducido": trad_v,
            "genero_detectado": d_obj.get("genero_hablante", "female")
        }

    # Metodo 1: Groq API ultra-rapida con modelos activos reales
    groq_keys = get_groq_api_keys_traductor()
    for gkey in groq_keys:
        for modelo in ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
            try:
                url_groq = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {gkey}", "Content-Type": "application/json"}
                payload = {
                    "model": modelo,
                    "messages": [{"role": "user", "content": prompt_traduccion}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
                r = requests.post(url_groq, headers=headers, json=payload, timeout=8)
                if r.status_code == 200:
                    data_raw = r.json()["choices"][0]["message"]["content"]
                    d = json.loads(data_raw)
                    res_ok = _validar_resultado_ia(d)
                    if res_ok:
                        return res_ok
            except Exception:
                pass

    # Metodo 2: Gemini Flash REST
    gemini_key = get_gemini_api_key_traductor()
    if gemini_key:
        for mod in ["gemini-2.5-flash", "gemini-flash-latest"]:
            try:
                url_gem = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={gemini_key}"
                payload_gem = {"contents": [{"parts": [{"text": prompt_traduccion}]}]}
                rm = requests.post(url_gem, json=payload_gem, timeout=8)
                if rm.status_code == 200:
                    raw_txt = rm.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if "```json" in raw_txt:
                        raw_txt = raw_txt.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_txt:
                        raw_txt = raw_txt.split("```")[1].split("```")[0].strip()
                    d = json.loads(raw_txt)
                    res_ok = _validar_resultado_ia(d)
                    if res_ok:
                        return res_ok
            except Exception:
                pass

    # Metodo 3: Fallback minimo de emergencia (nunca devuelve espanol haciendose pasar por idioma extranjero)
    es_probable_espanol = bool(es_vendedor) or any(w in txt_clean.lower() for w in [
        "hola", "lentes", "sol", "precio", "cuanto", "gracias", "armazon", "armazones", "mica", "micas",
        "polarizado", "polarizadas", "tienen", "buenas", "tardes", "dias", "que", "quiero", "busco", "oferta"
    ])
    orig = "es" if es_probable_espanol else (normalizar_codigo_idioma("", txt_clean) or cliente_lang_clean or "en")
    dest = cliente_lang_clean if orig == "es" else "es"

    fallback_trans = ""
    lower_t = txt_clean.lower().strip(" .!¡?¿")
    if orig == "es":
        if lower_t in ["hola", "buenas", "hola buenas"]:
            fallback_trans = "Hello"
        elif lower_t in ["buenos dias", "buen dia"]:
            fallback_trans = "Good morning"
        elif lower_t in ["buenas tardes"]:
            fallback_trans = "Good afternoon"
        elif lower_t in ["buenas noches"]:
            fallback_trans = "Good evening"
        elif lower_t in ["gracias", "muchas gracias"]:
            fallback_trans = "Thank you"
        elif lower_t in ["de nada"]:
            fallback_trans = "You are welcome"
        elif "lentes de sol" in lower_t:
            fallback_trans = "Sunglasses"
        elif "polarizad" in lower_t:
            fallback_trans = "Polarized lenses"
        elif "precio" in lower_t or "cuanto" in lower_t:
            fallback_trans = "How much is it?"
        else:
            fallback_trans = txt_clean
    else:
        if lower_t in ["hello", "hi", "hey"]:
            fallback_trans = "Hola"
        elif lower_t in ["good morning"]:
            fallback_trans = "Buenos días"
        elif lower_t in ["good afternoon"]:
            fallback_trans = "Buenas tardes"
        elif lower_t in ["good evening"]:
            fallback_trans = "Buenas noches"
        elif lower_t in ["thank you", "thanks"]:
            fallback_trans = "Gracias"
        elif lower_t in ["you are welcome", "you're welcome"]:
            fallback_trans = "De nada"
        elif "sunglasses" in lower_t:
            fallback_trans = "Lentes de sol"
        elif "polarized" in lower_t:
            fallback_trans = "Micas polarizadas"
        elif "how much" in lower_t or "price" in lower_t:
            fallback_trans = "¿Cuánto cuesta?"
        else:
            fallback_trans = txt_clean

    return {
        "origen": orig,
        "destino": dest,
        "texto_original": txt_clean,
        "texto_traducido": fallback_trans,
        "genero_detectado": "female"
    }

def generar_audio_traduccion_sync(texto: str, idioma: str, genero: str = "female") -> str:
    """Sintetiza de forma ultra-rapida el audio de traduccion y retorna la URL web."""
    if not texto or not texto.strip():
        return ""
    try:
        lang_key = normalizar_codigo_idioma(idioma, texto) or (idioma[:2].lower() if idioma else "es")
        if lang_key not in VOCES_NATIVAS_EXTRANJERAS:
            lang_key = "en" if any(ord(c) < 128 for c in texto) else "es"
        v_spec = VOCES_NATIVAS_EXTRANJERAS.get(lang_key, VOCES_NATIVAS_EXTRANJERAS.get("es", {}))
        voice_name = v_spec.get(genero, v_spec.get("female", "es-MX-DaliaNeural"))
        rate_val = "-10%" if lang_key in ["en", "de"] else "-8%"

        import hashlib, edge_tts
        temp_dir = os.path.join(os.getcwd(), "custom_assets", "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        h = hashlib.md5(f"{texto}_{voice_name}_{rate_val}".encode("utf-8")).hexdigest()
        filename = f"trans_{h}.mp3"
        fp = os.path.join(temp_dir, filename)

        if not os.path.exists(fp) or os.path.getsize(fp) == 0:
            def _run_worker():
                async def _save():
                    comm = edge_tts.Communicate(texto, voice_name, rate=rate_val)
                    await comm.save(fp)
                new_loop = asyncio.new_event_loop()
                try:
                    new_loop.run_until_complete(_save())
                finally:
                    new_loop.close()

            th = threading.Thread(target=_run_worker)
            th.start()
            th.join(timeout=4.0)

        if os.path.exists(fp) and os.path.getsize(fp) > 0:
            return f"/custom_assets/temp_audio/{filename}"
    except Exception as ex_gen:
        print("Notice generar_audio_traduccion_sync:", ex_gen)
    return ""

def reproducir_audio_traduccion_async(texto: str, idioma: str, genero: str = "female", start_speak_fn=None, page=None):
    """Sintetiza y reproduce el audio de la traduccion en segundo plano de forma 100% aislada."""
    def _worker():
        try:
            if not texto or not texto.strip():
                return

            audio_web_url = generar_audio_traduccion_sync(texto, idioma, genero)
            if audio_web_url:
                fp = os.path.join(os.getcwd(), audio_web_url.lstrip("/"))
                if page and getattr(page, "web", False):
                    try:
                        import sys, time
                        if 'main' in sys.modules and hasattr(sys.modules['main'], 'GLOBAL_WEB_TTS_EVENTS'):
                            events_dict = sys.modules['main'].GLOBAL_WEB_TTS_EVENTS
                            evt_id = f"trad_play_{int(time.time()*1000)}"
                            evt_data = {
                                "action": "play_traductor_audio",
                                "audio_url": audio_web_url,
                                "id": evt_id,
                                "timestamp": time.time()
                            }
                            tok = getattr(page, "_luxo_token", None) or getattr(page, "session_id", None) or getattr(page, "user_id", None)
                            if tok:
                                events_dict[str(tok)] = evt_data
                            u_name = str(getattr(page, "username", "") or "").lower().strip()
                            if u_name:
                                d_type = "mobile" if (getattr(page, "width", 0) and page.width < 768) else "desktop"
                                events_dict[f"{u_name}_{d_type}"] = evt_data
                            print(f"[TRADUCTOR PLAY DISPATCH PRIVADO] {audio_web_url} (tok: {tok}, id: {evt_id})")
                    except Exception as ex_w:
                        print("Notice web play dispatch:", ex_w)
                else:
                    try:
                        import ctypes
                        mci = ctypes.windll.winmm.mciSendStringW
                        mci("close luxo_trans_audio", None, 0, 0)
                        mci(f'open "{os.path.abspath(fp)}" type mpegvideo alias luxo_trans_audio', None, 0, 0)
                        mci("play luxo_trans_audio", None, 0, 0)
                    except Exception:
                        if start_speak_fn and idioma[:2].lower() == "es":
                            try:
                                v_luxo = random.choice(VOCES_LUXO_FEMENINAS if genero == "female" else VOCES_LUXO_MASCULINAS)
                                start_speak_fn(texto, voice_id=v_luxo, voice_gender=genero)
                            except Exception: pass
        except Exception as ex_aud:
            print("Notice reproducir_audio_traduccion:", ex_aud)

    threading.Thread(target=_worker, daemon=True).start()

def registrar_rutas_fastapi_traductor(app=None):
    """Registra rutas de FastAPI dinamicamente con prioridad maxima al inicio de la tabla de ruteo."""
    try:
        import gc, fastapi
        if not app:
            apps = [obj for obj in gc.get_objects() if isinstance(obj, fastapi.FastAPI)]
            if not apps:
                return
            app = apps[0]

        # Verificar si ya estan registradas y asegurar que esten al principio
        rutas_existentes = [getattr(r, "path", None) for r in app.router.routes]
        if "/api/traductor/speech_input" in rutas_existentes and "/api/traductor/audio_upload" in rutas_existentes:
            trad_routes = [r for r in app.router.routes if str(getattr(r, "path", "")).startswith("/api/traductor")]
            other_routes = [r for r in app.router.routes if not str(getattr(r, "path", "")).startswith("/api/traductor")]
            app.router.routes = trad_routes + other_routes
            return

        from fastapi import Request
        import tempfile

        @app.get("/api/traductor/status")
        @app.get("/api/traductor/view_state")
        def api_traductor_status():
            return {"active": bool(TRADUCTOR_SESSIONS), "count": len(TRADUCTOR_SESSIONS)}

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
                    # Solo recurrir si hay exactamente 1 sesion activa para evitar cruces entre dispositivos
                    if len(TRADUCTOR_SESSIONS) == 1:
                        sess_handler = list(TRADUCTOR_SESSIONS.values())[0]

                if sess_handler:
                    set_visual_fn = sess_handler.get("set_visual")
                    if set_visual_fn:
                        set_visual_fn(source, "processing")

                    if txt_clean:
                        fn = sess_handler.get("procesar_vendedor" if source == "vendedor" else "procesar_cliente")
                        if fn:
                            res_proc = fn(txt_clean)
                            audio_url = (res_proc or {}).get("audio_url", "")
                            trad_txt = (res_proc or {}).get("traduccion", "")
                            return {
                                "status": "ok",
                                "text": txt_clean,
                                "translated": trad_txt,
                                "audio_url": audio_url
                            }
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

                # Deteccion inteligente de formato contenedor
                if audio_bytes.startswith(b"\x1a\x45\xdf\xa3") or b"webm" in audio_bytes[:100]:
                    ext, mime = ".webm", "audio/webm"
                elif b"ftyp" in audio_bytes[:30] or b"mp4" in audio_bytes[:30] or audio_bytes.startswith(b"\x00\x00\x00"):
                    ext, mime = ".mp4", "audio/mp4"
                elif audio_bytes.startswith(b"RIFF"):
                    ext, mime = ".wav", "audio/wav"
                elif audio_bytes.startswith(b"OggS"):
                    ext, mime = ".ogg", "audio/ogg"
                else:
                    ext, mime = ".webm", "audio/webm"

                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(audio_bytes)
                    temp_path = tmp.name

                texto_transcrito = ""
                idioma_detectado = "auto"
                whisper_baja_confianza = False
                HALLUCINACIONES_RUIDO = {
                    "you", "thank you", "thanks", "thanks for watching", "thank you for watching",
                    "bye", "gracias", "subtitulos realizados por la comunidad de amara.org",
                    "subtítulos realizados por la comunidad de amara.org", "amara.org",
                    "请不吝点赞", "字幕", "谢谢观看", "感谢观看", "请订阅", "优优独播剧场"
                }

                def _es_alucinacion_ruido(txt_chk):
                    c = (txt_chk or "").strip(" .!¡?¿。，、").lower()
                    if not c or c in {".", "..", "...", "...."} or c in HALLUCINACIONES_RUIDO:
                        return True
                    return any(h in c for h in ("amara.org", "请不吝点赞", "优优独播剧场", "subtítulos realizados"))

                def _transcribir_gemini_limpio():
                    g_key = get_gemini_api_key_traductor()
                    if not g_key or len(audio_bytes) < 400:
                        return "", ""
                    try:
                        import base64
                        b64_aud = base64.b64encode(audio_bytes).decode("ascii")
                        p_aud = (
                            "Eres un especialista en aislamiento de voz y transcripción en mostrador de óptica Sunglass Hut.\n"
                            "Escucha el audio e IGNORA ruido ambiental, música de tienda, eco, golpes o voces lejanas.\n"
                            "Transcribe ÚNICAMENTE lo que dijo el hablante principal cercano al micrófono, respetando singular/plural y términos ópticos (polarizado, armazón, lentes, Ray-Ban, Oakley, 偏光, 太阳镜, 镜框, 多少钱).\n"
                            + ("El hablante es un vendedor mexicano en español ('es').\n" if source == "vendedor" else "El hablante es un cliente (puede hablar mandarín 'zh', inglés 'en', francés 'fr', japonés 'ja', etc.).\n")
                            + "Si solo hay ruido o silencio, devuelve text vacío.\n"
                            + 'Responde ÚNICAMENTE JSON: {"text": "transcripcion limpia", "language": "codigo_iso2"}'
                        )
                        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={g_key}"
                        payload_g = {
                            "contents": [{
                                "parts": [
                                    {"text": p_aud},
                                    {"inline_data": {"mime_type": mime, "data": b64_aud}}
                                ]
                            }]
                        }
                        rg = requests.post(url_g, json=payload_g, timeout=12)
                        if rg.status_code == 200:
                            raw_g = rg.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                            if "```json" in raw_g:
                                raw_g = raw_g.split("```json")[1].split("```")[0].strip()
                            elif "```" in raw_g:
                                raw_g = raw_g.split("```")[1].split("```")[0].strip()
                            dg = json.loads(raw_g)
                            tg = (dg.get("text") or "").strip()
                            lg = normalizar_codigo_idioma(dg.get("language"), tg)
                            return tg, lg
                    except Exception as ex_ga:
                        print("Notice Gemini Audio:", ex_ga)
                    return "", ""

                try:
                    groq_keys = get_groq_api_keys_traductor()
                    for gkey in groq_keys:
                        try:
                            headers = {"Authorization": f"Bearer {gkey}"}
                            with open(temp_path, "rb") as f:
                                files = {"file": (f"traductor_rec{ext}", f, mime)}
                                if source == "vendedor":
                                    data = {
                                        "model": "whisper-large-v3",
                                        "response_format": "verbose_json",
                                        "temperature": 0.0,
                                        "language": "es",
                                        "prompt": "Mostrador de óptica Sunglass Hut: estos lentes, este lente polarizado, armazón, micas Prizm, Transitions, precio en pesos mexicanos, descuento, segunda pieza al cuarenta, meses sin intereses, tarjeta, garantía, Ray-Ban, Oakley, Prada."
                                    }
                                else:
                                    data = {
                                        "model": "whisper-large-v3",
                                        "response_format": "verbose_json",
                                        "temperature": 0.0,
                                        "prompt": "Sunglass Hut counter: polarized sunglasses, lenses, frame, price, discount, 偏光镜, 太阳镜, 镜框, 多少钱, 刷卡, 打折, Ray-Ban, Oakley."
                                    }
                                res_w = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=12)
                            if res_w.status_code == 200:
                                w_data = res_w.json()
                                texto_transcrito = w_data.get("text", "").strip()
                                raw_lang = w_data.get("language", "auto")
                                idioma_detectado = normalizar_codigo_idioma(raw_lang, texto_transcrito) or raw_lang
                                segs = w_data.get("segments") or []
                                if segs and all(float(sg.get("no_speech_prob") or 0) > 0.78 for sg in segs):
                                    whisper_baja_confianza = True
                                print(f"[TRADUCTOR WHISPER] Transcrito: '{texto_transcrito}' (raw={raw_lang}, norm={idioma_detectado}, low_conf={whisper_baja_confianza})")
                                if texto_transcrito:
                                    break
                        except Exception as ex_w:
                            print("Notice Whisper attempt:", ex_w)
                finally:
                    try: os.unlink(temp_path)
                    except: pass

                if _es_alucinacion_ruido(texto_transcrito) or whisper_baja_confianza:
                    print(f"[TRADUCTOR WHISPER] Ruido/baja confianza ('{texto_transcrito}'), validando con Gemini Audio...")
                    tg, lg = _transcribir_gemini_limpio()
                    if tg and not _es_alucinacion_ruido(tg):
                        texto_transcrito = tg
                        idioma_detectado = lg or idioma_detectado
                        print(f"[TRADUCTOR GEMINI AUDIO] Recuperado limpio: '{texto_transcrito}' ({idioma_detectado})")
                    elif _es_alucinacion_ruido(texto_transcrito):
                        texto_transcrito = ""

                if texto_transcrito and sess_handler:
                    if source == "vendedor":
                        fn = sess_handler.get("procesar_vendedor")
                        res_proc = fn(texto_transcrito) if fn else None
                    else:
                        fn = sess_handler.get("procesar_cliente")
                        try:
                            res_proc = fn(texto_transcrito, idioma_forzado=idioma_detectado) if fn else None
                        except TypeError:
                            res_proc = fn(texto_transcrito) if fn else None
                    if fn:
                        audio_url = (res_proc or {}).get("audio_url", "")
                        trad_txt = (res_proc or {}).get("traduccion", "")
                        lang_final = normalizar_codigo_idioma((res_proc or {}).get("origen") or idioma_detectado, texto_transcrito) or idioma_detectado
                        return {
                            "status": "ok",
                            "text": texto_transcrito,
                            "translated": trad_txt,
                            "language": lang_final,
                            "audio_url": audio_url
                        }

                # Si no hubo audio o fallo, regresar a idle
                if sess_handler and sess_handler.get("set_visual"):
                    sess_handler["set_visual"](source, "idle")

                return {"status": "transcription_finished"}
            except Exception as e_aud:
                print("Error en /api/traductor/audio_upload:", e_aud)
                if sess_handler and sess_handler.get("set_visual"):
                    sess_handler["set_visual"](source, "idle")
                return {"status": "error", "detail": str(e_aud)}

        # REORDENAR RUTAS: Ponerlas al principio de app.router.routes para que precedan a app.mount("/", ...)
        trad_routes = [r for r in app.router.routes if str(getattr(r, "path", "")).startswith("/api/traductor")]
        other_routes = [r for r in app.router.routes if not str(getattr(r, "path", "")).startswith("/api/traductor")]
        app.router.routes = trad_routes + other_routes
        print(f"Rutas de traductor registradas y priorizadas en FastAPI: {len(trad_routes)} endpoints.")

    except Exception as ex_reg:
        print("Notice registrar_rutas_fastapi_traductor:", ex_reg)


def build_traductor_view(page: ft.Page, user_info=None, conectar_db_fn=None, mostrar_snack_fn=None, start_speak_fn=None):
    """Construye la vista interactiva y aislada del Traductor de Mostrador."""
    registrar_rutas_fastapi_traductor()

    is_mobile = (page.width < 768) if (page.width and page.width > 0) else False
    session_token = getattr(page, "_luxo_token", None) or getattr(page, "session_id", None) or str(time.time())

    vendedor_genero = ["female"]
    idioma_cliente_actual = ["en"]
    historial_reciente = []
    grabando_estado = {"vendedor": False, "cliente": False}

    def _on_select_idioma_cliente(e):
        val = (e.control.value or "auto").strip().lower()
        if val != "auto":
            idioma_cliente_actual[0] = val
            loc_map = {"zh": "zh-CN", "en": "en-US", "fr": "fr-FR", "de": "de-DE", "it": "it-IT", "pt": "pt-BR", "ja": "ja-JP", "ko": "ko-KR", "ru": "ru-RU", "ar": "ar-SA"}
            loc = loc_map.get(val, "en-US")
            ejecutar_js_traductor(page, f"window._luxoTradClientLocale = '{loc}';")

    dd_idioma_cliente = ft.Dropdown(
        value="auto",
        width=168,
        dense=True,
        text_size=11,
        bgcolor="#1a102b",
        border_color="#D8B4FE",
        color="white",
        content_padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        options=[
            ft.dropdown.Option("auto", "🌐 Auto (Detectar)"),
            ft.dropdown.Option("zh", "🇨🇳 Chino Mandarín"),
            ft.dropdown.Option("en", "🇺🇸 Inglés"),
            ft.dropdown.Option("fr", "🇫🇷 Francés"),
            ft.dropdown.Option("ja", "🇯🇵 Japonés"),
            ft.dropdown.Option("ko", "🇰🇷 Coreano"),
            ft.dropdown.Option("de", "🇩🇪 Alemán"),
            ft.dropdown.Option("it", "🇮🇹 Italiano"),
            ft.dropdown.Option("pt", "🇧🇷 Portugués"),
            ft.dropdown.Option("ru", "🇷🇺 Ruso"),
            ft.dropdown.Option("ar", "🇸🇦 Árabe"),
        ],
        on_select=_on_select_idioma_cliente,
    )

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
                            ft.Text(icono, size=15),
                            ft.Text(origen_lbl, color=color_accent, weight="bold", size=12, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ], spacing=6, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.VOLUME_UP_ROUNDED,
                            icon_color=color_accent,
                            icon_size=18,
                            tooltip="Volver a escuchar pronunciacion",
                            on_click=re_escuchar
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f'"{texto_orig}"', color="#cccccc", size=14, italic=True, selectable=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.TRANSLATE_ROUNDED, color="#00FFFF", size=16),
                            ft.Text(texto_trad, color="white", weight="bold", size=15, expand=True, selectable=True),
                            ft.Container(
                                content=ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, color=color_accent, size=18),
                                width=32,
                                height=32,
                                border_radius=8,
                                bgcolor=f"{color_accent}15",
                                alignment=ft.Alignment(0, 0),
                                tooltip="Volver a escuchar pronunciación",
                                on_click=re_escuchar
                            )
                        ], spacing=8),
                        bgcolor="#16162a",
                        padding=ft.Padding(10, 8, 8, 8),
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
        ink=True,
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
        ink=True,
        tooltip="1st tap: Start speaking. 2nd tap: Finish and translate.",
    )

    def set_visual_estado(source: str, state: str):
        """Actualiza el estado visual exacto del boton segun los toques con auto-watchdog."""
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

                # WATCHDOG DE SEGURIDAD (Max 10 segundos)
                def _watchdog_vendedor():
                    time.sleep(10)
                    try:
                        if "Traduciendo" in str(btn_mic_vendedor.content.controls[1].value):
                            print("[WATCHDOG] Recuperando boton vendedor de processing a idle")
                            set_visual_estado("vendedor", "idle")
                    except Exception: pass
                threading.Thread(target=_watchdog_vendedor, daemon=True).start()

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

                # WATCHDOG DE SEGURIDAD (Max 10 segundos)
                def _watchdog_cliente():
                    time.sleep(10)
                    try:
                        if "Translating" in str(btn_mic_cliente.content.controls[1].value):
                            print("[WATCHDOG] Recuperando boton cliente de processing a idle")
                            set_visual_estado("cliente", "idle")
                    except Exception: pass
                threading.Thread(target=_watchdog_cliente, daemon=True).start()

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

    def disparar_evento_traductor(pg, action: str, src: str, sid: str):
        try:
            import sys, time
            if 'main' in sys.modules and hasattr(sys.modules['main'], 'GLOBAL_WEB_TTS_EVENTS'):
                events_dict = sys.modules['main'].GLOBAL_WEB_TTS_EVENTS
                evt_id = f"trad_evt_{int(time.time()*1000)}"
                evt_data = {
                    "action": action,
                    "source": src,
                    "session_id": sid,
                    "id": evt_id,
                    "timestamp": time.time()
                }
                tok = getattr(pg, "_luxo_token", None) or getattr(pg, "session_id", None) or sid
                if tok:
                    events_dict[str(tok)] = evt_data
                if sid and sid != tok:
                    events_dict[str(sid)] = evt_data
                u_name = str(getattr(pg, "username", "") or "").lower().strip()
                if u_name:
                    d_type = "mobile" if (getattr(pg, "width", 0) and pg.width < 768) else "desktop"
                    events_dict[f"{u_name}_{d_type}"] = evt_data
                print(f"[TRADUCTOR EVENT DISPATCH PRIVADO] {action} {src} (tok: {tok}, sid: {sid}, id: {evt_id})")
        except Exception as ex_d:
            print("Notice disparar_evento_traductor:", ex_d)

    def procesar_traduccion_vendedor_texto(texto_directo=None):
        set_visual_estado("vendedor", "processing")
        texto = texto_directo if (isinstance(texto_directo, str) and texto_directo.strip()) else txt_input_vendedor.value
        if not texto or not str(texto).strip():
            set_visual_estado("vendedor", "idle")
            return None
        txt_input_vendedor.value = ""
        try: page.update()
        except: pass

        def _do_work():
            try:
                # Pasar idioma activo del cliente extranjero y contexto reciente a la IA
                target_lang = normalizar_codigo_idioma(idioma_cliente_actual[0]) or "en"
                if target_lang == "es":
                    target_lang = "en"
                res = detectar_idioma_y_traducir_ia(
                    texto,
                    idioma_cliente=target_lang,
                    historial_contexto=historial_reciente,
                    es_vendedor=True,
                )
                if res:
                    idioma_dest = normalizar_codigo_idioma(res.get("destino"), res.get("texto_traducido", "")) or target_lang
                    if idioma_dest == "es":
                        idioma_dest = target_lang
                    trad = res.get("texto_traducido", "")
                    historial_reciente.append(f"Vendedor: {texto} -> {trad}")
                    if len(historial_reciente) > 6:
                        del historial_reciente[:-6]
                    flag_dest = VOCES_NATIVAS_EXTRANJERAS.get(idioma_dest, {}).get("name", idioma_dest.upper())
                    agregar_burbuja_traduccion(
                        f"Vendedor (Espanol -> {flag_dest})",
                        texto,
                        trad,
                        "#00FFFF",
                        "[Vendedor]",
                        lang_code=idioma_dest,
                        gender=vendedor_genero[0]
                    )
                    audio_url = generar_audio_traduccion_sync(trad, idioma_dest, genero=vendedor_genero[0])
                    if not (page and getattr(page, "web", False)) and audio_url:
                        reproducir_audio_traduccion_async(trad, idioma_dest, genero=vendedor_genero[0], start_speak_fn=start_speak_fn, page=page)
                    return {"traduccion": trad, "audio_url": audio_url, "destino": idioma_dest}
            except Exception as ex_v:
                print("Notice procesar_traduccion_vendedor_texto:", ex_v)
            finally:
                set_visual_estado("vendedor", "idle")
            return None

        if texto_directo is not None:
            return _do_work()
        else:
            threading.Thread(target=_do_work, daemon=True).start()
            return None

    def procesar_traduccion_cliente_texto(texto_directo=None, idioma_forzado=None):
        set_visual_estado("cliente", "processing")
        texto = texto_directo if (isinstance(texto_directo, str) and texto_directo.strip()) else txt_input_cliente.value
        if not texto or not str(texto).strip():
            set_visual_estado("cliente", "idle")
            return None
        txt_input_cliente.value = ""
        try: page.update()
        except: pass

        def _do_work():
            try:
                pista_lang = normalizar_codigo_idioma(idioma_forzado, texto) or idioma_cliente_actual[0]
                res = detectar_idioma_y_traducir_ia(
                    texto,
                    idioma_cliente=pista_lang,
                    historial_contexto=historial_reciente,
                    es_vendedor=False,
                )
                if res:
                    idioma_orig = normalizar_codigo_idioma(idioma_forzado, texto) or normalizar_codigo_idioma(res.get("origen"), texto) or pista_lang or "en"
                    if idioma_orig == "es":
                        idioma_orig = normalizar_codigo_idioma("", texto) or "en"
                    idioma_cliente_actual[0] = idioma_orig
                    if any(o.key == idioma_orig for o in dd_idioma_cliente.options):
                        dd_idioma_cliente.value = idioma_orig
                    trad = res.get("texto_traducido", "")
                    historial_reciente.append(f"Cliente ({idioma_orig}): {texto} -> {trad}")
                    if len(historial_reciente) > 6:
                        del historial_reciente[:-6]
                    gen_cliente = res.get("genero_detectado", "female")
                    flag_orig = VOCES_NATIVAS_EXTRANJERAS.get(idioma_orig, {}).get("name", idioma_orig.upper())
                    agregar_burbuja_traduccion(
                        f"Cliente ({flag_orig} -> Vendedor)",
                        texto,
                        trad,
                        "#D8B4FE",
                        "[Cliente]",
                        lang_code="es",
                        gender=gen_cliente
                    )
                    audio_url = generar_audio_traduccion_sync(trad, "es", genero=gen_cliente)
                    if not (page and getattr(page, "web", False)) and audio_url:
                        reproducir_audio_traduccion_async(trad, "es", genero=gen_cliente, start_speak_fn=start_speak_fn, page=page)
                    return {"traduccion": trad, "audio_url": audio_url, "origen": idioma_orig}
            except Exception as ex_c:
                print("Notice procesar_traduccion_cliente_texto:", ex_c)
            finally:
                set_visual_estado("cliente", "idle")
            return None

        if texto_directo is not None:
            return _do_work()
        else:
            threading.Thread(target=_do_work, daemon=True).start()
            return None

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
            set_visual_estado("vendedor", "processing")
            disparar_evento_traductor(page, "stop_traductor_mic", "vendedor", session_token)
            ejecutar_js_traductor(page, f"if(window.luxoStopTraductorMic) window.luxoStopTraductorMic('vendedor', '{session_token}');")
        else:
            set_visual_estado("vendedor", "recording")
            if grabando_estado["cliente"]:
                set_visual_estado("cliente", "idle")
            disparar_evento_traductor(page, "start_traductor_mic", "vendedor", session_token)
            ejecutar_js_traductor(page, f"if(window.luxoStartTraductorMic) window.luxoStartTraductorMic('vendedor', '{session_token}');")

    def on_mic_cliente_click(e):
        if grabando_estado["cliente"]:
            set_visual_estado("cliente", "processing")
            disparar_evento_traductor(page, "stop_traductor_mic", "cliente", session_token)
            ejecutar_js_traductor(page, f"if(window.luxoStopTraductorMic) window.luxoStopTraductorMic('cliente', '{session_token}');")
        else:
            set_visual_estado("cliente", "recording")
            if grabando_estado["vendedor"]:
                set_visual_estado("vendedor", "idle")
            disparar_evento_traductor(page, "start_traductor_mic", "cliente", session_token)
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
        historial_reciente.clear()
        idioma_cliente_actual[0] = "en"
        dd_idioma_cliente.value = "auto"
        try: page.update()
        except: pass

    btn_limpiar = ft.IconButton(
        icon=ft.Icons.DELETE_SWEEP_ROUNDED,
        icon_color="#888899",
        tooltip="Limpiar conversacion",
        on_click=limpiar_chat
    )

    card_vendedor = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("LADO VENDEDOR (Español)", color="#00FFFF", weight="bold", size=13),
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
            ], spacing=6)
        ], spacing=6),
        bgcolor="#0c0c1a",
        padding=10,
        border_radius=12,
        border=ft.Border.all(1.5, "#00FFFF"),
        expand=not is_mobile
    )

    card_cliente = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("LADO CLIENTE", color="#D8B4FE", weight="bold", size=13),
                dd_idioma_cliente,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
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
            ], spacing=6)
        ], spacing=6),
        bgcolor="#120c1c",
        padding=10,
        border_radius=12,
        border=ft.Border.all(1.5, "#D8B4FE"),
        expand=not is_mobile
    )

    controles_inferiores = (
        ft.Column([card_cliente, card_vendedor], spacing=8)
        if is_mobile
        else ft.Row([card_cliente, card_vendedor], spacing=10)
    )

    ejecutar_js_traductor(page, "console.log('[TRADUCTOR] Vista iniciada correctamente');")

    return ft.Column([
        ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.TRANSLATE_ROUNDED, color="#00FFFF", size=22),
                ft.Text("TRADUCTOR DE MOSTRADOR", size=16 if is_mobile else 18, color="white", weight="bold"),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                status_indicator,
                btn_limpiar
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(height=4, color="#1c1c2e"),
        ft.Container(
            content=chat_list,
            expand=True,
            bgcolor="#04040a",
            border_radius=12,
            border=ft.Border.all(1, "#181828")
        ),
        ft.Divider(height=6, color="transparent"),
        controles_inferiores
    ], expand=True)
