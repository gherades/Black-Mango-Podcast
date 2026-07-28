document.addEventListener('DOMContentLoaded', () => {
  renderAll();
  renderSeries();
  renderDocs();
  renderMap();
  initTabs();
  initMapOutsideClick();

  const links = document.querySelectorAll('a[href^="#"]');
  links.forEach((link) => {
    link.addEventListener('click', (e) => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : String(str);
  return div.innerHTML;
}

function youtubeThumbnail(ytUrl) {
  // soporta tanto watch?v=ID (todos los episodios actuales) como youtu.be/ID,
  // por si algún enlace futuro llega en el formato corto
  const match = ytUrl && ytUrl.match(/(?:[?&]v=|youtu\.be\/)([\w-]+)/);
  return match ? `https://i.ytimg.com/vi/${match[1]}/hqdefault.jpg` : 'assets/spotify-cover-hq.jpg';
}

function platformLinkHTML(url, icon, label) {
  if (!url) return '';
  return `
    <a href="${escapeHtml(url)}" target="_blank" rel="noopener" title="Escuchar en ${label}" aria-label="Escuchar en ${label}">
      <img src="assets/icons/${icon}" alt="${label}">
    </a>`;
}

function episodeItemHTML(ep) {
  return `
    <li class="episode-card">
      <img class="episode-cover" src="${escapeHtml(youtubeThumbnail(ep.ytUrl))}" alt="" loading="lazy">
      <div class="episode-card-body">
        <p class="episode-title">${escapeHtml(ep.title)}</p>
        <span class="episode-links">
          ${platformLinkHTML(ep.url, 'spotify.png', 'Spotify')}
          ${platformLinkHTML(ep.appleUrl, 'apple-podcasts.png', 'Apple Podcasts')}
          ${platformLinkHTML(ep.ivooxUrl, 'ivoox.png', 'iVoox')}
          ${platformLinkHTML(ep.ytUrl, 'youtube.png', 'YouTube')}
        </span>
      </div>
    </li>
  `;
}

function renderAll() {
  const list = document.getElementById('all-list');
  if (!list || typeof SERIES === 'undefined' || typeof STANDALONE_EPISODES === 'undefined') return;

  const all = SERIES.flatMap((series) => series.episodes).concat(STANDALONE_EPISODES);
  all.sort((a, b) => b.epnum - a.epnum);
  list.innerHTML = all.map(episodeItemHTML).join('');
}

function renderSeries() {
  const container = document.querySelector('.series-list');
  if (!container || typeof SERIES === 'undefined') return;

  container.innerHTML = SERIES.map((series) => `
    <details class="series-card">
      <summary>
        <span class="series-name">${escapeHtml(series.name)}</span>
        <span class="series-meta">
          <span class="series-count">
            <span class="series-count-number">${series.episodes.length}</span><span class="series-count-label">ep</span>
          </span>
          <span class="series-toggle"></span>
        </span>
      </summary>
      <ul class="episode-list">
        ${series.episodes.map(episodeItemHTML).join('')}
      </ul>
    </details>
  `).join('');
}

function renderDocs() {
  const list = document.getElementById('docs-list');
  if (!list || typeof DOCUMENTALES === 'undefined') return;

  list.innerHTML = DOCUMENTALES.map(episodeItemHTML).join('');
}

function mapPopupEpisodeHTML(ep) {
  return `
    <li class="map-popup-episode">
      <span class="map-popup-ep-title">${escapeHtml(ep.title)}</span>
      <span class="episode-links">
        ${platformLinkHTML(ep.url, 'spotify.png', 'Spotify')}
        ${platformLinkHTML(ep.appleUrl, 'apple-podcasts.png', 'Apple Podcasts')}
        ${platformLinkHTML(ep.ivooxUrl, 'ivoox.png', 'iVoox')}
        ${platformLinkHTML(ep.ytUrl, 'youtube.png', 'YouTube')}
      </span>
    </li>
  `;
}

function renderMap() {
  const container = document.querySelector('.world-map');
  if (!container || typeof MAP_LOCATIONS === 'undefined') return;

  const pins = MAP_LOCATIONS.map((loc) => {
    const align = loc.xPct < 15 ? 'align-left' : loc.xPct > 85 ? 'align-right' : 'align-center';
    const side = loc.yPct < 45 ? 'side-below' : 'side-above';
    return `
      <button type="button" class="map-pin ${align} ${side}" style="left:${loc.xPct}%; top:${loc.yPct}%;" aria-label="${escapeHtml(loc.name)}: ${loc.episodes.length} episodio(s)">
        <span class="map-pin-dot"></span>
        <span class="map-popup">
          <span class="map-popup-title">${escapeHtml(loc.name)}</span>
          <ul class="map-popup-list">
            ${loc.episodes.map(mapPopupEpisodeHTML).join('')}
          </ul>
        </span>
      </button>
    `;
  }).join('');

  container.insertAdjacentHTML('beforeend', pins);

  container.querySelectorAll('.map-pin').forEach((pin) => {
    pin.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = pin.classList.contains('is-open');
      container.querySelectorAll('.map-pin.is-open').forEach((p) => p.classList.remove('is-open'));
      if (!isOpen) pin.classList.add('is-open');
    });
  });
}

// aparte de renderMap(): es un comportamiento de página (cerrar chinchetas
// al hacer clic fuera), no algo ligado a cada render del mapa. Si viviera
// dentro de renderMap(), cada llamada apilaría un listener de document más.
function initMapOutsideClick() {
  document.addEventListener('click', () => {
    document.querySelectorAll('.map-pin.is-open').forEach((p) => p.classList.remove('is-open'));
  });
}

function initTabs() {
  const buttons = document.querySelectorAll('.tab-button');
  const panels = document.querySelectorAll('.tab-panel');
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => {
        b.classList.remove('is-active');
        b.setAttribute('aria-selected', 'false');
      });
      panels.forEach((p) => p.classList.remove('is-active'));

      btn.classList.add('is-active');
      btn.setAttribute('aria-selected', 'true');
      document.querySelector(`.tab-panel[data-panel="${btn.dataset.tab}"]`).classList.add('is-active');
    });
  });
}
