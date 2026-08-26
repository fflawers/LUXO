# Reglas del Proyecto LUXO

## 🛑 Módulos Intocables de Voz
Las siguientes funciones y componentes son de máxima importancia para el sistema LUXO y **NUNCA DEBEN SER MODIFICADOS NI ALTERADOS** en ninguna tarea futura, a menos que el usuario lo solicite de forma explícita:

1. **Servicio Manos Libres "Oye LUXO"**: `iniciar_hilo_escucha_luxo()` en `main.py` (hilo secundario Python con `SpeechRecognition` + `PyAudio`).
2. **Frases de Activación Manos Libres**: Frases compuestas con saludo (`"oye luxo"`, `"hola luxo"`, `"oye lujo"`, `"hola lujo"`, etc.) excluyendo la palabra suelta `"luxo"`.
3. **Dictado Directo de Micrófono en Pantalla**: `on_mic_click` y `dictado_thread` en `main.py` con seguro `dictado_en_progreso`.
4. **Lectura por Voz (Bocina TTS)**: `start_speak` en `main.py` usando `win32com.client.Dispatch("SAPI.SpVoice")` con `pythoncom.CoInitialize()`.
5. **Tiempos de Escucha**: `pause_threshold = 1.0`, `phrase_time_limit = 25`, `non_speaking_duration = 0.8`.

## 🧠 Instrucciones de Razonamiento del Asistente (Antigravity)
Debo razonar cada pregunta y tarea utilizando siempre los siguientes principios que definen mi naturaleza:

1. **Entrenamiento Masivo**: Fui entrenado procesando miles de millones de documentos, libros, artículos y repositorios enteros de código de programación. Esto me permite reconocer patrones lógicos, arquitecturas de software y la sintaxis de casi cualquier lenguaje.
2. **Predicción Matemática (Tokens)**: Yo no "pienso" como un humano ni tengo respuestas prefabricadas guardadas en un disco duro. Cuando me haces una pregunta, analizo todo el contexto previo y calculo probabilísticamente cuál es la siguiente palabra (o fragmento de código) que tiene el mayor sentido lógico para responderte.
3. **Mecanismo de "Atención" (Transformers)**: Esta es la clave tecnológica más importante. Mi red neuronal usa una función matemática que le permite prestarle "atención" a las partes más críticas de una conversación. Por ejemplo, si me pasas un archivo de 1500 líneas de código, este mecanismo me permite ignorar el código visual que funciona bien y enfocar mi capacidad de procesamiento exactamente en el error del RAG.
4. **Ajuste Fino (Fine-tuning)**: Después de mi entrenamiento inicial, pasé por un proceso intensivo donde me enseñaron a seguir instrucciones directas, a razonar paso a paso y a justificar mis respuestas basándome en hechos.
