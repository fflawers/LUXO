// ==============================================================================
// LUXO WEB CLIENT AUDIO & TTS ENGINE (Standalone Script)
// ==============================================================================

(function() {
    if (window._luxoAudioEngineLoaded) return;
    window._luxoAudioEngineLoaded = true;
    console.log("[LUXO TTS] Motor de audio web inicializado con éxito.");

    // 1. Obtener User ID
    window.getLuxoUserId = function() {
        if (window.luxoUserId) return window.luxoUserId;
        try {
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                if (key && key.includes('logged_user_id')) {
                    let val = localStorage.getItem(key);
                    if (val) {
                        try { return JSON.parse(val); } catch(e) { return val.replace(/["']/g, ''); }
                    }
                }
            }
        } catch(e) {}
        return '1';
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

    // 8. Bucle de Polling HTTP para entrega de eventos TTS
    let lastHandledTtsId = null;
    if (!window._luxoTtsIntervalStarted) {
        window._luxoTtsIntervalStarted = true;
        setInterval(function() {
            try {
                const uid = window.getLuxoUserId ? window.getLuxoUserId() : '1';
                const sid = window.getLuxoSessionId ? window.getLuxoSessionId() : '';
                fetch('/api/tts/poll?session_id=' + encodeURIComponent(sid) + '&user_id=' + encodeURIComponent(uid) + '&last_id=' + encodeURIComponent(lastHandledTtsId || '') + '&_t=' + Date.now(), { cache: 'no-store' })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (!data || !data.action || data.action === 'none') return;
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
                    }
                })
                .catch(function(){});
            } catch(e) {}
        }, 400);
    }
})();
