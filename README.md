# Black Mango Podcast — Fan Page

Fan page no oficial del Black Mango Podcast. Sitio estático (HTML/CSS/JS) inspirado
en el estilo visual de [blackmangofilms.com](https://blackmangofilms.com/).

## Datos del podcast

- Logo/portada (`assets/spotify-cover-hq.jpg`) y episodios (`assets/episodes.js`)
  obtenidos del show real en Spotify: https://open.spotify.com/show/0WEqNybNBwZPZTM1V1iG2i
- Spotify solo expone en el reproductor web los ~61 episodios más recientes
  (del #103 al #42); para actualizar la lista, vuelve a esa página, pulsa
  "Cargar más episodios" hasta el final y regenera `episodes.js`.

## Pendiente de completar

- Descripción real del podcast (sección "Sobre").
- Enlaces reales a Apple Podcasts, YouTube, iVoox, etc.
- Enlaces a redes sociales (Instagram, Twitter/X) y email de contacto.

## Desarrollo

Es un sitio estático sin build step. Basta con abrir `index.html` en el navegador,
o servirlo con cualquier servidor estático, por ejemplo:

```bash
npx serve .
```
