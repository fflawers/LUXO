# Reglas del Proyecto LUXO

## 🛑 Módulos Intocables de Voz
Las siguientes funciones y componentes son de máxima importancia para el sistema LUXO y **NUNCA DEBEN SER MODIFICADOS NI ALTERADOS** en ninguna tarea futura, a menos que el usuario lo solicite de forma explícita:

1. **Servicio Manos Libres "Oye LUXO"**: `iniciar_hilo_escucha_luxo()` en `main.py` (hilo secundario Python con `SpeechRecognition` + `PyAudio`).
2. **Frases de Activación Manos Libres**: Frases compuestas con saludo (`"oye luxo"`, `"hola luxo"`, `"oye lujo"`, `"hola lujo"`, etc.) excluyendo la palabra suelta `"luxo"`.
3. **Dictado Directo de Micrófono en Pantalla**: `on_mic_click` y `dictado_thread` en `main.py` con seguro `dictado_en_progreso`.
4. **Lectura por Voz (Bocina TTS)**: `start_speak` en `main.py` usando `win32com.client.Dispatch("SAPI.SpVoice")` con `pythoncom.CoInitialize()`.
5. **Tiempos de Escucha**: `pause_threshold = 1.0`, `phrase_time_limit = 25`, `non_speaking_duration = 0.8`.
