document.addEventListener('DOMContentLoaded', () => {
  renderAll();
  renderSeries();
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

function youtubeThumbnail(ytUrl) {
  const match = ytUrl && ytUrl.match(/[?&]v=([\w-]+)/);
  return match ? `https://i.ytimg.com/vi/${match[1]}/hqdefault.jpg` : 'assets/spotify-cover-hq.jpg';
}

function platformLinkHTML(url, icon, label) {
  if (!url) return '';
  return `
    <a href="${url}" target="_blank" rel="noopener" title="Escuchar en ${label}" aria-label="Escuchar en ${label}">
      <img src="assets/icons/${icon}" alt="${label}">
    </a>`;
}

function episodeItemHTML(ep) {
  return `
    <li class="episode-card">
      <img class="episode-cover" src="${youtubeThumbnail(ep.ytUrl)}" alt="" loading="lazy">
      <div class="episode-card-body">
        <p class="episode-title">${ep.title}</p>
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
