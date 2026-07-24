# Black Mango Podcast — Fan Page

Fan page no oficial del Black Mango Podcast. Sitio estático (HTML/CSS/JS) inspirado
en el estilo visual de [blackmangofilms.com](https://blackmangofilms.com/).

## Datos del podcast

- Logo/portada (`assets/spotify-cover-hq.jpg`) y episodios (`assets/episodes.js`)
  obtenidos del show real en Spotify: https://open.spotify.com/show/0WEqNybNBwZPZTM1V1iG2i
- Lista completa: 98 episodios, del #103 hasta el "Episodio 1 | Indonesia"
  (el listado del reproductor web usa scroll infinito con virtualización, no
  solo el botón "Cargar más episodios" — hay que hacer scroll hasta el final,
  donde aparece la sección "Más pódcasts como este", para que cargue todo).
  Para actualizar la lista, repite ese proceso y regenera `episodes.js`.
- La sección "Episodios" agrupa los capítulos en dos pestañas, usando
  `assets/series-data.js` (generado a partir de `episodes.js`):
  - **Series**: capítulos que forman parte de una saga numerada dentro del
    título (p.ej. "Crímenes Imperfectos 3", "Catástrofes Aéreas 5") más dos
    agrupaciones temáticas sin número explícito (Mitología, La Mafia).
  - **Sueltos**: el resto de episodios, sin patrón de serie detectado.
  - Si añades episodios nuevos, regenera `series-data.js` repitiendo el
    análisis (buscar título con patrón "Nombre + número" y agrupar).

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
