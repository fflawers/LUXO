import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# 1. Replace globals with user_states
code = re.sub(
    r"global_meta = \{.*?\n\}\n\n# Inicialización de estado diario por tienda y semana\nstore_state = \{\}\nfor d in DIAS:.*?active_tab = \[\"DOMINGO\"\]\n\n# Histórico de semanas guardadas \(Semanas 1-52\)\nhistorico_semanal_state = \{\}\n\nimport json\n\nSTATE_FILE = os\.path\.join\(BASE_PATH, \"enfoque_diario_state\.json\"\)\n\ndef guardar_estado_persistente\(\):\n.*?\n# Cargar al importar\ncargar_estado_persistente\(\)",
    """def default_global_meta():
    return {
        "semana": "30",
        "tienda": "Vallejo",
        "num_tienda": "3645"
    }

def default_store_state():
    state = {}
    for d in DIAS:
        state[d] = {
            "meta_diaria": 4758.0,
            "trafico_esperado": 8,
            "conversion_target": 0.13,
            "vta_ly": 4758.0,
            "wearables_pct": 0.15,
            "kids_pct": 0.05,
            "carekits_pct": 0.30,
            "atv_dia": 3620.0,
            "aur_dia": 3620.0,
            "atv_mtd": 7597.0,
            "aur_mtd": 3362.0,
            "estrellas_logro": 5,
            "trafico_bloques": [4, 2, 2, 0, 0],
            "colaboradores": [
                {"nombre": "", "horas": 0.0, "interacciones": 0, "convertidos": 0, "vta_cierre": 0.0, "ana_cierre": 0, "wea_demos": 0, "wea_cierre": 0, "kid_cierre": 0}
                for _ in range(8)
            ],
            "venta_neta_dia": 0.0,
            "venta_unidades_dia": 0,
            "slp_dia": "",
            "onesight_dia": "",
            "enfoque_hoy": "Enfocar el 100% del equipo en ofrecer la solución limpiadora y bandeja de opciones para maximizar venta múltiple.",
            "logros_hoy": "Excelente retención de clientes y venta cruzada.",
            "plan_accion": [
                {"colaborador": "", "compromiso": ""} for _ in range(3)
            ]
        }
    return state

user_states = {}

def get_state_file(user_id):
    return os.path.join(BASE_PATH, f"enfoque_diario_state_{user_id}.json")

def init_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            "global_meta": default_global_meta(),
            "store_state": default_store_state(),
            "historico_semanal_state": {},
            "active_tab": ["DOMINGO"]
        }
        cargar_estado_persistente(user_id)

import json

def guardar_estado_persistente(user_id):
    try:
        if user_id not in user_states: return
        payload = {
            "global_meta": user_states[user_id]["global_meta"],
            "store_state": user_states[user_id]["store_state"],
            "historico_semanal_state": user_states[user_id]["historico_semanal_state"]
        }
        with open(get_state_file(user_id), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
    except Exception as ex:
        print(f"Error al guardar estado de enfoque diario para {user_id}:", ex)

def cargar_estado_persistente(user_id):
    try:
        sf = get_state_file(user_id)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                payload = json.load(f)
                if "store_state" in payload:
                    for d in DIAS:
                        if d in payload["store_state"]:
                            user_states[user_id]["store_state"][d].update(payload["store_state"][d])
                if "global_meta" in payload:
                    user_states[user_id]["global_meta"].update(payload["global_meta"])
                if "historico_semanal_state" in payload:
                    user_states[user_id]["historico_semanal_state"].update(payload["historico_semanal_state"])
        else:
            guardar_estado_persistente(user_id)
    except Exception as ex:
        print(f"Error al cargar estado de enfoque diario para {user_id}:", ex)""",
    code,
    flags=re.DOTALL
)

with open("enfoque_diario.py", "w") as f:
    f.write(code)

