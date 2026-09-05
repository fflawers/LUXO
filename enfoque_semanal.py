# -*- coding: utf-8 -*-
"""
MÓDULO: Enfoque Semanal SGH (¡ENFOQUÉMONOS!)
Metodología oficial Sunglass Hut Experience: INVITA · CONECTA · AGRADECE
Diseño visual de cuadrícula fiel a la bitácora física oficial de tienda.
"""

import os
import json
import datetime
import flet as ft

# ==============================================================================
# CONFIGURACIÓN Y METAS MÍNIMAS OFICIALES SGH TIENDA (LOS 7 INDICADORES CLAVE)
# ==============================================================================
SGH_MINIMUM_TARGETS = {
    "Conversión (% CONV)": "18%",
    "Múltiples (% MULT)": "45%",
    "AUR (Sun AUR)": "Meta Tienda",
    "PPT (Piezas x Transacción)": "1.45",
    "Polarizado (% POL)": "45%",
    "% Cumplimiento (% COMP)": "100%",
    "Lujo (% LUX)": "45%"
}

# ==============================================================================
# MATRIZ OFICIAL SGH: LOS 3 PILARES Y BLOQUES DE CONDUCTA (IMAGEN 2)
# ==============================================================================
# 1. INVITA   -> Bloque: "Atrae y da la bienvenida"
# 2. CONECTA  -> Bloques: "Crea una conexión auténtica" & "Sé un excelente anfitrión"
# 3. AGRADECE -> Bloque: "Agradece la visita"

SGH_BLOQUES = {
    # INVITA (Atrae y da la bienvenida)
    "Los clientes son primero": ("Invita", "💡 Consejo Analítico: Prioriza al cliente presencial sobre cualquier tarea operativa; dale contacto visual inmediato."),
    "Sonríe con propósito": ("Invita", "💡 Consejo Analítico: Saludar con energía y sonrisa sincera en los primeros 15 segundos eleva la disposición de compra en 30%."),
    "Di tu nombre y pide que te den el suyo": ("Invita", "💡 Consejo Analítico: Presentarte por tu nombre rompe la barrera comercial y conecta inmediatamente con el cliente."),
    "Muestra la tienda": ("Invita", "💡 Consejo Analítico: Guía al cliente hacia las novedades y muros de marcas icónicas; eleva el valor del ticket."),
    
    # CONECTA (Crea una conexión auténtica / Sé un excelente anfitrión)
    "Háblale por su nombre": ("Conecta", "💡 Consejo Analítico: Repetir su nombre 2 veces durante la prueba genera empatía y fidelidad hacia la recomendación."),
    "Realiza preguntas y escucha": ("Conecta", "💡 Consejo Analítico: Haz preguntas abiertas sobre su estilo de vida al sol antes de mostrar producto para perfilar la recomendación."),
    "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder": ("Conecta", "💡 Consejo Analítico: Pule las gafas frente al cliente antes de entregarlas; el brillo impecable impulsa la decisión de compra."),
    "Plática significativa y uso del SmartShopper": ("Conecta", "💡 Consejo Analítico: Explora el catálogo digital SmartShopper para modelos exclusivos y elevar el ticket promedio."),
    "Vuelve a acercarte al cliente y reconecta": ("Conecta", "💡 Consejo Analítico: Si el cliente duda en el espejo, acércate con el probador de polarizado para demostrar la eliminación de reflejos."),
    "Repite hasta cerrar la venta": ("Conecta", "💡 Consejo Analítico: Aplica la regla de 3 ofreciendo un segundo par complementario o accesorio antes de llegar a caja."),
    
    # AGRADECE (Agradece la visita)
    "Ajuste Perfecto": ("Agradece", "💡 Consejo Analítico: El ajuste perfecto de plaquetas y varillas al rostro del cliente asegura una experiencia memorable."),
    "Agradece por su nombre": ("Agradece", "💡 Consejo Analítico: Despide con calidez entregando la bolsa con ambas manos y agradeciendo por su nombre."),
    "Informa y mantente conectado": ("Agradece", "💡 Consejo Analítico: Explica los beneficios y servicios de limpieza y ajuste gratuitos de por vida en cualquier tienda.")
}

# MAPEO DE CADA KPI A SUS CONDUCTAS OFICIALES SEGÚN LA MATRIZ SGH
SGH_KPI_MAPPING = {
    "Conversión (% CONV)": [
        "Los clientes son primero",
        "Sonríe con propósito",
        "Di tu nombre y pide que te den el suyo",
        "Muestra la tienda",
        "Háblale por su nombre",
        "Realiza preguntas y escucha"
    ],
    "Polarizado (% POL)": [
        "Vuelve a acercarte al cliente y reconecta",
        "Realiza preguntas y escucha",
        "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder",
        "Informa y mantente conectado"
    ],
    "Múltiples (% MULT)": [
        "Repite hasta cerrar la venta",
        "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder",
        "Realiza preguntas y escucha"
    ],
    "PPT (Piezas x Transacción)": [
        "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder",
        "Repite hasta cerrar la venta",
        "Realiza preguntas y escucha"
    ],
    "AUR (Sun AUR)": [
        "Plática significativa y uso del SmartShopper",
        "Muestra la tienda",
        "Realiza preguntas y escucha",
        "Informa y mantente conectado"
    ],
    "Lujo (% LUX)": [
        "Muestra la tienda",
        "Plática significativa y uso del SmartShopper",
        "Ajuste Perfecto"
    ],
    "% Cumplimiento (% COMP)": [
        "Ajuste Perfecto",
        "Informa y mantente conectado",
        "Agradece por su nombre",
        "Sonríe con propósito",
        "Los clientes son primero"
    ]
}

def obtener_llaves_activas():
    keys = []
    for var in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"]:
        k = os.getenv(var, "").strip()
        if k and k not in keys:
            keys.append(k)
    cfg_paths = [
        os.path.join(BASE_DIR, "config.json"),
        os.path.join(os.path.dirname(BASE_DIR), "config.json")
    ]
    for p in cfg_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if isinstance(cfg, dict):
                        for m in cfg.get("models", []):
                            k = m.get("apiKey", "").strip()
                            if k and k not in keys:
                                keys.append(k)
            except Exception:
                pass
    return keys

def generar_consejo_desarrollo_ia(kpi_d, conducta_d, val_act_d, meta_d, extra_ctx="", rotacion_index=0):
    """Genera un consejo de desarrollo libre, analítico y contextualizado con IA para piso de venta."""
    keys = obtener_llaves_activas()
    
    # 1. Intentar consulta libre con IA en vivo (Groq / OpenRouter)
    if keys:
        system_prompt = (
            "Eres LUXO AI, el coach analítico y experto en ventas retail para tiendas Sunglass Hut (SGH). "
            "Genera un ÚNICO consejo táctico, libre y persuasivo de desarrollo para el equipo en piso de venta frente al cliente. "
            "Reglas obligatorias: "
            "1. Redacta de 1 a máximo 2 oraciones muy prácticas, claras y accionables en el piso de venta (en el espejo o probador). "
            "2. Conecta de forma natural la conducta SGH con el indicador de oportunidad y el contexto de venta. "
            "3. NO des introducciones, saludos ni explicaciones. Responde ÚNICAMENTE empezando con: "
            "💡 Consejo de Desarrollo: [tu consejo]"
        )
        user_msg = (
            f"Indicador bajo (Oportunidad): {kpi_d}\n"
            f"Resultado actual de la tienda: {val_act_d} (Meta SGH esperada: {meta_d})\n"
            f"Conducta oficial SGH asignada: {conducta_d}\n"
            f"Contexto o detalle de tienda: {extra_ctx or 'Ninguno'}\n"
            f"Genera el consejo táctico para cerrar la brecha métrica:"
        )
        
        for key in keys:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            target_url = "https://openrouter.ai/api/v1/chat/completions" if key.startswith("sk-or-") else "https://api.groq.com/openai/v1/chat/completions"
            models = ["groq/compound-mini", "meta-llama/llama-3.3-70b-instruct"] if key.startswith("sk-or-") else ["groq/compound-mini", "groq/compound", "qwen/qwen3.6-27b"]
            
            for mod in models:
                try:
                    payload = {
                        "model": mod,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg}
                        ],
                        "temperature": 0.75
                    }
                    res = requests.post(target_url, headers=headers, json=payload, timeout=3.5)
                    if res.status_code == 200:
                        data = res.json()
                        if "choices" in data and data["choices"]:
                            txt = data["choices"][0]["message"]["content"].strip()
                            txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL).strip()
                            if not txt.startswith("💡"):
                                if "Consejo de Desarrollo:" in txt:
                                    txt = "💡 " + txt[txt.find("Consejo de Desarrollo:"):]
                                else:
                                    txt = f"💡 Consejo de Desarrollo: {txt}"
                            return txt
                except Exception:
                    continue

    # 2. Catálogo dinámico y variado de respaldo (Fallback pedagógico SGH por KPI y Conducta)
    FALLBACKS = {
        "Polarizado": [
            "💡 Consejo de Desarrollo: Cuando el cliente tenga las gafas en el rostro, acércate con el probador de polarizado frente al espejo para evidenciar el 100% de eliminación de reflejos.",
            "💡 Consejo de Desarrollo: Haz la pregunta clave: '¿Manejas de día o realizas actividades al aire libre?' para justificar la tecnología polarizada antes de mencionar el precio.",
            "💡 Consejo de Desarrollo: Pule las gafas polarizadas frente al cliente y colócalas en sus manos invitándolo a mirar hacia una zona iluminada de la tienda.",
            "💡 Consejo de Desarrollo: Explica la protección UV400 y cómo la mica polarizada reduce el cansancio visual en un 80% frente a una mica convencional."
        ],
        "Conversión": [
            "💡 Consejo de Desarrollo: Saluda al cliente en los primeros 15 segundos y acompáñalo con 2 preguntas abiertas sobre qué estilo o marca prefiere hoy.",
            "💡 Consejo de Desarrollo: Presenta 3 modelos diferentes de forma consecutiva para mantener su atención y encontrar rápidamente su estilo ideal.",
            "💡 Consejo de Desarrollo: Guía al cliente al muro de marcas icónicas y rétalo a probarse un estilo nuevo que eleve su seguridad.",
            "💡 Consejo de Desarrollo: Si un cliente parece indeciso, acércate con una segunda opción y resalta un beneficio clave para facilitar su decisión de compra."
        ],
        "Múltiples": [
            "💡 Consejo de Desarrollo: Mientras el cliente se prueba su par favorito, acércale un segundo modelo con un uso distinto (deportivo vs casual) antes de ir a caja.",
            "💡 Consejo de Desarrollo: Ofrece la promoción de segundo par o complementos de limpieza y estuches especiales para asegurar 2 o más piezas por transacción.",
            "💡 Consejo de Desarrollo: Usa la técnica de 'Uno para ti y uno para regalo' o 'Uno para manejar y otro para el fin de semana' para cerrar pares adicionales."
        ],
        "PPT": [
            "💡 Consejo de Desarrollo: Aplica la regla del kit completo: cada armazón debe presentarse acompañado de microfibra premium, spray limpiador o cordón.",
            "💡 Consejo de Desarrollo: Invita al cliente a aprovechar el viaje a tienda para llevar una opción de reemplazo o un accesorio de protección con descuento.",
            "💡 Consejo de Desarrollo: Antes de procesar el pago, muestra físicamente el kit de cuidado y explica la garantía de por vida en ajustes."
        ],
        "AUR": [
            "💡 Consejo de Desarrollo: Utiliza el catálogo SmartShopper en tablet para mostrar ediciones limitadas y modelos premium exclusivos no exhibidos en piso.",
            "💡 Consejo de Desarrollo: Enfoca la conversación en el valor artesanal, materiales como titanio o acetato pulido a mano y prestigio de marca.",
            "💡 Consejo de Desarrollo: Realiza un recorrido por las marcas de alta gama de la tienda invitando a probar piezas icónicas de temporada."
        ],
        "Lujo": [
            "💡 Consejo de Desarrollo: Presenta piezas de firmas de lujo sobre paño de exhibición y resalta la exclusividad del diseño y acabados de lujo.",
            "💡 Consejo de Desarrollo: Aprovecha el SmartShopper para buscar lanzamientos internacionales de marcas de lujo y elevar el ticket promedio.",
            "💡 Consejo de Desarrollo: Ofrece el ajuste personalizado y entrega el empaque premium con ambas manos para transmitir el valor de lujo."
        ],
        "Cumplimiento": [
            "💡 Consejo de Desarrollo: Asegura que cada cliente reciba la bienvenida cálida y el ajuste perfecto antes de salir de la tienda.",
            "💡 Consejo de Desarrollo: Explica detalladamente los beneficios postventa y agradece al cliente llamándolo por su nombre al despedirlo."
        ]
    }
    
    for kpi_key, tips in FALLBACKS.items():
        if kpi_key.lower() in kpi_d.lower():
            idx = rotacion_index % len(tips)
            return tips[idx]
            
    return f"💡 Consejo de Desarrollo: Aplica la técnica de {conducta_d} de manera consistente en cada interacción para elevar {kpi_d} hacia {meta_d}."

def resolver_conducta_fuerte(kpi_f, extra_f, rotacion_idx=0):
    """Determina la conducta exacta para la Fortaleza según el KPI, el comentario opcional y la rotación semanal."""
    extra_lower = (extra_f or "").lower().strip()
    candidatas = SGH_KPI_MAPPING.get(kpi_f, ["Realiza preguntas y escucha"])
    
    if "Conversión" in kpi_f or "CONV" in kpi_f:
        if any(w in extra_lower for w in ["sonrisa", "saludo", "bienvenida", "energia", "puerta"]):
            return "Sonríe con propósito"
        elif any(w in extra_lower for w in ["nombre", "presentarse", "presento"]):
            return "Di tu nombre y pide que te den el suyo"
        elif any(w in extra_lower for w in ["tienda", "tour", "muros"]):
            return "Muestra la tienda"
        elif any(w in extra_lower for w in ["pregunto", "escucho", "indago", "necesidad"]):
            return "Realiza preguntas y escucha"
        elif extra_lower:
            return "Los clientes son primero"
            
    elif "Polarizado" in kpi_f or "POL" in kpi_f:
        if any(w in extra_lower for w in ["sol", "manejo", "conducir", "deporte", "pregunta"]):
            return "Realiza preguntas y escucha"
        elif any(w in extra_lower for w in ["pulir", "manos", "probar"]):
            return "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder"
        elif any(w in extra_lower for w in ["garantia", "proteccion", "uv"]):
            return "Informa y mantente conectado"
        elif extra_lower:
            return "Vuelve a acercarte al cliente y reconecta"
            
    elif "Múltiples" in kpi_f or "MULT" in kpi_f:
        if any(w in extra_lower for w in ["pulir", "probar", "espejo", "manos"]):
            return "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder"
        elif any(w in extra_lower for w in ["pregunta", "estilo", "ocasion"]):
            return "Realiza preguntas y escucha"
        elif extra_lower:
            return "Repite hasta cerrar la venta"
            
    elif "PPT" in kpi_f:
        if any(w in extra_lower for w in ["cerrar", "2do par", "segundo par", "kit", "cordon", "estuche", "equipo"]):
            return "Repite hasta cerrar la venta"
        elif any(w in extra_lower for w in ["pregunta", "cuidado"]):
            return "Realiza preguntas y escucha"
        elif extra_lower:
            return "Personaliza la Experiencia e invita a que se pruebe las gafas, recuerda que pulir es poder"
            
    elif "AUR" in kpi_f:
        if any(w in extra_lower for w in ["tienda", "muro", "marcas"]):
            return "Muestra la tienda"
        elif any(w in extra_lower for w in ["pregunta", "valor"]):
            return "Realiza preguntas y escucha"
        elif extra_lower:
            return "Plática significativa y uso del SmartShopper"
            
    elif "Lujo" in kpi_f or "LUX" in kpi_f:
        if any(w in extra_lower for w in ["smartshopper", "catalogo", "digital"]):
            return "Plática significativa y uso del SmartShopper"
        elif any(w in extra_lower for w in ["ajuste", "estuche", "certificado"]):
            return "Ajuste Perfecto"
        elif extra_lower:
            return "Muestra la tienda"
            
    elif "Cumplimiento" in kpi_f or "COMP" in kpi_f:
        if any(w in extra_lower for w in ["garantia", "postventa", "seguimiento"]):
            return "Informa y mantente conectado"
        elif any(w in extra_lower for w in ["despedida", "nombre", "calidez"]):
            return "Agradece por su nombre"
        elif any(w in extra_lower for w in ["bienvenida", "energia"]):
            return "Los clientes son primero"
        elif extra_lower:
            return "Ajuste Perfecto"

    # Si no hay palabra clave o es rotación general:
    return candidatas[rotacion_idx % len(candidatas)]

def calcular_meta_incremental(val_actual_str, meta_oficial_str):
    """Calcula una meta semanal realista y progresiva basada en el resultado actual."""
    clean_val = str(val_actual_str).replace("%", "").strip()
    clean_meta = str(meta_oficial_str).replace("%", "").strip()
    
    try:
        # Caso decimal (ej. PPT 1.14 o 1.45)
        if "." in clean_val or "." in clean_meta:
            val_num = float(clean_val)
            meta_num = float(clean_meta)
            if val_num < meta_num:
                paso = round(val_num + 0.15, 2)
                if paso >= meta_num:
                    return f"Subir a {meta_num} (Meta Tienda SGH)"
                return f"Subir a {paso} (Rumbo a {meta_num} PPT)"
            else:
                return f"Mantener arriba de {val_num}"
        # Caso porcentaje (ej. 8%, 14%, 45%)
        elif clean_val.isdigit() and clean_meta.isdigit():
            val_num = int(clean_val)
            meta_num = int(clean_meta)
            if val_num < meta_num:
                dif = meta_num - val_num
                if dif <= 5:
                    return f"Subir a {meta_num}% (Meta Tienda SGH)"
                elif dif <= 15:
                    paso = val_num + 4
                    return f"Subir a {paso}% (Rumbo a {meta_num}%)"
                else:
                    paso = val_num + 8
                    return f"Subir a {paso}% (Rumbo a {meta_num}%)"
            else:
                return f"Mantener arriba de {val_num}%"
    except Exception:
        pass
    return f"Subir a {meta_oficial_str} (Meta Tienda SGH)"

def get_current_week_number():
    """Calcula el número de la semana actual del año."""
    try:
        now = datetime.datetime.now()
        return now.isocalendar()[1]
    except Exception:
        return 35

# ==============================================================================
# PERSISTENCIA LOCAL DE ESTADO
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_state_file_path(store_code="general"):
    clean_code = "".join(filter(str.isalnum, str(store_code))) or "general"
    return os.path.join(BASE_DIR, f"enfoque_semanal_state_tienda_{clean_code}.json")

def load_enfoque_semanal_state(store_code="general"):
    filepath = get_state_file_path(store_code)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_enfoque_semanal_state(state_data, store_code="general"):
    filepath = get_state_file_path(store_code)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        print("Error guardando estado enfoque semanal:", ex)


# ==============================================================================
# VISTA PRINCIPAL FLET: ENFOQUE SEMANAL SGH (RÉPLICA AUTÉNTICA Y SIMÉTRICA)
# ==============================================================================
def build_enfoque_semanal_view(page: ft.Page, user_info=None):
    if user_info is None:
        user_info = {}

    is_mobile = (page.width < 750) if (page and page.width) else False

    st_u = str(user_info.get("usuario") or "").strip()
    st_digits = "".join(filter(str.isdigit, st_u))
    store_code = st_digits if st_digits else str(user_info.get("codigo_tienda") or user_info.get("tienda") or "A540").strip()

    initial_state = load_enfoque_semanal_state(store_code)
    current_week = initial_state.get("semana", get_current_week_number())

    # --- Lista de Colaboradores de Tienda ---
    colab_names = ["Romo", "Diego", "Moisés", "Ana", "Carlos", "Sofía", "Equipo Tienda"]
    try:
        import enfoque_diario
        stored_colabs = enfoque_diario.cargar_colaboradores(user_info)
        if stored_colabs and isinstance(stored_colabs, list):
            nombres_reales = [c.get("nombre") for c in stored_colabs if isinstance(c, dict) and c.get("nombre")]
            if nombres_reales:
                colab_names = nombres_reales
    except Exception:
        pass

    kpis_list = list(SGH_MINIMUM_TARGETS.keys())

    # --- Dropdowns de Entrada Rápida ---
    dd_semana = ft.Dropdown(
        value=str(current_week),
        options=[ft.dropdown.Option(str(w)) for w in range(1, 53)],
        width=90,
        height=36,
        content_padding=ft.Padding(8, 0, 8, 0),
        bgcolor="#181828",
        border_color="#00FFFF",
        text_size=13
    )

    # 1. Colaborador (Conducta / Fortaleza) - Editable libremente
    tf_colab_fuerte = ft.TextField(
        value=initial_state.get("colab_fuerte", initial_state.get("colab_fuerte_1", "Romo")),
        hint_text="Ej. Romo / Apoyo",
        height=36,
        content_padding=ft.Padding(8, 2, 8, 2),
        bgcolor="#141424",
        border_color="#00FFFF",
        focused_border_color="#00FFFF",
        text_size=12
    )

    kpi_fuerte_val = initial_state.get("kpi_fuerte", "Polarizado (% POL)")
    if kpi_fuerte_val not in kpis_list:
        kpi_fuerte_val = "Polarizado (% POL)"

    dd_kpi_fuerte = ft.Dropdown(
        value=kpi_fuerte_val,
        options=[ft.dropdown.Option(k) for k in kpis_list],
        height=36,
        content_padding=ft.Padding(8, 0, 8, 0),
        bgcolor="#141424",
        border_color="#00FFFF",
        text_size=12
    )

    tf_valor_actual_fuerte = ft.TextField(
        value=initial_state.get("actuales_fuerte", "50%"),
        hint_text="Ej. 50% ó 1.55",
        height=36,
        content_padding=ft.Padding(8, 4, 8, 4),
        bgcolor="#141424",
        border_color="#00FFFF",
        focused_border_color="#00FFFF",
        text_size=12
    )

    tf_extra_fuerte = ft.TextField(
        value=initial_state.get("extra_fuerte", ""),
        hint_text="Ej. Vendió en equipo, demostró polarizado con tester, buscó en SmartShopper...",
        height=36,
        content_padding=ft.Padding(8, 4, 8, 4),
        bgcolor="#141424",
        border_color="#3A3E5B",
        focused_border_color="#00FFFF",
        text_size=12
    )

    # 2. Indicador Bajo (Área de Desarrollo)
    kpi_debil_val = initial_state.get("kpi_debil", "PPT (Piezas x Transacción)")
    if kpi_debil_val not in kpis_list:
        kpi_debil_val = "PPT (Piezas x Transacción)"

    dd_kpi_debil = ft.Dropdown(
        value=kpi_debil_val,
        options=[ft.dropdown.Option(k) for k in kpis_list],
        height=36,
        content_padding=ft.Padding(8, 0, 8, 0),
        bgcolor="#141424",
        border_color="#FF7A33",
        text_size=12
    )

    tf_valor_actual_debil = ft.TextField(
        value=initial_state.get("valor_actual_debil", "14%"),
        hint_text="Ej. 14% ó 1.15",
        height=36,
        content_padding=ft.Padding(8, 4, 8, 4),
        bgcolor="#141424",
        border_color="#FF7A33",
        focused_border_color="#FF7A33",
        text_size=12
    )

    # --- Creador de Inputs para las Celdas de la Cuadrícula ---
    def crear_input_celda(val, color="#00FFFF", font_size=13, bold=True, multiline=False, min_lines=1, align=ft.TextAlign.LEFT, dense=False, height=None):
        return ft.TextField(
            value=val,
            text_size=font_size,
            multiline=multiline,
            min_lines=min_lines,
            dense=dense,
            height=height,
            text_align=align,
            content_padding=ft.Padding(4, 2, 4, 2) if not dense else ft.Padding(2, 2, 2, 2),
            bgcolor="transparent",
            border=ft.InputBorder.NONE,
            focused_border_color="transparent",
            cursor_color=color,
            text_style=ft.TextStyle(color=color, weight="bold" if bold else "normal")
        )

    # Izquierda (Fortaleza)
    tf_fuerza_comp = crear_input_celda(initial_state.get("fuerza_comp", "Conecta"), color="#00FFFF", font_size=15)
    tf_mejor_colab = crear_input_celda(initial_state.get("mejor_colab", initial_state.get("mejor_colab_1", "Romo")), color="#FFFFFF", font_size=14)
    tf_indicador_fuerte = crear_input_celda(initial_state.get("indicador_fuerte", "Polarizado"), color="#00FFFF", font_size=14)
    tf_accion_mantener = crear_input_celda(initial_state.get("accion_mantener", "Realiza preguntas y escucha.\n💡 Consejo Analítico: Indaga sobre actividades al aire libre antes de sugerir."), color="#E2E8F0", font_size=11.5, bold=False, multiline=True, min_lines=2)
    tf_previstos_fuerte = crear_input_celda(initial_state.get("previstos_fuerte", "Mantener arriba del 45% (Meta SGH)"), color="#7CFC00", font_size=11.5 if is_mobile else 12.5, multiline=True, min_lines=1)
    tf_actuales_fuerte = crear_input_celda(initial_state.get("actuales_fuerte", "50%"), color="#FFFFFF", font_size=12 if is_mobile else 13, bold=True, align=ft.TextAlign.CENTER, dense=True, height=28)

    # Derecha (Desarrollo)
    tf_desarrollo_comp = crear_input_celda(initial_state.get("desarrollo_comp", "Conecta"), color="#FF7A33", font_size=15)
    tf_indicador_debil = crear_input_celda(initial_state.get("indicador_debil", "PPT"), color="#FF7A33", font_size=14)
    tf_accion_desarrollo = crear_input_celda(initial_state.get("accion_desarrollo", "Repite hasta cerrar la venta.\n💡 Consejo de Desarrollo: Presenta siempre un segundo par complementario en el espejo."), color="#E2E8F0", font_size=11.5, bold=False, multiline=True, min_lines=2)
    tf_previstos_debil = crear_input_celda(initial_state.get("previstos_debil", "Subir a 1.45 (Meta Tienda SGH)"), color="#FFD700", font_size=11.5 if is_mobile else 12.5, multiline=True, min_lines=1)
    tf_actuales_debil = crear_input_celda(initial_state.get("actuales_debil", "14%"), color="#FFFFFF", font_size=12 if is_mobile else 13, bold=True, align=ft.TextAlign.CENTER, dense=True, height=28)

    rotacion_estado = {"fuerte": 0, "desarrollo": 0}

    def ejecutar_cruce_inteligente(e=None, rotar=False):
        if rotar:
            rotacion_estado["fuerte"] += 1
            rotacion_estado["desarrollo"] += 1

        kpi_f = dd_kpi_fuerte.value or "Polarizado (% POL)"
        colab_f = tf_colab_fuerte.value.strip() or "Romo"
        extra_f = tf_extra_fuerte.value.strip()

        kpi_d = dd_kpi_debil.value or "PPT (Piezas x Transacción)"
        val_act_d = tf_valor_actual_debil.value.strip() or "14%"
        val_act_f = tf_valor_actual_fuerte.value.strip() or "50%"

        # ======================================================================
        # 1. ANÁLISIS DE FORTALEZA SEGÚN MATRIZ OFICIAL SGH (ROTACIÓN DE CONDUCTAS)
        # ======================================================================
        conducta_f = resolver_conducta_fuerte(kpi_f, extra_f, rotacion_estado["fuerte"])
        pilar_f, consejo_f = SGH_BLOQUES.get(conducta_f, ("Invita", "💡 Consejo Analítico: Prioriza al cliente presencial."))

        clean_kpi_name_f = kpi_f.split("(")[0].strip()
        previsto_texto_f = f"Mantener arriba de {val_act_f}" if val_act_f else f"Mantener arriba del {SGH_MINIMUM_TARGETS.get(kpi_f, '45%')}"

        tf_fuerza_comp.value = pilar_f.capitalize()
        tf_mejor_colab.value = colab_f
        tf_indicador_fuerte.value = clean_kpi_name_f
        tf_accion_mantener.value = f"{conducta_f}.\n{consejo_f}"
        tf_previstos_fuerte.value = previsto_texto_f
        tf_actuales_fuerte.value = val_act_f

        # ======================================================================
        # 2. ÁREA DE DESARROLLO (CONSEJO LIBRE Y DINÁMICO GENERADO POR IA)
        # ======================================================================
        candidatas_d = SGH_KPI_MAPPING.get(kpi_d, ["Repite hasta cerrar la venta"])
        candidatas_d_filtradas = [c for c in candidatas_d if c != conducta_f]
        if not candidatas_d_filtradas:
            candidatas_d_filtradas = candidatas_d

        conducta_d = candidatas_d_filtradas[rotacion_estado["desarrollo"] % len(candidatas_d_filtradas)]
        pilar_d, _ = SGH_BLOQUES.get(conducta_d, ("Conecta", ""))

        clean_kpi_name_d = kpi_d.split("(")[0].strip()
        meta_min_d = SGH_MINIMUM_TARGETS.get(kpi_d, "45%")
        previsto_texto_d = calcular_meta_incremental(val_act_d, meta_min_d)

        # Llamada a la IA para generar el consejo de desarrollo libre y táctico para piso de venta
        consejo_d_dinamico = generar_consejo_desarrollo_ia(
            kpi_d=clean_kpi_name_d,
            conducta_d=conducta_d,
            val_act_d=val_act_d,
            meta_d=meta_min_d,
            extra_ctx=extra_f,
            rotacion_index=rotacion_estado["desarrollo"]
        )

        tf_desarrollo_comp.value = pilar_d.capitalize()
        tf_indicador_debil.value = clean_kpi_name_d
        tf_accion_desarrollo.value = f"{conducta_d}.\n{consejo_d_dinamico}"
        tf_previstos_debil.value = previsto_texto_d
        tf_actuales_debil.value = val_act_d

        guardar_estado(mostrar_alerta=False)
        if page:
            page.snack_bar = ft.SnackBar(ft.Text("⚡ ¡Enfoque Semanal actualizado con Inteligencia Artificial!"), bgcolor="#008080")
            page.snack_bar.open = True
            page.update()

    # Vinculación de eventos on_change para reactividad instantánea
    dd_kpi_fuerte.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=False)
    dd_kpi_debil.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=False)
    tf_valor_actual_fuerte.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=False)
    tf_valor_actual_debil.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=False)
    tf_extra_fuerte.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=False)
    tf_colab_fuerte.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=False)
    dd_semana.on_change = lambda e: ejecutar_cruce_inteligente(e, rotar=True)

    def guardar_estado(e=None, mostrar_alerta=True):
        data = {
            "semana": dd_semana.value,
            "colab_fuerte": tf_colab_fuerte.value,
            "kpi_fuerte": dd_kpi_fuerte.value,
            "actuales_fuerte": tf_valor_actual_fuerte.value,
            "extra_fuerte": tf_extra_fuerte.value,
            "kpi_debil": dd_kpi_debil.value,
            "valor_actual_debil": tf_valor_actual_debil.value,
            "fuerza_comp": tf_fuerza_comp.value,
            "mejor_colab": tf_mejor_colab.value,
            "indicador_fuerte": tf_indicador_fuerte.value,
            "accion_mantener": tf_accion_mantener.value,
            "previstos_fuerte": tf_previstos_fuerte.value,
            "desarrollo_comp": tf_desarrollo_comp.value,
            "indicador_debil": tf_indicador_debil.value,
            "accion_desarrollo": tf_accion_desarrollo.value,
            "previstos_debil": tf_previstos_debil.value,
            "actuales_debil": tf_actuales_debil.value,
            "timestamp": datetime.datetime.now().isoformat()
        }
        save_enfoque_semanal_state(data, store_code)
        if mostrar_alerta and page:
            page.snack_bar = ft.SnackBar(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#7CFC00", size=18),
                    ft.Text("✅ ¡Enfoque Semanal guardado exitosamente!", color="white", weight="bold", size=13)
                ], spacing=8),
                bgcolor="#1B4332",
                duration=3500
            )
            page.snack_bar.open = True
            page.update()

    # Detección de dispositivo móvil / pantalla angosta (oculta columna 0 y adapta panel superior para vista óptima)
    is_mobile = (page.width < 750) if (page and page.width) else False

    # --- Header Superior con Semana ---
    header_section = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Text("📅", size=16 if is_mobile else 18),
                ft.Text("ENFOQUE SEMANAL" if is_mobile else "NUESTRO ENFOQUE SEMANAL", size=13 if is_mobile else 15, weight="heavy", color="white"),
                ft.Text("(Matriz Oficial SGH: INVITA · CONECTA · AGRADECE)", size=11, color="#8B949E", italic=True) if not is_mobile else ft.Container(height=0),
            ], spacing=6),
            ft.Container(expand=True),
            ft.Row([
                ft.Text("SEM:" if is_mobile else "SEMANA ACTUAL:", size=10 if is_mobile else 11, weight="bold", color="#8B949E"),
                dd_semana
            ], spacing=6, alignment=ft.MainAxisAlignment.END)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(10, 6, 10, 6) if is_mobile else ft.Padding(12, 6, 12, 6),
        bgcolor="#0C101C",
        border=ft.Border.all(1, "#28324E"),
        border_radius=ft.BorderRadius(6, 6, 6, 6)
    )

    # --- Panel Superior de Captura (Adaptativo: 2 Filas en PC, Tarjetas Organizadas en Celular) ---
    if is_mobile:
        panel_preguntas = ft.Container(
            content=ft.Column([
                # 1. Tarjeta Fortaleza
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#00FFFF", size=14),
                            ft.Text("FORTALEZA (MANTENER)", size=11, weight="bold", color="#00FFFF"),
                        ], spacing=4),
                        ft.Row([
                            ft.Container(content=ft.Column([ft.Text("Mejor Colaborador:", size=9, color="#CBD5E1"), tf_colab_fuerte], spacing=1), expand=1),
                        ], spacing=4),
                        ft.Row([
                            ft.Container(content=ft.Column([ft.Text("KPI Fuerte:", size=9, color="#CBD5E1"), dd_kpi_fuerte], spacing=1), expand=2),
                            ft.Container(content=ft.Column([ft.Text("Valor:", size=9, color="#00FFFF", weight="bold"), tf_valor_actual_fuerte], spacing=1), width=75),
                        ], spacing=4),
                    ], spacing=5),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor="#0B1528",
                    border=ft.Border.all(1, "#00FFFF"),
                    border_radius=ft.BorderRadius(5, 5, 5, 5)
                ),
                # 2. Tarjeta Desarrollo
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, color="#FF7A33", size=14),
                            ft.Text("DESARROLLO (OPORTUNIDAD)", size=11, weight="bold", color="#FF7A33"),
                        ], spacing=4),
                        ft.Row([
                            ft.Container(content=ft.Column([ft.Text("KPI Oportunidad:", size=9, color="#CBD5E1"), dd_kpi_debil], spacing=1), expand=2),
                            ft.Container(content=ft.Column([ft.Text("Valor:", size=9, color="#FF7A33", weight="bold"), tf_valor_actual_debil], spacing=1), width=75),
                        ], spacing=4),
                    ], spacing=5),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor="#190F16",
                    border=ft.Border.all(1, "#FF7A33"),
                    border_radius=ft.BorderRadius(5, 5, 5, 5)
                ),
                # 3. ¿Hicieron algo extraordinario?
                ft.Column([
                    ft.Text("¿Hicieron algo extraordinario? (Opcional):", size=9.5, color="#94A3B8"),
                    tf_extra_fuerte
                ], spacing=2),
                # 4. Botones
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([ft.Text("⚡", size=12), ft.Text("Generar Enfoque", weight="heavy", size=11)], alignment=ft.MainAxisAlignment.CENTER, spacing=3),
                        style=ft.ButtonStyle(bgcolor="#008080", color="white", shape=ft.RoundedRectangleBorder(radius=5), padding=ft.Padding(6, 6, 6, 6)),
                        height=36,
                        expand=2,
                        on_click=lambda e: ejecutar_cruce_inteligente(e, rotar=True)
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([ft.Text("💾", size=12), ft.Text("Guardar", weight="bold", size=11)], alignment=ft.MainAxisAlignment.CENTER, spacing=3),
                        style=ft.ButtonStyle(bgcolor="#1B4332", color="white", shape=ft.RoundedRectangleBorder(radius=5), padding=ft.Padding(6, 6, 6, 6)),
                        height=36,
                        expand=1,
                        on_click=guardar_estado
                    )
                ], spacing=6)
            ], spacing=6),
            padding=ft.Padding(8, 8, 8, 8),
            bgcolor="#0B0F1C",
            border=ft.Border.all(1, "#1E2742"),
            border_radius=ft.BorderRadius(6, 6, 6, 6)
        )
    else:
        panel_preguntas = ft.Container(
            content=ft.Column([
                # Fila 1: Indicadores y Nombres de Colaboradores (Directamente Editables)
                ft.Row([
                    # Fortaleza
                    ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#00FFFF", size=14),
                    ft.Text("FORTALEZA:", size=11, weight="bold", color="#00FFFF"),
                    ft.Text("Colaborador:", size=10, color="#CBD5E1"),
                    ft.Container(content=tf_colab_fuerte, width=125),
                    ft.Text("KPI Fuerte:", size=10, color="#CBD5E1"),
                    ft.Container(content=dd_kpi_fuerte, width=175),
                    ft.Text("Val:", size=10, color="#00FFFF", weight="bold"),
                    ft.Container(content=tf_valor_actual_fuerte, width=65),

                    ft.Container(width=6),
                    ft.Container(width=1, height=28, bgcolor="#334155"),
                    ft.Container(width=6),

                    # Desarrollo
                    ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, color="#FF7A33", size=14),
                    ft.Text("DESARROLLO:", size=11, weight="bold", color="#FF7A33"),
                    ft.Text("KPI Oportunidad:", size=10, color="#CBD5E1"),
                    ft.Container(content=dd_kpi_debil, width=180),
                    ft.Text("Val:", size=10, color="#FF7A33", weight="bold"),
                    ft.Container(content=tf_valor_actual_debil, width=65),
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                # Fila 2: ¿Hicieron algo extraordinario? (Con separación para que no se encime)
                ft.Row([
                    ft.Text("¿Hicieron algo extraordinario? (Opcional):", size=10.5, color="#94A3B8"),
                    ft.Container(content=tf_extra_fuerte, expand=True),
                    ft.ElevatedButton(
                        content=ft.Row([ft.Text("⚡", size=13), ft.Text("Generar Enfoque", weight="heavy", size=11)], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                        style=ft.ButtonStyle(
                            bgcolor="#008080",
                            color="white",
                            shape=ft.RoundedRectangleBorder(radius=5),
                            padding=ft.Padding(12, 8, 12, 8)
                        ),
                        height=36,
                        on_click=lambda e: ejecutar_cruce_inteligente(e, rotar=True)
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([ft.Text("💾", size=12), ft.Text("Guardar", weight="bold", size=11)], alignment=ft.MainAxisAlignment.CENTER, spacing=3),
                        style=ft.ButtonStyle(
                            bgcolor="#1B4332",
                            color="white",
                            shape=ft.RoundedRectangleBorder(radius=5),
                            padding=ft.Padding(12, 8, 12, 8)
                        ),
                        height=36,
                        on_click=guardar_estado
                    )
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=10),
            padding=ft.Padding(10, 10, 10, 10),
            bgcolor="#0B0F1C",
            border=ft.Border.all(1, "#1E2742"),
            border_radius=ft.BorderRadius(6, 6, 6, 6)
        )

    # ==============================================================================
    # TABLA UNIFICADA IDÉNTICA A LA BITÁCORA FÍSICA (UN SOLO RECTÁNGULO CONTINUO)
    # ==============================================================================
    BORDER_COLOR = "#475569"      # Líneas de cuadrícula estilo hoja física
    COL0_WIDTH = 125

    # Helper para celda individual dentro de la cuadrícula unificada
    def celda_grid(titulo, subtitulo, control, border_right=True, expand=1, title_color="#00FFFF"):
        borders = {}
        if border_right:
            borders["right"] = ft.BorderSide(1, BORDER_COLOR)

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(titulo, size=9.5, weight="heavy", color=title_color),
                        ft.Text(subtitulo, size=8, color="#94A3B8", italic=True, no_wrap=True) if subtitulo else ft.Container(height=0)
                    ], spacing=1),
                    padding=ft.Padding(6, 4, 6, 2),
                    bgcolor="#0F172A",
                    border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR))
                ),
                ft.Container(
                    content=control,
                    padding=ft.Padding(6, 2, 6, 2),
                    expand=True,
                    alignment=ft.Alignment(-1, 0)
                )
            ], spacing=0),
            bgcolor="#060A14",
            border=ft.Border(**borders) if borders else None,
            expand=expand
        )

    # Fila 4 con Resultados Previstos y Cajita Anidada en la esquina inferior derecha
    def celda_previstos_grid(titulo, subtitulo, control_previstos, control_actuales, border_right=True, title_color="#7CFC00", border_box_color="#00FFFF", expand=1):
        borders = {}
        if border_right:
            borders["right"] = ft.BorderSide(1, BORDER_COLOR)

        if is_mobile:
            cuerpo = ft.Column([
                ft.Container(
                    content=control_previstos,
                    expand=True,
                    padding=ft.Padding(2, 2, 2, 0)
                ),
                ft.Row([
                    ft.Text("ACTUAL:", size=7.5, weight="heavy", color="#CBD5E1"),
                    ft.Container(
                        content=control_actuales,
                        width=54,
                        height=24,
                        bgcolor="#040711",
                        border=ft.Border.all(1.2, border_box_color),
                        border_radius=ft.BorderRadius(3, 3, 3, 3),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding(1, 0, 1, 0)
                    )
                ], spacing=4, alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=2)
        else:
            cuerpo = ft.Row([
                ft.Container(
                    content=control_previstos,
                    expand=True,
                    alignment=ft.Alignment(-1, 0)
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("RESULTADOS ACTUALES:", size=7.5, weight="heavy", color="#CBD5E1"),
                        ft.Container(
                            content=control_actuales,
                            width=78,
                            height=30,
                            bgcolor="#040711",
                            border=ft.Border.all(1.2, border_box_color),
                            border_radius=ft.BorderRadius(3, 3, 3, 3),
                            alignment=ft.Alignment(0, 0),
                            padding=ft.Padding(2, 0, 2, 0)
                        )
                    ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.Padding(0, 0, 6, 2)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                # Header de la celda
                ft.Container(
                    content=ft.Column([
                        ft.Text(titulo, size=9.5, weight="heavy", color=title_color),
                        ft.Text(subtitulo, size=8, color="#94A3B8", italic=True, no_wrap=True) if subtitulo else ft.Container(height=0)
                    ], spacing=1),
                    padding=ft.Padding(6, 4, 6, 2),
                    bgcolor="#0F172A",
                    border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR))
                ),
                # Cuerpo
                ft.Container(
                    content=cuerpo,
                    padding=ft.Padding(4, 2, 4, 2) if is_mobile else ft.Padding(6, 2, 6, 2),
                    expand=True
                )
            ], spacing=0),
            bgcolor="#060A14",
            border=ft.Border(**borders) if borders else None,
            expand=expand
        )

    # 1. Fila Encabezado Superior (Banner)
    banner_controls = []
    if not is_mobile:
        banner_controls.append(
            ft.Container(
                content=ft.Text("¡ENFOQUÉMONOS!", size=13, weight="heavy", color="white", text_align=ft.TextAlign.CENTER),
                width=COL0_WIDTH,
                alignment=ft.Alignment(0, 0),
                border=ft.Border(right=ft.BorderSide(1.5, BORDER_COLOR))
            )
        )
    banner_controls.extend([
        ft.Container(
            content=ft.Text("Completa esta columna primero ➔", size=9.5 if is_mobile else 10.5, color="#00FFFF", italic=True, weight="bold", text_align=ft.TextAlign.CENTER),
            expand=1,
            alignment=ft.Alignment(0, 0),
            border=ft.Border(right=ft.BorderSide(1.5, BORDER_COLOR))
        ),
        ft.Container(
            content=ft.Text("Completa esta columna después ➔", size=9.5 if is_mobile else 10.5, color="#FF7A33", italic=True, weight="bold", text_align=ft.TextAlign.CENTER),
            expand=1,
            alignment=ft.Alignment(0, 0)
        )
    ])
    row_banner = ft.Container(
        content=ft.Row(banner_controls, spacing=0),
        height=30 if is_mobile else 34,
        bgcolor="#131B2E",
        border=ft.Border(bottom=ft.BorderSide(1.5, BORDER_COLOR))
    )

    # 2. Fila 1: Fuerza de Comportamiento / Área de Desarrollo
    r1_controls = []
    if not is_mobile:
        r1_controls.append(
            ft.Container(
                content=ft.Text("RESULTADOS\nSEMANA\nANTERIOR", size=9, weight="heavy", color="#E2E8F0", text_align=ft.TextAlign.CENTER),
                width=COL0_WIDTH,
                alignment=ft.Alignment(0, 0),
                bgcolor="#0B101E",
                border=ft.Border(right=ft.BorderSide(1.5, BORDER_COLOR)),
                padding=ft.Padding(4, 4, 4, 4)
            )
        )
    r1_controls.extend([
        celda_grid("FUERZA DE COMPORTAMIENTO", "" if is_mobile else "Identifica tu fortaleza: INVITA, CONECTA, AGRADECE", tf_fuerza_comp, border_right=True, title_color="#00FFFF", expand=6),
        celda_grid("MEJOR COLAB" if is_mobile else "MEJOR COLABORADOR", "" if is_mobile else "Nombre (Conducta)", tf_mejor_colab, border_right=True, title_color="#FFFFFF", expand=4),
        celda_grid("ÁREA DE DESARROLLO" if is_mobile else "ÁREA DE DESARROLLO DEL COMPORTAMIENTO", "" if is_mobile else "Identifica un área para enfocarte: INVITA, CONECTA, AGRADECE", tf_desarrollo_comp, border_right=False, title_color="#FF7A33", expand=10),
    ])
    row_1 = ft.Container(
        content=ft.Row(r1_controls, spacing=0),
        height=68 if is_mobile else 78,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR))
    )

    # 3. Fila 2: Indicador Métrico (Un solo recuadro continuo de 100% de ancho en cada columna)
    r2_controls = []
    if not is_mobile:
        r2_controls.append(
            ft.Container(
                content=ft.Text("Considera los componentes de las ECUACIONES DE VENTA y observaciones SGH.", size=7, color="#64748B", italic=True, text_align=ft.TextAlign.CENTER),
                width=COL0_WIDTH,
                alignment=ft.Alignment(0, 0),
                bgcolor="#0B101E",
                border=ft.Border(right=ft.BorderSide(1.5, BORDER_COLOR)),
                padding=ft.Padding(4, 2, 4, 2)
            )
        )
    r2_controls.extend([
        celda_grid("INDICADOR MÉTRICO", "" if is_mobile else "Indicador métrico: POLARIZADO, LUJO, MULT, PPT...", tf_indicador_fuerte, border_right=True, title_color="#00FFFF", expand=10),
        celda_grid("INDICADOR MÉTRICO", "" if is_mobile else "Indicador métrico soporte: MULT, PPT, CONV...", tf_indicador_debil, border_right=False, title_color="#FF7A33", expand=10),
    ])
    row_2 = ft.Container(
        content=ft.Row(r2_controls, spacing=0),
        height=68 if is_mobile else 78,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR))
    )

    # 4. Fila 3: Acción Clave (Espaciosa para móvil)
    r3_controls = []
    if not is_mobile:
        r3_controls.append(
            ft.Container(
                content=ft.Container(),
                width=COL0_WIDTH,
                bgcolor="#0B101E",
                border=ft.Border(right=ft.BorderSide(1.5, BORDER_COLOR))
            )
        )
    r3_controls.extend([
        celda_grid("ACCIÓN PARA MANTENER" if is_mobile else "ACCIÓN CLAVE PARA MANTENER (CONDUCTA O SECRETO DE LA EXPERIENCIA)", "" if is_mobile else "Acción para mantener la fortaleza + Consejo táctico analítico", tf_accion_mantener, border_right=True, title_color="#00FFFF", expand=10),
        celda_grid("ACCIÓN EL DESARROLLO" if is_mobile else "ACCIÓN CLAVE EL DESARROLLO (CONDUCTA O SECRETO DE LA EXPERIENCIA)", "" if is_mobile else "Acción clave para desarrollar la conducta + Consejo táctico analítico", tf_accion_desarrollo, border_right=False, title_color="#FF7A33", expand=10),
    ])
    row_3 = ft.Container(
        content=ft.Row(r3_controls, spacing=0),
        height=130 if is_mobile else 100,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR))
    )

    # 5. Fila 4: Resultados Previstos con Cajita Anidada
    r4_controls = []
    if not is_mobile:
        r4_controls.append(
            ft.Container(
                content=ft.Container(),
                width=COL0_WIDTH,
                bgcolor="#0B101E",
                border=ft.Border(right=ft.BorderSide(1.5, BORDER_COLOR)),
                padding=ft.Padding(4, 2, 4, 2)
            )
        )
    r4_controls.extend([
        celda_previstos_grid("RESULTADOS PREVISTOS", "" if is_mobile else "Resultados específicos que esperas alcanzar con base en la fortaleza", tf_previstos_fuerte, tf_actuales_fuerte, border_right=True, title_color="#7CFC00", border_box_color="#00FFFF", expand=10),
        celda_previstos_grid("RESULTADOS PREVISTOS", "" if is_mobile else "Establece resultados específicos que esperas alcanzar esta semana", tf_previstos_debil, tf_actuales_debil, border_right=False, title_color="#FFD700", border_box_color="#FF7A33", expand=10),
    ])
    row_4 = ft.Container(
        content=ft.Row(r4_controls, spacing=0),
        height=96 if is_mobile else 85,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR))
    )

    # 6. Fila Pie de Página
    row_footer = ft.Container(
        content=ft.Row([
            ft.Text("ℹ️ Matriz Oficial Sunglass Hut Experience: INVITA · CONECTA · AGRADECE" if is_mobile else "ℹ️ Para el correcto llenado, deberás consultar KPI CONEXIÓN (Matriz Oficial Sunglass Hut Experience)", size=8.5 if is_mobile else 9, color="#94A3B8", italic=True)
        ], alignment=ft.MainAxisAlignment.START),
        padding=ft.Padding(8, 4, 8, 4) if is_mobile else ft.Padding(12, 4, 12, 4),
        bgcolor="#0C101C",
        height=26 if is_mobile else 28
    )

    # Cuadrícula Rectangular Completa (Un Solo Bloque Sólido de Filas)
    rectangulo_bitacora_completa = ft.Container(
        content=ft.Column([
            row_banner,
            row_1,
            row_2,
            row_3,
            row_4,
            row_footer
        ], spacing=0),
        bgcolor="#060A14",
        border=ft.Border.all(1.5, BORDER_COLOR),
        border_radius=ft.BorderRadius(6, 6, 6, 6)
    )

    # Vista General
    return ft.Column(
        controls=[
            header_section,
            panel_preguntas,
            rectangulo_bitacora_completa,
            ft.Container(height=20),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )




