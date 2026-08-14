import flet as ft

def build_header(
    page: ft.Page,
    toggle_sidebar,
    on_global_master_refresh_click
):
        btn_global_master_refresh = ft.Container(
            content=ft.Row([
                ft.Text("🔄", size=12),
                ft.Text("Sincronizar LUXO", color="#00FF88", weight="bold", size=11)
            ], spacing=4),
            border=ft.Border.all(1.5, "#00FF88"),
            border_radius=6,
            padding=8,
            bgcolor="transparent",
            ink=True,
            on_click=on_global_master_refresh_click,
            tooltip="Recargar y sincronizar el módulo activo actual"
        )

        # Definir la cabecera superior permanente para toda la aplicación
        top_appbar = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Text("☰", color="#00FFFF", size=18, weight="bold"),
                        on_click=toggle_sidebar,
                        tooltip="Mostrar/Ocultar Menú",
                        padding=8,
                        alignment=ft.alignment.Alignment(0, 0),
                        ink=True,
                        border_radius=4
                    ),
                    ft.Text("LUXO AI SYSTEM", color="white", weight="bold", size=15),
                ], vertical_alignment="center", spacing=4),
                btn_global_master_refresh
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#0B0E17",
            padding=6,
            border=ft.Border(bottom=ft.BorderSide(1, "#1F2937")),
            visible=True
        )
        return btn_global_master_refresh, top_appbar
