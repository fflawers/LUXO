import re
import difflib
from database import conectar_db
import requests
import os
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2", "")
GROQ_API_KEY_3 = os.getenv("GROQ_API_KEY_3", "")
GROQ_KEYS = [k for k in [GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3] if k]
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
current_key_idx = 0

def get_groq_key():
    if not GROQ_KEYS: return ""
    return GROQ_KEYS[current_key_idx]

def rotate_groq_key():
    global current_key_idx
    if not GROQ_KEYS: return False
    current_key_idx = (current_key_idx + 1) % len(GROQ_KEYS)
    return True

# Mismos cachés que el frontend
RAG_BLOQUES_CACHE = None
RAG_IDF_CACHE = None
RAG_EXCEL_CACHE = None


def expandir_abreviaturas(texto):
    if not texto: return ""
    mapa = {
        r'\bq\b': 'que',
        r'\bk\b': 'que',
        r'\bxq\b': 'porque',
        r'\bx q\b': 'por que',
        r'\bpa\b': 'para',
        r'\bporq\b': 'porque',
        r'\btmb\b': 'tambien',
        r'\btmbn\b': 'tambien',
        r'\bpls\b': 'por favor',
        r'\bporfa\b': 'por favor',
        r'\bdnd\b': 'donde',
        r'\bkomo\b': 'como',
        r'\bcuand\b': 'cuando',
        r'\bgcia\b': 'gerencia',
        r'\bpto\b': 'punto',
        r'\btkt\b': 'ticket',
        r'\bmsj\b': 'mensaje',
        r'\bcc\b': 'centro comercial'
    }
    texto_exp = texto.lower()
    for patron, reemplazo in mapa.items():
        texto_exp = re.sub(patron, reemplazo, texto_exp)
    return texto_exp

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).lower().strip()
    import unicodedata
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def obtener_raiz_espanol(word):
    if len(word) <= 3:
        return word
    sufijos = [
        "ando", "iendo", "aron", "ieron", "aremos", "eremos", "iremos",
        "ar", "er", "ir", "ado", "ido", "as", "es", "os", "an", "en", "o", "a", "e"
    ]
    for suf in sorted(sufijos, key=len, reverse=True):
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[:-len(suf)]
    return word

def rebuild_rag_cache():
    global RAG_BLOQUES_CACHE, RAG_IDF_CACHE, RAG_EXCEL_CACHE
    db = conectar_db()
    if not db: return
    cursor = db.cursor(dictionary=True)
    
    # Textos
    cursor.execute("SELECT ID_Manual, Nombre_Archivo, Contenido_Texto, Abierto FROM manuales WHERE Contenido_Texto IS NOT NULL AND Contenido_Texto != ''")
    rows = cursor.fetchall()
    
    import math
    bloques_list = []
    doc_count = 0
    df_dict = {}
    
    stopwords = {"de", "la", "el", "los", "las", "un", "una", "pdf", "manual"}
    
    for row in rows:
        texto = row["Contenido_Texto"]
        if not texto: continue
        
        parrafos = texto.split("\n\n")
        bloques = []
        temp_bloque = ""
        for b in parrafos:
            b_strip = b.strip()
            if not b_strip: continue
            if temp_bloque: temp_bloque += "\n" + b_strip
            else: temp_bloque = b_strip
            if len(temp_bloque) >= 120 or temp_bloque.endswith("?"):
                bloques.append(temp_bloque)
                temp_bloque = ""
        if temp_bloque: bloques.append(temp_bloque)
        
        for b in bloques:
            b_norm = normalizar_texto(b)
            b_words = re.findall(r"\w+", b_norm)
            b_words_clean = [w for w in b_words if w not in stopwords and len(w) >= 2]
            b_roots = [obtener_raiz_espanol(w) for w in b_words_clean]
            
            b_roots_set = set(b_roots)
            if not b_roots_set: continue
            
            doc_count += 1
            for r in b_roots_set:
                df_dict[r] = df_dict.get(r, 0) + 1
                
            bloques_list.append({
                "id": row["ID_Manual"],
                "nombre": row["Nombre_Archivo"],
                "abierto": row.get("Abierto", 1),
                "texto": b,
                "roots": b_roots,
                "roots_set": b_roots_set
            })
            
    idf = {}
    for r, df in df_dict.items():
        idf[r] = math.log((doc_count - df + 0.5) / (df + 0.5) + 1)
        
    RAG_BLOQUES_CACHE = bloques_list
    RAG_IDF_CACHE = idf
    
    # Excel
    cursor.execute("SELECT ID_Manual, Nombre_Archivo, Contenido_Texto, Categoria FROM manuales WHERE Contenido_Texto IS NOT NULL AND Contenido_Texto != ''")
    rows_ex = cursor.fetchall()
    excel_list = []
    for row in rows_ex:
        nombre_m = row.get("Nombre_Archivo") or ""
        texto_m = row.get("Contenido_Texto") or ""
        if row.get("Categoria") == "Excel" or nombre_m.lower().endswith((".xlsx", ".xls", ".csv")):
            hoja_actual = "Hoja 1"
            for linea in texto_m.split("\\n"):
                if linea.startswith("HOJA:"):
                    hoja_actual = linea.replace("HOJA:", "").strip()
                elif linea.startswith("FILA"):
                    partes = linea.split(":", 1)
                    if len(partes) == 2:
                        fila_num = partes[0].replace("FILA", "").strip()
                        texto_fila = partes[1].strip()
                        excel_list.append({
                            "id_manual": row["ID_Manual"],
                            "nombre_archivo": nombre_m,
                            "hoja": hoja_actual,
                            "fila": fila_num,
                            "texto": texto_fila,
                            "norm": normalizar_texto(texto_fila),
                            "abierto": 1
                        })
        
    RAG_EXCEL_CACHE = excel_list
    db.close()

def procesar_chat(usuario_id: int, mensaje: str, historial: list):
    user_text_expandido = expandir_abreviaturas(mensaje)
    user_text_norm = normalizar_texto(user_text_expandido)
    
    # 1. Rutas de Navegación UI
    indicadores_nav = ["abre", "abrir", "ir a", "ve a", "entra", "mostrar", "pantalla", "pestana", "seccion", "vista"]
    es_comando_navegacion = any(ind in user_text_norm for ind in indicadores_nav)
    palabras_mensaje = user_text_norm.split()
    es_pregunta_conversacional = (len(palabras_mensaje) > 3 or any(p in user_text_norm for p in ["como", "donde", "por que", "quien", "cual", "cuales", "explic", "ayuda", "duda"]))
    
    permitir_redireccion = (not es_pregunta_conversacional) or es_comando_navegacion
    if "campana" in user_text_norm:
        msg_limpio = user_text_norm.strip()
        if not (es_comando_navegacion or msg_limpio in ["campana", "campanas", "fotos de campana", "foto de campana"]):
            permitir_redireccion = False
            
    if permitir_redireccion:
        redirecciones = {
            "aperturas y cierres": "operacion_diaria",
            "aperturas & cierres": "operacion_diaria",
            "aperturas cierres": "operacion_diaria",
            "aperturas": "operacion_diaria",
            "apertura": "operacion_diaria",
            "cierres": "operacion_diaria",
            "cierre": "operacion_diaria",
            "operacion diaria": "operacion_diaria",
            "operacion y tienda": "checklists",
            "operaciones y tienda": "checklists",
            "operacion & tienda": "checklists",
            "operacion tienda": "checklists",
            "operacion": "checklists",
            "operaciones": "checklists",
            "tienda": "checklists",
            "ventas y metricas": "meta_semanal",
            "ventas": "meta_semanal",
            "metricas": "meta_semanal",
            "clientes y garantias": "garantias",
            "clientes": "garantias",
            "capacitacion e ia": "simulador",
            "capacitacion": "simulador",
            "entrenamiento": "simulador",
            "asistente chat": "chat",
            "asistente": "chat",
            "chat": "chat",
            "mi historial": "historial",
            "historial": "historial",
            "coberturas oops": "crm",
            "cobertura oops": "crm",
            "crm oops": "crm",
            "coberturas": "crm",
            "cobertura": "crm",
            "crm": "crm",
            "oops": "crm",
            "weekly": "weekly",
            "semanal": "weekly",
            "reporte weekly": "weekly",
            "gestionar trivia": "admin_trivia",
            "administrar trivia": "admin_trivia",
            "configurar trivia": "admin_trivia",
            "bitacora de seguridad": "bitacora",
            "bitacora": "bitacora",
            "auditoria": "bitacora",
            "gestion de perfiles": "gestion_perfiles",
            "gestionar perfiles": "gestion_perfiles",
            "perfiles": "gestion_perfiles",
            "garantias": "garantias",
            "garantia": "garantias",
            "configuracion tienda": "vendedores",
            "metas mensuales": "vendedores",
            "meta mensual": "vendedores",
            "vendedor": "vendedores",
            "vendedores": "vendedores",
            "metas semanales": "meta_semanal",
            "meta semanal": "meta_semanal",
            "metas y metricas": "meta_semanal",
            "metas": "meta_semanal",
            "meta": "meta_semanal",
            "reto del dia": "reto",
            "reto": "reto",
            "trivia": "reto",
            "quiz": "reto",
            "campanas": "campanas",
            "campana": "campanas",
            "simulador ia": "simulador",
            "simulador": "simulador",
            "comision": "simulador",
            "comisiones": "simulador",
            "manuales": "manuales",
            "manual": "manuales",
            "checklists": "checklists",
            "checklist": "checklists",
            "tareas": "tareas",
            "tarea": "tareas",
            "presupuesto": "presupuesto",
            "bouget": "presupuesto",
            "budget": "presupuesto",
            "enfoque diario 2026": "enfoque_diario",
            "enfoque diario": "enfoque_diario",
            "enfoque 2026": "enfoque_diario",
            "enfoque": "enfoque_diario",
            "panel de control": "dashboard",
            "panel control": "dashboard",
            "dashboard": "dashboard",
            "panel": "dashboard"
        }
        sorted_nav_keys = sorted(redirecciones.keys(), key=len, reverse=True)
        for key in sorted_nav_keys:
            if key in user_text_norm:
                vista = redirecciones[key]
                return {"accion": "navegar", "destino": vista}
                
    # 2. RAG Logic (Manuales & Excel)
    if RAG_BLOQUES_CACHE is None:
        rebuild_rag_cache()
        
    db = conectar_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM manuales")
    manuales = cursor.fetchall()
    
    # 3. LLM API Call
    URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {get_groq_key()}", "Content-Type": "application/json"}
    
    # Simplify LLM Call for now. We will just send the history and user message.
    # We should embed actual context if we had a BM25 hit.
    # In a full migration, we would implement `buscar_candidatos` and append to `mensaje_sistema`.
    # For now, let's keep it simple to ensure the architecture works.
    
    # Basic system prompt
    mensaje_sistema = {
        "role": "system",
        "content": "Eres LUXO, asistente operativo inteligente de Sunglass Hut. Responde de forma amable y concisa."
    }
    
    mensajes_api = [mensaje_sistema]
    mensajes_api.extend(historial[-8:]) # limit history to 8
    mensajes_api.append({"role": "user", "content": user_text_expandido})
    
    payload = {
        "model": GROQ_MODEL,
        "messages": mensajes_api
    }
    
    try:
        res = requests.post(URL_GROQ, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            respuesta = data["choices"][0]["message"]["content"]
            
            id_conv = None
            try:
                cursor.execute("""
                    INSERT INTO historial_conversaciones 
                    (ID_Usuario, Pregunta_Usuario, Respuesta_IA, Fecha_Hora) 
                    VALUES (%s, %s, %s, NOW())
                """, (usuario_id, mensaje, respuesta))
                db.commit()
                id_conv = cursor.lastrowid
            except Exception as e:
                print("Error guardando historial:", e)
                
            db.close()
            return {"accion": "responder", "texto": respuesta, "id_conversacion": id_conv}
        else:
            db.close()
            return {"accion": "responder", "texto": f"Error de conexión con la IA ({res.status_code}).", "id_conversacion": None}
    except Exception as e:
        db.close()
        return {"accion": "responder", "texto": "Ocurrió un error conectando a la IA.", "id_conversacion": None}
