import flet as ft
from dataclasses import dataclass, field
from typing import Callable, Any, Dict

@dataclass
class AppState:
    page: ft.Page
    user_info: Dict[str, Any] = field(default_factory=dict)
    active_sessions: Dict[str, Any] = field(default_factory=dict)
    
    # Global Functions and Callbacks
    api_url: str = ""
    on_login_success: Callable = None
    mostrar_snack: Callable = None
    enviar_mensaje: Callable = None
    g_tr: Callable = None
    _lanzar_js: Callable = None
    inyectar_script_voz_luxo: Callable = None
    conectar_db: Callable = None
    
    # UI Components that are shared
    chat_display: Any = None
    input_msg: Any = None
    
    # Additional generic dictionary to hold dynamic variables if needed
    data: Dict[str, Any] = field(default_factory=dict)
