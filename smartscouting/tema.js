/* Mantiene el mismo tema (claro u oscuro) en todas las páginas.
   La preferencia se guarda en el navegador con la misma llave que usa
   la calculadora, así que elegir el tema en un lado se refleja en todos. */
(function () {
  var LLAVE = 'ss_theme';
  var tema = localStorage.getItem(LLAVE) || 'dark';
  document.documentElement.setAttribute('data-theme', tema);

  window.alternarTema = function () {
    var actual = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', actual);
    localStorage.setItem(LLAVE, actual);
    document.querySelectorAll('[data-tema-icono]').forEach(pintarIcono);
  };

  var SOL = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var LUNA = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';

  function pintarIcono(btn) {
    var claro = document.documentElement.getAttribute('data-theme') === 'light';
    btn.innerHTML = claro ? LUNA : SOL;
    btn.title = claro ? 'Cambiar a tema oscuro' : 'Cambiar a tema claro';
  }

  window.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-tema-icono]').forEach(function (btn) {
      pintarIcono(btn);
      btn.addEventListener('click', window.alternarTema);
    });
  });
})();
