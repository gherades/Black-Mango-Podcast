document.addEventListener('DOMContentLoaded', () => {
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
        <a href="${ep.url}" target="_blank" rel="noopener">Spotify</a>
        <a href="${ep.appleUrl}" target="_blank" rel="noopener">Apple Podcasts</a>
      </span>
    </li>
  `;
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
