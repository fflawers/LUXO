// ==============================================================================
// LUXO WEB CLIENT AUDIO & TTS ENGINE (Standalone Script)
// ==============================================================================

(function() {
    if (window._luxoAudioEngineLoaded) return;
    window._luxoAudioEngineLoaded = true;
    console.log("[LUXO TTS] Motor de audio web inicializado con éxito.");
    console.log("🚀 [LUXO JS] Script biométrico cargado correctamente en window");

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

    // 4. Desbloqueo de Audio por Gesto de Usuario & Gestión de Avatar de Inicio
    window._lastInteractionTime = Date.now();
    window._luxoAvatarAudioActive = false;
    window._luxoAvatarAudioMuted = false;
    window.luxoUserIsLoggedIn = false;

    function hasActiveStoredSession() {
        try {
            let u = localStorage.getItem('logged_user_id') || sessionStorage.getItem('logged_user_id');
            if (u && !['unknown', '', 'null', 'undefined'].includes(String(u).toLowerCase())) {
                return true;
            }
        } catch(e){}
        return false;
    }

    window.luxoPlayLoginAvatarAudio = function(force) {
        if (force === true) {
            window.luxoUserIsLoggedIn = false;
        }
        const uid = window.getLuxoUserId ? window.getLuxoUserId() : (window.luxoUserId || null);
        if (window.luxoUserIsLoggedIn || uid) {
            window.luxoStopLoginAvatarAudio();
            return;
        }
        window._luxoAvatarAudioActive = true;
        if (window._luxoAvatarAudioMuted) return;

        try {
            let snd = document.getElementById('luxo_avatar_audio_el');
            if (snd) {
                // Si ya está reproduciéndose activamente, no interrumpir ni recargar
                if (!snd.paused && snd.currentTime > 0) {
                    return;
                }
                if (!snd.src || !snd.src.includes('saludo_login')) {
                    snd.src = '/custom_assets/saludo_login.mp3';
                }
                snd.loop = true;
                snd.volume = 1.0;
            } else {
                snd = document.createElement('audio');
                snd.id = 'luxo_avatar_audio_el';
                snd.preload = 'auto';
                snd.src = '/custom_assets/saludo_login.mp3';
                snd.loop = true;
                snd.volume = 1.0;
                (document.body || document.documentElement).appendChild(snd);
            }
            let p = snd.play();
            if (p !== undefined) {
                p.then(function() {
                    console.log('[LUXO AVATAR] Audio reproduciéndose en bucle.');
                }).catch(function(err) {
                    console.log('[LUXO AVATAR] Autoplay esperando interacción del usuario.');
                });
            }
        } catch(e){
            console.log('[LUXO AVATAR] Error al reproducir:', e);
        }
    };

    // Auto-activación al cargar el DOM si no se ha iniciado sesión
    try {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                if (!window.luxoUserIsLoggedIn) {
                    window.luxoPlayLoginAvatarAudio();
                }
            });
        } else {
            if (!window.luxoUserIsLoggedIn) {
                window.luxoPlayLoginAvatarAudio();
            }
        }
    } catch(e){}

    window.luxoStopLoginAvatarAudio = function() {
        window._luxoAvatarAudioActive = false;
        try {
            let snd = document.getElementById('luxo_avatar_audio_el');
            if (snd) {
                try {
                    snd.pause();
                    snd.currentTime = 0;
                    snd.loop = false;
                    snd.muted = true;
                    snd.removeAttribute('src');
                    snd.load();
                } catch(e){}
                if (snd.parentNode) {
                    try { snd.parentNode.removeChild(snd); } catch(e){}
                }
            }
        } catch(e){}
    };

    // Interceptor INMEDIATO al hacer clic en ACCEDER o presionar Enter (corta el audio al instante con 0ms de latencia)
    try {
        document.addEventListener('click', function(e) {
            let t = e.target;
            if (t && (t.innerText === 'ACCEDER' || (t.textContent && t.textContent.trim().toUpperCase() === 'ACCEDER') || (t.getAttribute && t.getAttribute('tooltip') === 'ACCEDER'))) {
                window.luxoUserIsLoggedIn = true;
                window.luxoStopLoginAvatarAudio();
            }
        }, true);
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                window.luxoStopLoginAvatarAudio();
            }
        }, true);
    } catch(e){}

    window.luxoToggleLoginAvatarAudio = function() {
        let snd = document.getElementById('luxo_avatar_audio_el');
        let isCurrentlyPlaying = (snd && !snd.paused && !snd.muted && snd.currentTime > 0);
        if (isCurrentlyPlaying || (!window._luxoAvatarAudioMuted && window._luxoAvatarAudioActive && snd && !snd.paused)) {
            window._luxoAvatarAudioMuted = true;
            window.luxoStopLoginAvatarAudio();
            return true; // Silenciado
        } else {
            window._luxoAvatarAudioMuted = false;
            window.luxoPlayLoginAvatarAudio();
            return false; // Con audio
        }
    };

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
            // Si el usuario YA tiene sesión o está autenticado, DESTRUIR el audio del avatar
            const uid = window.getLuxoUserId ? window.getLuxoUserId() : (window.luxoUserId || null);
            if (window.luxoUserIsLoggedIn || uid) {
                window.luxoStopLoginAvatarAudio();
                return;
            }
            // Si estamos en la pantalla de login y el avatar no está silenciado, iniciar en el primer gesto
            if (!window.luxoUserIsLoggedIn && !window._luxoAvatarAudioMuted) {
                let snd = document.getElementById('luxo_avatar_audio_el');
                if (snd) {
                    if (snd.paused) {
                        let p = snd.play();
                        if (p !== undefined) {
                            p.catch(function(){});
                        }
                    }
                } else {
                    window.luxoPlayLoginAvatarAudio();
                }
            }
        } catch(e){}
    };
    try {
        ['pointerdown', 'keydown'].forEach(function(evName) {
            window.addEventListener(evName, window.luxoUnmuteAudio, { capture: true, passive: true });
        });
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
            if (voiceId === 'luxo_avatar' || (failedAudioUrl && failedAudioUrl.includes('saludo_login'))) {
                console.log('[LUXO TTS] Omitiendo WebSpeech para audio del avatar original.');
                return;
            }
            window.speechSynthesis.cancel();

            let cleanText = (text || '').replace(/https?:\/\/\S+/g, '')
                                      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
                                      .replace(/```[\s\S]*?```/g, '')
                                      .replace(/`[^`]*`/g, '')
                                      .replace(/<[^>]+>/g, '')
                                      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{2B50}-\u{2B55}\u{FE0F}\u{200D}]/gu, ' ')
                                      .replace(/#+\s*/g, '')
                                      .replace(/[*_~`|]+/g, ' ')
                                      .replace(/^\s*[-•*+–—]\s+/gm, '')
                                      .replace(/[-•*+–—]\s+/g, '. ')
                                      .replace(/÷/g, ' entre ')
                                      .replace(/\bPPT\b/gi, 'P P T')
                                      .replace(/\bUPT\b/gi, 'U P T')
                                      .replace(/\bSAP\b/gi, 'S A P')
                                      .replace(/\bKPI\b/gi, 'K P I')
                                      .replace(/\bVLT\b/gi, 'V L T')
                                      .replace(/\bUPC\b/gi, 'U P C')
                                      .replace(/[:;]+/g, '.')
                                      .replace(/[¿¡]+/g, '')
                                      .replace(/[?!]+/g, '.')
                                      .replace(/[()[\]{}"']+/g, ' ')
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
    window.luxoPlayDirect = function(audioUrl, text, voiceId, voiceGender, id) {
        let playId = id || ('direct_' + Date.now());
        lastHandledTtsId = playId;
        window.luxoPlayTts(text, audioUrl, playId, voiceId, voiceGender);
    };

    window.luxoPlayTts = function(text, audioUrl, id, voiceId, voiceGender) {
        if (id) {
            lastHandledTtsId = id;
        }
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

                    if (uid || window.luxoUserIsLoggedIn) {
                        let oldAvatarSnd = document.getElementById('luxo_avatar_audio_el');
                        if (oldAvatarSnd) {
                            window.luxoStopLoginAvatarAudio();
                        }
                    }

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
                            } else if (data.action === 'open_facial_login' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                if (!document.getElementById('luxo-facial-modal')) {
                                    console.log("[LUXO BIOMETRIA] Disparando Reconocimiento Facial Login");
                                    if (window.luxoAbrirCamaraFacialLogin) {
                                        window.luxoAbrirCamaraFacialLogin();
                                    }
                                }
                            } else if (data.action === 'open_passkey_login' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                if (!document.getElementById('luxo-passkey-login-banner')) {
                                    console.log("[LUXO BIOMETRIA] Disparando WebAuthn / Passkey Login");
                                    if (window.luxoActivarPasskeyLogin) {
                                        window.luxoActivarPasskeyLogin();
                                    }
                                }
                            } else if (data.action === 'open_colab_face' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                console.log("[LUXO BIOMETRIA] Disparando Registro Facial Colaborador:", data.colab_id, data.colab_name);
                                if (window.luxoAbrirCamaraFacialColab) {
                                    window.luxoAbrirCamaraFacialColab(data.colab_id, data.colab_name);
                                }
                            } else if (data.action === 'open_colab_huella' && data.id && data.id !== lastHandledTtsId) {
                                lastHandledTtsId = data.id;
                                console.log("[LUXO BIOMETRIA] Disparando Registro Huella Colaborador:", data.colab_id, data.colab_name);
                                if (window.luxoAbrirHuellaColab) {
                                    window.luxoAbrirHuellaColab(data.colab_id, data.colab_name);
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
                const targetModo = window._simCurrentMode || _simCurrentMode || 'chat';
                updateSimMicButtonMode(targetModo);
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

    // ==============================================================================
    // SUITE BIOMÉTRICA NATIVA DE LUXO (Face ID & Huella / WebAuthn)
    // ==============================================================================

    window.luxoAbrirCamaraFacialLogin = function() {
        if (document.getElementById('luxo-facial-modal')) return;

        const exist = document.getElementById('luxo-facial-modal');
        if (exist) exist.remove();
        
        const modal = document.createElement('div');
        modal.id = 'luxo-facial-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:99999999;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Segoe UI,sans-serif;backdrop-filter:blur(8px);';
        modal.innerHTML = `
            <div style="background:#0a0a16;border:2px solid #00FFFF;border-radius:24px;padding:28px 24px;max-width:420px;width:92%;text-align:center;box-shadow:0 0 45px rgba(0,255,255,0.4);position:relative;">
                <div style="font-size:32px;margin-bottom:4px;">📷</div>
                <h3 style="color:#00FFFF;margin:0 0 6px;font-size:20px;letter-spacing:1px;">Reconocimiento Facial</h3>
                <p style="color:#aaa;font-size:13px;margin:0 0 16px;">Coloca tu rostro frente a la cámara y presiona Capturar</p>
                <div style="position:relative;width:220px;height:220px;margin:0 auto 16px;">
                    <video id="luxo-cam-login" autoplay playsinline muted style="width:220px;height:220px;object-fit:cover;border-radius:50%;border:3px solid #00FFFF;box-shadow:0 0 20px rgba(0,255,255,0.3);"></video>
                    <canvas id="luxo-canvas-login" width="220" height="220" style="display:none;"></canvas>
                </div>
                <p id="luxo-face-login-msg" style="color:#00FFFF;font-size:13px;min-height:22px;margin:0 0 16px;font-weight:600;">Iniciando cámara...</p>
                <div style="display:flex;gap:12px;justify-content:center;">
                    <button id="btn-cap-login" style="background:linear-gradient(135deg,#0055ff,#00bbff);color:white;border:none;padding:11px 24px;border-radius:12px;font-size:14px;font-weight:bold;cursor:pointer;box-shadow:0 4px 15px rgba(0,187,255,0.4);">📸 Capturar</button>
                    <button id="btn-close-face-login" style="background:#222233;color:#aaa;border:1px solid #444;padding:11px 20px;border-radius:12px;font-size:14px;cursor:pointer;">✕ Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        let stream = null;
        function stopCam() { if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; } }

        function closeModal() {
            stopCam();
            modal.remove();
        }

        document.getElementById('btn-close-face-login').onclick = closeModal;

        const setMsg = (msg, color) => {
            const el = document.getElementById('luxo-face-login-msg');
            if (el) { el.innerText = msg; el.style.color = color || '#00FFFF'; }
        };

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 640 } } })
        .then(s => {
            stream = s;
            const vid = document.getElementById('luxo-cam-login');
            if (vid) vid.srcObject = s;
            setMsg('🟢 Cámara activa. Presiona Capturar para ingresar.', '#00FFFF');
        })
        .catch(err => {
            setMsg('⚠️ Permiso de cámara denegado o no disponible en este dispositivo.', '#FF4500');
        });

        document.getElementById('btn-cap-login').onclick = function() {
            const video = document.getElementById('luxo-cam-login');
            const canvas = document.getElementById('luxo-canvas-login');
            if (!video || !canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 220, 220);
            const frameB64 = canvas.toDataURL('image/jpeg', 0.85);

            setMsg('⏳ Analizando vector facial...', '#FFD700');

            fetch('/api/biometria/facial_login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    frame_base64: frameB64,
                    device_token: window.luxoDeviceId || window.luxoSessionId || ''
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'ok') {
                    setMsg('✅ ¡Identidad Verificada! Bienvenido, ' + data.nombre, '#7CFC00');
                    stopCam();
                    try {
                        localStorage.setItem('logged_user_id', String(data.usuario_id || data.user_id || ''));
                        localStorage.setItem('logged_username', String(data.usuario || ''));
                    } catch(e){}
                    setTimeout(() => {
                        modal.remove();
                    }, 800);
                } else {
                    setMsg('❌ ' + (data.message || 'Rostro no reconocido.'), '#FF4500');
                }
            })
            .catch(err => {
                setMsg('❌ Error de comunicación con el servidor.', '#FF4500');
            });
        };
    };

    window.luxoActivarPasskeyLogin = async function() {
        if (document.getElementById('luxo-passkey-login-banner')) return;

        console.log("LUXO: [DIAGNÓSTICO INICIAL WEBAUTHN]");
        const exist = document.getElementById('luxo-passkey-login-banner');
        if (exist) exist.remove();

        const banner = document.createElement('div');
        banner.id = 'luxo-passkey-login-banner';
        banner.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#0a0a16;border:2px solid #D8B4FE;color:#D8B4FE;padding:16px 28px;border-radius:16px;font-size:14px;font-weight:bold;z-index:99999999;box-shadow:0 0 35px rgba(216,180,254,0.4);display:flex;align-items:center;gap:12px;font-family:Segoe UI,sans-serif;';
        banner.innerHTML = '<span style="font-size:24px;">👆</span><span id="luxo-pk-txt">Iniciando sensor biométrico...</span>';
        document.body.appendChild(banner);

        const setTxt = (msg, color) => {
            const el = document.getElementById('luxo-pk-txt');
            if (el) { el.innerText = msg; }
            if (color) banner.style.borderColor = color;
        };

        if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            console.warn("LUXO: [SEGURIDAD W3C] La página se está ejecutando en un origen no seguro (HTTP IP). WebAuthn exige HTTPS o localhost.");
            setTxt('⚠️ WebAuthn requiere HTTPS o localhost en celulares. Revisa la consola o activa chrome://flags/#unsafely-treat-insecure-origin-as-secure', '#FF8C00');
            setTimeout(() => { banner.remove(); window._luxoPasskeyActivo = false; }, 7000);
            return;
        }

        if (!window.PublicKeyCredential || !navigator.credentials || !navigator.credentials.get) {
            console.error("LUXO: navigator.credentials o PublicKeyCredential no disponibles.");
            setTxt('⚠️ Tu navegador o dispositivo no tiene habilitado WebAuthn / Passkeys.', '#FF8C00');
            setTimeout(() => { banner.remove(); window._luxoPasskeyActivo = false; }, 4500);
            return;
        }

        try {
            console.log("LUXO: iniciando WebAuthn -> solicitando challenge a /api/biometria/passkey_challenge");
            const challResp = await fetch('/api/biometria/passkey_challenge');
            const challData = await challResp.json();
            console.log("LUXO: challenge recibido del servidor:", challData);

            if (!challData.challenge) {
                setTxt('❌ Error al obtener desafío del servidor.', '#FF4500');
                setTimeout(() => { banner.remove(); window._luxoPasskeyActivo = false; }, 3000);
                return;
            }

            const challenge = Uint8Array.from(atob(challData.challenge.replace(/-/g,'+').replace(/_/g,'/')), c => c.charCodeAt(0));
            setTxt('👆 Toca el lector de huella o sensor biométrico...', '#00FFFF');

            const credential = await navigator.credentials.get({
                publicKey: {
                    challenge: challenge,
                    rpId: challData.rp_id || window.location.hostname,
                    userVerification: 'preferred',
                    timeout: 60000
                }
            });

            console.log("LUXO: [ÉXITO WEBAUTHN] Credencial obtenida del sensor biométrico:", credential);
            setTxt('⏳ Validando firma criptográfica...', '#FFD700');
            const credIdUrl = credential.id || '';
            const credIdRaw = btoa(String.fromCharCode(...new Uint8Array(credential.rawId)));
            let userHandleStr = '';
            if (credential.response && credential.response.userHandle) {
                try {
                    userHandleStr = new TextDecoder().decode(credential.response.userHandle);
                } catch(e) {}
            }

            const verResp = await fetch('/api/biometria/passkey_verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    credential_id: credIdUrl,
                    raw_id: credIdRaw,
                    user_handle: userHandleStr,
                    device_token: window.luxoDeviceId || window.luxoSessionId || ''
                })
            });
            const verData = await verResp.json();
            console.log("LUXO: respuesta de verificación passkey_verify:", verData);

            if (verData.status === 'ok') {
                setTxt('✅ ¡Bienvenido, ' + verData.nombre + '!', '#7CFC00');
                banner.style.borderColor = '#7CFC00';
                banner.style.color = '#7CFC00';
                try {
                    localStorage.setItem('logged_user_id', String(verData.usuario_id || verData.user_id || ''));
                    localStorage.setItem('logged_username', String(verData.usuario || ''));
                } catch(e){}
                setTimeout(() => {
                    banner.remove();
                }, 800);
            } else {
                setTxt('❌ ' + (verData.message || 'Huella / Passkey no encontrada.'), '#FF4500');
                banner.style.borderColor = '#FF4500';
                setTimeout(() => {
                    banner.remove();
                }, 3500);
            }
        } catch(ex) {
            console.error("LUXO: [ERROR WEBAUTHN]:", ex);
            banner.style.borderColor = '#FF8C00';
            if (ex.name === 'NotAllowedError') {
                setTxt('⚠️ Lectura biométrica cancelada por el usuario.', '#FF8C00');
            } else if (ex.name === 'SecurityError') {
                setTxt('🔒 Error de Seguridad WebAuthn: Requiere HTTPS.', '#FF4500');
            } else {
                setTxt('⚠️ ' + ex.message, '#FF8C00');
            }
            setTimeout(() => {
                banner.remove();
                window._luxoPasskeyActivo = false;
            }, 3500);
        }
    };

    window.luxoAbrirCamaraFacialColab = function(colabId, colabName) {
        const exist = document.getElementById('luxo-reg-facial-modal');
        if (exist) exist.remove();
        
        const modal = document.createElement('div');
        modal.id = 'luxo-reg-facial-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:99999999;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Segoe UI,sans-serif;backdrop-filter:blur(8px);';
        modal.innerHTML = `
            <div style="background:#0a0a16;border:2px solid #00FFFF;border-radius:24px;padding:26px;max-width:420px;width:92%;text-align:center;box-shadow:0 0 45px rgba(0,255,255,0.4);">
                <h3 style="color:#00FFFF;margin:0 0 6px;font-size:18px;">📷 Registrar Rostro (Face ID)</h3>
                <p style="color:#aaa;font-size:13px;margin:0 0 14px;">Colaborador: <b style="color:white;">` + colabName + `</b></p>
                <div style="position:relative;width:220px;height:220px;margin:0 auto 16px;">
                    <video id="luxo-cam-reg" autoplay playsinline muted style="width:220px;height:220px;object-fit:cover;border-radius:50%;border:3px solid #00FFFF;"></video>
                    <canvas id="luxo-canvas-reg" width="220" height="220" style="display:none;"></canvas>
                </div>
                <p id="luxo-reg-msg" style="color:#00FFFF;font-size:13px;min-height:20px;margin-bottom:14px;font-weight:600;">Iniciando cámara...</p>
                <div style="display:flex;gap:12px;justify-content:center;">
                    <button id="btn-cap-colab" style="background:linear-gradient(135deg,#0055ff,#00bbff);color:white;border:none;padding:10px 22px;border-radius:10px;font-size:14px;font-weight:bold;cursor:pointer;">📸 Capturar Foto</button>
                    <button id="btn-close-colab" style="background:#222233;color:#aaa;border:1px solid #444;padding:10px 20px;border-radius:10px;font-size:14px;cursor:pointer;">✕ Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        let stream = null;
        function stopCam() { if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; } }
        
        document.getElementById('btn-close-colab').onclick = function() {
            stopCam();
            modal.remove();
        };
        
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 640 } } })
        .then(s => {
            stream = s;
            const vid = document.getElementById('luxo-cam-reg');
            if (vid) vid.srcObject = s;
            document.getElementById('luxo-reg-msg').innerText = '🟢 Cámara lista. Presiona Capturar Foto.';
        })
        .catch(err => {
            document.getElementById('luxo-reg-msg').innerText = '⚠️ No se pudo acceder a la cámara. Revisa permisos.';
            document.getElementById('luxo-reg-msg').style.color = '#FF4500';
        });
        
        document.getElementById('btn-cap-colab').onclick = function() {
            const video = document.getElementById('luxo-cam-reg');
            const canvas = document.getElementById('luxo-canvas-reg');
            if (!video || !canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 220, 220);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
            
            document.getElementById('luxo-reg-msg').innerText = '⏳ Guardando vector biométrico facial...';
            document.getElementById('luxo-reg-msg').style.color = '#FFD700';
            
            fetch('/api/biometria/registrar_rostro_colaborador', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({colaborador_id: colabId, nombre: colabName, imagen: dataUrl})
            })
            .then(r => r.json())
            .then(d => {
                if (d.ok) {
                    document.getElementById('luxo-reg-msg').innerText = '✅ ¡Rostro registrado exitosamente!';
                    document.getElementById('luxo-reg-msg').style.color = '#7CFC00';
                    stopCam();
                    setTimeout(() => { modal.remove(); }, 1800);
                } else {
                    document.getElementById('luxo-reg-msg').innerText = '❌ Error: ' + (d.error || 'No se detectó un rostro claro.');
                    document.getElementById('luxo-reg-msg').style.color = '#FF4500';
                }
            })
            .catch(() => {
                document.getElementById('luxo-reg-msg').innerText = '❌ Error al conectar con el servidor';
                document.getElementById('luxo-reg-msg').style.color = '#FF4500';
            });
        };
    };

    window.luxoAbrirHuellaColab = async function(colabId, colabName) {
        const existModal = document.getElementById('luxo-huella-modal');
        if (existModal) existModal.remove();
        
        const modal = document.createElement('div');
        modal.id = 'luxo-huella-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:99999999;display:flex;align-items:center;justify-content:center;font-family:Segoe UI,sans-serif;backdrop-filter:blur(8px);';
        modal.innerHTML = `
            <div style="background:#0a0a16;border:2px solid #D8B4FE;border-radius:24px;padding:26px;max-width:400px;width:92%;text-align:center;box-shadow:0 0 45px rgba(216,180,254,0.35);">
                <div style="font-size:44px;margin-bottom:10px;">👆</div>
                <h3 style="color:#D8B4FE;margin:0 0 6px;font-size:18px;">Registrar Huella / Passkey</h3>
                <p style="color:#aaa;font-size:13px;margin:0 0 14px;">Colaborador: <b style="color:white;">` + colabName + `</b></p>
                <p id="luxo-hue-status" style="color:#FFD700;font-size:13px;min-height:22px;margin-bottom:16px;font-weight:600;">Iniciando sensor biométrico...</p>
                <button id="btn-hue-close" style="padding:10px 22px;background:#222233;color:#aaa;border:1px solid #444;border-radius:10px;cursor:pointer;font-size:14px;">Cancelar</button>
            </div>
        `;
        document.body.appendChild(modal);
        
        document.getElementById('btn-hue-close').onclick = function() { modal.remove(); };
        
        const setStatus = (msg, color) => {
            const el = document.getElementById('luxo-hue-status');
            if (el) { el.innerText = msg; el.style.color = color || '#FFD700'; }
        };
        
        if (!window.PublicKeyCredential) {
            setStatus('⚠️ Tu navegador o dispositivo no soporta lectura de huella.', '#FF8C00');
            return;
        }
        
        try {
            const resp = await fetch('/api/biometria/passkey_challenge_registro?colaborador_id=' + colabId + '&nombre=' + encodeURIComponent(colabName));
            const opts = await resp.json();
            if (!opts.publicKey) { setStatus('❌ Error al obtener configuración del servidor.', '#FF4500'); return; }
            
            const decode = s => Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')), c => c.charCodeAt(0));
            opts.publicKey.challenge = decode(opts.publicKey.challenge);
            opts.publicKey.user.id = decode(opts.publicKey.user.id);
            
            setStatus('👆 Toca el lector de huella o sensor biométrico del dispositivo...', '#D8B4FE');
            const credential = await navigator.credentials.create({ publicKey: opts.publicKey });
            
            setStatus('⏳ Guardando registro biométrico seguro...', '#FFD700');
            const payload = {
                colaborador_id: colabId,
                nombre: colabName,
                id: credential.id,
                rawId: btoa(String.fromCharCode(...new Uint8Array(credential.rawId))),
                type: credential.type,
                response: {
                    attestationObject: btoa(String.fromCharCode(...new Uint8Array(credential.response.attestationObject))),
                    clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(credential.response.clientDataJSON)))
                }
            };
            
            const vResp = await fetch('/api/biometria/registrar_huella_colaborador', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const vData = await vResp.json();
            if (vData.ok) {
                setStatus('✅ ¡Huella dactilar registrada exitosamente!', '#7CFC00');
                setTimeout(() => { modal.remove(); }, 1800);
            } else {
                setStatus('❌ Error: ' + (vData.error || 'No se pudo guardar la huella'), '#FF4500');
            }
        } catch(err) {
            if (err.name === 'NotAllowedError') {
                setStatus('⚠️ Lectura de huella cancelada por el usuario.', '#FF8C00');
            } else {
                setStatus('⚠️ Nota de lectura: ' + err.message, '#FF8C00');
            }
        }
    };

    // Reconciliación periódica ligera (cada 2s) sin provocar reflow de layout
    setInterval(evaluarVisibilidadSimulador, 2000);
    window.addEventListener('hashchange', evaluarVisibilidadSimulador);
    window.addEventListener('popstate', evaluarVisibilidadSimulador);
})();


