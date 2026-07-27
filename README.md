# Black Mango Podcast

Sitio estático (HTML/CSS/JS) inspirado en el estilo visual de
[blackmangofilms.com](https://blackmangofilms.com/).

## Datos del podcast

- Logo/portada (`assets/spotify-cover-hq.jpg`) y episodios (`assets/episodes.js`)
  obtenidos del show real en Spotify: https://open.spotify.com/show/0WEqNybNBwZPZTM1V1iG2i
- Lista completa: 97 episodios únicos en Spotify, del #103 hasta el "Episodio 1 |
  Indonesia" (el listado del reproductor web usa scroll infinito con
  virtualización, no solo el botón "Cargar más episodios" — hay que hacer
  scroll hasta el final, donde aparece la sección "Más pódcasts como este",
  para que cargue todo). Para actualizar la lista, repite ese proceso y
  regenera `episodes.js`. El "Episodio 12" tenía dos versiones en Spotify (una
  de pago); se dejó solo la gratuita, con "| Daniel Sancho" añadido al título.
- Los episodios 4-8 nunca estuvieron en Spotify/Apple/iVoox, solo en YouTube
  (`url`, `appleUrl` e `ivooxUrl` vacíos, solo `ytUrl`). Se añadieron a mano
  a partir de la playlist de YouTube. Total del sitio: 102 episodios.
- La sección "Episodios" agrupa los capítulos en tres pestañas, usando
  `assets/series-data.js` (generado a partir de `episodes.js`, ya no cargado
  directamente por la página):
  - **Series**: capítulos que forman parte de una saga numerada dentro del
    título (p.ej. "Crímenes Imperfectos 3", "Catástrofes Aéreas 5"), más
    agrupaciones temáticas sin número explícito (Mitología, La Mafia, Los
    Terribles — este último para títulos que contienen "terrible"/"terribles"
    y no pertenecen ya a una saga numerada como Historias Terribles).
  - **Documentales**: los 7 vídeos de la playlist de YouTube
    `PLGR6l-llOTj52NWifz_9red7xPk-56WDf`, contenido aparte de los episodios
    numerados (array `DOCUMENTALES`, solo tienen `ytUrl`).
  - **Todos**: series y episodios sueltos juntos, ordenados por número.
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
  por número de episodio. Cubre los 102 episodios (los primeros, #1-#16, solo
  aparecían al abrir un vídeo de la playlist directamente — la vista
  `/playlist` los recorta — y usan un formato de título distinto en YouTube
  ("Black Mango #Podcast N") pero corresponden al mismo contenido).
- La plantilla de episodio (`episodeItemHTML` en `script.js`) solo dibuja el
  icono de cada plataforma si esa URL no está vacía, para soportar episodios
  como el 4-8 que solo tienen `ytUrl`.

## Mapa ("El mundo de Black Mango")

`assets/map-data.js` define las chinchetas: cada una agrupa los episodios y
documentales que hablan de ese país o civilización.

- El mapa base (`assets/world-map-illustrated.png`) es una **ilustración**, no
  una proyección cartográfica exacta: Europa está dibujada más al norte y más
  estirada de lo que le correspondería. Por eso las coordenadas no se pueden
  calcular con una fórmula de proyección sin más.
- `xPct` sale de un ajuste lineal longitud→píxel (residuos ±8 px, calibrado con
  los extremos de Australia, Sudamérica y África, que son masas de tierra
  aisladas y por tanto medibles con fiabilidad).
- `yPct` sale de una interpolación **por tramos** entre 13 puntos de control
  medidos sobre el propio dibujo (Cabo Norte, norte y sur de Gran Bretaña,
  Finisterre, Estaca de Bares, Tarifa, sur de Italia, Kanyakumari, Cabo York,
  Agulhas, Cabo Froward…). Así se absorbe la distorsión del dibujo.
- Partiendo del centroide real de cada país, el punto se ajusta a la tierra
  dibujada más cercana cuando hace falta (Japón y Corea están desplazados en
  el dibujo respecto a su posición real).
- La chincheta (`assets/pin.png`) se ancla **por la punta**
  (`transform: translate(-50%, -100%)`), así que la punta marca la coordenada.

## Pendiente de completar

- Descripción real del podcast (sección "Sobre").

## Desarrollo

Es un sitio estático sin build step. Para desarrollar, usa el servidor incluido:

```bash
python3 serve.py 8765 .
```

Es `http.server` con cabeceras anti-caché. Son necesarias: sin ellas el
navegador se queda con el CSS/JS antiguo tras cada cambio y no hay forma de
refrescarlo salvo cambiando de puerto.
