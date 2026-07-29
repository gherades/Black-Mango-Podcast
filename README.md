# Black Mango Podcast

Sitio estático (HTML/CSS/JS) inspirado en el estilo visual de
[blackmangofilms.com](https://blackmangofilms.com/).

## Datos del podcast

- Logo/portada (`assets/spotify-cover-hq.jpg`) y episodios
  (`assets/series-data.js`) obtenidos del show real en Spotify:
  https://open.spotify.com/show/0WEqNybNBwZPZTM1V1iG2i
- Lista completa: 97 episodios únicos en Spotify, del #103 hasta el "Episodio 1 |
  Indonesia" (el listado del reproductor web usa scroll infinito con
  virtualización, no solo el botón "Cargar más episodios" — hay que hacer
  scroll hasta el final, donde aparece la sección "Más pódcasts como este",
  para que cargue todo). El "Episodio 12" tenía dos versiones en Spotify (una
  de pago); se dejó solo la gratuita, con "| Daniel Sancho" añadido al título.
- Los episodios 4-8 nunca estuvieron en Spotify/Apple/iVoox, solo en YouTube
  (`url`, `appleUrl` e `ivooxUrl` vacíos, solo `ytUrl`). Se añadieron a mano
  a partir de la playlist de YouTube. Total del sitio: 103 episodios.
- La sección "Episodios" agrupa los capítulos en tres pestañas, usando
  `assets/series-data.js` (la única fuente de datos que carga la página):
  - **Series**: capítulos que forman parte de una saga numerada dentro del
    título (p.ej. "Crímenes Imperfectos 3", "Catástrofes Aéreas 5"), más
    agrupaciones temáticas sin número explícito (Mitología, La Mafia, Los
    Terribles — este último para títulos que contienen "terrible"/"terribles"
    y no pertenecen ya a una saga numerada como Historias Terribles).
  - **Documentales**: los 7 vídeos de la playlist de YouTube
    `PLGR6l-llOTj52NWifz_9red7xPk-56WDf`, contenido aparte de los episodios
    numerados (array `DOCUMENTALES`, solo tienen `ytUrl`).
  - **Todos**: series y episodios sueltos juntos, ordenados por número.
  - Si creas una serie nueva a mano en `SERIES`, añade también su palabra
    clave en `SERIES_KEYWORDS` (`scripts/check_new_episodes.py`) — si no,
    el script de episodios automáticos (ver más abajo) no reconocerá esa
    serie y avisará por consola en cada ejecución mientras falte.
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

## Episodios nuevos automáticos

`.github/workflows/check-new-episodes.yml` ejecuta `scripts/check_new_episodes.py`
todos los lunes (y también se puede lanzar a mano desde la pestaña Actions,
botón "Run workflow"). El script:

1. Compara el RSS oficial del show (`https://anchor.fm/s/e0c735b8/podcast/rss`)
   contra los `epnum` que ya hay en `series-data.js`.
2. Para cada episodio nuevo, busca su enlace en Apple Podcasts (API de
   iTunes), YouTube (feed público del canal, sin API key) e iVoox. iVoox no
   tiene API pública, así que su enlace se extrae del HTML de la página 1
   del propio podcast en ivoox.com — como un episodio recién detectado es,
   por definición, de los últimos publicados, siempre está ahí (no hace
   falta recorrer la paginación). Si alguna plataforma aún no ha indexado
   el episodio (pasa a veces si es muy reciente), ese campo se deja en
   blanco para completar a mano.
3. Clasifica el título por palabras clave contra las series existentes
   (`SERIES_KEYWORDS` en el script). Si no reconoce ninguna Y el título tiene
   pinta de arrancar una saga nueva (frase en mayúsculas + número, como
   "ROBOS IMPOSIBLES 1"), lo añade igualmente como suelto pero marcado con un
   comentario `// NECESITA REVISIÓN` — y todo el lote de ese run se manda por
   Pull Request en vez de directo a `main`, para que alguien decida si hace
   falta agrupar o renombrar algo (igual que se ha hecho siempre a mano en
   este proyecto).
4. Si todo lo del lote se clasificó con confianza, se compromete y se sube
   directo a `main`.

Para probarlo en local sin tocar nada: `python3 scripts/check_new_episodes.py --dry-run`.

## Tests

Dos suites independientes, cada una con las herramientas mínimas de su
ecosistema — nada que el sitio en sí necesite en producción.

### Python (`scripts/check_new_episodes.py`)

```bash
python3 -m unittest scripts.test_check_new_episodes -v
```

40 tests, cero llamadas de red reales: `fetch()` (el único punto por el que
pasan Spotify/Apple/YouTube/iVoox) se mockea siempre con `unittest.mock`,
así que la suite es determinista y corre en milisegundos. Incluye una
prueba de extremo a extremo de `main()` completo (RSS → clasificar →
escribir → resumen JSON) contra copias temporales de
`series-data.js`/`index.html`, nunca los archivos reales.

Cobertura medida de verdad (no un número inventado):

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m coverage run -m unittest scripts.test_check_new_episodes
python3 -m coverage report -m --include='scripts/check_new_episodes.py'
```

**98%** (181/184 líneas). Las 3 líneas sin cubrir son el fallback de
`certifi` cuando no está instalado (depende del entorno de quien ejecute
el test) y el `if __name__ == "__main__":` final — ambas de bajo valor
para testear y se dejan así a propósito, no por descuido.

### JavaScript (`script.js`)

```bash
npm install
npm test
```

27 tests con el runner nativo de Node (`node:test` + `node:assert`, cero
frameworks) y `jsdom` como única dependencia de desarrollo (no se usa en
producción: `index.html` sigue cargando `script.js` con un `<script>`
normal, sin build step). Dos niveles:

- **Unitarios rápidos** (`test/pure.test.js`, `test/dom.test.js`): cada
  función de `script.js` con datos de mentira pequeños y a medida.
  Las funciones que solo construyen HTML como texto (`escapeHtml`,
  `episodeItemHTML`...) se cargan con `vm` y un `document` de mentira —
  no hace falta jsdom para ellas. Las que tocan el DOM de verdad
  (`renderMap`, `initTabs`...) sí usan jsdom.
- **Un test de integración** (`test/integration.test.js`): carga el
  `index.html` + `series-data.js` + `map-data.js` + `script.js` **reales**
  juntos, para detectar desajustes de cableado entre ellos que los tests
  unitarios (con sus propios datos) no pueden ver. A propósito hay solo
  uno — la pirámide de tests no necesita más para un sitio de este tamaño.

**Sobre medir cobertura de `script.js`**: `node --test --experimental-test-coverage`
y `c8` no le atribuyen líneas cubiertas, aunque los tests sí lo ejecuten de
verdad. La causa es cómo se carga: `script.js` no es un módulo (no tiene
`export`, es JS de toda la vida pensado para un `<script>` normal), así que
los tests lo cargan con `vm`/`eval` en vez de `require()` — y V8 no asocia
ese código evaluado dinámicamente con el archivo en disco para el reporte
de cobertura, aunque internamente sí sepa qué se ejecutó (se puede
comprobar leyendo el JSON crudo de `NODE_V8_COVERAGE`). Convertir
`script.js` en un módulo real arreglaría esto, pero sería cambiar la
arquitectura del sitio solo para complacer una herramienta — no vale la
pena. La cobertura real, verificada a mano: **las 11 funciones de
`script.js` tienen al menos un test dedicado**, varias con casos de borde
explícitos (título con HTML, plataforma sin enlace, sin datos definidos).

### CI

`.github/workflows/tests.yml` corre ambas suites en cada push y Pull
Request a `main` (con cobertura de Python exigida ≥90%) — independiente
del workflow semanal de episodios nuevos, que solo corre su propio test
de regresión antes de tocar nada (ver más abajo).

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
