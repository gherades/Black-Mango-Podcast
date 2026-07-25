document.addEventListener('DOMContentLoaded', () => {
  renderAll();
  renderSeries();
  renderStandalone();
  initTabs();

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

function episodeBadge(title) {
  const match = title.match(/#(\d+)/) || title.match(/Episodio (\d+)/);
  return match ? `#${match[1]}` : '';
}

function episodeItemHTML(ep) {
  return `
    <li class="episode">
      <span class="episode-number">${episodeBadge(ep.title)}</span>
      <span class="episode-title">${ep.title}</span>
      <span class="episode-links">
        <a href="${ep.url}" target="_blank" rel="noopener" title="Escuchar en Spotify" aria-label="Escuchar en Spotify">
          <img src="assets/icons/spotify.png" alt="Spotify">
        </a>
        <a href="${ep.appleUrl}" target="_blank" rel="noopener" title="Escuchar en Apple Podcasts" aria-label="Escuchar en Apple Podcasts">
          <img src="assets/icons/apple-podcasts.png" alt="Apple Podcasts">
        </a>
        <a href="${ep.ivooxUrl}" target="_blank" rel="noopener" title="Escuchar en iVoox" aria-label="Escuchar en iVoox">
          <img src="assets/icons/ivoox.png" alt="iVoox">
        </a>
        ${ep.ytUrl ? `
        <a href="${ep.ytUrl}" target="_blank" rel="noopener" title="Ver en YouTube" aria-label="Ver en YouTube">
          <img src="assets/icons/youtube.png" alt="YouTube">
        </a>` : ''}
      </span>
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

function renderStandalone() {
  const list = document.getElementById('standalone-list');
  if (!list || typeof STANDALONE_EPISODES === 'undefined') return;
  list.innerHTML = STANDALONE_EPISODES.map(episodeItemHTML).join('');
}

function renderSeries() {
  const container = document.querySelector('.series-list');
  if (!container || typeof SERIES === 'undefined') return;

  container.innerHTML = SERIES.map((series) => `
    <details class="series-card">
      <summary>
        <span class="series-name">${series.name}</span>
        <span class="series-count">${series.episodes.length} ep.</span>
      </summary>
      <ul class="episode-list">
        ${series.episodes.map(episodeItemHTML).join('')}
      </ul>
    </details>
  `).join('');
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
