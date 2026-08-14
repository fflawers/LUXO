import flet as ft
from frontend.core.state import AppState
from frontend.components.ui import EmojiIconButton
import threading

def build_chat_view(estado: AppState):
    user_info = estado.user_info
    active_sessions = estado.active_sessions
    chat_display = estado.chat_display
    input_msg = estado.input_msg
    enviar_mensaje = estado.enviar_mensaje
    mostrar_snack = estado.mostrar_snack
    g_tr = estado.g_tr
    inyectar_script_voz_luxo = estado.inyectar_script_voz_luxo
    page = estado.page

    inyectar_script_voz_luxo()

    dictado_en_progreso = [False]

    def on_mic_click(e):
        print(f"[DEBUG-MIC] on_mic_click disparado. dictado_en_progreso={dictado_en_progreso[0]}, platform={page.platform}")
        if dictado_en_progreso[0]:
            print("⚠️ Dictado en progreso, ignorando clic.")
            return
        dictado_en_progreso[0] = True

        try:
            mostrar_snack("🎙️ Preparando micrófono...", "#00FFFF")
            btn_mic_container.bgcolor = "#FF0000"
            btn_mic_container.border = ft.Border.all(2, "white")
            btn_mic_container.update()

            print("[DEBUG-MIC] UI actualizada a ROJO. Lanzando JS...")

            # Agregamos alerts de depuración al JS para que el usuario las vea en su celular
            js_dictate = """javascript:void((function(){
                try {
                    const SR = window.SpeechRecognition || window.webkitSpeechRecognition || (window.top && (window.top.SpeechRecognition || window.top.webkitSpeechRecognition));
                    if (!SR) { 
                        alert('❌ API no soportada en este navegador.'); 
                        return; 
                    }
                    const r = new SR();
                    r.lang = 'es-MX';
                    r.interimResults = false;
                    r.continuous = false;
                    r.maxAlternatives = 1;
                    
                    r.onstart = function() {
                        console.log('[DEBUG-MIC] JS: onstart');
                    };
                    r.onresult = function(ev) {
                        const txt = ev.results[0][0].transcript;
                        if (txt) {
                            fetch('/text_input?user_id=1&text=' + encodeURIComponent(txt), { method: 'POST' });
                        }
                    };
                    r.onerror = function(ev) { 
                        alert('❌ Error JS Dictado: ' + ev.error); 
                    };
                    r.onend = function() { 
                        console.log('[DEBUG-MIC] JS: onend');
                    };
                    
                    r.start();
                } catch(err) {
                    alert('❌ Excepción JS: ' + err.message);
                }
            })());"""

            def revert_ui():
                import time
                time.sleep(6) 
                dictado_en_progreso[0] = False
                try:
                    btn_mic_container.bgcolor = "#1E1E2E"
                    btn_mic_container.border = ft.Border.all(1.5, "#00FFFF")
                    btn_mic_container.update()
                    print("[DEBUG-MIC] UI restaurada a normal.")
                except Exception as e:
                    print("[DEBUG-MIC] Error restaurando UI:", e)

            async def _lanzar_js():
                try:
                    await page.launch_url(js_dictate)
                    print("[DEBUG-MIC] launch_url ejecutado exitosamente.")
                except Exception as ex:
                    print("[DEBUG-MIC] Error lanzando URL js_dictate:", ex)

            # Ejecutar el JS de manera asíncrona correcta
            page.run_task(_lanzar_js)

            threading.Thread(target=revert_ui, daemon=True).start()

        except Exception as ex:
            dictado_en_progreso[0] = False
            print("[DEBUG-MIC] Error crítico en on_mic_click:", ex)

    btn_mic = EmojiIconButton(
        icon_emoji="🎙️",
        active_emoji="⏹️",
        icon_color="#00FFFF",
        on_click=on_mic_click,
        tooltip="Dictar por voz / Oye LUXO 🎙️",
        width=40,
        height=40,
        border_radius=20
    )

    btn_mic_container = ft.Container(
        content=btn_mic,
        bgcolor="#1E1E2E",
        border_radius=23,
        border=ft.Border.all(1.5, "#00FFFF"),
        width=46,
        height=46,
        alignment=ft.alignment.Alignment(0, 0),
        visible=False  # Oculto a petición del usuario, se usa el botón nativo en celular y background en PC
    )

    siri_orb_flet = ft.Container(
        width=80, height=80, border_radius=40,
        gradient=ft.RadialGradient(center=ft.alignment.Alignment(0, 0), radius=0.5, colors=["#E040FB", "#00F0FF", "#0A0A18"]),
        shadow=ft.BoxShadow(spread_radius=10, blur_radius=20, color="#00F0FF", offset=ft.Offset(0,0)),
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
        scale=0.1, opacity=0, bottom=30, right=30
    )

    if user_info.get("id") and user_info["id"] in active_sessions:
        active_sessions[user_info["id"]]["btn_mic"] = btn_mic
        active_sessions[user_info["id"]]["btn_mic_container"] = btn_mic_container
        active_sessions[user_info["id"]]["siri_orb"] = siri_orb_flet

    btn_send_whatsapp = ft.Container(
        content=ft.Text("✈️", color="white", size=16, weight="bold"),
        gradient=ft.LinearGradient(
            colors=["#00F0FF", "#9D50BB"],
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1)
        ),
        border_radius=23,
        width=46,
        height=46,
        on_click=enviar_mensaje,
        ink=True,
        tooltip="Enviar mensaje",
        shadow=[
            ft.BoxShadow(
                color="#00F0FF",
                blur_radius=12,
                spread_radius=1
            )
        ],
        alignment=ft.alignment.Alignment(0, 0)
    )

    return ft.Column([
        ft.Row([
            ft.Text(g_tr("Asistente Virtual LUXO AI", "LUXO AI Assistant", "Assistant Virtuel LUXO AI", "Assistente Virtuale LUXO AI", "LUXO AI 虚拟助手"), size=24, color="#D8B4FE", weight="bold")
        ], vertical_alignment="center"),
        ft.Container(
            content=ft.SelectionArea(content=chat_display),
            expand=True,
            bgcolor="#080812",
            border_radius=20,
            padding=10,
            border=ft.Border.all(2, "#D8B4FE"),
            shadow=[
                ft.BoxShadow(
                    color="#D8B4FE",
                    blur_radius=15,
                    spread_radius=1,
                )
            ]
        ),
        ft.Row([
            input_msg,
            btn_mic_container,
            btn_send_whatsapp
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    ], expand=True)
