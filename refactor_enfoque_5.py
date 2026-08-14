import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# Replace remaining `active_tab` inside build_enfoque_diario_view
# We can just replace `active_tab` with `user_states[user_id]["active_tab"]` except the one in the global initialization.
# Since active_tab globally is gone, any active_tab inside the functions must be updated.

# Find where `user_states = {}` is
parts = code.split("user_states = {}")
if len(parts) == 2:
    func_body = parts[1]
    
    # Replace active_tab[0] with user_states[user_id]["active_tab"][0]
    func_body = func_body.replace("active_tab[0]", "user_states[user_id]['active_tab'][0]")
    
    # Also fix url="/print_enfoque/DOMINGO"
    func_body = func_body.replace('url="/api/download_excel/DOMINGO"', 'url=f"/api/download_excel/DOMINGO?user_id={user_id}"')
    func_body = func_body.replace('url="/print_enfoque/DOMINGO"', 'url=f"/print_enfoque/DOMINGO?user_id={user_id}"')
    func_body = func_body.replace('generar_excel_enfoque(user_states[user_id][\'active_tab\'][0] if user_states[user_id][\'active_tab\'][0] in DIAS else "DOMINGO")', 'generar_excel_enfoque(user_states[user_id][\'active_tab\'][0] if user_states[user_id][\'active_tab\'][0] in DIAS else "DOMINGO", user_id)')

    code = parts[0] + "user_states = {}" + func_body

with open("enfoque_diario.py", "w") as f:
    f.write(code)

