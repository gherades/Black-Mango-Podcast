'use strict';
// Carga script.js de verdad dentro de un documento jsdom con el marcado
// mínimo que espera encontrar (mismas clases/ids que index.html). Los datos
// (SERIES, MAP_LOCATIONS...) los define cada test, pequeños y a medida —
// nunca el catálogo real, para que estos tests no dependan del contenido
// del podcast y sean deterministas.
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const SCRIPT_PATH = path.join(__dirname, '..', '..', 'script.js');

const FIXTURE_HTML = `<!DOCTYPE html>
<html>
<body>
<header class="site-header"><nav class="nav">
  <a href="#inicio">Inicio</a>
  <a href="#episodios">Episodios</a>
</nav></header>
<main>
  <section id="episodios" class="section">
    <div class="tabs" role="tablist">
      <button class="tab-button is-active" data-tab="series" role="tab" aria-selected="true">Series</button>
      <button class="tab-button" data-tab="documentales" role="tab" aria-selected="false">Documentales</button>
      <button class="tab-button" data-tab="todos" role="tab" aria-selected="false">Todos</button>
    </div>
    <div class="tab-panel is-active" data-panel="series"><div class="series-list"></div></div>
    <div class="tab-panel" data-panel="documentales"><ul class="episode-list" id="docs-list"></ul></div>
    <div class="tab-panel" data-panel="todos"><ul class="episode-list" id="all-list"></ul></div>
  </section>
  <section id="mapa" class="section">
    <div class="world-map">
      <img src="assets/world-map-illustrated.png" alt="Mapa del mundo" class="world-map-img">
    </div>
  </section>
</main>
</body>
</html>`;

/**
 * @param {object} dataGlobals - p.ej. { SERIES, STANDALONE_EPISODES, DOCUMENTALES, MAP_LOCATIONS }
 * @returns {JSDOM}
 */
function loadDom(dataGlobals = {}) {
  const dom = new JSDOM(FIXTURE_HTML, { runScripts: 'outside-only', url: 'http://localhost/' });
  Object.assign(dom.window, dataGlobals);
  const src = fs.readFileSync(SCRIPT_PATH, 'utf8');
  dom.window.eval(src);
  return dom;
}

module.exports = { loadDom, FIXTURE_HTML };
