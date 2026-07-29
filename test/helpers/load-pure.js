'use strict';
// Carga script.js con un "document" de mentira que solo sabe registrar el
// listener de DOMContentLoaded del arranque del archivo. Sirve para probar
// las funciones que construyen HTML como texto (escapeHtml,
// episodeItemHTML, platformLinkHTML...) sin pagar el coste de jsdom, que
// no hace falta para estas: no leen ni escriben el DOM de verdad.
const vm = require('vm');
const fs = require('fs');
const path = require('path');

const SCRIPT_PATH = path.join(__dirname, '..', '..', 'script.js');

function loadPure() {
  const src = fs.readFileSync(SCRIPT_PATH, 'utf8');
  const sandbox = {
    document: {
      addEventListener() {},
      querySelectorAll() { return []; },
      querySelector() { return null; },
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox, { filename: 'script.js' });
  return sandbox;
}

module.exports = { loadPure };
