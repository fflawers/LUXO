import flet as ft

def build_sidebar(
    page: ft.Page,
    obtener_64,
    es_admin,
    operacion_tiendas,
    star_icon_container,
    conectar_db,
    bell_icon_container,
    profile_row,
    btn_operacion_diaria,
    btn_chat,
    btn_historial,
    btn_enfoque,
    tile_ventas,
    tile_clientes,
    tile_operacion,
    tile_entrenamiento,
    suggestion_box,
    lang_row,
    btn_logout
):
        avatar_luxo2_base64 = obtener_64("luxo_avatar2.png") or obtener_64("avatar_luxo2.png")
        
        avatar_header_widget = ft.Container(
            content=ft.Image(
                src=avatar_luxo2_base64,
                width=34,
                height=34,
                fit=ft.controls.box.BoxFit.COVER
            ) if avatar_luxo2_base64 else ft.Text("🤖", size=18, color="#00FFFF"),
            width=34,
            height=34,
            border_radius=17,
            bgcolor="#1A102F",
            border=ft.Border.all(1.5, "#00FFFF"),
            alignment=ft.alignment.Alignment(0, 0),
            shadow=[
                ft.BoxShadow(
                    color="#4000FFFF",
                    blur_radius=10,
                    spread_radius=1
                )
            ]
        )
        return sidebar
