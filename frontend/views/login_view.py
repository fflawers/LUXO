import flet as ft
import flet_video as fv

def build_login_view(
    page: ft.Page,
    user_info: dict,
    API_URL: str,
    mostrar_snack,
    obtener_avatar_usuario,
    reproducir_saludo_login,
    cargar_chat,
    active_file_callback,
    active_sessions,
    video_login_exists,
    video_login_url,
    img_avatar,
    is_mobile
):
    # =====================================
    # LOGIN
    # =====================================

    def login_click(e):
        # 1. Feedback visual inmediato en el botón
        btn_acceder.disabled = True
        btn_acceder.content.value = "Validando credenciales..."
        try: page.update()
        except: pass
        import time
        time.sleep(0.01)

        def procesar_login():
            try:
                import requests as req
                api_url = f"{API_URL}/api/auth/login"
                payload = {"user": txt_user.value, "password": txt_pass.value}
                try:
                    resp = req.post(api_url, json=payload, timeout=10)
                except Exception as req_ex:
                    mostrar_snack(f"Error conectando al backend: {str(req_ex)}", color="#FF4B4B")
                    btn_acceder.disabled = False
                    btn_acceder.content.value = "ACCEDER"
                    try: page.update()
                    except: pass
                    return
                
                data = resp.json()
                if data.get("status") == "ok":
                    login_message.value = ""
                    login_error_box.visible = False

                    user_info["id"] = data["usuario_id"]
                    user_info["usuario"] = data.get("usuario") or ""
                    user_info["nombre"] = data["nombre"]
                    user_info["rol"] = data["rol"]
                    user_info["tienda"] = data["tienda"] if data["tienda"] is not None else ""
                    user_info["zona"] = data["zona"] if data["zona"] is not None else "Zona Centro"
                    user_info["img_usuario"] = obtener_avatar_usuario(data["usuario_id"])
                    user_info["biometria_metodo"] = None
                    user_info["es_gerente_verificado"] = False
                    
                    reproducir_saludo_login(data["nombre"])
                    
                    # Guardar sesión de forma en memoria active_sessions
                    user_id_key = data["usuario_id"]
                    active_sessions[user_id_key] = {
                        "page": page,
                        "user_info": user_info,
                        "cargar_chat": cargar_chat,
                        "active_file_callback": active_file_callback
                    }

                    async def guardar_sesion_storage():
                        try:
                            import time
                            if hasattr(page, "shared_preferences") and page.shared_preferences:
                                await page.shared_preferences.set("logged_user_id", str(user_info["id"]))
                                await page.shared_preferences.set("last_activity_timestamp", str(int(time.time())))
                        except Exception as ex_st:
                            print("Notice guardar shared_preferences:", ex_st)

                    page.run_task(guardar_sesion_storage)
                    cargar_chat()
                else:
                    login_message.value = data.get("message", "Credenciales incorrectas")
                    login_message.color = "#FF4B4B"
                    login_error_box.visible = True
                    
                    btn_acceder.disabled = False
                    btn_acceder.content.value = "ACCEDER"
                    page.update()

            except Exception as err:
                import traceback
                tb_str = traceback.format_exc()
                print("--- DETECTADO ERROR EN LOGIN ---")
                print(tb_str)
                try:
                    with open("login_error.log", "w", encoding="utf-8") as log_f:
                        log_f.write(tb_str)
                except Exception as e_log:
                    print("No se pudo escribir en login_error.log:", e_log)
            finally:
                # FIX Bug 2: Siempre restablecer el botón, sin importar si el login tuvo éxito o error
                try:
                    btn_acceder.disabled = False
                    btn_acceder.content.value = "ACCEDER"
                    page.update()
                except Exception:
                    pass

        import threading
        threading.Thread(target=procesar_login, daemon=True).start()

    # =====================================
    # LOGIN UI
    # =====================================

    login_video_player = None
    btn_audio = None

    def toggle_audio(e):
        nonlocal login_video_player, btn_audio
        if login_video_player:
            try:
                currently_unmuted = e.control.data
                if currently_unmuted:
                    login_video_player.volume = 0
                    login_video_player.muted = True
                    btn_audio.content = ft.Text("🔇", size=11, color="#00FFFF", text_align="center")
                    btn_audio.tooltip = "Activar Audio"
                    e.control.data = False
                else:
                    login_video_player.volume = 100
                    login_video_player.muted = False
                    btn_audio.content = ft.Text("🔊", size=11, color="#00FFFF", text_align="center")
                    btn_audio.tooltip = "Silenciar Audio"
                    e.control.data = True
                login_video_player.update()
                btn_audio.update()
            except Exception as err:
                print("Error al cambiar estado de audio:", err)

    txt_user_input = ft.TextField(
        hint_text="Ej. admin",
        hint_style=ft.TextStyle(color="#555566", size=13),
        width=300,
        height=45,
        border_color="#121620",
        focused_border_color="#00F0FF",
        color="white",
        bgcolor="#040407",
        border_radius=10,
        content_padding=12
    )

    is_pass_hidden = [True]
    def toggle_pass_visibility(e):
        is_pass_hidden[0] = not is_pass_hidden[0]
        txt_pass_input.password = is_pass_hidden[0]
        btn_eye_3d.content.color = "#E040FB" if is_pass_hidden[0] else "#00F0FF"
        txt_pass_input.update()
        btn_eye_3d.update()

    btn_eye_3d = ft.Container(
        content=ft.Text("👁️", size=16, color="#E040FB"),
        alignment=ft.alignment.Alignment(0, 0),
        width=32,
        height=32,
        on_click=toggle_pass_visibility,
        tooltip="Mostrar / Ocultar Contraseña"
    )

    txt_pass_input = ft.TextField(
        hint_text="••••••••",
        hint_style=ft.TextStyle(color="#555566", size=13),
        password=True,
        width=300,
        height=45,
        border_color="#121620",
        focused_border_color="#E040FB",
        color="white",
        bgcolor="#040407",
        border_radius=10,
        content_padding=12,
        on_submit=login_click,
        suffix=btn_eye_3d
    )

    txt_user = txt_user_input
    txt_pass = txt_pass_input

    login_message = ft.Text(
        "",
        size=14,
        weight="bold",
        color="#FF4B4B"
    )

    login_error_box = ft.Container(
        content=login_message,
        bgcolor="#000000",
        padding=8,
        border_radius=8,
        visible=False,
        width=300
    )

    video_avatar = None
    if video_login_exists:
        try:
            login_video_player = fv.Video(
                playlist=[fv.VideoMedia(video_login_url)],
                playlist_mode=fv.PlaylistMode.LOOP,
                autoplay=True,
                volume=100.0,
                muted=False,
                show_controls=False,
                expand=True,
                fit=ft.BoxFit.COVER,
                filter_quality=ft.FilterQuality.HIGH,
            )
            def on_avatar_tap(e):
                if login_video_player:
                    try:
                        login_video_player.play()
                        login_video_player.volume = 100
                        login_video_player.muted = False
                        login_video_player.update()
                    except Exception: pass

            btn_audio = ft.Container(
                content=ft.Text("🔊", size=11, color="#00FFFF", text_align="center"),
                bgcolor="#111111",
                width=28,
                height=28,
                border_radius=14,
                alignment=ft.alignment.Alignment(0, 0),
                tooltip="Silenciar Audio",
                data=True,
                on_click=toggle_audio
            )
            video_avatar = ft.Stack([
                ft.Container(
                    content=login_video_player,
                    width=108,
                    height=108,
                    border_radius=54,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    border=ft.Border.all(2, "#00F0FF"),
                    shadow=[ft.BoxShadow(color="#4000FFFF", blur_radius=20, spread_radius=1)],
                    on_click=on_avatar_tap
                ),
                ft.Container(
                    content=btn_audio,
                    right=0,
                    bottom=0,
                    width=28,
                    height=28,
                    border_radius=14,
                )
            ], width=108, height=108)
        except Exception as ex_v:
            print("Notice video login load:", ex_v)
            video_avatar = None

    header_title = ft.Column([
        ft.ShaderMask(
            content=ft.Text("LUXO OS", size=28, weight="bold", color="white"),
            blend_mode=ft.BlendMode.SRC_IN,
            shader=ft.LinearGradient(
                colors=["#00F0FF", "#E040FB"],
                begin=ft.alignment.Alignment(-1, 0),
                end=ft.alignment.Alignment(1, 0)
            )
        ),
        ft.Text(
            "PORTAL DE AUTENTICACIÓN",
            size=9,
            weight="bold",
            color="#8899A6"
        )
    ], horizontal_alignment="center", spacing=3)

    user_field_group = ft.Column([
        ft.Text("USUARIO", size=10, weight="bold", color="#00F0FF"),
        txt_user_input
    ], spacing=4, width=300)

    pass_field_group = ft.Column([
        ft.Text("CONTRASEÑA", size=10, weight="bold", color="#E040FB"),
        txt_pass_input
    ], spacing=4, width=300)

    btn_acceder = ft.Container(
        content=ft.Text("ACCEDER", color="white", weight="bold", size=14),
        alignment=ft.alignment.Alignment(0, 0),
        gradient=ft.LinearGradient(
            colors=["#00A3FF", "#E040FB"],
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1)
        ),
        padding=14,
        border_radius=22,
        width=300,
        height=46,
        on_click=login_click,
        shadow=[
            ft.BoxShadow(
                color="#E040FB",
                blur_radius=18,
                spread_radius=1
            )
        ]
    )

    login_card = ft.Container(
        content=ft.Column([
            video_avatar if video_avatar else (
                ft.Container(
                    content=ft.Image(
                        src=img_avatar,
                        width=108,
                        height=108,
                        fit=ft.BoxFit.COVER
                    ),
                    width=108,
                    height=108,
                    border_radius=54,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    border=ft.Border.all(2, "#00F0FF"),
                    shadow=[ft.BoxShadow(color="#4000FFFF", blur_radius=20, spread_radius=1)]
                ) if img_avatar else ft.Text(
                    "LUXO",
                    size=28,
                    color="#FFFFFF",
                    weight="bold"
                )
            ),
            login_error_box,
            header_title,
            user_field_group,
            pass_field_group,
            ft.Container(height=6),
            btn_acceder
        ],
        horizontal_alignment="center",
        spacing=16 if is_mobile else 18),
        padding=32 if is_mobile else 42,
        bgcolor="#06070B",
        border_radius=24,
        border=ft.Border.all(1.2, "#0A202A"),
        shadow=[
            ft.BoxShadow(
                color="#000000",
                blur_radius=35,
                spread_radius=5,
            )
        ],
        width=370,
        clip_behavior=ft.ClipBehavior.HARD_EDGE
    )

    # Fondo Ambiental de Pantalla con degradado nativo de Flet (Cian a la izquierda, Obsidiana al centro, Magenta a la derecha)
    full_screen_background = ft.Container(
        content=login_card,
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
        gradient=ft.LinearGradient(
            colors=["#021622", "#05070D", "#220228"],
            begin=ft.alignment.Alignment(-1, -0.2),
            end=ft.alignment.Alignment(1, 0.2)
        )
    )

    page.bgcolor = "#05070D"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.controls.clear()
    page.add(full_screen_background)
    page.update()
