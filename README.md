# Black Mango Podcast

Sitio estático (HTML/CSS/JS) inspirado en el estilo visual de
[blackmangofilms.com](https://blackmangofilms.com/).

## Datos del podcast

- Logo/portada (`assets/spotify-cover-hq.jpg`) y episodios (`assets/episodes.js`)
  obtenidos del show real en Spotify: https://open.spotify.com/show/0WEqNybNBwZPZTM1V1iG2i
- Lista completa: 97 episodios únicos, del #103 hasta el "Episodio 1 | Indonesia"
  (el listado del reproductor web usa scroll infinito con virtualización, no
  solo el botón "Cargar más episodios" — hay que hacer scroll hasta el final,
  donde aparece la sección "Más pódcasts como este", para que cargue todo).
  Para actualizar la lista, repite ese proceso y regenera `episodes.js`.
  El "Episodio 12" tenía dos versiones en Spotify (una de pago); se dejó solo
  la gratuita, con "| Daniel Sancho" añadido al título.
- La sección "Episodios" agrupa los capítulos en dos pestañas, usando
  `assets/series-data.js` (generado a partir de `episodes.js`, ya no cargado
  directamente por la página):
  - **Series**: capítulos que forman parte de una saga numerada dentro del
    título (p.ej. "Crímenes Imperfectos 3", "Catástrofes Aéreas 5"), más
    agrupaciones temáticas sin número explícito (Mitología, La Mafia, Los
    Terribles — este último para títulos que contienen "terrible"/"terribles"
    y no pertenecen ya a una saga numerada como Historias Terribles).
  - **Sueltos**: el resto de episodios, sin patrón de serie detectado.
  - Si añades episodios nuevos, regenera `series-data.js` repitiendo el
    análisis (buscar título con patrón "Nombre + número" y agrupar).
- Cada episodio incluye también su enlace de Apple Podcasts (`appleUrl`),
  obtenido de https://podcasts.apple.com/es/podcast/black-mango-podcast/id1726276206
  y su enlace de iVoox (`ivooxUrl`), obtenido de
  https://www.ivoox.com/podcast-black-mango-podcast_sq_f12370133_1.html
  (paginación clásica `..._1.html` a `..._5.html`, 20 episodios por página).
  Ambos se emparejan por número de episodio (coinciden 1:1 con Spotify, 97 en
  los tres). El botón "Escuchar" enlaza a los tres shows completos.
- También incluye el enlace de YouTube (`ytUrl`) del canal oficial
  https://www.youtube.com/@blackmangopodcast (playlist "Podcast"), emparejado
  por número de episodio. Cubre los 97 episodios (los primeros, #1-#16, solo
  aparecían al abrir un vídeo de la playlist directamente — la vista
  `/playlist` los recorta — y usan un formato de título distinto en YouTube
  ("Black Mango #Podcast N") pero corresponden al mismo contenido).

## Pendiente de completar

- Descripción real del podcast (sección "Sobre").

## Desarrollo

Es un sitio estático sin build step. Basta con abrir `index.html` en el navegador,
o servirlo con cualquier servidor estático, por ejemplo:

```bash
npx serve .
```
