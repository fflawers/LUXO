/* ═══════════════════════════════════════════════════════════════════
   SmartScouting · Capa de acceso a datos

   Funciona de dos maneras y decide sola cuál usar:

   · MODO LOCAL   — mientras config.js siga con los valores de ejemplo.
                    Todo se guarda en el navegador. Sirve para trabajar
                    de inmediato, sin instalar nada.
   · MODO NUBE    — en cuanto pongas tu URL y tu clave de Supabase.
                    Los datos viven en la base de datos compartida.

   Las dos ofrecen exactamente las mismas funciones, así que las
   pantallas no cambian ni se enteran de cuál está activa.
   ═══════════════════════════════════════════════════════════════════ */

const MODO_LOCAL =
  typeof SHEETS_URL !== 'string' || !SHEETS_URL ||
  SHEETS_URL.includes('TU-URL') ||
  typeof SHEETS_TOKEN !== 'string' || !SHEETS_TOKEN ||
  SHEETS_TOKEN.includes('CAMBIA-ESTO');

/* ─── Utilidades comunes ─────────────────────────────────────────── */

async function sha256(txt) {
  try {
    const c = (typeof window !== 'undefined' && window.crypto) ? window.crypto : null;
    if (c && c.subtle && typeof c.subtle.digest === 'function') {
      const buf = await c.subtle.digest('SHA-256', new TextEncoder().encode(txt));
      return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch (e) {}
  return txt;
}

function traducirError(m) {
  const t = (m || '').toLowerCase();
  if (t.includes('invalid login')) return 'Correo o contraseña incorrectos. Verifica e intenta de nuevo.';
  if (t.includes('email not confirmed')) return 'La cuenta todavía no está confirmada. Pide al administrador que la active.';
  if (t.includes('too many')) return 'Demasiados intentos seguidos. Espera un momento antes de reintentar.';
  if (t.includes('failed to fetch')) return 'No hay conexión con el servidor. Revisa tu internet.';
  return 'No fue posible entrar: ' + m;
}

/* ═══════════════════════════════════════════════════════════════════
   MODO LOCAL
   ═══════════════════════════════════════════════════════════════════ */

function crearLocal() {
  const K_USUARIOS = 'ss_usuarios';
  const K_SESION   = 'ss_sesion';
  const K_CONFIG   = 'ss_config';
  const K_COTIZ    = 'ss_cotizaciones';

  const leer  = (k, x) => { try { return JSON.parse(localStorage.getItem(k)) ?? x; } catch (e) { return x; } };
  const poner = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  const idNuevo = () => 'u' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

  /* La primera vez deja creada la cuenta del administrador */
  async function sembrar() {
    const us = leer(K_USUARIOS, null);
    if (us && us.length) return us;
    const inicial = [{
      id: 'u-admin',
      nombre: 'Juan Manuel',
      apellidos: 'Almazán Arteaga',
      edad: 25,
      correo: 'juan.manuel@gmail.com',
      clave: await sha256('shopx2026'),
      rol: 'admin',
      activo: true,
      creado_en: new Date().toISOString()
    }];
    poner(K_USUARIOS, inicial);
    return inicial;
  }

  const sinClave = u => { const { clave, ...r } = u; return r; };

  async function sesion() {
    try { return JSON.parse(sessionStorage.getItem(K_SESION)); } catch (e) { return null; }
  }

  async function perfil() {
    const s = await sesion();
    if (!s) return null;
    const us = await sembrar();
    const u = us.find(x => x.id === s.id);
    if (!u || !u.activo) { await salir(); return null; }
    return sinClave(u);
  }

  async function entrar(correo, contrasena) {
    const us = await sembrar();
    const u = us.find(x => x.correo.toLowerCase() === correo.trim().toLowerCase());
    const clave = await sha256(contrasena);
    if (!u || u.clave !== clave) return { ok: false, mensaje: traducirError('invalid login') };
    if (!u.activo) return { ok: false, mensaje: 'Tu cuenta está desactivada. Contacta al administrador.' };
    sessionStorage.setItem(K_SESION, JSON.stringify({ id: u.id }));
    return { ok: true, rol: u.rol, nombre: u.nombre };
  }

  async function salir() { sessionStorage.removeItem(K_SESION); }

  async function proteger(rolRequerido) {
    const p = await perfil();
    if (!p) { location.replace('index.html'); return null; }
    if (rolRequerido === 'admin' && p.rol !== 'admin') { location.replace('app.html'); return null; }
    return p;
  }

  async function leerConfig() { return leer(K_CONFIG, null); }

  async function guardarConfig(datos) {
    poner(K_CONFIG, datos);
    localStorage.setItem('ss_config_fecha', new Date().toISOString());
    return { ok: true, mensaje: '' };
  }

  async function listarCotizaciones() {
    const p = await perfil();
    if (!p) return { ok: true, filas: [] };
    const todas = leer(K_COTIZ, []);
    const vis = p.rol === 'admin' ? todas : todas.filter(c => c.autorId === p.id);
    return { ok: true, filas: vis };
  }

  async function guardarCotizacion(q, p) {
    const fila = {
      ...q,
      id: 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      fecha: new Date().toISOString(),
      autor: (p.nombre + ' ' + p.apellidos).trim(),
      autorId: p.id
    };
    poner(K_COTIZ, [fila, ...leer(K_COTIZ, [])]);
    return { ok: true, fila };
  }

  async function borrarCotizaciones(ids) {
    const set = new Set(ids.map(String));
    poner(K_COTIZ, leer(K_COTIZ, []).filter(c => !set.has(String(c.id))));
    return { ok: true, mensaje: '' };
  }

  async function listarUsuarios() {
    const us = await sembrar();
    return { ok: true, filas: us.map(sinClave) };
  }

  async function crearUsuario({ nombre, apellidos, edad, correo, contrasena, rol }) {
    const us = await sembrar();
    if (us.some(u => u.correo.toLowerCase() === correo.trim().toLowerCase()))
      return { ok: false, mensaje: 'Ese correo ya tiene una cuenta.' };
    if (contrasena.length < 6)
      return { ok: false, mensaje: 'La contraseña debe tener al menos 6 caracteres.' };
    us.push({
      id: idNuevo(),
      nombre: nombre.trim(),
      apellidos: apellidos.trim(),
      edad: Number(edad),
      correo: correo.trim().toLowerCase(),
      clave: await sha256(contrasena),
      rol: rol || 'scouting',
      activo: true,
      creado_en: new Date().toISOString()
    });
    poner(K_USUARIOS, us);
    return { ok: true };
  }

  async function cambiarEstado(id, activo) {
    const us = await sembrar();
    const u = us.find(x => x.id === id);
    if (!u) return { ok: false, mensaje: 'No se encontró la cuenta.' };
    u.activo = activo; poner(K_USUARIOS, us);
    return { ok: true, mensaje: '' };
  }

  async function cambiarRol(id, rol) {
    const us = await sembrar();
    const u = us.find(x => x.id === id);
    if (!u) return { ok: false, mensaje: 'No se encontró la cuenta.' };
    u.rol = rol; poner(K_USUARIOS, us);
    return { ok: true, mensaje: '' };
  }

  /* En modo local se puede corregir todo, incluidos correo y contraseña */
  async function actualizarUsuario(id, d) {
    const us = await sembrar();
    const u = us.find(x => x.id === id);
    if (!u) return { ok: false, mensaje: 'No se encontró la cuenta.' };
    if (d.correo && us.some(x => x.id !== id && x.correo.toLowerCase() === d.correo.trim().toLowerCase()))
      return { ok: false, mensaje: 'Ese correo ya lo usa otra cuenta.' };
    if (d.contrasena) {
      if (d.contrasena.length < 6) return { ok: false, mensaje: 'La contraseña necesita al menos 6 caracteres.' };
      u.clave = await sha256(d.contrasena);
    }
    if (d.nombre != null)    u.nombre = d.nombre.trim();
    if (d.apellidos != null) u.apellidos = d.apellidos.trim();
    if (d.edad != null)      u.edad = Number(d.edad);
    if (d.correo != null)    u.correo = d.correo.trim().toLowerCase();
    if (d.rol != null)       u.rol = d.rol;
    if (d.activo != null)    u.activo = !!d.activo;
    poner(K_USUARIOS, us);
    return { ok: true, mensaje: '' };
  }

  const PUEDE_EDITAR_ACCESO = true;

  /* Reemplaza la consulta de conteo que usa el panel en modo nube */
  const cliente = {
    from: () => ({
      select: () => ({
        eq: () => ({ maybeSingle: async () => ({ data: { actualizado_en: localStorage.getItem('ss_config_fecha') } }) }),
        then: undefined
      })
    })
  };

  async function contarCotizaciones() {
    const r = await listarCotizaciones();
    return r.filas.length;
  }

  async function fechaConfig() { return localStorage.getItem('ss_config_fecha'); }

  /* Copia de seguridad, útil para pasar los datos a Supabase después */
  async function exportarTodo() {
    return {
      generado: new Date().toISOString(),
      usuarios: leer(K_USUARIOS, []).map(sinClave),
      configuracion: leer(K_CONFIG, null),
      cotizaciones: leer(K_COTIZ, [])
    };
  }

  return {
    MODO_LOCAL: true, cliente,
    sesion, perfil, entrar, salir, proteger,
    leerConfig, guardarConfig,
    listarCotizaciones, guardarCotizacion, borrarCotizaciones,
    listarUsuarios, crearUsuario, cambiarEstado, cambiarRol, actualizarUsuario,
    PUEDE_EDITAR_ACCESO,
    contarCotizaciones, fechaConfig, exportarTodo
  };
}

/* ═══════════════════════════════════════════════════════════════════
   MODO NUBE (Google Sheets vía Apps Script)

   La app nunca habla directo con la hoja: manda peticiones firmadas con
   el token a la URL de Apps Script, que es quien lee y escribe. Las
   contraseñas viajan como huella SHA-256 y en la hoja se guardan igual,
   nunca en texto legible. La sesión se guarda en este navegador.
   ═══════════════════════════════════════════════════════════════════ */

function crearRemoto() {
  const K_SESION = 'ss_sesion';

  /* Petición al backend. Se usa text/plain a propósito: evita que el
     navegador dispare la verificación CORS previa, que Apps Script no
     responde bien. El cuerpo sigue siendo JSON. */
  async function llamar(accion, datos) {
    try {
      const resp = await fetch(SHEETS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({ token: SHEETS_TOKEN, accion, datos: datos || {} })
      });
      return await resp.json();
    } catch (e) {
      return { ok: false, mensaje: 'No hay conexión con el servidor. Revisa tu internet.' };
    }
  }

  const guardarSesion = p => sessionStorage.setItem(K_SESION, JSON.stringify(p));
  const sesionGuardada = () => { try { return JSON.parse(sessionStorage.getItem(K_SESION)); } catch (e) { return null; } };

  async function sesion() { return sesionGuardada(); }

  async function perfil() {
    const s = sesionGuardada();
    if (!s) return null;
    const r = await llamar('perfil', { id: s.id });
    if (!r.ok) { await salir(); return null; }
    return r.perfil;
  }

  async function entrar(correo, contrasena) {
    const clave = await sha256(contrasena);
    const r = await llamar('entrar', { correo, contrasena: clave });
    if (!r.ok) {
      if (r.mensaje === 'inactivo') return { ok: false, mensaje: 'Tu cuenta está desactivada. Contacta al administrador.' };
      return { ok: false, mensaje: traducirError(r.mensaje) };
    }
    guardarSesion(r.perfil);
    return { ok: true, rol: r.rol, nombre: r.nombre };
  }

  async function salir() { sessionStorage.removeItem(K_SESION); }

  async function proteger(rolRequerido) {
    const p = await perfil();
    if (!p) { location.replace('index.html'); return null; }
    if (rolRequerido === 'admin' && p.rol !== 'admin') { location.replace('app.html'); return null; }
    return p;
  }

  async function leerConfig() {
    const r = await llamar('leerConfig', {});
    return r.ok ? r.datos : null;
  }

  async function guardarConfig(datos, usuarioId) {
    const r = await llamar('guardarConfig', { datos, usuarioId });
    return { ok: r.ok, mensaje: r.mensaje || '' };
  }

  async function listarCotizaciones() {
    const p = sesionGuardada();
    if (!p) return { ok: true, filas: [] };
    const r = await llamar('listarCotizaciones', { usuarioId: p.id, rol: p.rol });
    if (!r.ok) return { ok: false, mensaje: r.mensaje, filas: [] };
    return { ok: true, filas: r.filas };
  }

  async function guardarCotizacion(q, p) {
    const r = await llamar('guardarCotizacion', {
      cotizacion: q, usuarioId: p.id, usuarioNombre: (p.nombre + ' ' + p.apellidos).trim()
    });
    if (!r.ok) return { ok: false, mensaje: r.mensaje };
    return { ok: true, fila: r.fila };
  }

  async function borrarCotizaciones(ids) {
    const p = sesionGuardada();
    const r = await llamar('borrarCotizaciones', { ids, usuarioId: p ? p.id : null, rol: p ? p.rol : null });
    return { ok: r.ok, mensaje: r.mensaje || '' };
  }

  async function listarUsuarios() {
    const r = await llamar('listarUsuarios', {});
    if (!r.ok) return { ok: false, mensaje: r.mensaje, filas: [] };
    return { ok: true, filas: r.filas };
  }

  async function crearUsuario(d) {
    if (!d.contrasena || d.contrasena.length < 6)
      return { ok: false, mensaje: 'La contraseña debe tener al menos 6 caracteres.' };
    const env = Object.assign({}, d, { contrasena: await sha256(d.contrasena) });
    const r = await llamar('crearUsuario', env);
    return { ok: r.ok, mensaje: r.mensaje || '' };
  }

  async function actualizarUsuario(id, d) {
    const env = Object.assign({ id }, d);
    if (d.contrasena) {
      if (d.contrasena.length < 6) return { ok: false, mensaje: 'La contraseña necesita al menos 6 caracteres.' };
      env.contrasena = await sha256(d.contrasena);
    }
    const r = await llamar('actualizarUsuario', env);
    return { ok: r.ok, mensaje: r.mensaje || '' };
  }

  async function cambiarEstado(id, activo) {
    const r = await llamar('cambiarEstado', { id, activo });
    return { ok: r.ok, mensaje: r.mensaje || '' };
  }

  async function cambiarRol(id, rol) {
    const r = await llamar('cambiarRol', { id, rol });
    return { ok: r.ok, mensaje: r.mensaje || '' };
  }

  /* En Sheets sí se puede corregir correo y contraseña desde el módulo */
  const PUEDE_EDITAR_ACCESO = true;

  async function contarCotizaciones() {
    const p = sesionGuardada();
    const r = await llamar('listarCotizaciones', { usuarioId: p ? p.id : null, rol: p ? p.rol : null });
    return r.ok ? r.filas.length : null;
  }

  async function fechaConfig() {
    const r = await llamar('leerConfig', {});
    return r.ok ? r.fecha : null;
  }

  async function exportarTodo() {
    const [u, c, cot] = await Promise.all([listarUsuarios(), leerConfig(), listarCotizaciones()]);
    return { generado: new Date().toISOString(), usuarios: u.filas, configuracion: c, cotizaciones: cot.filas };
  }

  return {
    MODO_LOCAL: false, cliente: null,
    sesion, perfil, entrar, salir, proteger,
    leerConfig, guardarConfig,
    listarCotizaciones, guardarCotizacion, borrarCotizaciones,
    listarUsuarios, crearUsuario, cambiarEstado, cambiarRol, actualizarUsuario,
    PUEDE_EDITAR_ACCESO,
    contarCotizaciones, fechaConfig, exportarTodo
  };
}

const db = MODO_LOCAL ? crearLocal() : crearRemoto();

/* Distintivo visible para no confundir un modo con el otro */
if (db.MODO_LOCAL) {
  window.addEventListener('DOMContentLoaded', () => {
    const d = document.createElement('div');
    d.id = 'modo-local';
    d.title = 'Los datos se guardan en este navegador. Al llenar config.js con tus claves de Supabase, la aplicación cambia sola al modo compartido.';
    d.innerHTML = '<span></span>Modo local';
    document.body.appendChild(d);
  });
}
