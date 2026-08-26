/* Conexión Dinámica para Celulares y PC */
const API_HOST = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : 'http://localhost:8560';
const SHEETS_URL   = API_HOST + '/api/action';
const SHEETS_TOKEN = 'Pelusa';
