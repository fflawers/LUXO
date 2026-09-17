// ==============================================================================
// LUXO WEB CLIENT AUDIO & TTS ENGINE (Standalone Script)
// ==============================================================================

(function() {
    if (window._luxoAudioEngineLoaded) return;
    window._luxoAudioEngineLoaded = true;
    console.log("[LUXO TTS] Motor de audio web inicializado con éxito.");

    // 1. Obtener User ID y Username
    window.getLuxoUserId = function() {
        if (window.luxoUserId && !['unknown', '', 'null', 'undefined'].includes(String(window.luxoUserId).toLowerCase())) {
            return String(window.luxoUserId);
        }
        try {
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                if (key && (key.includes('logged_user_id') || key === 'luxo_user_id')) {
                    let val = localStorage.getItem(key);
                    if (val) {
                        try { val = JSON.parse(val); } catch(e) { val = val.replace(/["']/g, ''); }
                        if (val && !['unknown', '', 'null', 'undefined'].includes(String(val).toLowerCase())) {
                            window.luxoUserId = String(val);
                            return String(val);
                        }
                    }
                }
            }
        } catch(e) {}
        return '';
    };

    window.getLuxoUsername = function() {
        if (window.luxoUsername && !['unknown', '', 'null', 'undefined'].includes(String(window.luxoUsername).toLowerCase())) {
            return String(window.luxoUsername).toLowerCase().trim();
        }
        try {
            let val = localStorage.getItem('logged_username') || sessionStorage.getItem('logged_username');
            if (val && !['unknown', '', 'null', 'undefined'].includes(String(val).toLowerCase())) {
                return String(val).toLowerCase().trim();
            }
        } catch(e) {}
        return '';
    };

    // 2. Obtener Session ID
    window.getLuxoSessionId = function() {
        if (window._luxoClientToken) return window._luxoClientToken;
        try {
            let stored = sessionStorage.getItem('luxo_client_session_id');
            if (stored) {
                window._luxoClientSessionId = stored;
                return stored;
            }
        } catch(e){}
        if (!window._luxoClientSessionId) {
            window._luxoClientSessionId = 'sess_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
            try { sessionStorage.setItem('luxo_client_session_id', window._luxoClientSessionId); } catch(e){}
        }
        return window._luxoClientSessionId;
    };

    // 3. Crear / Obtener elemento de audio persistente en el DOM
    function getOrCreateAudioElement() {
        let el = document.getElementById("luxo_global_tts_player");
        if (!el) {
            el = document.createElement("audio");
            el.id = "luxo_global_tts_player";
            el.style.display = "none";
            el.muted = false;
            el.volume = 1.0;
            (document.body || document.documentElement).appendChild(el);

            const ttsEvents = ['loadstart', 'loadedmetadata', 'canplay', 'canplaythrough', 'play', 'playing', 'pause', 'ended', 'error', 'stalled', 'abort'];
            ttsEvents.forEach(function(evName) {
                el.addEventListener(evName, function(e) {
                    console.log("[LUXO TTS EVENT] " + evName, {
                        src: el.src,
                        currentTime: el.currentTime,
                        duration: el.duration,
                        paused: el.paused,
                        muted: el.muted,
                        volume: el.volume,
                        readyState: el.readyState,
                        networkState: el.networkState,
                        error: el.error ? { code: el.error.code, message: el.error.message } : null,
                        visibilityState: document.visibilityState
                    });
                });
            });
        }
        return el;
    }

    // 4. Desbloqueo de Audio por Gesto de Usuario
    window._lastInteractionTime = Date.now();
    window.luxoUnmuteAudio = function() {
        window._lastInteractionTime = Date.now();
        try {
            if (!window._luxoAudioUnlocked) {
                window._luxoAudioUnlocked = true;
                try {
                    const AC = window.AudioContext || window.webkitAudioContext;
                    if (AC) {
                        if (!window._luxoACtx) window._luxoACtx = new AC();
                        if (window._luxoACtx.state === 'suspended') {
                            window._luxoACtx.resume();
                        }
                    }
                } catch(e){}
            }
        } catch(e){}
    };
    try {
        window.addEventListener('pointerdown', window.luxoUnmuteAudio, { capture: true, passive: true });
        window.addEventListener('touchstart', window.luxoUnmuteAudio, { capture: true, passive: true });
        window.addEventListener('mousedown', window.luxoUnmuteAudio, { capture: true, passive: true });
        window.addEventListener('click', window.luxoUnmuteAudio, { capture: true, passive: true });
        window.addEventListener('keydown', window.luxoUnmuteAudio, { capture: true, passive: true });
    } catch(e) {}

    // 5. Detener Audio / Speech
    window.luxoStopTts = function() {
        let el = document.getElementById("luxo_global_tts_player");
        if (el) {
            try {
                el.pause();
                el.currentTime = 0;
            } catch(e){}
        }
        if ('speechSynthesis' in window) {
            try { window.speechSynthesis.cancel(); } catch(e){}
        }
    };

    // 6. Fallback WebSpeech Synthesis
    window.luxoSpeakWebSpeech = function(text, voiceId, voiceGender, failedAudioUrl) {
        try {
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();

            let cleanText = (text || '').replace(/https?:\/\/\S+/g, '')
                                      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
                                      .replace(/[*_#`~>\[\]\(\)\|\-]+/g, ' ')
                                      .replace(/["']/g, '')
                                      .replace(/\s+/g, ' ')
                                      .trim();
            if (!cleanText) return;

            setTimeout(function() {
                try {
                    const u = new SpeechSynthesisUtterance(cleanText);
                    u.volume = 1.0;
                    const vId = (voiceId || '').toLowerCase();
                    const voices = window.speechSynthesis.getVoices() || [];
                    const esVoices = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith('es'));
                    const maleVoices = esVoices.filter(v => (v.name.toLowerCase().includes('male') || v.name.toLowerCase().includes('raul') || v.name.toLowerCase().includes('pablo') || v.name.toLowerCase().includes('jorge') || v.name.toLowerCase().includes('david') || v.name.toLowerCase().includes('alvaro') || v.name.toLowerCase().includes('alonso') || v.name.toLowerCase().includes('enrique')));
                    const femaleVoices = esVoices.filter(v => (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('sabina') || v.name.toLowerCase().includes('helena') || v.name.toLowerCase().includes('monica') || v.name.toLowerCase().includes('lucia') || v.name.toLowerCase().includes('dalia') || v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('laura')));

                    if (vId === 'jarvis' || vId === 'yarvis') {
                        u.lang = "es-ES";
                        u.pitch = 0.55;
                        u.rate = 0.90;
                        if (maleVoices.length > 0) u.voice = maleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else if (vId === 'jorge' || vId === 'alonso') {
                        u.lang = "es-MX";
                        u.pitch = 0.65;
                        u.rate = 0.92;
                        if (maleVoices.length > 0) u.voice = maleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else if (vId === 'luxo_avatar' || vId === 'barbara') {
                        u.lang = "es-MX";
                        u.pitch = 1.35;
                        u.rate = 1.10;
                        if (femaleVoices.length > 0) u.voice = femaleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else if (vId === 'helena' || vId === 'sabina') {
                        u.lang = "es-MX";
                        u.pitch = 1.15;
                        u.rate = 1.02;
                        if (femaleVoices.length > 0) u.voice = femaleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else {
                        u.lang = "es-MX";
                        u.pitch = (voiceGender === 'female') ? 1.20 : 0.70;
                        u.rate = 1.0;
                        if (voiceGender === 'male' && maleVoices.length > 0) u.voice = maleVoices[0];
                        else if (voiceGender === 'female' && femaleVoices.length > 0) u.voice = femaleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    }

                    window.speechSynthesis.speak(u);
                } catch(e){}
            }, 50);
        } catch(e) {
            console.log("[LUXO TTS] SpeechSynthesis error:", e);
        }
    };

    // 7. Reproducir Audio Principal con Telemetría
    window.luxoPlayDirect = function(audioUrl, text, voiceId, voiceGender) {
        window.luxoPlayTts(text, audioUrl, 'direct_' + Date.now(), voiceId, voiceGender);
    };

    window.luxoPlayTts = function(text, audioUrl, id, voiceId, voiceGender) {
        window.luxoStopTts();
        if (audioUrl) {
            function tryPlayAudio(retriesLeft) {
                try {
                    let el = getOrCreateAudioElement();
                    el.muted = false;
                    el.volume = 1.0;
                    let fullUrl = audioUrl;
                    if (fullUrl.startsWith('/')) {
                        fullUrl = window.location.origin + fullUrl;
                    }
                    
                    console.log("[LUXO TTS] DIAGNOSTICO DE REPRODUCCION:", {
                        audioUrl_recibido: audioUrl,
                        url_absoluta_final: fullUrl,
                        window_location_origin: window.location.origin,
                        voiceId: voiceId,
                        voiceGender: voiceGender,
                        texto_longitud: (text || '').length,
                        audio_muted: el.muted,
                        audio_volume: el.volume,
                        audio_src: el.src,
                        audio_readyState: el.readyState,
                        audio_networkState: el.networkState,
                        audio_paused: el.paused,
                        audio_currentTime: el.currentTime,
                        audio_error: el.error,
                        document_visibilityState: document.visibilityState,
                        retriesLeft: retriesLeft
                    });

                    el.src = fullUrl;
                    let playPromise = el.play();
                    if (playPromise !== undefined) {
                        playPromise.then(function() {
                            console.log("[LUXO TTS SUCCESS] audio.play() iniciado exitosamente:", fullUrl);
                        }).catch(function(err) {
                            console.error("[LUXO TTS ERROR] audio.play() fue rechazado/fallo:", {
                                err_name: err.name,
                                err_message: err.message,
                                es_bloqueo_autoplay: (err.name === 'NotAllowedError'),
                                audio_src: el.src,
                                audio_muted: el.muted,
                                audio_volume: el.volume,
                                audio_readyState: el.readyState,
                                audio_networkState: el.networkState,
                                document_visibilityState: document.visibilityState,
                                retriesLeft: retriesLeft
                            });
                            // Si la reproducción fue abortada por una nueva solicitud de audio, no disparar WebSpeech
                            if (err.name === 'AbortError') {
                                console.log("[LUXO TTS] Play abortado de forma controlada por cambio de audio.");
                                return;
                            }
                            if (retriesLeft > 0) {
                                setTimeout(function() { tryPlayAudio(retriesLeft - 1); }, 350);
                            } else {
                                console.warn("[LUXO TTS FALLBACK] Activando WebSpeech como respaldo tras fallos en HTML5 Audio");
                                window.luxoSpeakWebSpeech(text, voiceId, voiceGender, fullUrl);
                            }
                        });
                    }
                } catch(err) {
                    console.error("[LUXO TTS EXCEPTION] Excepcion sincrona en tryPlayAudio:", err);
                    if (retriesLeft > 0) {
                        setTimeout(function() { tryPlayAudio(retriesLeft - 1); }, 350);
                    } else {
                        window.luxoSpeakWebSpeech(text, voiceId, voiceGender, audioUrl);
                    }
                }
            }
            tryPlayAudio(5);
        } else if (text) {
            console.log("[LUXO TTS] Sin audioUrl, ejecutando WebSpeech directamente");
            window.luxoSpeakWebSpeech(text, voiceId, voiceGender);
        }
    };

    // 8. Bucle de Polling HTTP Inteligente para entrega de eventos TTS (0% CPU impact)
    let lastHandledTtsId = null;
    let isTtsPolling = false;
    if (!window._luxoTtsIntervalStarted) {
        window._luxoTtsIntervalStarted = true;
        
        async function smartTtsPollLoop() {
            if (!isTtsPolling) {
                isTtsPolling = true;
                try {
                    const uid = window.getLuxoUserId ? window.getLuxoUserId() : '';
                    const uname = window.getLuxoUsername ? window.getLuxoUsername() : '';
                    const sid = window.getLuxoSessionId ? window.getLuxoSessionId() : '';
                    const res = await fetch('/api/tts/poll?session_id=' + encodeURIComponent(sid) + '&user_id=' + encodeURIComponent(uid) + '&username=' + encodeURIComponent(uname) + '&last_id=' + encodeURIComponent(lastHandledTtsId || '') + '&_t=' + Date.now(), { cache: 'no-store' });
                    if (res && res.ok) {
                        const data = await res.json();
                        if (typeof data.sim_visible !== 'undefined') {
                            window.showSimuladorMicBtn(data.sim_visible, data.sim_mode || 'chat');
                        }
                        if (data && data.action && data.action !== 'none') {
                            if (data.action === 'speak' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                window.luxoPlayTts(data.text, data.audio_url, data.id, data.voice_id, data.voice_gender);
                            } else if (data.action === 'stop' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                window.luxoStopTts();
                            } else if (data.action === 'pause') {
                                let el = getOrCreateAudioElement();
                                if (el) { try { el.pause(); } catch(e){} }
                                if ('speechSynthesis' in window) { try { window.speechSynthesis.pause(); } catch(e){} }
                            } else if (data.action === 'resume') {
                                let el = getOrCreateAudioElement();
                                if (el) { try { el.play(); } catch(e){} }
                                if ('speechSynthesis' in window) { try { window.speechSynthesis.resume(); } catch(e){} }
                            } else if (data.action === 'dictate_simulador' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                console.log("[LUXO TTS POLL] Disparando dictado simulador vía evento:", data.mode);
                                if (window.iniciarDictadoSimulador) {
                                    window.iniciarDictadoSimulador(data.mode || 'chat');
                                }
                            }
                        }
                    }
                } catch(e) {}
                isTtsPolling = false;
            }
            const nextDelay = document.hidden ? 2500 : 700;
            setTimeout(smartTtsPollLoop, nextDelay);
        }
        
        setTimeout(smartTtsPollLoop, 800);
    }

    // ==============================================================================
    // RECONOCIMIENTO DE VOZ Y BOTÓN NATIVO PARA EL SIMULADOR IA (100% AISLADO)
    // ==============================================================================
    let _simRecognitionActive = null;
    let _simCurrentMode = 'chat';

    function playToneSim(count) {
        try {
            const cnt = count || 1;
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            function emit(freq, duration, delay) {
                setTimeout(function() {
                    try {
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.type = 'sine';
                        osc.frequency.value = freq;
                        gain.gain.setValueAtTime(0.12, ctx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start();
                        osc.stop(ctx.currentTime + duration);
                    } catch(err){}
                }, delay);
            }
            if (cnt === 1) { emit(880, 0.12, 0); } 
            else { emit(1046, 0.1, 0); emit(1318, 0.15, 100); }
        } catch(err) {}
    }

    let _simMediaRecorder = null;
    let _simAudioStream = null;
    let _simAudioChunks = [];
    let _simMediaStopTimer = null;

    function iniciarGrabacionMediaRecorderSimulador(modo) {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('❌ Tu navegador no permite acceso al micrófono.');
            updateSimMicUiState(false);
            return;
        }

        if (window.pausarReconocimientoGlobal) window.pausarReconocimientoGlobal();
        else window._simuladorActivo = true;

        navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
            _simAudioStream = stream;
            _simAudioChunks = [];
            let mimeType = 'audio/webm';
            if (!MediaRecorder.isTypeSupported('audio/webm') && MediaRecorder.isTypeSupported('audio/mp4')) {
                mimeType = 'audio/mp4';
            } else if (!MediaRecorder.isTypeSupported('audio/webm')) {
                mimeType = '';
            }
            
            const options = mimeType ? { mimeType: mimeType } : {};
            _simMediaRecorder = new MediaRecorder(stream, options);

            _simMediaRecorder.ondataavailable = function(e) {
                if (e.data && e.data.size > 0) {
                    _simAudioChunks.push(e.data);
                }
            };

            _simMediaRecorder.onstart = function() {
                console.log("[SIMULADOR MIC] Grabando audio por MediaRecorder...");
                playToneSim(1);
                updateSimMicUiState(true);
            };

            _simMediaRecorder.onstop = function() {
                console.log("[SIMULADOR MIC] Grabación MediaRecorder detenida, enviando a Whisper...");
                updateSimMicUiState(false);
                if (_simAudioStream) {
                    _simAudioStream.getTracks().forEach(function(t) { t.stop(); });
                    _simAudioStream = null;
                }
                if (_simAudioChunks.length > 0) {
                    playToneSim(2);
                    const audioBlob = new Blob(_simAudioChunks, { type: mimeType || 'audio/webm' });
                    const uid = window.getLuxoUserId ? window.getLuxoUserId() : '';
                    const uname = window.getLuxoUsername ? window.getLuxoUsername() : '';
                    const sid = window.getLuxoSessionId ? window.getLuxoSessionId() : '';
                    const did = window.getLuxoDeviceId ? window.getLuxoDeviceId() : '';
                    
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'sim_recording.webm');
                    formData.append('session_id', sid);
                    formData.append('device_id', did);
                    formData.append('user_id', uid);
                    formData.append('username', uname);
                    formData.append('mode', modo || 'chat');

                    fetch('/simulador_text_input', {
                        method: 'POST',
                        body: formData
                    }).then(function(r) { return r.json(); })
                    .then(function(res) {
                        console.log("[SIMULADOR MIC] Respuesta backend Whisper:", res);
                    }).catch(function(err) {
                        console.log("[SIMULADOR MIC] Error enviando audio:", err);
                    });
                }
            };

            _simMediaRecorder.start();

            if (_simMediaStopTimer) clearTimeout(_simMediaStopTimer);
            _simMediaStopTimer = setTimeout(function() {
                if (_simMediaRecorder && _simMediaRecorder.state === 'recording') {
                    _simMediaRecorder.stop();
                }
            }, 8000);

        }).catch(function(err) {
            console.log("[SIMULADOR MIC] Error getUserMedia:", err);
            updateSimMicUiState(false);
            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                alert('⚠️ Permiso de micrófono denegado. Permite el acceso al micrófono en la barra de tu navegador.');
            }
        });
    }

    window.iniciarDictadoSimulador = function(modo) {
        try {
            _simCurrentMode = modo || _simCurrentMode || 'chat';

            // Si ya hay una grabación en progreso con MediaRecorder, detenerla para procesar
            if (_simMediaRecorder && _simMediaRecorder.state === 'recording') {
                if (_simMediaStopTimer) clearTimeout(_simMediaStopTimer);
                _simMediaRecorder.stop();
                return;
            }

            if (window.pausarReconocimientoGlobal) window.pausarReconocimientoGlobal();
            else window._simuladorActivo = true;

            let SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SR) {
                try {
                    if (window.top) SR = window.top.SpeechRecognition || window.top.webkitSpeechRecognition;
                } catch(eTop){}
            }

            // Si no hay WebSpeech disponible, usar fallback universal MediaRecorder
            if (!SR) { 
                console.log("[SIMULADOR MIC] WebSpeech no disponible, usando fallback MediaRecorder...");
                iniciarGrabacionMediaRecorderSimulador(_simCurrentMode);
                return; 
            }

            if (_simRecognitionActive) {
                try { 
                    if (typeof _simRecognitionActive.abort === "function") _simRecognitionActive.abort();
                    else if (typeof _simRecognitionActive.stop === "function") _simRecognitionActive.stop();
                } catch(e){}
                _simRecognitionActive = null;
            }

            const rSim = new SR();
            rSim.lang = 'es-MX';
            rSim.interimResults = false;
            rSim.continuous = false;
            rSim.maxAlternatives = 1;
            _simRecognitionActive = rSim;

            rSim.onstart = function() {
                console.log("[SIMULADOR MIC] ACTIVANDO MICROFONO SIMULADOR (WebSpeech)", { modo: _simCurrentMode, timestamp: Date.now() });
                playToneSim(1);
                updateSimMicUiState(true);
            };

            rSim.onresult = function(ev) {
                const txt = ev.results && ev.results[0] && ev.results[0][0] ? ev.results[0][0].transcript : '';
                if (txt) {
                    playToneSim(2);
                    console.log("[SIMULADOR MIC] Texto capturado:", txt);
                    const uid = window.getLuxoUserId ? window.getLuxoUserId() : '';
                    const uname = window.getLuxoUsername ? window.getLuxoUsername() : '';
                    const sid = window.getLuxoSessionId ? window.getLuxoSessionId() : '';
                    const did = window.getLuxoDeviceId ? window.getLuxoDeviceId() : '';
                    fetch('/simulador_text_input?session_id=' + encodeURIComponent(sid) + '&device_id=' + encodeURIComponent(did) + '&user_id=' + encodeURIComponent(uid) + '&username=' + encodeURIComponent(uname) + '&mode=' + encodeURIComponent(_simCurrentMode) + '&text=' + encodeURIComponent(txt), { method: 'POST' })
                    .then(function(r) { return r.json(); })
                    .then(function(res) {
                        console.log("[SIMULADOR MIC] Respuesta backend:", res);
                    }).catch(function(err){
                        console.log("[SIMULADOR MIC] Error enviando texto:", err);
                    });
                }
            };

            rSim.onerror = function(ev) { 
                console.log("[SIMULADOR MIC] Error WebSpeech:", ev.error);
                _simRecognitionActive = null;
                updateSimMicUiState(false);
                if (ev.error === 'not-allowed') {
                    alert('⚠️ Permiso de micrófono denegado. Permite el acceso al micrófono en la barra de tu navegador.');
                } else if (ev.error !== 'no-speech' && ev.error !== 'aborted') {
                    // Si WebSpeech falla por red u otra causa, usar fallback MediaRecorder
                    console.log("[SIMULADOR MIC] Reintentando con MediaRecorder fallback...");
                    iniciarGrabacionMediaRecorderSimulador(_simCurrentMode);
                }
            };

            rSim.onend = function() { 
                console.log("[SIMULADOR MIC] DETENIENDO MICROFONO", { timestamp: Date.now() });
                _simRecognitionActive = null;
                updateSimMicUiState(false);
            };
            
            rSim.start();
        } catch(e) {
            console.log("Error iniciando WebSpeech, ejecutando fallback:", e);
            _simRecognitionActive = null;
            iniciarGrabacionMediaRecorderSimulador(_simCurrentMode);
        }
    };

    function updateSimMicButtonMode(modo) {
        const btn = document.getElementById("luxo-floating-sim-mic");
        if (!btn) return;
        const m = modo || window._simCurrentMode || _simCurrentMode || 'chat';
        if (m === 'voz') {
            btn.innerHTML = `<span style="font-size:18px;">🎙️</span><span id="luxo-sim-btn-label" style="font-size:10px;font-weight:900;color:#00FFAA;margin-left:2px;">VOZ</span>`;
            btn.style.background = "linear-gradient(135deg, #0575E6 0%, #00F260 100%)";
            btn.style.borderColor = "#00FFAA";
            btn.style.boxShadow = "0 0 15px rgba(0, 255, 170, 0.8)";
            btn.setAttribute("title", "Hablar por Voz (Simulador IA)");
        } else {
            btn.innerHTML = `<span style="font-size:18px;">🎙️</span><span id="luxo-sim-btn-label" style="font-size:10px;font-weight:900;color:#00FFFF;margin-left:2px;">CHAT</span>`;
            btn.style.background = "linear-gradient(135deg, #7928CA 0%, #B800FF 100%)";
            btn.style.borderColor = "#00FFFF";
            btn.style.boxShadow = "0 0 12px rgba(184, 0, 255, 0.7)";
            btn.setAttribute("title", "Dictar al Chat (Simulador IA)");
        }
    }

    function updateSimMicUiState(isRecording) {
        const btn = document.getElementById("luxo-floating-sim-mic");
        if (btn) {
            if (isRecording) {
                btn.style.borderColor = "#FFFFFF";
                btn.style.boxShadow = "0 0 25px #FF0055";
                btn.style.background = "#FF0000";
            } else {
                updateSimMicButtonMode(window._simCurrentMode || _simCurrentMode || 'chat');
            }
        }
    }

    function ensureSimMicBtnCreated() {
        let simMicBtn = document.getElementById("luxo-floating-sim-mic");
        if (!simMicBtn && (document.body || document.documentElement)) {
            simMicBtn = document.createElement("div");
            simMicBtn.id = "luxo-floating-sim-mic";
            simMicBtn.innerHTML = `<span style="font-size:18px;">🎙️</span><span id="luxo-sim-btn-label" style="font-size:10px;font-weight:900;color:#00FFFF;margin-left:2px;">CHAT</span>`;
            simMicBtn.setAttribute("title", "Micrófono Simulador de Ventas IA");
            simMicBtn.style.cssText = "position: fixed; bottom: 12px; right: 118px; z-index: 9999999; font-size: 18px; background: linear-gradient(135deg, #7928CA 0%, #B800FF 100%); border: 1.8px solid #00FFFF; border-radius: 23px; width: 56px; height: 46px; display: none; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(184, 0, 255, 0.7); cursor: pointer; transition: background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease; touch-action: manipulation; user-select: none;";
            
            let isDraggingSim = false;
            let startXSim, startYSim, initialXSim, initialYSim;
            
            simMicBtn.addEventListener('touchstart', function(e) {
                isDraggingSim = false;
                let touch = e.touches[0];
                startXSim = touch.clientX;
                startYSim = touch.clientY;
                let rect = simMicBtn.getBoundingClientRect();
                initialXSim = rect.left;
                initialYSim = rect.top;
                simMicBtn.style.transition = 'none';
            });

            simMicBtn.addEventListener('touchmove', function(e) {
                let touch = e.touches[0];
                let dx = touch.clientX - startXSim;
                let dy = touch.clientY - startYSim;
                
                if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                    isDraggingSim = true;
                    e.preventDefault();
                    let newX = Math.max(0, Math.min(initialXSim + dx, window.innerWidth - 56));
                    let newY = Math.max(0, Math.min(initialYSim + dy, window.innerHeight - 46));
                    
                    simMicBtn.style.left = newX + 'px';
                    simMicBtn.style.top = newY + 'px';
                    simMicBtn.style.right = 'auto';
                    simMicBtn.style.bottom = 'auto';
                }
            }, { passive: false });

            simMicBtn.addEventListener('touchend', function(e) {
                simMicBtn.style.transition = 'background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease';
            });
            
            function onSimMicPress(e) {
                if (isDraggingSim) return;
                if (e) { try { e.preventDefault(); e.stopPropagation(); } catch(err){} }
                const currentModo = window._simCurrentMode || _simCurrentMode || 'chat';
                console.log("[SIMULADOR MIC] Clic físico nativo en #luxo-floating-sim-mic con modo:", currentModo);
                simMicBtn.style.transform = "scale(0.9)";
                setTimeout(function() { simMicBtn.style.transform = "scale(1)"; }, 150);
                window.iniciarDictadoSimulador(currentModo);
            }

            simMicBtn.onclick = onSimMicPress;
            (document.body || document.documentElement).appendChild(simMicBtn);
        }
        return simMicBtn;
    }

    window.detenerDictadoSimulador = function() {
        try {
            if (_simMediaRecorder && _simMediaRecorder.state === 'recording') {
                if (_simMediaStopTimer) clearTimeout(_simMediaStopTimer);
                _simMediaRecorder.stop();
            }
            if (_simAudioStream) {
                _simAudioStream.getTracks().forEach(function(t) { t.stop(); });
                _simAudioStream = null;
            }
            if (_simRecognitionActive) {
                if (typeof _simRecognitionActive.abort === "function") {
                    _simRecognitionActive.abort();
                } else if (typeof _simRecognitionActive.stop === "function") {
                    _simRecognitionActive.stop();
                }
                _simRecognitionActive = null;
            }
            if (window.reanudarReconocimientoGlobal) {
                window.reanudarReconocimientoGlobal();
            } else {
                window._simuladorActivo = false;
            }
            updateSimMicUiState(false);
        } catch(e){}
    };

    function evaluarVisibilidadSimulador() {
        // 1. Detección por ruta de URL en navegador (Flet SPA routing)
        const hash = (window.location.hash || '').toLowerCase();
        const path = (window.location.pathname || '').toLowerCase();
        const isUrlSim = hash.includes('simulador') || path.includes('simulador') || hash.includes('capacitacion') || path.includes('capacitacion');
        
        // 2. Detección por estado en memoria JS
        const isStateSim = (window._simuladorVisible === true) || (window._luxoActiveView === 'simulador') || (window._luxoActiveView === 'capacitacion_ia');
        
        // 3. Detección por respuesta de polling backend
        const isPollSim = (window._simPollVisible === true);
        
        const shouldBeVisible = (isUrlSim || isStateSim || isPollSim);
        const btn = ensureSimMicBtnCreated();
        if (btn) {
            const currentDisplay = btn.style.display;
            const targetDisplay = shouldBeVisible ? "flex" : "none";
            if (currentDisplay !== targetDisplay) {
                btn.style.display = targetDisplay;
            }
            if (shouldBeVisible) {
                updateSimMicButtonMode(window._simCurrentMode || _simCurrentMode || 'chat');
            }
        }
        return shouldBeVisible;
    }

    window.evaluarVisibilidadSimulador = evaluarVisibilidadSimulador;

    window.showSimuladorMicBtn = function(visible, modo) {
        _simCurrentMode = modo || _simCurrentMode || 'chat';
        window._simCurrentMode = _simCurrentMode;
        window._simuladorVisible = (visible !== false);
        window._simPollVisible = (visible !== false);
        if (!visible) {
            window.detenerDictadoSimulador();
        } else {
            if (window.pausarReconocimientoGlobal) window.pausarReconocimientoGlobal();
            else window._simuladorActivo = true;
        }
        evaluarVisibilidadSimulador();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            ensureSimMicBtnCreated();
            evaluarVisibilidadSimulador();
        });
    } else {
        ensureSimMicBtnCreated();
        evaluarVisibilidadSimulador();
    }

    // Reconciliación continua ultra-rápida (cada 400ms) para respuesta visual instantánea
    setInterval(evaluarVisibilidadSimulador, 400);
    window.addEventListener('hashchange', evaluarVisibilidadSimulador);
    window.addEventListener('popstate', evaluarVisibilidadSimulador);
})();
