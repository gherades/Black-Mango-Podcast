'use strict';
// Único test de integración (a propósito: la pirámide de test debe tener
// pocos de estos). Carga el index.html, los datos y el script.js REALES
// —no fixtures— para detectar desajustes de cableado entre ellos que los
// tests unitarios, con sus propios datos de mentira, no pueden ver
// (p.ej. si alguien renombra una clase en index.html sin tocar script.js).
//
// Deliberadamente flojo en las aserciones sobre CONTENIDO (no comprueba
// "hay exactamente 103 episodios"): eso cambiará cada semana con el
// checker automático y no es lo que este test intenta vigilar.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.join(__dirname, '..');

test('index.html + series-data.js + map-data.js + script.js reales funcionan juntos', () => {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'outside-only', url: 'http://localhost/' });

  // Un solo eval() con los tres archivos concatenados, en el mismo orden
  // que index.html los carga como <script>. Importante: si se hiciera un
  // dom.window.eval(...) POR ARCHIVO, cada llamada obtiene su propio scope
  // léxico y los "const" de series-data.js/map-data.js no serían visibles
  // desde script.js (aunque SÍ lo son entre <script> reales en un
  // navegador, y aquí necesitamos replicar exactamente ese comportamiento).
  const files = ['assets/series-data.js', 'assets/map-data.js', 'script.js'];
  const combinedSrc = files.map((f) => fs.readFileSync(path.join(ROOT, f), 'utf8')).join('\n;\n');
  assert.doesNotThrow(() => dom.window.eval(combinedSrc), 'los archivos de datos + script.js deberían cargar sin lanzar');

  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded', { bubbles: true }));

  const { document } = dom.window;

  const seriesCards = document.querySelectorAll('.series-card');
  assert.ok(seriesCards.length > 0, 'debería haber al menos una serie renderizada');

  const allEpisodes = document.querySelectorAll('#all-list .episode-card');
  assert.ok(allEpisodes.length > 50, 'la pestaña "Todos" debería tener bastantes episodios');

  const docs = document.querySelectorAll('#docs-list .episode-card');
  assert.ok(docs.length > 0, 'debería haber al menos un documental');

  const pins = document.querySelectorAll('.map-pin');
  assert.ok(pins.length > 0, 'el mapa debería tener al menos una chincheta');
  for (const pin of pins) {
    assert.match(pin.style.left, /%$/, 'cada chincheta debe posicionarse en % de left');
    assert.match(pin.style.top, /%$/, 'cada chincheta debe posicionarse en % de top');
  }

  // cambiar de pestaña funciona con el cableado real (no un fixture)
  const todosBtn = document.querySelector('[data-tab="todos"]');
  todosBtn.dispatchEvent(new dom.window.Event('click', { bubbles: true }));
  assert.equal(document.querySelector('.tab-panel[data-panel="todos"]').classList.contains('is-active'), true);
  assert.equal(document.querySelector('.tab-panel[data-panel="series"]').classList.contains('is-active'), false);

  // ningún título real se ha colado sin escapar como HTML vivo dentro de
  // una tarjeta (comprobación barata de que escapeHtml se está aplicando)
  const rawScriptTags = document.querySelectorAll('#all-list script, .series-list script, #docs-list script');
  assert.equal(rawScriptTags.length, 0);
});
