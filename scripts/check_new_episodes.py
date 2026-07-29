#!/usr/bin/env python3
"""Busca episodios nuevos del podcast y los añade a assets/series-data.js.

Fuentes (todas públicas, sin credenciales):
  - Spotify: el RSS oficial del show (vía Anchor/Spotify for Podcasters).
    Es la fuente de verdad para "qué episodios existen" — da número, título,
    fecha y un enlace público para escuchar.
  - Apple Podcasts: API de búsqueda de iTunes (episodio por episodio).
  - YouTube: feed público Atom del canal (sin API key, solo los últimos 15
    vídeos, pero eso basta para detectar episodios nuevos).
  - iVoox no tiene API pública: se extrae del HTML de la página 1 del propio
    podcast en ivoox.com (mismo sitio de donde se sacaron a mano los enlaces
    existentes, ver README). Solo hace falta la página 1: un episodio recién
    detectado como nuevo es, por definición, de los últimos publicados.

Cada episodio nuevo se clasifica por palabras clave contra las series ya
existentes en SERIES. Si no encaja en ninguna, se añade a
STANDALONE_EPISODES (igual que se ha hecho siempre a mano en este proyecto:
mejor dejarlo suelto que adivinar mal una serie).

Si el título sugiere el arranque de una saga nueva (una frase en mayúsculas
seguida de un número, como "ROBOS IMPOSIBLES 1") que no coincide con ninguna
serie conocida, el episodio se añade igualmente como suelto pero marcado con
un comentario "// NECESITA REVISIÓN: ...", y todo el lote de ese run se
manda por Pull Request en vez de directo a main (campo "route" en el
resumen JSON de la salida) — así el PR tiene un cambio real que revisar.

Uso:
  python3 scripts/check_new_episodes.py            # aplica los cambios
  python3 scripts/check_new_episodes.py --dry-run  # solo informa, no toca nada
"""
import json
import re
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    # en macOS el Python de python.org no siempre enlaza con el almacén de
    # certificados del sistema; si certifi está instalado, se usa su bundle.
    # En el runner de GitHub Actions (Ubuntu) esto no hace falta.
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = None

ROOT = Path(__file__).resolve().parent.parent
SERIES_DATA = ROOT / "assets" / "series-data.js"
INDEX_HTML = ROOT / "index.html"

SPOTIFY_RSS = "https://anchor.fm/s/e0c735b8/podcast/rss"
APPLE_SHOW_ID = "1726276206"
YOUTUBE_CHANNEL_ID = "UCL1ITQtr7ogwPN-5w96kG7Q"
IVOOX_PODCAST_URL = "https://www.ivoox.com/podcast-black-mango-podcast_sq_f12370133_1.html"

UA = "Mozilla/5.0 (compatible; BlackMangoEpisodeChecker/1.0)"

# Palabras clave -> serie existente. Deliberadamente específicas: es mejor
# dejar un episodio como suelto (para que alguien lo agrupe a mano después,
# como se ha hecho siempre en este proyecto) que meterlo en la serie
# equivocada por una coincidencia demasiado genérica.
SERIES_KEYWORDS = [
    (r"historias terribles", "Historias Terribles"),
    (r"cr[ií]menes sin resolver", "Crímenes Sin Resolver"),
    (r"mitolog[ií]a", "Mitología"),
    (r"mafia", "La Mafia"),
    (r"cr[ií]menes imperfectos", "Crímenes Imperfectos"),
    (r"cat[aá]strofes a[eé]reas", "Catástrofes Aéreas"),
    (r"asesinos en serie", "Asesinos en Serie"),
    (r"\bdios\b|jes[uú]s|nazaret", "Religión"),
    (r"la antigua", "La Antigua Civilización"),
    (r"robos imposibles", "Robos Imposibles"),
    (r"experimentos m[eé]dicos", "Experimentos Médicos Terribles"),
    (r"fugas imposibles", "Fugas Imposibles"),
    (r"secta", "Las Peores Sectas de la Historia"),
    (r"\bterrible", "Los Terribles"),
]

# Detecta "FRASE EN MAYÚSCULAS + número" (el patrón que usan los nombres de
# saga: "Robos Imposibles 1", "Catástrofes Aéreas 5"...). Si aparece una
# frase así y no matchea ninguna keyword de arriba, probablemente sea el
# arranque de una serie nueva: mejor pedir revisión humana.
NEW_SAGA_PATTERN = re.compile(r"\b([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ]{5,40})\s+(\d{1,2})\b")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CONTEXT) as r:
        return r.read()


def get_spotify_episodes():
    """Devuelve [(epnum, title, spotify_url, pubdate)] desde el RSS oficial."""
    xml_bytes = fetch(SPOTIFY_RSS)
    root = ET.fromstring(xml_bytes)
    out = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        m = re.search(r"#(\d+)", title)
        if not m:
            continue
        epnum = int(m.group(1))
        link = (item.findtext("link") or "").strip()
        pubdate = (item.findtext("pubDate") or "").strip()
        out.append((epnum, title, link, pubdate))
    return out


def get_apple_url(epnum):
    try:
        data = json.loads(fetch(
            f"https://itunes.apple.com/lookup?id={APPLE_SHOW_ID}"
            f"&entity=podcastEpisode&limit=200"
        ))
    except Exception:
        return ""
    needle = f"#{epnum} "
    needle_alt = f"#{epnum}-"
    for r in data.get("results", []):
        if r.get("kind") != "podcast-episode":
            continue
        name = r.get("trackName", "")
        if needle in name or needle_alt in name or name.rstrip().endswith(f"#{epnum}"):
            url = r.get("trackViewUrl", "")
            # normaliza a la locale española y sin el parámetro de tracking,
            # para que quede igual que el resto de enlaces del sitio
            url = url.replace("/us/podcast/", "/es/podcast/")
            url = re.sub(r"&uo=\d+$", "", url)
            return url
    return ""


def get_youtube_url(epnum):
    try:
        xml_bytes = fetch(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        )
    except Exception:
        return ""
    ns = {"yt": "http://www.youtube.com/xml/schemas/2015",
          "atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_bytes)
    needle = f"#{epnum} "
    needle_alt = f"#{epnum}-"
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns)
        if needle in title or needle_alt in title or title.rstrip().endswith(f"#{epnum}"):
            vid = entry.findtext("yt:videoId", default="", namespaces=ns)
            if vid:
                return f"https://www.youtube.com/watch?v={vid}"
    return ""


def get_ivoox_url(epnum):
    try:
        html = fetch(IVOOX_PODCAST_URL).decode("utf-8", errors="replace")
    except Exception:
        return ""
    # el guion justo después del número evita que "105" case con "1050":
    # si el siguiente carácter no es "-", no es el mismo episodio.
    m = re.search(rf'href="(/black-mango-{epnum}-[a-z0-9-]*_rf_\d+_1\.html)"', html)
    if m:
        return "https://www.ivoox.com" + m.group(1)
    return ""


def existing_epnums(series_js_text):
    return {int(n) for n in re.findall(r"epnum:\s*(\d+)", series_js_text)}


def series_names_in_data(series_js_text):
    return re.findall(r'\{ name: "([^"]+)", episodes: \[', series_js_text)


def warn_uncovered_series(series_js_text):
    """SERIES_KEYWORDS es una lista mantenida a mano, aparte de SERIES.

    Si alguien crea una serie nueva a mano en series-data.js y no añade su
    palabra clave aquí, los episodios futuros de esa serie no se
    reconocerán (caerán como sueltos, sin romper nada — pero en silencio).
    Este chequeo hace el desfase visible en vez de silencioso: se imprime
    en cada ejecución, no solo cuando hay episodios nuevos que clasificar.
    """
    covered = {name for _, name in SERIES_KEYWORDS}
    existing = series_names_in_data(series_js_text)
    sin_cubrir = [n for n in existing if n not in covered]
    if sin_cubrir:
        print(
            "AVISO: estas series de series-data.js no tienen ninguna palabra "
            "clave en SERIES_KEYWORDS — sus episodios futuros no se "
            "reconocerán automáticamente:"
        )
        for n in sin_cubrir:
            print(f"  - {n}")
    return sin_cubrir


def classify(title):
    """Devuelve (nombre_de_serie_o_None, necesita_revision, motivo)."""
    low = title.lower()
    for pattern, series_name in SERIES_KEYWORDS:
        if re.search(pattern, low):
            return series_name, False, None

    m = NEW_SAGA_PATTERN.search(title)
    if m:
        phrase = m.group(1).strip()
        return None, True, (
            f"El título sugiere una posible serie nueva (\"{phrase} {m.group(2)}\") "
            f"que no coincide con ninguna serie existente. Podría ser el episodio "
            f"{m.group(2)} de una saga que aún no está en el sitio, o simplemente "
            f"un episodio suelto — hace falta un vistazo humano."
        )
    return None, False, None


def js_string(value):
    """Escapa un valor como literal de string de JS/JSON válido.

    Los títulos vienen de un feed externo (no de confianza): si alguno
    trajera unas comillas dobles sin escapar, una interpolación ingenua
    (f'"{title}"') rompería la sintaxis de todo series-data.js y se
    caería el sitio entero. json.dumps produce un literal de string
    válido tanto en JSON como en JS.
    """
    return json.dumps(value, ensure_ascii=False)


def js_episode_entry(epnum, title, spotify_url, apple_url, ivoox_url, yt_url, indent="    "):
    parts = [f'epnum: {epnum}', f'title: {js_string(title)}', f'url: {js_string(spotify_url)}',
              f'appleUrl: {js_string(apple_url)}', f'ivooxUrl: {js_string(ivoox_url)}', f'ytUrl: {js_string(yt_url)}']
    return indent + "{ " + ", ".join(parts) + " },"


def insert_into_standalone(series_js_text, entry_line, comment=None):
    marker = "const STANDALONE_EPISODES = ["
    pos = series_js_text.find(marker)
    if pos == -1:
        raise RuntimeError(f"no se encontró '{marker}' en series-data.js")
    idx = pos + len(marker)
    prefix = f"\n    // {comment}" if comment else ""
    return series_js_text[:idx] + prefix + "\n" + entry_line + series_js_text[idx:]


def update_episode_count_note(series_js_text):
    """Recalcula el texto "N episodios (M de ellos solo en YouTube)." del HTML."""
    total = len(re.findall(r"epnum:\s*\d+", series_js_text))
    youtube_only = len(re.findall(r'url:\s*""[^}]*ivooxUrl:\s*""', series_js_text))
    html = INDEX_HTML.read_text(encoding="utf-8")
    new_html, n = re.subn(
        r"\d+ episodios \(\d+ de ellos solo disponibles en YouTube\)\.",
        f"{total} episodios ({youtube_only} de ellos solo disponibles en YouTube).",
        html,
    )
    if n == 1:
        INDEX_HTML.write_text(new_html, encoding="utf-8")
        print(f"  index.html actualizado: {total} episodios, {youtube_only} solo en YouTube")
    else:
        # antes esto fallaba en silencio: si el texto de index.html cambiara
        # de forma (o el patrón dejara de encajar), el contador simplemente
        # se quedaría desactualizado sin ningún aviso en el log.
        print(
            f"AVISO: no se pudo actualizar el contador de episodios en index.html "
            f"(se esperaba encontrar el texto exactamente 1 vez, se encontró {n})."
        )


def insert_into_series(series_js_text, series_name, entry_line):
    pattern = re.compile(
        r'(\{ name: "' + re.escape(series_name) + r'", episodes: \[)(.*?)(\n  \] \})',
        re.S,
    )
    def repl(m):
        # group(3) (el cierre "\n  ] }") se reinserta TAL CUAL, sin tocarlo.
        # Antes se reconstruía a mano ("\n " + group(3)[1:]) y colaba un
        # espacio de más en cada llamada. Con dos episodios nuevos de la
        # misma serie en un mismo run, la 2ª llamada ya no encontraba el
        # cierre de 2 espacios (ahora eran 3) y el ".*?" no-greedy se comía
        # de un tirón la serie entera hasta el cierre de la SIGUIENTE serie
        # sin tocar — fusionando dos series en una silenciosamente.
        return m.group(1) + m.group(2) + "\n" + entry_line + m.group(3)
    new_text, n = pattern.subn(repl, series_js_text, count=1)
    if n != 1:
        raise RuntimeError(f"no se encontró la serie '{series_name}' en series-data.js")
    return new_text


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Consultando el RSS de Spotify: {SPOTIFY_RSS}")
    feed_episodes = get_spotify_episodes()
    print(f"  {len(feed_episodes)} episodios en el feed")

    series_js_text = SERIES_DATA.read_text(encoding="utf-8")
    known = existing_epnums(series_js_text)
    print(f"  {len(known)} episodios ya en series-data.js (más alto: #{max(known)})")
    warn_uncovered_series(series_js_text)

    new_ones = sorted(
        (ep for ep in feed_episodes if ep[0] not in known),
        key=lambda e: e[0],
    )
    if not new_ones:
        print("No hay episodios nuevos. Nada que hacer.")
        print("\n=== RESUMEN JSON ===")
        print(json.dumps({"added": [], "needs_review": [], "route": "none"}, ensure_ascii=False))
        return 0

    added = []
    needs_review = []

    for epnum, title, spotify_url, pubdate in new_ones:
        print(f"\n#{epnum}: {title}")
        series_name, review, reason = classify(title)

        apple_url = get_apple_url(epnum)
        ivoox_url = get_ivoox_url(epnum)
        yt_url = get_youtube_url(epnum)
        print(f"  Spotify: {spotify_url}")
        print(f"  Apple:   {apple_url or '(no encontrado todavía)'}")
        print(f"  iVoox:   {ivoox_url or '(no encontrado todavía)'}")
        print(f"  YouTube: {yt_url or '(no encontrado todavía)'}")

        entry_line = js_episode_entry(epnum, title, spotify_url, apple_url, ivoox_url, yt_url)

        if review:
            # se inserta igualmente (como suelto, la ubicación segura por
            # defecto) pero marcado con un comentario, para que el PR tenga
            # un cambio real que revisar y no solo un aviso en el aire.
            # El prefijo "NECESITA REVISIÓN" tiene que quedar literalmente
            # en el archivo (no solo en este print): es lo que hace el
            # comentario greppable en el diff del PR, y es lo que el propio
            # cuerpo del PR (ver el workflow) le dice a quien lo revise que
            # busque.
            print(f"  -> NECESITA REVISIÓN: {reason}")
            series_js_text = insert_into_standalone(
                series_js_text, entry_line, comment=f"NECESITA REVISIÓN: {reason}"
            )
            needs_review.append((epnum, title, reason))
        elif series_name:
            print(f"  -> clasificado en la serie existente '{series_name}'")
            series_js_text = insert_into_series(series_js_text, series_name, entry_line)
        else:
            print("  -> sin serie reconocida, se añade como episodio suelto")
            series_js_text = insert_into_standalone(series_js_text, entry_line)

        added.append((epnum, title, series_name))

    if dry_run:
        print("\n--dry-run: no se ha escrito ni comprometido nada.")
    else:
        SERIES_DATA.write_text(series_js_text, encoding="utf-8")
        print(f"\nEscrito {SERIES_DATA} con {len(added)} episodio(s) nuevo(s).")
        update_episode_count_note(series_js_text)

    # resumen máquina-legible para el workflow de GitHub Actions: si algo
    # necesitó revisión, el lote entero de este run se manda por PR en vez
    # de ir directo a main (ver .github/workflows/check-new-episodes.yml)
    summary = {
        "added": [{"epnum": e, "title": t, "series": s} for e, t, s in added],
        "needs_review": [{"epnum": e, "title": t, "reason": r} for e, t, r in needs_review],
        "route": "pull_request" if needs_review else "main",
    }
    print("\n=== RESUMEN JSON ===")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
