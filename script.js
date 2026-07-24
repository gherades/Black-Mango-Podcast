document.addEventListener('DOMContentLoaded', () => {
  renderEpisodes();

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

function renderEpisodes() {
  const list = document.querySelector('.episode-list');
  if (!list || typeof EPISODES === 'undefined') return;

  list.innerHTML = EPISODES.map((ep) => {
    const match = ep.title.match(/#(\d+)/);
    const number = match ? `#${match[1]}` : '';
    return `
      <li class="episode">
        <span class="episode-number">${number}</span>
        <a class="episode-title" href="${ep.url}" target="_blank" rel="noopener">${ep.title}</a>
      </li>
    `;
  }).join('');
}
