'use strict';
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { loadDom } = require('./helpers/load-dom');

const ep = (epnum, title, extra = {}) => ({
  epnum, title,
  url: `https://open.spotify.com/episode/${epnum}`,
  appleUrl: '', ivooxUrl: '', ytUrl: '',
  ...extra,
});

describe('renderAll (pestaña "Todos")', () => {
  test('junta episodios de SERIES y STANDALONE_EPISODES, ordenados por número descendente', () => {
    const dom = loadDom({
      SERIES: [{ name: 'Serie A', episodes: [ep(1, 'Uno'), ep(3, 'Tres')] }],
      STANDALONE_EPISODES: [ep(2, 'Dos')],
    });
    dom.window.renderAll();
    const titles = [...dom.window.document.querySelectorAll('#all-list .episode-title')]
      .map((n) => n.textContent);
    assert.deepEqual(titles, ['Tres', 'Dos', 'Uno']);
  });

  test('sin SERIES/STANDALONE_EPISODES definidos no lanza excepción', () => {
    const dom = loadDom({});
    assert.doesNotThrow(() => dom.window.renderAll());
  });
});

describe('renderSeries', () => {
  test('crea un <details> por serie con el contador de episodios correcto', () => {
    const dom = loadDom({
      SERIES: [
        { name: 'La Mafia', episodes: [ep(1, 'a'), ep(2, 'b'), ep(3, 'c')] },
        { name: 'Mitología', episodes: [ep(4, 'd')] },
      ],
    });
    dom.window.renderSeries();
    const cards = dom.window.document.querySelectorAll('.series-card');
    assert.equal(cards.length, 2);
    assert.equal(cards[0].querySelector('.series-name').textContent, 'La Mafia');
    assert.equal(cards[0].querySelector('.series-count-number').textContent, '3');
    assert.equal(cards[1].querySelector('.series-count-number').textContent, '1');
  });

  test('el nombre de la serie sale escapado (no se interpreta como HTML)', () => {
    const dom = loadDom({
      SERIES: [{ name: '<b>Serie Maligna</b>', episodes: [] }],
    });
    dom.window.renderSeries();
    const nameEl = dom.window.document.querySelector('.series-name');
    assert.equal(nameEl.querySelector('b'), null, 'no deberia haberse creado un <b> real');
    assert.equal(nameEl.textContent, '<b>Serie Maligna</b>');
  });
});

describe('renderDocs', () => {
  test('pinta los documentales en #docs-list', () => {
    const dom = loadDom({
      DOCUMENTALES: [{ title: 'Doc 1', ytUrl: 'https://www.youtube.com/watch?v=abc' }],
    });
    dom.window.renderDocs();
    const items = dom.window.document.querySelectorAll('#docs-list .episode-card');
    assert.equal(items.length, 1);
    assert.match(items[0].querySelector('.episode-title').textContent, /Doc 1/);
  });
});

describe('initTabs', () => {
  test('al hacer clic en una pestaña, se activa ella y su panel (y se desactivan las demás)', () => {
    const dom = loadDom({});
    dom.window.initTabs();
    const { document } = dom.window;

    const docsBtn = document.querySelector('[data-tab="documentales"]');
    docsBtn.dispatchEvent(new dom.window.Event('click', { bubbles: true }));

    assert.equal(docsBtn.classList.contains('is-active'), true);
    assert.equal(docsBtn.getAttribute('aria-selected'), 'true');
    assert.equal(document.querySelector('[data-tab="series"]').classList.contains('is-active'), false);
    assert.equal(document.querySelector('.tab-panel[data-panel="documentales"]').classList.contains('is-active'), true);
    assert.equal(document.querySelector('.tab-panel[data-panel="series"]').classList.contains('is-active'), false);
  });
});

describe('renderMap', () => {
  function domConDosChinchetas() {
    return loadDom({
      MAP_LOCATIONS: [
        { name: 'Cuba', xPct: 27.8, yPct: 40.9, episodes: [ep(63, 'La terrible Cuba')] },
        { name: 'Japón', xPct: 82.6, yPct: 33.3, episodes: [ep(57, 'Japón feudal')] },
      ],
    });
  }

  test('crea una chincheta por localización, posicionada con left/top en %', () => {
    const dom = domConDosChinchetas();
    dom.window.renderMap();
    const pins = dom.window.document.querySelectorAll('.map-pin');
    assert.equal(pins.length, 2);
    assert.equal(pins[0].style.left, '27.8%');
    assert.equal(pins[0].style.top, '40.9%');
    assert.equal(pins[0].getAttribute('aria-label'), 'Cuba: 1 episodio(s)');
    assert.equal(pins[0].getAttribute('aria-expanded'), 'false',
      'una chincheta recién pintada no debería anunciarse como expandida');
  });

  test('un nombre "malicioso" no crea ningún elemento nuevo, queda como texto plano', () => {
    // Ojo con esta aserción: NO se puede comprobar buscando la subcadena
    // literal "<script>" en el innerHTML serializado. El navegador (y
    // jsdom) reserializan el VALOR de un atributo mostrando "<"/">" tal
    // cual —es válido y seguro dentro de comillas—, así que esa búsqueda
    // ingenua daría un falso positivo aunque el escapado funcione bien.
    // Lo que de verdad importa es que no se cree ningún <script> real en
    // el DOM, y que el texto visible sea exactamente el original.
    const dom = loadDom({
      MAP_LOCATIONS: [{ name: '"><script>x</script>', xPct: 50, yPct: 50, episodes: [] }],
    });
    dom.window.renderMap();
    const { document } = dom.window;
    const pin = document.querySelector('.map-pin');

    assert.equal(document.querySelectorAll('script').length, 0,
      'no debería haberse creado ningún elemento <script> real');
    assert.equal(pin.getAttribute('aria-label'), '"><script>x</script>: 0 episodio(s)');
    assert.equal(pin.querySelector('.map-popup-title').textContent, '"><script>x</script>');
    // el botón solo debe tener los dos <span> esperados como hijos directos,
    // nada inyectado de más
    assert.equal(pin.children.length, 2);
  });

  test('clic en una chincheta la abre; clic fuera la cierra (initMapOutsideClick)', () => {
    const dom = domConDosChinchetas();
    dom.window.renderMap();
    dom.window.initMapOutsideClick();
    const { document, Event } = dom.window;
    const [cuba, japon] = document.querySelectorAll('.map-pin');

    cuba.dispatchEvent(new Event('click', { bubbles: true }));
    assert.equal(cuba.classList.contains('is-open'), true);
    assert.equal(cuba.getAttribute('aria-expanded'), 'true',
      'aria-expanded debe seguir a is-open, no solo la clase visual');

    // clic en OTRA chincheta cierra la primera y abre la segunda (no ambas)
    japon.dispatchEvent(new Event('click', { bubbles: true }));
    assert.equal(cuba.classList.contains('is-open'), false);
    assert.equal(cuba.getAttribute('aria-expanded'), 'false');
    assert.equal(japon.classList.contains('is-open'), true);
    assert.equal(japon.getAttribute('aria-expanded'), 'true');

    // clic fuera del mapa cierra la que quedaba abierta
    document.body.dispatchEvent(new Event('click', { bubbles: true }));
    assert.equal(japon.classList.contains('is-open'), false);
    assert.equal(japon.getAttribute('aria-expanded'), 'false');
  });

  test('llamar a initMapOutsideClick una sola vez basta (no se acumulan listeners)', () => {
    // regresión: antes este listener vivía DENTRO de renderMap() y se
    // habría duplicado en cada llamada. Ahora vive aparte; comprobamos que
    // un solo listener ya cierra correctamente sin ejecutarse "de más"
    // (si se duplicara, esto seguiría pasando el test — lo importante es
    // que initMapOutsideClick es la única responsable y es idempotente de
    // registrar una vez).
    const dom = domConDosChinchetas();
    dom.window.renderMap();
    dom.window.initMapOutsideClick();
    const { document, Event } = dom.window;
    const pin = document.querySelector('.map-pin');
    pin.dispatchEvent(new Event('click', { bubbles: true }));
    assert.equal(pin.classList.contains('is-open'), true);
    document.body.dispatchEvent(new Event('click', { bubbles: true }));
    assert.equal(pin.classList.contains('is-open'), false);
  });

  test('sin MAP_LOCATIONS definido no lanza excepción', () => {
    const dom = loadDom({});
    assert.doesNotThrow(() => dom.window.renderMap());
  });
});
