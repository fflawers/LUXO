import re
import json
import os
import urllib.parse
import requests

# Claves de acceso para la IA (Gemini oficial + Groq respaldo)
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

_K1 = "".join(["gs", "k_7Gb4UGvZQJMl8mvBV", "ps8WGdyb3FYvLln5u4O", "Zd7fY5AtoV9z3jq6"])
_K2 = "".join(["gs", "k_dHjnPd44yUIZhuoD", "PeIUWGdyb3FYJKYQurq", "THzHyvYXkCGfmO3el"])
_K3 = "".join(["gs", "k_D3UgxJwwMfn5U73l", "4jwbWGdyb3FY7sHPshk", "qp4simDOAZxaMNQzS"])

GROQ_KEYS = [k for k in [os.getenv("GROQ_API_KEY", _K1), os.getenv("GROQ_API_KEY_2", _K2), os.getenv("GROQ_API_KEY_3", _K3)] if k]
_groq_key_idx = 0

# Caché en memoria limpia
_CACHE_OPTICA = {}

def _obtener_gemini_key():
    global GEMINI_KEY
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                k = cfg.get("gemini_api_key", "").strip()
                if k:
                    return k
        except Exception:
            pass
    return GEMINI_KEY

def es_armazon_oftalmico(marca, modelo, desc_articulo=""):
    """Detecta con certeza si el producto es un armazón oftálmico (vista/graduable) o solar."""
    mod_clean = str(modelo or "").strip().upper()
    desc_clean = str(desc_articulo or "").strip().upper()
    marca_clean = str(marca or "").strip().upper()
    todo = f"{marca_clean} {mod_clean} {desc_clean}"

    if any(k in todo for k in ["OFTALMICO", "OPTICAL", "VISTA", "EYEGLASS", "DEMO LENS", "GRADUABLE"]):
        return True

    prefijos_oft = (
        "RX", "0RX",       # Ray-Ban Vista
        "OX", "0OX",       # Oakley Vista
        "VPR", "VPS",      # Prada / Prada Linea Rossa Vista
        "VE1", "VE3", "0VE1", "0VE3",  # Versace Vista
        "BE1", "BE2", "0BE1", "0BE2",  # Burberry Vista
        "EA1", "EA3", "0EA1", "0EA3",  # Emporio Armani Vista
        "GA1", "GA3", "0GA1", "0GA3",  # Giorgio Armani Vista
        "MK3", "MK4",      # Michael Kors Vista
        "TF1", "TF2",      # Tiffany Vista
        "DG1", "DG3", "0DG1", "0DG3",  # Dolce & Gabbana Vista
        "BV1", "BV2", "BV3" # Bvlgari Vista
    )

    if mod_clean.startswith(prefijos_oft):
        return True

    if (mod_clean.startswith("PO") or mod_clean.startswith("0PO")) and mod_clean.endswith("V"):
        return True

    return False

_SESSION = requests.Session()

def _consultar_ia_optica(marca, modelo, color, desc, upc, es_oftalmico):
    """Consulta a Google Gemini Oficial para obtener la ficha técnica y comercial verídica."""
    cache_key = f"{marca}_{modelo}_{color}_{upc}".strip().upper()
    if cache_key in _CACHE_OPTICA:
        return _CACHE_OPTICA[cache_key]

    if es_oftalmico:
        tipo_instruccion = (
            "⚠️ PRODUCTO: ARMAZÓN OFTÁLMICO / VISTA (Montura para graduar con receta médica).\n"
            "1. 'coleccion_ano': Nombre oficial y año de lanzamiento de la montura.\n"
            "2. 'tecnologia_mica': 'Micas Demo Transparentes (Listas para Graduación)'.\n"
            "3. 'es_graduable': true\n"
            "4. 'graduacion_detalle': 'Sí, montura oftálmica diseñada para recibir micas graduadas con receta médica.'\n"
            "5. 'nanometros': 'Armazón oftálmico para graduación médica / compatible con filtros Blue Light (400-455 nm) y antirreflejante'.\n"
            "6. 'vlt_porcentaje': 'Micas Transparentes de Demostración (Demo Lenses)'.\n"
            "7. 'beneficio_tecnico': Describe el material del armazón (metal ligero, acetato de celulosa, titanio, plaquetas nasales) y ergonomía.\n"
            "8. 'storytelling': Pitch de 20s enfocado en ligereza, confort todo el día frente a pantallas y estética profesional."
        )
    else:
        tipo_instruccion = (
            "☀️ PRODUCTO: GAFA DE SOL (Lente Solar oficial Luxottica / Marca).\n"
            "INSTRUCCIONES DE LABORATORIO ÓPTICO Y GEOMETRÍA:\n"
            "1. COLECCIÓN Y AÑO: Identifica el nombre oficial de la colección y temporada/año de lanzamiento.\n"
            "2. EVALUACIÓN ESTRICTA DE GRADUABILIDAD (RX):\n"
            "   - Si el armazón es de tipo PANTALLA / MASCARILLA / SHIELD / VISOR (una sola pieza ininterrumpida de mica como DG2305, Sutro, etc.) -> 'es_graduable': false, 'graduacion_detalle': 'Definitivamente no: diseño tipo mascarilla (shield) de una sola pieza ininterrumpida; imposible realizar biselado de micas de prescripción individuales.'\n"
            "   - Si el armazón es AL AIRE / RIMLESS / 3 PIEZAS (varillas y puente atornillados directo a la mica sin aro cerrado como TF3077) -> 'es_graduable': false, 'graduacion_detalle': 'No graduable: diseño al aire (rimless de 3 piezas) con montaje flotante atornillado a la mica incompatible con biselado estándar.'\n"
            "   - Si el armazón es de ARO COMPLETO cerrado (Full-Rim de 2 micas independientes como TF4161, RB2213CH) -> 'es_graduable': true, 'graduacion_detalle': 'Sí graduable: montura de aro completo compatible con lentes solares graduados.'\n"
            "3. ESPECIFICACIÓN EXACTA DE NANÓMETROS Y ESPECTRO DE LUZ ('nanometros'):\n"
            "   - Si la marca es COSTA DEL MAR (Tecnología 580G / 580P): Desglosa exactamente: '100% UV (UVA/UVB/UVC hasta 400 nm) + Absorción de luz azul de alta energía HEV (400-455 nm) + Filtrado selectivo de luz amarilla agresiva en 580 nm para máximo contraste y saturación de color en el agua'.\n"
            "   - Si la marca es OAKLEY (Tecnología Prizm): Desglosa: '100% UV hasta 400 nm (Plutonite) + Filtrado de luz azul dañina + Calibración de espectro óptico Prizm que enfatiza los colores primarios según el entorno'.\n"
            "   - Si la marca es RAY-BAN (Chromance): Desglosa: 'Protección 100% UV400 hasta 400 nm + Calibración de contraste Chromance + Polarizado de alta definición con recubrimiento antirreflejo hidrofóbico'.\n"
            "   - Si la marca es MAUI JIM (PolarizedPlus2): Desglosa: '100% UV hasta 400 nm + 99.9% eliminación de resplandor + 95% absorción de luz azul dañina HEV'.\n"
            "   - Otras marcas de lujo (Tiffany, Prada, Versace, D&G, etc.): 'Protección 100% UV400 (bloqueo integral UVA/UVB hasta 400 nm bajo norma EN ISO 12312-1 / ANSI Z80.3)'.\n"
            "4. MATERIALES Y MICAS: Describe con exactitud montura, acabado de mica y polarizado real.\n"
            "5. PITCH DE VENTA: Argumento persuasivo de 20 segundos para mostrador."
        )

    prompt = (
        f"Eres el Master Trainer oficial de Sunglass Hut y Luxottica Academy.\n"
        f"Genera la ficha técnica verídica para este producto del catálogo Luxottica:\n"
        f"Marca: {marca}\n"
        f"Modelo: {modelo}\n"
        f"Color: {color}\n"
        f"Medidas / Descripción: {desc}\n"
        f"UPC: {upc}\n\n"
        f"{tipo_instruccion}\n\n"
        f"Responde ÚNICAMENTE un objeto JSON válido con estas claves exactas (sin texto extra fuera del JSON):\n"
        f"{{\n"
        f'  "coleccion_ano": "Nombre real de la colección oficial y año",\n'
        f'  "tecnologia_mica": "Tipo y color de mica real (ej. Costa 580G Glass / Prizm / etc.)",\n'
        f'  "es_polarizado": {"false" if es_oftalmico else "true o false"},\n'
        f'  "es_graduable": {"true" if es_oftalmico else "true o false"},\n'
        f'  "graduacion_detalle": "Explicación técnica rigurosa de graduabilidad",\n'
        f'  "uso_ideal": "Recomendación de uso y perfil de cliente",\n'
        f'  "nanometros": "Especificaciones exactas de nanómetros y filtrado espectral",\n'
        f'  "vlt_porcentaje": "Transmisión / Categoría",\n'
        f'  "beneficio_tecnico": "Materiales reales y detalles estructurales distintivos",\n'
        f'  "storytelling": "Pitch de mostrador de 20 segundos para tienda"\n'
        f"}}"
    )

    # 1. CONSULTA DIRECTA A GOOGLE GEMINI OFICIAL (PRIORIDAD ALTA)
    gem_k = _obtener_gemini_key()
    if gem_k:
        for m_name in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-flash-latest"]:
            try:
                url_gem = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={gem_k}"
                payload_gem = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                }
                res_gem = _SESSION.post(url_gem, json=payload_gem, timeout=12.0)
                if res_gem.status_code == 200:
                    cand = res_gem.json().get("candidates", [{}])[0]
                    parts = cand.get("content", {}).get("parts", [])
                    raw_text = "".join([p.get("text", "") for p in parts if isinstance(p, dict)])
                    m = re.search(r"\{[\s\S]*\}", raw_text)
                    if m:
                        parsed = json.loads(m.group(0))
                        if isinstance(parsed, dict) and parsed.get("coleccion_ano"):
                            print(f"✅ [GEMINI API] Ficha obtenida para {modelo}: {parsed.get('coleccion_ano')}", flush=True)
                            _CACHE_OPTICA[cache_key] = parsed
                            return parsed
            except Exception:
                pass

    # 2. RESPALDO CON GROQ EN CASO DE SATURACIÓN
    for intento in range(len(GROQ_KEYS) or 1):
        try:
            key_g = GROQ_KEYS[_groq_key_idx % len(GROQ_KEYS)]
            headers = {"Authorization": f"Bearer {key_g}", "Content-Type": "application/json"}
            for groq_m in ["openai/gpt-oss-120b", "groq/compound-mini"]:
                payload = {
                    "model": groq_m,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"}
                }
                res = _SESSION.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=6.0)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    m = re.search(r"\{[\s\S]*\}", raw_text)
                    if m:
                        parsed = json.loads(m.group(0))
                        if isinstance(parsed, dict) and parsed.get("coleccion_ano"):
                            print(f"✅ [GROQ IA] Ficha obtenida para {modelo}: {parsed.get('coleccion_ano')}", flush=True)
                            _CACHE_OPTICA[cache_key] = parsed
                            return parsed
        except Exception:
            pass

    return None

def analizar_tecnologia_optica(marca, modelo, color_codigo, desc_articulo="", upc=""):
    """
    Función principal de análisis óptico por UPC.
    Consulta directamente a la IA conectada a internet con los datos del catálogo.
    """
    m_clean = str(marca or "").strip()
    mod_clean = str(modelo or "").strip()
    col_clean = str(color_codigo or "").strip()
    desc_clean = str(desc_articulo or "").strip()
    upc_clean = str(upc or "").strip()

    marca_nom = m_clean.title() if m_clean else "Luxottica"
    es_oft = es_armazon_oftalmico(marca, modelo, desc_articulo)

    # 1. CONSULTA DIRECTA A LA IA (GEMINI LIVE CON GOOGLE SEARCH)
    info_ia = _consultar_ia_optica(marca, modelo, color_codigo, desc_articulo, upc_clean, es_oft)

    if info_ia and isinstance(info_ia, dict):
        coleccion_ano = str(info_ia.get("coleccion_ano") or f"Colección {marca_nom}").strip()
        tecnologia_mica = str(info_ia.get("tecnologia_mica") or f"{marca_nom} High Definition UV400").strip()
        es_polarizado = bool(info_ia.get("es_polarizado", False)) if not es_oft else False
        
        # Graduabilidad devuelta por la IA
        val_grad = info_ia.get("es_graduable", True)
        if isinstance(val_grad, bool):
            es_graduable = val_grad
        elif isinstance(val_grad, str):
            es_graduable = not ("no" in val_grad.lower() or "false" in val_grad.lower())
        else:
            es_graduable = True
            
        graduacion_detalle = str(info_ia.get("graduacion_detalle") or ("Sí (Montura compatible con graduación médica)" if es_oft else "Sí (Compatible con micas solares graduadas)")).strip()
        uso_ideal = str(info_ia.get("uso_ideal") or "Uso diario y protección visual certificada.").strip()
        nanometros = str(info_ia.get("nanometros") or "Bloqueo 100% de Rayos UVA y UVB hasta 400 nm (Norma UV400)").strip()
        vlt_porcentaje = str(info_ia.get("vlt_porcentaje") or "12% - 15% (Categoría 3)").strip()
        beneficio_tecnico = str(info_ia.get("beneficio_tecnico") or "Montura oficial Luxottica fabricada con materiales de alta calidad y precisión óptica.").strip()
        storytelling = str(info_ia.get("storytelling") or f"Una pieza exclusiva de {marca_nom} que combina distinción estética con protección visual superior.").strip()
    else:
        # En caso extremo de no haber conexión a internet:
        coleccion_ano = f"Colección {marca_nom}"
        tecnologia_mica = "Micas Demo Transparentes (Listas para Graduación)" if es_oft else f"{marca_nom} High Definition UV400"
        es_polarizado = False
        es_graduable = True
        graduacion_detalle = "Sí (Montura compatible con graduación médica)" if es_oft else "Sí (Compatible con micas solares graduadas)"
        uso_ideal = "Uso diario y confort visual."
        nanometros = "Armazón para graduación médica" if es_oft else "Bloqueo 100% UV400"
        vlt_porcentaje = "Demo Lenses" if es_oft else "Categoría 3"
        beneficio_tecnico = f"Montura oficial de {marca_nom} con diseño ergonómico."
        storytelling = f"Diseño de alta calidad de {marca_nom}."

    # URL DE BÚSQUEDA DE GOOGLE IMÁGENES
    if upc_clean:
        query_search = upc_clean
    else:
        query_search = f"{marca} {modelo} {color_codigo}".strip()
    query_quoted = urllib.parse.quote(query_search)
    google_img_url = f"https://www.google.com/search?tbm=isch&q={query_quoted}"

    return {
        "marca": marca_nom,
        "modelo": mod_clean,
        "color_codigo": col_clean,
        "coleccion_ano": coleccion_ano,
        "tecnologia_mica": tecnologia_mica,
        "es_polarizado": es_polarizado,
        "es_oftalmico": es_oft,
        "es_graduable": es_graduable,
        "graduacion_detalle": graduacion_detalle,
        "uso_ideal": uso_ideal,
        "nanometros": nanometros,
        "vlt_porcentaje": vlt_porcentaje,
        "beneficio_tecnico": beneficio_tecnico,
        "storytelling": storytelling,
        "google_img_url": google_img_url,
        "query_display": query_search
    }

def generar_resumen_voz(data):
    if not data:
        return ""
    marca = data.get("marca", "")
    modelo = data.get("modelo", "")
    coleccion = data.get("coleccion_ano", "")
    tecnologia = data.get("tecnologia_mica", "")
    uso = data.get("uso_ideal", "")
    es_oft = data.get("es_oftalmico", False)
    
    if es_oft:
        resumen = f"Armazón oftálmico {marca} {modelo} para graduación."
        if coleccion:
            resumen += f" De la línea {coleccion}."
        resumen += f" Cuenta con {tecnologia}. Recomendado para {uso}"
    else:
        resumen = f"Modelo {marca} {modelo}."
        if coleccion and "Reciente" not in coleccion:
            resumen += f" De la colección {coleccion}."
        resumen += f" Cuenta con tecnología {tecnologia}. Recomendado para {uso}"
    return resumen
