import re

with open("main.py", "r") as f:
    code = f.read()

code = code.replace(
"""    @app.get("/api/download_excel/{day}")
    async def download_excel_route(day: str):
        try:
            import enfoque_diario
            enfoque_diario.generar_excel_enfoque(day)""",
"""    @app.get("/api/download_excel/{day}")
    async def download_excel_route(day: str, user_id: str = "invitado"):
        try:
            import enfoque_diario
            enfoque_diario.generar_excel_enfoque(day, user_id)"""
)

code = code.replace(
"""    @app.get("/print_enfoque/{day}")
    async def print_enfoque_route(day: str):
        try:
            import enfoque_diario
            calc = enfoque_diario.calcular_dia(day)
            data = enfoque_diario.store_state[day]
            meta = enfoque_diario.global_meta""",
"""    @app.get("/print_enfoque/{day}")
    async def print_enfoque_route(day: str, user_id: str = "invitado"):
        try:
            import enfoque_diario
            calc = enfoque_diario.calcular_dia(day, user_id)
            data = enfoque_diario.user_states.get(user_id, {}).get("store_state", {}).get(day, {})
            meta = enfoque_diario.user_states.get(user_id, {}).get("global_meta", {})"""
)

with open("main.py", "w") as f:
    f.write(code)

