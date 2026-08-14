import re

with open("enfoque_diario.py", "r") as f:
    code = f.read()

# Fix generar_pdf_enfoque_file
code = code.replace(
"""def generar_pdf_enfoque_file(d_name):
    if not REPORTLAB_AVAILABLE:
        return None
    try:
        calc = calcular_dia(d_name)
        data = store_state[d_name]""",
"""def generar_pdf_enfoque_file(d_name, user_id):
    if not REPORTLAB_AVAILABLE:
        return None
    try:
        calc = calcular_dia(d_name, user_id)
        g_meta = user_states[user_id]["global_meta"]
        s_state = user_states[user_id]["store_state"]
        data = s_state[d_name]"""
)
code = code.replace(
"""        header_data = [
            [Paragraph(f"<b>DÍA:</b> {d_name}", header_style),
             Paragraph(f"<b>SEMANA:</b> {global_meta['semana']}", header_style),
             Paragraph(f"<b>TIENDA:</b> {global_meta['tienda']}", header_style)]
        ]""",
"""        header_data = [
            [Paragraph(f"<b>DÍA:</b> {d_name}", header_style),
             Paragraph(f"<b>SEMANA:</b> {g_meta['semana']}", header_style),
             Paragraph(f"<b>TIENDA:</b> {g_meta['tienda']}", header_style)]
        ]"""
)

# Fix other calcs
code = code.replace(
"""            c = calcular_dia(d)""",
"""            c = calcular_dia(d, user_id)"""
)
code = code.replace(
"""        calcular_dia(d_name)""",
"""        calcular_dia(d_name, user_id)"""
)

with open("enfoque_diario.py", "w") as f:
    f.write(code)

