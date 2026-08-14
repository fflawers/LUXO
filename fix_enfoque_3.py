import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# Find the start of the function body
start_idx = code.find("def build_enfoque_diario_view")
if start_idx != -1:
    end_of_def = code.find(":", start_idx) + 1
    head = code[:end_of_def]
    body = code[end_of_def:]
    
    # Replace global state variables in the body
    body = re.sub(r'\bstore_state\b', 's_state', body)
    body = re.sub(r'\bglobal_meta\b', 'g_meta', body)
    body = re.sub(r'\bhistorico_semanal_state\b', 'h_state', body)
    
    # Replace active_tab[0] if still there
    body = body.replace('active_tab[0]', 'user_states[user_id]["active_tab"][0]')
    
    # Replace missing user_id in function calls
    body = body.replace('guardar_estado_persistente()', 'guardar_estado_persistente(user_id)')
    body = body.replace('guardar_semana_historico()', 'guardar_semana_historico(user_id)')
    body = re.sub(r'cargar_semana_historico\(([^,)]+)\)', r'cargar_semana_historico(user_id, \1)', body)
    
    # Fix the url assignment
    body = body.replace('url=f"/api/download_excel/{d_name}"', 'url=f"/api/download_excel/{d_name}?user_id={user_id}"')
    body = body.replace('url=f"/print_enfoque/{d_name}"', 'url=f"/print_enfoque/{d_name}?user_id={user_id}"')
    
    code = head + body

with open("enfoque_diario.py", "w") as f:
    f.write(code)

