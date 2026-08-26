/**
 * ═══════════════════════════════════════════════════════════════════════
 *  SmartScouting · Backend en Google Apps Script
 *  Convierte una hoja de cálculo de Google en la base de datos de la app.
 *
 *  CÓMO INSTALARLO (los pasos completos están en LEEME.md):
 *   1. Crea una hoja nueva en Google Sheets.
 *   2. Extensiones → Apps Script. Borra lo que haya y pega TODO este archivo.
 *   3. Cambia el valor de TOKEN por una frase larga tuya (abajo).
 *   4. Ejecuta una vez la función  instalar  (menú Ejecutar).
 *   5. Implementar → Nueva implementación → Aplicación web:
 *        Ejecutar como: Yo
 *        Con acceso:    Cualquier persona
 *      Copia la URL que termina en /exec.
 *   6. Pega esa URL y el mismo TOKEN en config.js.
 * ═══════════════════════════════════════════════════════════════════════
 */

/** Debe ser IDÉNTICO al de config.js. Cámbialo por una frase larga y única. */
const TOKEN = 'CAMBIA-ESTO-POR-UNA-FRASE-LARGA-Y-SECRETA';

const HOJAS = {
  usuarios:      ['id', 'nombre', 'apellidos', 'edad', 'correo', 'clave', 'rol', 'activo', 'creado_en'],
  configuracion: ['id', 'datos', 'actualizado_en', 'actualizado_por'],
  cotizaciones:  ['id', 'usuario_id', 'usuario_nombre', 'producto', 'proveedor', 'categoria',
                  'costo_mxn', 'costo_original', 'moneda_original', 'tipo_ml', 'mejor_plataforma',
                  'precios', 'resultados', 'creado_en']
};

/* ─── Instalación: crea las hojas y el primer administrador ───────────── */
function instalar() {
  const libro = SpreadsheetApp.getActiveSpreadsheet();
  Object.keys(HOJAS).forEach(nombre => {
    let h = libro.getSheetByName(nombre);
    if (!h) h = libro.insertSheet(nombre);
    if (h.getLastRow() === 0) h.appendRow(HOJAS[nombre]);
  });

  const u = libro.getSheetByName('usuarios');
  if (u.getLastRow() === 1) {
    u.appendRow([
      'u-admin', 'Juan Manuel', 'Almazán Arteaga', 25,
      'juan.manuel@gmail.com', sha256('shopx2026'), 'admin', true, new Date().toISOString()
    ]);
  }
  const c = libro.getSheetByName('configuracion');
  if (c.getLastRow() === 1) c.appendRow([1, '{}', new Date().toISOString(), '']);

  const hoja1 = libro.getSheetByName('Hoja 1') || libro.getSheetByName('Sheet1');
  if (hoja1 && libro.getSheets().length > 1) libro.deleteSheet(hoja1);
}

/* ─── Punto de entrada ───────────────────────────────────────────────── */
function doPost(e) {
  try {
    const p = JSON.parse(e.postData.contents || '{}');
    if (p.token !== TOKEN) return responder({ ok: false, mensaje: 'Token inválido.' });

    const bloqueo = LockService.getScriptLock();
    bloqueo.waitLock(20000);
    try {
      const r = manejar(p.accion, p.datos || {});
      return responder(r);
    } finally {
      bloqueo.releaseLock();
    }
  } catch (err) {
    return responder({ ok: false, mensaje: String(err) });
  }
}

function doGet() {
  return responder({ ok: true, mensaje: 'SmartScouting API activa.' });
}

function responder(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ─── Enrutador de acciones ──────────────────────────────────────────── */
function manejar(accion, d) {
  switch (accion) {
    case 'entrar':              return accEntrar(d);
    case 'perfil':              return accPerfil(d);
    case 'listarUsuarios':      return { ok: true, filas: leerTabla('usuarios').map(sinClave) };
    case 'crearUsuario':        return accCrearUsuario(d);
    case 'actualizarUsuario':   return accActualizarUsuario(d);
    case 'cambiarEstado':       return accCampo('usuarios', d.id, 'activo', d.activo);
    case 'cambiarRol':          return accCampo('usuarios', d.id, 'rol', d.rol);
    case 'leerConfig':          return accLeerConfig();
    case 'guardarConfig':       return accGuardarConfig(d);
    case 'listarCotizaciones':  return accListarCotiz(d);
    case 'guardarCotizacion':   return accGuardarCotiz(d);
    case 'borrarCotizaciones':  return accBorrarCotiz(d);
    default:                    return { ok: false, mensaje: 'Acción desconocida: ' + accion };
  }
}

/* ─── Usuarios ───────────────────────────────────────────────────────── */
function accEntrar(d) {
  const correo = (d.correo || '').trim().toLowerCase();
  const u = leerTabla('usuarios').find(x => String(x.correo).toLowerCase() === correo);
  if (!u || String(u.clave) !== String(d.contrasena || '')) return { ok: false, mensaje: 'invalid login' };
  if (!verdad(u.activo)) return { ok: false, mensaje: 'inactivo' };
  return { ok: true, rol: u.rol, nombre: u.nombre, perfil: sinClave(u) };
}

function accPerfil(d) {
  const u = leerTabla('usuarios').find(x => x.id === d.id);
  if (!u || !verdad(u.activo)) return { ok: false };
  return { ok: true, perfil: sinClave(u) };
}

function accCrearUsuario(d) {
  const us = leerTabla('usuarios');
  const correo = (d.correo || '').trim().toLowerCase();
  if (us.some(x => String(x.correo).toLowerCase() === correo))
    return { ok: false, mensaje: 'Ese correo ya tiene una cuenta.' };
  if ((d.contrasena || '').length !== 64)
    return { ok: false, mensaje: 'La contraseña no llegó correctamente.' };

  const fila = {
    id: 'u' + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36),
    nombre: (d.nombre || '').trim(),
    apellidos: (d.apellidos || '').trim(),
    edad: Number(d.edad) || '',
    correo: correo,
    clave: d.contrasena,
    rol: d.rol === 'admin' ? 'admin' : 'scouting',
    activo: true,
    creado_en: new Date().toISOString()
  };
  agregar('usuarios', fila);
  return { ok: true };
}

function accActualizarUsuario(d) {
  const us = leerTabla('usuarios');
  const i = us.findIndex(x => x.id === d.id);
  if (i < 0) return { ok: false, mensaje: 'No se encontró la cuenta.' };
  const u = us[i];

  if (d.correo != null) {
    const nuevo = String(d.correo).trim().toLowerCase();
    if (us.some(x => x.id !== d.id && String(x.correo).toLowerCase() === nuevo))
      return { ok: false, mensaje: 'Ese correo ya lo usa otra cuenta.' };
    u.correo = nuevo;
  }
  if (d.contrasena) {
    if (d.contrasena.length !== 64) return { ok: false, mensaje: 'La contraseña no llegó correctamente.' };
    u.clave = d.contrasena;
  }
  if (d.nombre != null)    u.nombre = String(d.nombre).trim();
  if (d.apellidos != null) u.apellidos = String(d.apellidos).trim();
  if (d.edad != null)      u.edad = Number(d.edad);
  if (d.rol != null)       u.rol = d.rol;
  if (d.activo != null)    u.activo = !!d.activo;

  escribirFila('usuarios', i, u);
  return { ok: true };
}

function accCampo(tabla, id, campo, valor) {
  const filas = leerTabla(tabla);
  const i = filas.findIndex(x => x.id === id);
  if (i < 0) return { ok: false, mensaje: 'No se encontró el registro.' };
  filas[i][campo] = valor;
  escribirFila(tabla, i, filas[i]);
  return { ok: true };
}

/* ─── Configuración ──────────────────────────────────────────────────── */
function accLeerConfig() {
  const c = leerTabla('configuracion').find(x => String(x.id) === '1');
  if (!c) return { ok: true, datos: null, fecha: null };
  let datos = {};
  try { datos = JSON.parse(c.datos || '{}'); } catch (e) {}
  return { ok: true, datos: datos, fecha: c.actualizado_en };
}

function accGuardarConfig(d) {
  const filas = leerTabla('configuracion');
  let i = filas.findIndex(x => String(x.id) === '1');
  const fila = {
    id: 1,
    datos: JSON.stringify(d.datos || {}),
    actualizado_en: new Date().toISOString(),
    actualizado_por: d.usuarioId || ''
  };
  if (i < 0) { agregar('configuracion', fila); } else { escribirFila('configuracion', i, fila); }
  return { ok: true };
}

/* ─── Cotizaciones ───────────────────────────────────────────────────── */
function accListarCotiz(d) {
  let filas = leerTabla('cotizaciones');
  if (d.rol !== 'admin') filas = filas.filter(x => x.usuario_id === d.usuarioId);
  filas.sort((a, b) => String(b.creado_en).localeCompare(String(a.creado_en)));
  return { ok: true, filas: filas.map(aFormatoApp) };
}

function accGuardarCotiz(d) {
  const q = d.cotizacion || {};
  const fila = {
    id: 'c' + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36),
    usuario_id: d.usuarioId,
    usuario_nombre: d.usuarioNombre || '',
    producto: q.name, proveedor: q.supplier, categoria: q.category,
    costo_mxn: q.costMXN, costo_original: q.originalCost, moneda_original: q.originalCurrency,
    tipo_ml: q.mlType, mejor_plataforma: q.bestPlatform,
    precios: JSON.stringify(q.originalPrices || {}),
    resultados: JSON.stringify(q.fullResults || {}),
    creado_en: new Date().toISOString()
  };
  agregar('cotizaciones', fila);
  return { ok: true, fila: aFormatoApp(fila) };
}

function accBorrarCotiz(d) {
  const ids = new Set((d.ids || []).map(String));
  const hoja = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('cotizaciones');
  const filas = leerTabla('cotizaciones');
  for (let i = filas.length - 1; i >= 0; i--) {
    const propia = d.rol === 'admin' || filas[i].usuario_id === d.usuarioId;
    if (ids.has(String(filas[i].id)) && propia) hoja.deleteRow(i + 2);
  }
  return { ok: true };
}

/* ─── Utilidades de hoja ─────────────────────────────────────────────── */
function hojaDe(nombre) {
  return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(nombre);
}

function leerTabla(nombre) {
  const h = hojaDe(nombre);
  const rango = h.getDataRange().getValues();
  if (rango.length < 2) return [];
  const cols = rango[0];
  return rango.slice(1).map(r => {
    const o = {};
    cols.forEach((c, i) => { o[c] = r[i]; });
    return o;
  });
}

function agregar(nombre, obj) {
  const h = hojaDe(nombre);
  h.appendRow(HOJAS[nombre].map(c => obj[c] != null ? obj[c] : ''));
}

function escribirFila(nombre, indice, obj) {
  const h = hojaDe(nombre);
  const fila = HOJAS[nombre].map(c => obj[c] != null ? obj[c] : '');
  h.getRange(indice + 2, 1, 1, fila.length).setValues([fila]);
}

function sinClave(u) {
  const o = {};
  Object.keys(u).forEach(k => { if (k !== 'clave') o[k] = u[k]; });
  o.activo = verdad(u.activo);
  o.edad = u.edad === '' ? null : Number(u.edad);
  return o;
}

function aFormatoApp(f) {
  const j = s => { try { return JSON.parse(s || '{}'); } catch (e) { return {}; } };
  return {
    id: f.id, fecha: f.creado_en, autor: f.usuario_nombre, autorId: f.usuario_id,
    name: f.producto, supplier: f.proveedor, category: f.categoria,
    costMXN: Number(f.costo_mxn), originalCost: Number(f.costo_original),
    originalCurrency: f.moneda_original, mlType: f.tipo_ml, bestPlatform: f.mejor_plataforma,
    originalPrices: j(f.precios), fullResults: j(f.resultados)
  };
}

function verdad(v) {
  return v === true || v === 'true' || v === 'TRUE' || v === 1 || v === '1';
}

function sha256(txt) {
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(txt), Utilities.Charset.UTF_8);
  return bytes.map(b => ((b & 0xff) + 0x100).toString(16).slice(1)).join('');
}
