import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# Fix inside build_sheet_ui
code = code.replace(
"""    def build_sheet_ui(d_name):
        calc = calcular_dia(d_name)""",
"""    def build_sheet_ui(d_name):
        calc = calcular_dia(d_name, user_id)"""
)

code = code.replace(
"""        def sync_green_cells():
            c = calcular_dia(d_name)""",
"""        def sync_green_cells():
            c = calcular_dia(d_name, user_id)"""
)

# Fix on_click in Tabs
code = code.replace(
"""        on_click=lambda e: (
            active_tab.__setitem__(0, tab_name),""",
"""        on_click=lambda e: (
            user_states[user_id]["active_tab"].__setitem__(0, tab_name),"""
)

with open("enfoque_diario.py", "w") as f:
    f.write(code)

