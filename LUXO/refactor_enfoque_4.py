import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# Replace inside `build_enfoque_diario_view` all instances of:
# store_state -> s_state
# global_meta -> g_meta
# historico_semanal_state -> h_state
# active_tab -> user_states[user_id]["active_tab"]
# guardar_estado_persistente() -> guardar_estado_persistente(user_id)
# cargar_semana_historico -> cargar_semana_historico(user_id, ...)
# guardar_semana_historico() -> guardar_semana_historico(user_id)
# calcular_dia(d_name) -> calcular_dia(d_name, user_id)
# generar_excel_enfoque(d_name) -> generar_excel_enfoque(d_name, user_id)
# generar_pdf_enfoque_file(d_name) -> generar_pdf_enfoque_file(d_name, user_id)
# sincronizar_colaboradores_db(...) -> sincronizar_colaboradores_db(user_info=session_user, tienda_name=g_meta["tienda"], user_id=user_id)

parts = code.split("def build_enfoque_diario_view(page: ft.Page, session_user=None):")
if len(parts) == 2:
    func_body = parts[1]
    
    # Simple token replacements for state vars
    func_body = re.sub(r'\bstore_state\b', 's_state', func_body)
    func_body = re.sub(r'\bglobal_meta\b', 'g_meta', func_body)
    func_body = re.sub(r'\bhistorico_semanal_state\b', 'h_state', func_body)
    func_body = re.sub(r'\bactive_tab\b', 'user_states[user_id]["active_tab"]', func_body)
    
    # Function call replacements
    func_body = func_body.replace("guardar_estado_persistente()", "guardar_estado_persistente(user_id)")
    func_body = func_body.replace("guardar_semana_historico()", "guardar_semana_historico(user_id)")
    func_body = re.sub(r'cargar_semana_historico\((.*?)\)', r'cargar_semana_historico(user_id, \1)', func_body)
    func_body = re.sub(r'calcular_dia\((.*?)\)', r'calcular_dia(\1, user_id)', func_body)
    
    # Exporters
    func_body = re.sub(r'generar_pdf_enfoque_file\((.*?)\)', r'generar_pdf_enfoque_file(\1, user_id)', func_body)
    # the excel one might have page attached: generar_excel_enfoque(d_name, page)
    # generating excel is done via web api probably, wait, the button uses `url = f"/api/download_excel/{d_name}"`. So the API needs user_id too!
    
    # Sincronizar
    func_body = re.sub(r'sincronizar_colaboradores_db\(.*?\)', r'sincronizar_colaboradores_db(session_user, g_meta["tienda"], user_id)', func_body)

    code = parts[0] + "def build_enfoque_diario_view(page: ft.Page, session_user=None):" + func_body

with open("enfoque_diario.py", "w") as f:
    f.write(code)

