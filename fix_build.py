with open("enfoque_diario.py", "r") as f:
    code = f.read()

old_str = """def build_enfoque_diario_view(page: ft.Page, session_user: dict = None):
    \"\"\"
    Construye la vista principal del Módulo Enfoque Diario 2026 SGH
    con navegación por pestañas (Resumen Semanal, Días y Planes de Acción).
    \"\"\"
    sincronizar_colaboradores_db(session_user)"""

new_str = """def build_enfoque_diario_view(page: ft.Page, session_user: dict = None):
    \"\"\"
    Construye la vista principal del Módulo Enfoque Diario 2026 SGH
    con navegación por pestañas (Resumen Semanal, Días y Planes de Acción).
    \"\"\"
    if session_user is None:
        session_user = {"user": "invitado"}
    user_id = session_user.get("user", "invitado")
    init_user_state(user_id)
    g_meta = user_states[user_id]["global_meta"]
    s_state = user_states[user_id]["store_state"]
    h_state = user_states[user_id]["historico_semanal_state"]
    
    sincronizar_colaboradores_db(session_user, g_meta["tienda"], user_id)"""

code = code.replace(old_str, new_str)

with open("enfoque_diario.py", "w") as f:
    f.write(code)

