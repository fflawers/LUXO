import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# Replace build_enfoque_diario_view definition and usage of global state
code = code.replace(
"""def build_enfoque_diario_view(page: ft.Page, session_user=None):
    if session_user is None:
        session_user = {"user": "invitado"}""",
"""def build_enfoque_diario_view(page: ft.Page, session_user=None):
    if session_user is None:
        session_user = {"user": "invitado"}
    user_id = session_user.get("user", "invitado")
    init_user_state(user_id)
    g_meta = user_states[user_id]["global_meta"]
    s_state = user_states[user_id]["store_state"]
    h_state = user_states[user_id]["historico_semanal_state"]"""
)

# In build_enfoque_diario_view, update global_meta and store_state access.
# We'll use re to replace `global_meta` with `g_meta` and `store_state` with `s_state` but ONLY inside `build_enfoque_diario_view`.
# But `build_enfoque_diario_view` spans hundreds of lines.
# Instead of doing that, I'll write a python script that finds `def build_enfoque_diario_view` and then replaces it.

