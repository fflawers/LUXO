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

    window.luxoPlayLoginAvatarAudio = function(force) {
        if (force === true) {
            window.luxoUserIsLoggedIn = false;
            window._luxoAvatarAudioMuted = false;
        }
        if (window.luxoUserIsLoggedIn === true) {
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
                snd.loop = false; // Una sola reproducción controlada (sin bucle infinito)
                snd.volume = 1.0;
                snd.muted = false;
            } else {
                snd = document.createElement('audio');
                snd.id = 'luxo_avatar_audio_el';
                snd.preload = 'auto';
                snd.src = '/custom_assets/saludo_login.mp3';
                snd.loop = false; // Una sola reproducción controlada (sin bucle infinito)
                snd.volume = 1.0;
                snd.muted = false;
                (document.body || document.documentElement).appendChild(snd);
            }
            snd.onended = function() {
                window._luxoAvatarAudioActive = false;
            };
            let p = snd.play();
            if (p !== undefined) {
                p.then(function() {
                    console.log('[LUXO AVATAR] Audio reproduciéndose exitosamente en inicio de sesión.');
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
        if (!window.luxoUserIsLoggedIn) {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    if (!window.luxoUserIsLoggedIn) {
                        window.luxoPlayLoginAvatarAudio();
                    }
                });
            } else {
                window.luxoPlayLoginAvatarAudio();
            }
            setTimeout(function() { if (!window.luxoUserIsLoggedIn) window.luxoPlayLoginAvatarAudio(); }, 500);
            setTimeout(function() { if (!window.luxoUserIsLoggedIn) window.luxoPlayLoginAvatarAudio(); }, 1200);
        }
    } catch(e){}

    window.luxoStopLoginAvatarAudio = function() {
        window._luxoAvatarAudioActive = false;
        try {
            let audios = document.querySelectorAll('audio');
            audios.forEach(function(snd) {
                if (snd.id === 'luxo_avatar_audio_el' || (snd.src && snd.src.includes('saludo_login.mp3'))) {
                    try {
                        snd.pause();
                        snd.currentTime = 0;
                        snd.loop = false;
                        snd.muted = true;
                        snd.removeAttribute('src');
                        snd.src = '';
                        snd.load();
                    } catch(e){}
                    try {
                        if (snd.parentNode) snd.parentNode.removeChild(snd);
                    } catch(e){}
                }
            });
            let directEl = document.getElementById('luxo_avatar_audio_el');
            if (directEl) {
                try {
                    directEl.pause();
                    directEl.currentTime = 0;
                    directEl.loop = false;
                    directEl.muted = true;
                    directEl.src = '';
                    if (directEl.parentNode) directEl.parentNode.removeChild(directEl);
                } catch(e){}
            }
        } catch(e){}
    };

    // Interceptor INMEDIATO al hacer clic en ACCEDER, Huella o Face ID (0ms de latencia)
    try {
        function _obtenerTextoElementoYPadres(el, maxDepth = 4) {
            let combined = '';
            let curr = el;
            let depth = 0;
            while (curr && depth < maxDepth) {
                let txt = (curr.innerText || curr.textContent || '').trim();
                let tt = (curr.getAttribute && curr.getAttribute('tooltip')) || '';
                let al = (curr.getAttribute && curr.getAttribute('aria-label')) || '';
                let ti = (curr.getAttribute && curr.getAttribute('title')) || '';
                combined += ` ${txt} ${tt} ${al} ${ti}`;
                curr = curr.parentElement;
                depth++;
            }
            return combined.toLowerCase();
        }

        document.addEventListener('click', function(e) {
            let t = e.target;
            if (!t) return;
            let combined = _obtenerTextoElementoYPadres(t);

            // 1. Acceder (corta el audio del avatar inmediatamente y pre-desbloquea reproductor)
            if (combined.includes('acceder')) {
                window.luxoUserIsLoggedIn = true;
                window.luxoStopLoginAvatarAudio();
                try {
                    let a = document.getElementById("luxo_global_tts_player");
                    if (!a) {
                        a = document.createElement("audio");
                        a.id = "luxo_global_tts_player";
                        (document.body || document.documentElement).appendChild(a);
                    }
                    a.muted = false;
                    let p = a.play();
                    if (p !== undefined) p.catch(function(){});
                } catch(e){}
            }

            // 2. Huella / Passkey instantáneo (0ms sin esperar WebSocket/polling)
            if (!window.luxoUserIsLoggedIn && (combined.includes('huella') || combined.includes('passkey'))) {
                console.log("[LUXO BIOMETRIA] Clic directo detectado: Abriendo Huella / Passkey instantáneamente (0ms)");
                if (window.luxoActivarPasskeyLogin) {
                    window.luxoActivarPasskeyLogin();
                }
            }

            // 3. Face ID instantáneo (0ms sin esperar WebSocket/polling)
            if (!window.luxoUserIsLoggedIn && (combined.includes('face id') || combined.includes('reconocimiento facial') || combined.includes('facial'))) {
                console.log("[LUXO BIOMETRIA] Clic directo detectado: Abriendo Face ID instantáneamente (0ms)");
                if (window.luxoAbrirCamaraFacialLogin) {
                    window.luxoAbrirCamaraFacialLogin();
                }
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
            window.luxoPlayLoginAvatarAudio(true);
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
            // Si el usuario YA tiene sesión activa confirmada, detener el audio del avatar
            if (window.luxoUserIsLoggedIn === true) {
                window.luxoStopLoginAvatarAudio();
                return;
            }
            // Si estamos en la pantalla de login y el avatar no está silenciado, iniciar o reanudar
            if (!window.luxoUserIsLoggedIn && !window._luxoAvatarAudioMuted) {
                let snd = document.getElementById('luxo_avatar_audio_el');
                if (snd) {
                    if (snd.paused && !snd.ended) {
                        snd.muted = false;
                        snd.volume = 1.0;
                        let p = snd.play();
                        if (p !== undefined) {
                            p.catch(function(){});
                        }
                    }
                } else {
                    window.luxoPlayLoginAvatarAudio(false);
                }
            }
        } catch(e){}
    };
    try {
        ['pointerdown', 'keydown', 'click', 'touchstart'].forEach(function(evName) {
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
            if (voiceId === 'luxo_avatar' || failedAudioUrl) {
                console.log('[LUXO TTS] Omitiendo WebSpeech para audio neural generado.');
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
                    u.pitch = 1.0;
                    u.rate = 1.0;
                    const vId = (voiceId || '').toLowerCase();
                    const voices = window.speechSynthesis.getVoices() || [];
                    const esVoices = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith('es'));
                    const maleVoices = esVoices.filter(v => (v.name.toLowerCase().includes('male') || v.name.toLowerCase().includes('raul') || v.name.toLowerCase().includes('pablo') || v.name.toLowerCase().includes('jorge') || v.name.toLowerCase().includes('david') || v.name.toLowerCase().includes('alvaro') || v.name.toLowerCase().includes('alonso') || v.name.toLowerCase().includes('enrique')));
                    const femaleVoices = esVoices.filter(v => (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('sabina') || v.name.toLowerCase().includes('helena') || v.name.toLowerCase().includes('monica') || v.name.toLowerCase().includes('lucia') || v.name.toLowerCase().includes('dalia') || v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('laura')));

                    if (vId === 'jarvis' || vId === 'yarvis') {
                        u.lang = "es-ES";
                        if (maleVoices.length > 0) u.voice = maleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else if (vId === 'jorge' || vId === 'alonso') {
                        u.lang = "es-MX";
                        if (maleVoices.length > 0) u.voice = maleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else if (vId === 'barbara') {
                        u.lang = "es-MX";
                        if (femaleVoices.length > 0) u.voice = femaleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else if (vId === 'helena' || vId === 'sabina') {
                        u.lang = "es-MX";
                        if (femaleVoices.length > 0) u.voice = femaleVoices[0];
                        else if (esVoices.length > 0) u.voice = esVoices[0];
                    } else {
                        u.lang = "es-MX";
                        if (voiceGender === 'female' && femaleVoices.length > 0) u.voice = femaleVoices[0];
                        else if (voiceGender === 'male' && maleVoices.length > 0) u.voice = maleVoices[0];
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
    let lastHandledTtsId = null;
    let playedAudioIds = new Set();
    let lastPlayedAudioUrl = '';
    let lastPlayedAudioTime = 0;

    window.luxoPlayDirect = function(audioUrl, text, voiceId, voiceGender, id) {
        let playId = id || ('direct_' + Date.now());
        lastHandledTtsId = playId;
        window.luxoPlayTts(text, audioUrl, playId, voiceId, voiceGender);
    };

    window.luxoPlayTts = function(text, audioUrl, id, voiceId, voiceGender) {
        if (id) {
            if (playedAudioIds.has(id)) {
                console.log("[LUXO TTS] Evento TTS ya reproducido (id=" + id + "), ignorando.");
                return;
            }
            playedAudioIds.add(id);
            if (playedAudioIds.size > 200) playedAudioIds.clear();
            lastHandledTtsId = id;
        }
        if (audioUrl) {
            let fullUrl = audioUrl;
            if (fullUrl.startsWith('/')) {
                fullUrl = window.location.origin + fullUrl;
            }
            let now = Date.now();
            let existingAudio = document.getElementById("luxo_global_tts_player");
            if (existingAudio && !existingAudio.paused && existingAudio.currentTime > 0 && !existingAudio.ended && (now - lastPlayedAudioTime < 5000)) {
                console.log("[LUXO TTS] Audio actualmente en reproducción activa, ignorando llamada duplicada.");
                return;
            }
            if (lastPlayedAudioUrl === fullUrl && (now - lastPlayedAudioTime < 6000)) {
                console.log("[LUXO TTS] Audio idéntico ya reproducido recientemente (<6s), ignorando repetición.");
                return;
            }
            lastPlayedAudioUrl = fullUrl;
            lastPlayedAudioTime = now;

            window.luxoStopTts();

            function tryPlayAudio(retriesLeft) {
                try {
                    let audioEl = getOrCreateAudioElement();
                    audioEl.muted = false;
                    audioEl.volume = 1.0;
                    
                    console.log("[LUXO TTS] DIAGNOSTICO DE REPRODUCCION:", {
                        audioUrl_recibido: audioUrl,
                        url_absoluta_final: fullUrl,
                        window_location_origin: window.location.origin,
                        voiceId: voiceId,
                        voiceGender: voiceGender,
                        texto_longitud: (text || '').length,
                        audio_muted: audioEl.muted,
                        audio_volume: audioEl.volume,
                        audio_src: audioEl.src,
                        audio_readyState: audioEl.readyState,
                        audio_networkState: audioEl.networkState,
                        audio_paused: audioEl.paused,
                        audio_currentTime: audioEl.currentTime,
                        audio_error: audioEl.error,
                        document_visibilityState: document.visibilityState,
                        retriesLeft: retriesLeft
                    });

                    audioEl.src = fullUrl;
                    let playPromise = audioEl.play();
                    if (playPromise !== undefined) {
                        playPromise.then(function() {
                            console.log("[LUXO TTS SUCCESS] audio.play() iniciado exitosamente:", fullUrl);
                        }).catch(function(err) {
                            console.error("[LUXO TTS ERROR] audio.play() fue rechazado/fallo:", {
                                err_name: err.name,
                                err_message: err.message,
                                es_bloqueo_autoplay: (err.name === 'NotAllowedError'),
                                audio_src: audioEl.src,
                                audio_muted: audioEl.muted,
                                audio_volume: audioEl.volume,
                                audio_readyState: audioEl.readyState,
                                audio_networkState: audioEl.networkState,
                                document_visibilityState: document.visibilityState,
                                retriesLeft: retriesLeft
                            });
                            // Si la reproducción fue abortada por una nueva solicitud de audio, no hacer nada
                            if (err.name === 'AbortError') {
                                console.log("[LUXO TTS] Play abortado de forma controlada por cambio de audio.");
                                return;
                            }
                            if (retriesLeft > 0) {
                                setTimeout(function() { tryPlayAudio(retriesLeft - 1); }, 350);
                            } else {
                                console.warn("[LUXO TTS] Autoplay bloqueado por política del navegador; esperando interacción de usuario.");
                            }
                        });
                    }
                } catch(err) {
                    console.error("[LUXO TTS EXCEPTION] Excepcion sincrona en tryPlayAudio:", err);
                    if (retriesLeft > 0) {
                        setTimeout(function() { tryPlayAudio(retriesLeft - 1); }, 350);
                    }
                }
            }
            tryPlayAudio(5);
        } else if (text) {
            window.luxoStopTts();
            console.log("[LUXO TTS] Sin audioUrl, ejecutando WebSpeech directamente");
            window.luxoSpeakWebSpeech(text, voiceId, voiceGender);
        }
    };

    // 8. Bucle de Polling HTTP Inteligente para entrega de eventos TTS (0% CPU impact)
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

                    const hasUserSess = (window.luxoUserIsLoggedIn === true);
                    if (hasUserSess) {
                        let oldAvatarSnd = document.getElementById('luxo_avatar_audio_el');
                        if (oldAvatarSnd) {
                            window.luxoStopLoginAvatarAudio();
                        }
                    }

                    const res = await fetch('/api/tts/poll?session_id=' + encodeURIComponent(sid) + '&user_id=' + encodeURIComponent(uid) + '&username=' + encodeURIComponent(uname) + '&last_id=' + encodeURIComponent(lastHandledTtsId || '') + '&_t=' + Date.now(), { cache: 'no-store' });
                    if (res && res.ok) {
                        const data = await res.json();
                        if (typeof data.sim_visible !== 'undefined') {
                            window._simPollVisible = (data.sim_visible === true);
                            if (data.sim_mode) window._simCurrentMode = data.sim_mode;
                            if (typeof window.showSimuladorMicBtn === 'function') {
                                window.showSimuladorMicBtn(data.sim_visible, data.sim_mode || 'chat');
                            }
                            if (typeof window.evaluarVisibilidadSimulador === 'function') {
                                window.evaluarVisibilidadSimulador();
                            }
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
            const nextDelay = document.hidden ? 3500 : 1400;
            setTimeout(smartTtsPollLoop, nextDelay);
        }
        
        setTimeout(smartTtsPollLoop, 1200);
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

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } } })
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
            const vW = video.videoWidth || 640;
            const vH = video.videoHeight || 480;
            const minDim = Math.min(vW, vH);
            const sx = (vW - minDim) / 2;
            const sy = (vH - minDim) / 2;
            ctx.drawImage(video, sx, sy, minDim, minDim, 0, 0, 220, 220);
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
                    window.luxoUserIsLoggedIn = true;
                    if (window.luxoStopLoginAvatarAudio) window.luxoStopLoginAvatarAudio();
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
        console.log("LUXO: [DIAGNÓSTICO INICIAL WEBAUTHN]");
        const exist = document.getElementById('luxo-passkey-login-banner');
        if (exist) {
            try { exist.remove(); } catch(e){}
        }

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
            setTxt('⚠️ WebAuthn requiere HTTPS o localhost en celulares.', '#FF8C00');
            setTimeout(() => { try { banner.remove(); } catch(e){} window._luxoPasskeyActivo = false; }, 4000);
            return;
        }

        if (!window.PublicKeyCredential || !navigator.credentials || !navigator.credentials.get) {
            console.error("LUXO: navigator.credentials o PublicKeyCredential no disponibles.");
            setTxt('⚠️ Tu navegador o dispositivo no tiene habilitado WebAuthn / Passkeys.', '#FF8C00');
            setTimeout(() => { try { banner.remove(); } catch(e){} window._luxoPasskeyActivo = false; }, 4000);
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
                window.luxoUserIsLoggedIn = true;
                if (window.luxoStopLoginAvatarAudio) window.luxoStopLoginAvatarAudio();
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
            const vW = video.videoWidth || 640;
            const vH = video.videoHeight || 480;
            const minDim = Math.min(vW, vH);
            const sx = (vW - minDim) / 2;
            const sy = (vH - minDim) / 2;
            ctx.drawImage(video, sx, sy, minDim, minDim, 0, 0, 220, 220);
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

        // --------------------------------------------------------------------------
    // MÓDULO INDEPENDIENTE TRADUCTOR DE MOSTRADOR LUXO (2 TOQUES / CONTINUO)
    // --------------------------------------------------------------------------
    window._luxoTradRecording = { 'vendedor': false, 'cliente': false };
    window._luxoTradMediaRecorder = { 'vendedor': null, 'cliente': null };
    window._luxoTradAudioStream = { 'vendedor': null, 'cliente': null };
    window._luxoTradChunks = { 'vendedor': [], 'cliente': [] };
    window._luxoTradSR = { 'vendedor': null, 'cliente': null };
    window._luxoTradText = { 'vendedor': '', 'cliente': '' };

    window.luxoStartTraductorMic = function(source, sessionId) {
        console.log('[TRADUCTOR JS] Iniciar grabacion continua para:', source, sessionId);
        window._luxoTradText[source] = '';
        window._luxoTradChunks[source] = [];

        // Detener la otra vía si estuviera activa
        ['vendedor', 'cliente'].forEach(function(s) {
            if (s !== source && window._luxoTradRecording[s]) {
                window.luxoStopTraductorMic(s, sessionId);
            }
        });

        window._luxoTradRecording[source] = true;
        fetch('/api/traductor/mic_state?source=' + encodeURIComponent(source) + '&session_id=' + encodeURIComponent(sessionId) + '&state=recording', { method: 'POST' }).catch(function(){});

        // 1. Iniciar MediaRecorder nativo (Audio directo a Whisper - 100% compatible)
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
                if (!window._luxoTradRecording[source]) {
                    stream.getTracks().forEach(function(t) { t.stop(); });
                    return;
                }
                window._luxoTradAudioStream[source] = stream;
                window._luxoTradChunks[source] = [];

                let mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported('audio/webm') && MediaRecorder.isTypeSupported('audio/mp4')) {
                    mimeType = 'audio/mp4';
                } else if (!MediaRecorder.isTypeSupported('audio/webm')) {
                    mimeType = '';
                }

                const options = mimeType ? { mimeType: mimeType } : {};
                const mr = new MediaRecorder(stream, options);
                window._luxoTradMediaRecorder[source] = mr;

                mr.ondataavailable = function(e) {
                    if (e.data && e.data.size > 0) {
                        window._luxoTradChunks[source].push(e.data);
                    }
                };

                mr.onstart = function() {
                    console.log('[TRADUCTOR MR] Grabacion de audio iniciada para:', source);
                };

                mr.start(250); // recolectar fragmentos cada 250ms
            }).catch(function(err) {
                console.log('[TRADUCTOR MR ERROR]', err);
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    alert('⚠️ Permiso de micrófono denegado. Permite el acceso al micrófono en la barra de tu navegador.');
                    window._luxoTradRecording[source] = false;
                    fetch('/api/traductor/mic_state?source=' + encodeURIComponent(source) + '&session_id=' + encodeURIComponent(sessionId) + '&state=idle', { method: 'POST' }).catch(function(){});
                }
            });
        }

        // 2. Reconocimiento WebSpeech opcional en paralelo para texto rápido
        try {
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition || (window.top && (window.top.SpeechRecognition || window.top.webkitSpeechRecognition));
            if (SR) {
                const rec = new SR();
                rec.continuous = true;
                rec.interimResults = false;
                rec.maxAlternatives = 1;
                rec.lang = (source === 'vendedor') ? 'es-MX' : 'en-US';

                rec.onresult = function(ev) {
                    let txt = '';
                    for (let i = ev.resultIndex; i < ev.results.length; ++i) {
                        if (ev.results[i].isFinal) {
                            txt += ev.results[i][0].transcript + ' ';
                        }
                    }
                    if (txt.trim()) {
                        window._luxoTradText[source] = (window._luxoTradText[source] + ' ' + txt).trim();
                        console.log('[TRADUCTOR SPEECH NATIVO]', source, ':', window._luxoTradText[source]);
                    }
                };

                rec.onerror = function(err) {
                    console.log('[TRADUCTOR SR ERROR]', err);
                };

                window._luxoTradSR[source] = rec;
                try { rec.start(); } catch(eStart){}
            }
        } catch(eSR) {
            console.log('[TRADUCTOR SR INIT]', eSR);
        }
    };

    window.luxoStopTraductorMic = function(source, sessionId) {
        console.log('[TRADUCTOR JS] Detener grabacion para:', source, sessionId);
        window._luxoTradRecording[source] = false;

        // Detener WebSpeech si estaba activo
        if (window._luxoTradSR && window._luxoTradSR[source]) {
            try { window._luxoTradSR[source].stop(); } catch(e){}
            window._luxoTradSR[source] = null;
        }

        fetch('/api/traductor/mic_state?source=' + encodeURIComponent(source) + '&session_id=' + encodeURIComponent(sessionId) + '&state=processing', { method: 'POST' }).catch(function(){});

        // Detener MediaRecorder y despachar audio
        const mr = window._luxoTradMediaRecorder[source];
        const stream = window._luxoTradAudioStream[source];

        if (mr && mr.state === 'recording') {
            mr.onstop = function() {
                if (stream) {
                    stream.getTracks().forEach(function(t) { t.stop(); });
                    window._luxoTradAudioStream[source] = null;
                }
                window._luxoTradMediaRecorder[source] = null;

                const chunks = window._luxoTradChunks[source] || [];
                const recognizedText = (window._luxoTradText[source] || '').trim();

                if (chunks.length > 0) {
                    const audioBlob = new Blob(chunks, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'traductor_' + source + '.webm');
                    formData.append('session_id', sessionId);
                    formData.append('source', source);

                    fetch('/api/traductor/audio_upload', {
                        method: 'POST',
                        body: formData
                    }).then(function(res) {
                        return res.json();
                    }).then(function(data) {
                        console.log('[TRADUCTOR AUDIO UPLOAD RESULT]:', data);
                    }).catch(function(err) {
                        console.log('[TRADUCTOR UPLOAD ERROR]:', err);
                        // Fallback a texto si WebSpeech tenia algo
                        if (recognizedText.length > 0) {
                            fetch('/api/traductor/speech_input', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ session_id: sessionId, source: source, text: recognizedText })
                            }).catch(function(){});
                        } else {
                            fetch('/api/traductor/mic_state?source=' + encodeURIComponent(source) + '&session_id=' + encodeURIComponent(sessionId) + '&state=idle', { method: 'POST' }).catch(function(){});
                        }
                    });
                } else if (recognizedText.length > 0) {
                    fetch('/api/traductor/speech_input', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_id: sessionId, source: source, text: recognizedText })
                    }).catch(function(){});
                } else {
                    fetch('/api/traductor/mic_state?source=' + encodeURIComponent(source) + '&session_id=' + encodeURIComponent(sessionId) + '&state=idle', { method: 'POST' }).catch(function(){});
                }
            };
            try { mr.stop(); } catch(eStop){
                if (stream) stream.getTracks().forEach(function(t) { t.stop(); });
            }
        } else {
            if (stream) {
                stream.getTracks().forEach(function(t) { t.stop(); });
                window._luxoTradAudioStream[source] = null;
            }
            const recognizedText = (window._luxoTradText[source] || '').trim();
            if (recognizedText.length > 0) {
                fetch('/api/traductor/speech_input', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId, source: source, text: recognizedText })
                }).catch(function(){});
            } else {
                fetch('/api/traductor/mic_state?source=' + encodeURIComponent(source) + '&session_id=' + encodeURIComponent(sessionId) + '&state=idle', { method: 'POST' }).catch(function(){});
            }
        }
    };

    window.luxoPlayTraductorAudio = function(audioUrl) {
        if (!audioUrl) return;
        try {
            let a = new Audio(audioUrl);
            a.play().catch(function(e) { console.log('[TRADUCTOR AUDIO AUTOPLAY]', e); });
        } catch(e) {}
    };

    // =========================================================================
    // GESTIÓN DE SUSPENSIÓN Y RECONEXIÓN ROBUSTA EN IPAD / TABLETS / MÓVILES
    // =========================================================================
    (function() {
        let _bgSuspendedTimestamp = 0;

        window.addEventListener('pageshow', function(event) {
            if (event && event.persisted) {
                console.log('[LUXO MOBILE] Restaurado de BFCache suspendido. Reconectando...');
                window.location.reload();
            }
        });

        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                _bgSuspendedTimestamp = Date.now();
            } else {
                if (_bgSuspendedTimestamp > 0) {
                    const diffMs = Date.now() - _bgSuspendedTimestamp;
                    _bgSuspendedTimestamp = 0;
                    if (diffMs > 15000) {
                        console.log('[LUXO MOBILE] Retorno tras suspension prolongada (' + Math.round(diffMs/1000) + 's). Reconectando limpiamente...');
                        window.location.reload();
                    }
                }
            }
        });

        let _lastInteractionPing = 0;
        function renovarActividadUsuario() {
            const now = Date.now();
            if (now - _lastInteractionPing > 120000) {
                _lastInteractionPing = now;
                try {
                    const uid = window.getLuxoUserId ? window.getLuxoUserId() : '';
                    const sid = window.getLuxoSessionId ? window.getLuxoSessionId() : '';
                    if (uid && uid !== 'unknown') {
                        fetch('/api/user_activity', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: uid, session_id: sid }),
                            keepalive: true
                        }).catch(function(){});
                    }
                } catch(e){}
            }
        }

        ['pointerdown', 'keydown', 'click', 'touchstart'].forEach(function(ev) {
            window.addEventListener(ev, renovarActividadUsuario, { passive: true, capture: true });
        });
    })();
})();


