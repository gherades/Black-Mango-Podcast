'use strict';
const { test, describe } = require('node:test');
const assert = require('node:assert/strict');
const { loadPure } = require('./helpers/load-pure');

describe('escapeHtml', () => {
  test('escapa los cinco caracteres peligrosos', () => {
    const { escapeHtml } = loadPure();
    assert.equal(escapeHtml(`<script>alert('x')</script> & "quotes"`),
      '&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt; &amp; &quot;quotes&quot;');
  });

  test('null y undefined dan cadena vacía, no "null"/"undefined"', () => {
    const { escapeHtml } = loadPure();
    assert.equal(escapeHtml(null), '');
    assert.equal(escapeHtml(undefined), '');
  });

  test('texto sin caracteres especiales no cambia', () => {
    const { escapeHtml } = loadPure();
    assert.equal(escapeHtml('Black Mango #63 - Cuba'), 'Black Mango #63 - Cuba');
  });

  test('convierte a string valores no-string (p.ej. números)', () => {
    const { escapeHtml } = loadPure();
    assert.equal(escapeHtml(104), '104');
  });
});

describe('youtubeThumbnail', () => {
  test('extrae el id de una URL watch?v=', () => {
    const { youtubeThumbnail } = loadPure();
    assert.equal(
      youtubeThumbnail('https://www.youtube.com/watch?v=xMnB9slrtVI'),
      'https://i.ytimg.com/vi/xMnB9slrtVI/hqdefault.jpg'
    );
  });

  test('extrae el id de un enlace corto youtu.be/ID', () => {
    const { youtubeThumbnail } = loadPure();
    assert.equal(
      youtubeThumbnail('https://youtu.be/xMnB9slrtVI'),
      'https://i.ytimg.com/vi/xMnB9slrtVI/hqdefault.jpg'
    );
  });

  test('sin ytUrl cae al logo de portada', () => {
    const { youtubeThumbnail } = loadPure();
    assert.equal(youtubeThumbnail(''), 'assets/spotify-cover-hq.jpg');
    assert.equal(youtubeThumbnail(undefined), 'assets/spotify-cover-hq.jpg');
  });

  test('URL de YouTube sin id reconocible también cae al logo', () => {
    const { youtubeThumbnail } = loadPure();
    assert.equal(youtubeThumbnail('https://www.youtube.com/'), 'assets/spotify-cover-hq.jpg');
  });
});

describe('platformLinkHTML', () => {
  test('sin url no genera ningún enlace', () => {
    const { platformLinkHTML } = loadPure();
    assert.equal(platformLinkHTML('', 'spotify.png', 'Spotify'), '');
    assert.equal(platformLinkHTML(undefined, 'spotify.png', 'Spotify'), '');
  });

  test('con url genera un <a> con el icono correcto', () => {
    const { platformLinkHTML } = loadPure();
    const html = platformLinkHTML('https://open.spotify.com/episode/abc', 'spotify.png', 'Spotify');
    assert.match(html, /<a href="https:\/\/open\.spotify\.com\/episode\/abc"/);
    assert.match(html, /assets\/icons\/spotify\.png/);
    assert.match(html, /Escuchar en Spotify/);
  });

  test('una url con comillas no rompe el atributo href', () => {
    const { platformLinkHTML } = loadPure();
    const html = platformLinkHTML('https://x.test/"><script>alert(1)</script>', 'spotify.png', 'Spotify');
    assert.ok(!html.includes('"><script>'), 'la url deberia venir escapada dentro del atributo href');
  });
});

describe('episodeItemHTML', () => {
  const epBase = {
    epnum: 1,
    title: 'Black Mango #1 - Episodio de prueba',
    url: 'https://open.spotify.com/episode/x',
    appleUrl: 'https://podcasts.apple.com/x',
    ivooxUrl: 'https://www.ivoox.com/x',
    ytUrl: 'https://www.youtube.com/watch?v=abc123',
  };

  test('incluye el título y los cuatro enlaces cuando existen', () => {
    const { episodeItemHTML } = loadPure();
    const html = episodeItemHTML(epBase);
    assert.match(html, /Black Mango #1 - Episodio de prueba/);
    assert.match(html, /spotify\.png/);
    assert.match(html, /apple-podcasts\.png/);
    assert.match(html, /ivoox\.png/);
    assert.match(html, /youtube\.png/);
    assert.match(html, /i\.ytimg\.com\/vi\/abc123\/hqdefault\.jpg/);
  });

  test('omite el icono de una plataforma sin enlace (p.ej. episodios solo-YouTube)', () => {
    const { episodeItemHTML } = loadPure();
    const soloYoutube = { ...epBase, url: '', appleUrl: '', ivooxUrl: '' };
    const html = episodeItemHTML(soloYoutube);
    assert.ok(!html.includes('spotify.png'));
    assert.ok(!html.includes('apple-podcasts.png'));
    assert.ok(!html.includes('ivoox.png'));
    assert.match(html, /youtube\.png/);
  });

  test('un título con HTML no se interpreta: sale escapado', () => {
    const { episodeItemHTML } = loadPure();
    const maligno = { ...epBase, title: '<img src=x onerror=alert(1)>' };
    const html = episodeItemHTML(maligno);
    assert.ok(!html.includes('<img src=x onerror=alert(1)>'),
      'el titulo no deberia aparecer sin escapar: seria XSS almacenado');
    assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  });
});

describe('mapPopupEpisodeHTML', () => {
  test('mismo criterio de escapado que episodeItemHTML', () => {
    const { mapPopupEpisodeHTML } = loadPure();
    const html = mapPopupEpisodeHTML({ title: '<b>x</b>', ytUrl: '' });
    assert.ok(!html.includes('<b>x</b>'));
    assert.match(html, /&lt;b&gt;x&lt;\/b&gt;/);
  });
});
