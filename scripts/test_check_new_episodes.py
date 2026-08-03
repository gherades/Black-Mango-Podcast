#!/usr/bin/env python3
"""Suite de tests para scripts/check_new_episodes.py.

unittest + unittest.mock, ambos de librería estándar — cero dependencias
nuevas, consistente con el resto del proyecto. Ninguna llamada de red real:
fetch() se mockea siempre, así que estos tests son deterministas y rápidos.

Uso:
  python3 -m unittest scripts.test_check_new_episodes -v
  python3 scripts/test_check_new_episodes.py            # equivalente

Cobertura (ver "coverage" más abajo para medirla de verdad):
  python3 -m coverage run -m unittest scripts.test_check_new_episodes
  python3 -m coverage report -m --include='scripts/check_new_episodes.py'
"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import check_new_episodes as cne  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REAL_SERIES_DATA = ROOT / "assets" / "series-data.js"


# ---------------------------------------------------------------------------
# Fixtures de red: bytes crudos que fetch() devolvería para cada fuente.
# Deliberadamente mínimos (no son los feeds reales) para que los tests no
# dependan de que Spotify/Apple/YouTube sigan devolviendo lo mismo mañana.
# ---------------------------------------------------------------------------

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item><title>Black Mango #105 - LA MAFIA SUIZA | episodio de prueba</title>
<link>https://podcasters.spotify.com/pod/x105</link>
<pubDate>Mon, 05 Jan 2026 13:00:00 GMT</pubDate><guid>guid-105</guid></item>
<item><title>Black Mango #104 - CIVILIZACIONES PERDIDAS | ya existente</title>
<link>https://podcasters.spotify.com/pod/x104</link>
<pubDate>Fri, 24 Jul 2026 13:00:00 GMT</pubDate><guid>guid-104</guid></item>
<item><title>Sin numero de episodio, se debe ignorar</title>
<link>https://podcasters.spotify.com/pod/xNaN</link>
<pubDate>Mon, 01 Jan 2020 00:00:00 GMT</pubDate><guid>guid-nan</guid></item>
</channel></rss>"""

ITUNES_FIXTURE = json.dumps({
    "results": [
        # la API real siempre devuelve el show en sí como resultado 0, con
        # kind="podcast" (no "podcast-episode") — get_apple_url() debe
        # saltárselo sin liarse.
        {"kind": "podcast", "trackName": "Black Mango Podcast"},
        {"kind": "podcast-episode", "trackName": "Black Mango #105 - LA MAFIA SUIZA | episodio de prueba",
         "trackViewUrl": "https://podcasts.apple.com/us/podcast/black-mango-105/id1726276206?i=1000900000105&uo=4"},
        {"kind": "podcast-episode", "trackName": "Black Mango #104 - CIVILIZACIONES PERDIDAS",
         "trackViewUrl": "https://podcasts.apple.com/us/podcast/black-mango-104/id1726276206?i=1000900000104&uo=4"},
    ]
})

YOUTUBE_FIXTURE = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
<entry><title>Black Mango #105 - LA MAFIA SUIZA | episodio de prueba</title>
<yt:videoId>videoId105</yt:videoId></entry>
<entry><title>Black Mango #104 - CIVILIZACIONES PERDIDAS</title>
<yt:videoId>videoId104</yt:videoId></entry>
</feed>"""

# HTML mínimo con la forma real de la página del podcast en ivoox.com (solo
# los <a href> importan: get_ivoox_url() no mira nada más). Incluye el "105"
# junto a un "1050" a propósito: si la regexp no exigiera el guion justo
# después del número, "105" encajaría por error dentro de "1050".
IVOOX_FIXTURE = """<html><body>
<a href="/black-mango-105-la-mafia-suiza-audios-mp3_rf_178000105_1.html">#105</a>
<a href="/black-mango-104-civilizaciones-perdidas-los-audios-mp3_rf_177850316_1.html">#104</a>
<a href="/black-mango-1050-episodio-trampa-audios-mp3_rf_999999_1.html">trampa numérica</a>
</body></html>"""


def fake_fetch(url):
    """side_effect de fetch(): responde según qué endpoint se pida."""
    if "anchor.fm" in url:
        return RSS_FIXTURE.encode("utf-8")
    if "itunes.apple.com" in url:
        return ITUNES_FIXTURE.encode("utf-8")
    if "youtube.com/feeds" in url:
        return YOUTUBE_FIXTURE.encode("utf-8")
    if "ivoox.com" in url:
        return IVOOX_FIXTURE.encode("utf-8")
    raise AssertionError(f"URL no esperada en un test: {url}")


def silent(fn, *a, **kw):
    """Ejecuta fn ocultando su stdout, y devuelve (resultado, texto_impreso)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*a, **kw)
    return result, buf.getvalue()


# ---------------------------------------------------------------------------

class ClassifyTests(unittest.TestCase):
    """classify(): la única regla de negocio real del proyecto."""

    CASOS_SERIE_EXISTENTE = [
        ('Black Mango #103 - CRÍMENES IMPERFECTOS 5 | Los 4 de Idaho', 'Crímenes Imperfectos'),
        ('Black Mango #102 – CATÁSTROFES AÉREAS 5 | El secuestro imposible', 'Catástrofes Aéreas'),
        ('Black Mango #98 - Asesinos en Serie 4 - Jeffrey Dahmer', 'Asesinos en Serie'),
        ('Black Mango #34 - Historias Terribles 3 | CAZA DE BRUJAS', 'Historias Terribles'),
        ('Black Mango #63 - LA TERRIBLE CUBA | Fidel Castro', 'Los Terribles'),
        ('Black Mango #101 - LA MAFIA CHINA | Las Tríadas', 'La Mafia'),
        ('Black Mango #62 - Mitología CHINA | EL REY MONO WUKONG', 'Mitología'),
        ('Black Mango #78 - LA ANTIGUA CHINA | Conspiraciones', 'La Antigua Civilización'),
        ('Black Mango #97 - Los SECRETOS de DIOS | Las Historias más terribles', 'Religión'),
        ('Black Mango #43 - LAS PEORES SECTAS DE LA HISTORIA', 'Las Peores Sectas de la Historia'),
    ]

    def test_reconoce_series_existentes_por_palabra_clave(self):
        for title, esperado in self.CASOS_SERIE_EXISTENTE:
            with self.subTest(title=title):
                serie, review, _ = cne.classify(title)
                self.assertEqual(serie, esperado)
                self.assertFalse(review)

    def test_episodio_sin_patron_de_serie_queda_suelto(self):
        for title in ('Black Mango #1 - Indonesia',
                       'Black Mango #104 - CIVILIZACIONES PERDIDAS | Los mayores misterios'):
            with self.subTest(title=title):
                serie, review, reason = cne.classify(title)
                self.assertIsNone(serie)
                self.assertFalse(review)
                self.assertIsNone(reason)

    def test_frase_en_mayusculas_mas_numero_pide_revision(self):
        for title in ('Black Mango #110 - ASESINATOS EN EL METAVERSO 1 | Un caso real',
                       'Black Mango #111 - EL ARTE DEL ENGAÑO 2 | Estafas legendarias'):
            with self.subTest(title=title):
                serie, review, reason = cne.classify(title)
                self.assertIsNone(serie)
                self.assertTrue(review)
                self.assertIn(title.split(' - ', 1)[1].rsplit(' ', 1)[0].split(' |')[0][:6], reason)

    def test_keyword_gana_a_pesar_de_tener_forma_de_saga_nueva(self):
        # "LA MAFIA SUIZA" tiene forma de "MAYUSCULAS + episodio suelto" pero
        # "mafia" ya es una keyword existente: debe ganar la serie, no la
        # revisión (SERIES_KEYWORDS se comprueba antes que NEW_SAGA_PATTERN).
        serie, review, _ = cne.classify('Black Mango #105 - LA MAFIA SUIZA | episodio de prueba')
        self.assertEqual(serie, 'La Mafia')
        self.assertFalse(review)

    def test_caso_documentado_sin_arreglo_titulo_en_minusculas_no_activa_revision(self):
        # Limitación conocida y aceptada (ver auditoría): NEW_SAGA_PATTERN
        # solo reconoce frases en TODO MAYUSCULAS, como las usa el podcast
        # de verdad. Si algún día publican una saga nueva en "Title Case" el
        # episodio cae como suelto SIN aviso de revisión — no rompe nada
        # (sigue siendo el fallback seguro) pero no hay red de aviso extra.
        # Este test documenta el comportamiento actual, no lo corrige.
        serie, review, _ = cne.classify('Black Mango #205 - Estafas Legendarias 1 | El timo del siglo')
        self.assertIsNone(serie)
        self.assertFalse(review)


class EscapingTests(unittest.TestCase):
    """js_string(): el fallo que habría tumbado el sitio entero."""

    def test_produce_un_literal_reversible(self):
        peligroso = 'Título con "comillas", barra\\ y <script>alert(1)</script>'
        self.assertEqual(json.loads(cne.js_string(peligroso)), peligroso)

    def test_escapa_comillas_dobles(self):
        self.assertIn('\\"', cne.js_string('con "comillas"'))

    def test_cadena_vacia(self):
        self.assertEqual(cne.js_string(""), '""')


class JsEpisodeEntryTests(unittest.TestCase):
    def test_genera_un_objeto_js_bien_formado_y_parseable(self):
        entry = cne.js_episode_entry(999, 'Título "raro"', "https://s", "https://a", "https://i", "https://y")
        self.assertTrue(entry.strip().startswith("{ epnum: 999,"))
        self.assertTrue(entry.rstrip().endswith("},"))
        self.assertIn('ivooxUrl: "https://i"', entry)

    def test_ivoox_no_encontrado_queda_vacio_igual_que_las_demas_plataformas(self):
        entry = cne.js_episode_entry(999, "Título", "https://s", "", "", "")
        self.assertIn('ivooxUrl: ""', entry)


class SeriesDataMutationTests(unittest.TestCase):
    """Las funciones que reescriben series-data.js como texto.

    Todas contra una copia en memoria de los datos REALES (solo lectura de
    disco, nunca se escribe el archivo real desde un test).
    """

    @classmethod
    def setUpClass(cls):
        cls.real_text = REAL_SERIES_DATA.read_text(encoding="utf-8")

    def test_insert_into_standalone_antepone_la_entrada(self):
        entry = cne.js_episode_entry(999, "Test", "", "", "", "")
        result = cne.insert_into_standalone(self.real_text, entry)
        marker = "const STANDALONE_EPISODES = ["
        pos = result.index(marker) + len(marker)
        # la nueva entrada debe ser lo primero tras el marcador
        self.assertIn("epnum: 999", result[pos:pos + 200])

    def test_insert_into_standalone_con_comentario_de_revision(self):
        entry = cne.js_episode_entry(999, "Test", "", "", "", "")
        result = cne.insert_into_standalone(self.real_text, entry, comment="motivo de prueba")
        self.assertIn("// motivo de prueba", result)
        self.assertLess(result.index("// motivo de prueba"), result.index("epnum: 999"))

    def test_insert_into_standalone_falla_con_mensaje_claro_si_falta_el_marcador(self):
        with self.assertRaises(RuntimeError) as ctx:
            cne.insert_into_standalone("sin ningún marcador aquí", "x")
        self.assertIn("STANDALONE_EPISODES", str(ctx.exception))

    def test_insert_into_series_coloca_la_entrada_en_la_serie_correcta(self):
        entry = cne.js_episode_entry(999, "Black Mango #999 - test", "", "", "", "")
        result = cne.insert_into_series(self.real_text, "La Mafia", entry)
        bloque = result[result.index('name: "La Mafia"'):result.index('] },', result.index('name: "La Mafia"'))]
        self.assertIn("#999", bloque)

    def test_insert_into_series_serie_inexistente_lanza_error_claro(self):
        with self.assertRaises(RuntimeError) as ctx:
            cne.insert_into_series(self.real_text, "Serie Que No Existe", "x")
        self.assertIn("Serie Que No Existe", str(ctx.exception))

    def test_regresion_dos_episodios_nuevos_de_la_misma_serie_en_un_run(self):
        """Bug real encontrado inspeccionando una ejecución en producción:
        insert_into_series() reconstruía el cierre "] }" con un espacio de
        más, así que la 2ª llamada en el mismo run no lo reconocía y el
        regex no-greedy se comía la siguiente serie entera. Sin este test,
        el bug volvería a colarse la próxima vez que alguien "simplifique"
        esa función.
        """
        series_antes = cne.series_names_in_data(self.real_text)
        idx_mafia = series_antes.index("La Mafia")
        siguiente_serie = series_antes[idx_mafia + 1]

        t = self.real_text
        e1 = cne.js_episode_entry(901, "Black Mango #901 - LA MAFIA DE PRUEBA UNO | test", "https://s/1", "", "", "")
        e2 = cne.js_episode_entry(902, "Black Mango #902 - LA MAFIA DE PRUEBA DOS | test", "https://s/2", "", "", "")
        t = cne.insert_into_series(t, "La Mafia", e1)
        t = cne.insert_into_series(t, "La Mafia", e2)

        self.assertEqual(cne.series_names_in_data(t), series_antes,
                          "la lista de series cambió: alguna se fusionó con otra")
        bloque_mafia = t[t.index('name: "La Mafia"'):t.index(f'name: "{siguiente_serie}"')]
        self.assertIn("#901", bloque_mafia)
        self.assertIn("#902", bloque_mafia)

    def test_existing_epnums_extrae_todos_los_numeros(self):
        nums = cne.existing_epnums(self.real_text)
        self.assertIsInstance(nums, set)
        self.assertIn(1, nums)
        self.assertIn(104, nums)
        self.assertNotIn(999, nums)

    def test_series_names_in_data_devuelve_las_14_series_reales(self):
        nombres = cne.series_names_in_data(self.real_text)
        self.assertEqual(len(nombres), 14)
        self.assertIn("La Mafia", nombres)

    def test_warn_uncovered_series_no_avisa_con_los_datos_reales(self):
        # si esto falla, alguien añadió una serie a mano sin su keyword
        sin_cubrir, _ = silent(cne.warn_uncovered_series, self.real_text)
        self.assertEqual(sin_cubrir, [])

    def test_warn_uncovered_series_detecta_una_serie_sin_keyword(self):
        simulado = ('{ name: "Los Terribles", episodes: [] },\n'
                    '{ name: "Una Serie Sin Keyword", episodes: [] },')
        sin_cubrir, salida = silent(cne.warn_uncovered_series, simulado)
        self.assertEqual(sin_cubrir, ["Una Serie Sin Keyword"])
        self.assertIn("Una Serie Sin Keyword", salida)


class NetworkParsingTests(unittest.TestCase):
    """get_spotify_episodes / get_apple_url / get_youtube_url / get_ivoox_url.

    get_apple_url/get_youtube_url/get_ivoox_url ya NO llaman a fetch() por
    su cuenta (ver fetch_optional y main): reciben el contenido ya
    descargado como argumento, así que estos tests lo pasan directamente
    desde los fixtures, sin mockear nada. Sí se mockea fetch() para
    get_spotify_episodes (esa sigue llamando a fetch() ella misma) y para
    fetch_optional en su propia clase de tests, más abajo.
    """

    @patch("check_new_episodes.fetch", side_effect=fake_fetch)
    def test_get_spotify_episodes_extrae_numero_titulo_y_enlace(self, _mock):
        episodios = cne.get_spotify_episodes()
        self.assertEqual(len(episodios), 2)  # el 3º item del fixture no tiene "#N"
        epnum, title, link, pubdate = episodios[0]
        self.assertEqual(epnum, 105)
        self.assertIn("LA MAFIA SUIZA", title)
        self.assertTrue(link.startswith("https://"))

    def test_get_apple_url_encuentra_el_episodio_por_numero(self):
        url = cne.get_apple_url(105, ITUNES_FIXTURE.encode("utf-8"))
        self.assertIn("/es/podcast/", url)   # normalizado desde /us/
        self.assertNotIn("&uo=", url)        # tracking param quitado

    def test_get_apple_url_episodio_no_encontrado_devuelve_vacio(self):
        self.assertEqual(cne.get_apple_url(999999, ITUNES_FIXTURE.encode("utf-8")), "")

    def test_get_apple_url_sin_datos_devuelve_vacio(self):
        # itunes_raw=None: así es como fetch_optional marca que la
        # descarga falló (ver FetchOptionalTests). No debe tumbar el script.
        self.assertEqual(cne.get_apple_url(105, None), "")

    def test_get_apple_url_json_corrupto_devuelve_vacio(self):
        # una respuesta a medias (corte de red, error 5xx con cuerpo HTML...)
        # no debe tumbar el script: mismo criterio que sin datos.
        self.assertEqual(cne.get_apple_url(105, b"{esto no es json"), "")

    def test_get_youtube_url_encuentra_el_video_por_numero(self):
        url = cne.get_youtube_url(105, YOUTUBE_FIXTURE.encode("utf-8"))
        self.assertEqual(url, "https://www.youtube.com/watch?v=videoId105")

    def test_get_youtube_url_no_encontrado_devuelve_vacio(self):
        self.assertEqual(cne.get_youtube_url(999999, YOUTUBE_FIXTURE.encode("utf-8")), "")

    def test_get_youtube_url_sin_datos_devuelve_vacio(self):
        self.assertEqual(cne.get_youtube_url(105, None), "")

    def test_get_youtube_url_xml_corrupto_devuelve_vacio(self):
        self.assertEqual(cne.get_youtube_url(105, b"<feed>sin cerrar"), "")

    def test_get_ivoox_url_encuentra_el_episodio_por_numero(self):
        url = cne.get_ivoox_url(105, IVOOX_FIXTURE)
        self.assertEqual(
            url,
            "https://www.ivoox.com/black-mango-105-la-mafia-suiza-audios-mp3_rf_178000105_1.html",
        )

    def test_get_ivoox_url_no_confunde_105_con_1050(self):
        # sin el guion exigido justo tras el número, "105" habría casado
        # por error dentro del "black-mango-1050-..." de la trampa del fixture
        url = cne.get_ivoox_url(105, IVOOX_FIXTURE)
        self.assertNotIn("1050", url)

    def test_get_ivoox_url_episodio_no_encontrado_devuelve_vacio(self):
        self.assertEqual(cne.get_ivoox_url(999999, IVOOX_FIXTURE), "")

    def test_get_ivoox_url_sin_datos_devuelve_vacio(self):
        # igual que Apple/YouTube: si ivoox.com falló al descargarse, el
        # campo queda vacío y se completa a mano, no se cae todo el script
        self.assertEqual(cne.get_ivoox_url(105, None), "")

    def test_fetch_manda_user_agent_y_devuelve_bytes(self):
        # el único test que baja hasta fetch() en sí (todo lo demás mockea
        # fetch directamente) — aquí se mockea un nivel más abajo, urlopen,
        # para comprobar que fetch() arma bien la petición sin tocar la red.
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b"contenido de prueba"

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as mock_urlopen:
            resultado = cne.fetch("https://ejemplo.test/x")

        self.assertEqual(resultado, b"contenido de prueba")
        peticion = mock_urlopen.call_args.args[0]
        self.assertEqual(peticion.get_header("User-agent"), cne.UA)


class FetchOptionalTests(unittest.TestCase):
    """fetch_optional(): la pieza que evita repetir la misma descarga por
    cada episodio nuevo del lote (ver comentario en main() y el hallazgo de
    la revisión de rendimiento: get_apple_url/get_youtube_url/get_ivoox_url
    piden siempre la MISMA url sin importar el episodio)."""

    @patch("check_new_episodes.fetch", side_effect=fake_fetch)
    def test_devuelve_bytes_crudos_por_defecto(self, _mock):
        resultado = cne.fetch_optional("https://itunes.apple.com/lookup?id=x")
        self.assertIsInstance(resultado, bytes)

    @patch("check_new_episodes.fetch", side_effect=fake_fetch)
    def test_decode_true_devuelve_str(self, _mock):
        resultado = cne.fetch_optional("https://www.ivoox.com/podcast-x", decode=True)
        self.assertIsInstance(resultado, str)
        self.assertIn("black-mango", resultado)

    @patch("check_new_episodes.fetch", side_effect=lambda url: (_ for _ in ()).throw(TimeoutError("boom")))
    def test_fallo_de_red_devuelve_none_en_vez_de_propagar(self, _mock):
        self.assertIsNone(cne.fetch_optional("https://ejemplo.test/x"))


class UpdateEpisodeCountNoteTests(unittest.TestCase):
    """update_episode_count_note(): toca index.html, así que se aísla con
    un archivo temporal — nunca el index.html real."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.fake_index = Path(self.tmpdir.name) / "index.html"
        self._orig_index_html = cne.INDEX_HTML
        cne.INDEX_HTML = self.fake_index

    def tearDown(self):
        cne.INDEX_HTML = self._orig_index_html

    def test_actualiza_el_contador_cuando_el_texto_encaja(self):
        self.fake_index.write_text(
            "<p>103 episodios (5 de ellos solo disponibles en YouTube).</p>", encoding="utf-8"
        )
        series_text = (
            '{ epnum: 1, title: "a", url: "https://x", ivooxUrl: "" },'
            '{ epnum: 2, title: "b", url: "", ivooxUrl: "" },'  # solo YouTube
        )
        _, salida = silent(cne.update_episode_count_note, series_text)
        nuevo_html = self.fake_index.read_text(encoding="utf-8")
        self.assertIn("2 episodios (1 de ellos solo disponibles en YouTube).", nuevo_html)
        self.assertIn("actualizado", salida)

    def test_avisa_en_vez_de_fallar_en_silencio_si_el_texto_no_encaja(self):
        # antes de este fix: si el patrón no encajaba, la función no
        # escribía nada Y no decía nada — el contador se quedaba
        # desactualizado sin que nadie se enterase por el log.
        self.fake_index.write_text("<p>sin el texto esperado aquí</p>", encoding="utf-8")
        original = self.fake_index.read_text(encoding="utf-8")
        _, salida = silent(cne.update_episode_count_note, "{ epnum: 1, title: \"a\" },")
        self.assertEqual(self.fake_index.read_text(encoding="utf-8"), original, "no debería escribir nada")
        self.assertIn("AVISO", salida)


class MainOrchestrationTests(unittest.TestCase):
    """main(): la pieza que nunca se había probado de punta a punta.

    Aísla SERIES_DATA e INDEX_HTML en archivos temporales (copias de los
    reales) y mockea fetch() — así se ejercita el flujo completo (RSS ->
    clasificar -> escribir -> resumen JSON) sin tocar ni el repo ni la red.
    """

    def setUp(self):
        import shutil
        import tempfile
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        self.series_data = Path(self.tmpdir.name) / "series-data.js"
        shutil.copy(REAL_SERIES_DATA, self.series_data)
        self.index_html = Path(self.tmpdir.name) / "index.html"
        self.index_html.write_text(
            "<p>103 episodios (5 de ellos solo disponibles en YouTube).</p>", encoding="utf-8"
        )

        self._orig_series_data = cne.SERIES_DATA
        self._orig_index_html = cne.INDEX_HTML
        cne.SERIES_DATA = self.series_data
        cne.INDEX_HTML = self.index_html

    def tearDown(self):
        cne.SERIES_DATA = self._orig_series_data
        cne.INDEX_HTML = self._orig_index_html

    def _run_main(self, argv_extra=()):
        with patch("check_new_episodes.fetch", side_effect=fake_fetch), \
             patch.object(sys, "argv", ["check_new_episodes.py", *argv_extra]):
            (returncode,), salida = silent(lambda: (cne.main(),))
        return returncode, salida

    def test_episodio_nuevo_que_encaja_en_serie_existente_va_directo_a_main(self):
        # el fixture trae el #105 "LA MAFIA SUIZA" (keyword "mafia" ya existe)
        code, salida = self._run_main()
        self.assertEqual(code, 0)

        resumen = json.loads(salida.rsplit("=== RESUMEN JSON ===", 1)[1].strip())
        self.assertEqual(resumen["route"], "main")  # sin needs_review -> directo
        self.assertEqual([e["epnum"] for e in resumen["added"]], [105])
        self.assertEqual(resumen["added"][0]["series"], "La Mafia")
        self.assertEqual(resumen["needs_review"], [])

        nuevo_texto = self.series_data.read_text(encoding="utf-8")
        self.assertIn("#105", nuevo_texto)
        self.assertIn("videoId105", nuevo_texto)  # el enlace de YouTube se resolvió
        self.assertIn("black-mango-105-la-mafia-suiza", nuevo_texto)  # y el de iVoox también
        # el #104 del fixture YA estaba en los datos reales: no debe duplicarse
        self.assertEqual(nuevo_texto.count("epnum: 104"), 1)

    def test_episodio_sin_serie_ni_patron_de_saga_va_suelto_directo_a_main(self):
        # a diferencia del "SAGA NUEVA 1" (mayúsculas + número -> revisión),
        # un título sin ningún patrón reconocible es el caso más simple y
        # más común: suelto, sin comentario, sin pasar por PR.
        rss_generico = RSS_FIXTURE.replace(
            "Black Mango #105 - LA MAFIA SUIZA | episodio de prueba",
            "Black Mango #105 - Un tema variado sin patrón reconocible",
        )

        def fetch_generico(url):
            if "anchor.fm" in url:
                return rss_generico.encode("utf-8")
            return fake_fetch(url)

        with patch("check_new_episodes.fetch", side_effect=fetch_generico), \
             patch.object(sys, "argv", ["check_new_episodes.py"]):
            (code,), salida = silent(lambda: (cne.main(),))

        resumen = json.loads(salida.rsplit("=== RESUMEN JSON ===", 1)[1].strip())
        self.assertEqual(resumen["route"], "main")
        self.assertIsNone(resumen["added"][0]["series"])
        self.assertEqual(resumen["needs_review"], [])

        nuevo_texto = self.series_data.read_text(encoding="utf-8")
        marker = "const STANDALONE_EPISODES = ["
        pos = nuevo_texto.index(marker) + len(marker)
        self.assertIn("#105", nuevo_texto[pos:pos + 200])
        self.assertNotIn("NECESITA REVISIÓN", nuevo_texto)

    def test_dry_run_no_escribe_nada(self):
        original = self.series_data.read_text(encoding="utf-8")
        code, salida = self._run_main(argv_extra=["--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("--dry-run", salida)
        self.assertEqual(self.series_data.read_text(encoding="utf-8"), original)

    def test_sin_episodios_nuevos_no_toca_nada(self):
        # RSS que solo trae episodios que YA existen en los datos reales
        rss_sin_novedades = RSS_FIXTURE.replace("#105", "#104-bis").replace("guid-105", "guid-105b")
        original = self.series_data.read_text(encoding="utf-8")

        def fetch_sin_novedades(url):
            if "anchor.fm" in url:
                return rss_sin_novedades.encode("utf-8")
            return fake_fetch(url)

        with patch("check_new_episodes.fetch", side_effect=fetch_sin_novedades), \
             patch.object(sys, "argv", ["check_new_episodes.py"]):
            (code,), salida = silent(lambda: (cne.main(),))

        resumen = json.loads(salida.rsplit("=== RESUMEN JSON ===", 1)[1].strip())
        self.assertEqual(resumen["route"], "none")
        self.assertEqual(self.series_data.read_text(encoding="utf-8"), original)

    def test_episodio_sin_serie_reconocida_se_marca_para_revision_y_va_por_pr(self):
        rss_saga_nueva = RSS_FIXTURE.replace(
            "Black Mango #105 - LA MAFIA SUIZA | episodio de prueba",
            "Black Mango #105 - SAGA COMPLETAMENTE NUEVA 1 | primer caso",
        )

        def fetch_saga_nueva(url):
            if "anchor.fm" in url:
                return rss_saga_nueva.encode("utf-8")
            return fake_fetch(url)

        with patch("check_new_episodes.fetch", side_effect=fetch_saga_nueva), \
             patch.object(sys, "argv", ["check_new_episodes.py"]):
            (code,), salida = silent(lambda: (cne.main(),))

        resumen = json.loads(salida.rsplit("=== RESUMEN JSON ===", 1)[1].strip())
        self.assertEqual(resumen["route"], "pull_request")
        self.assertEqual(len(resumen["needs_review"]), 1)
        self.assertEqual(resumen["needs_review"][0]["epnum"], 105)

        nuevo_texto = self.series_data.read_text(encoding="utf-8")
        self.assertIn("NECESITA REVISIÓN", nuevo_texto)
        self.assertIn("#105", nuevo_texto)

    def test_dos_episodios_nuevos_misma_serie_en_un_solo_main_no_se_corrompen(self):
        # variante de extremo a extremo del test de regresión: aquí se
        # ejercita a través de main(), no llamando a insert_into_series()
        # directamente, para probar el camino real que usaría producción.
        rss_dos_de_mafia = RSS_FIXTURE.replace(
            "Sin numero de episodio, se debe ignorar",
            "Black Mango #106 - LA MAFIA HOLANDESA | segundo caso de prueba",
        ).replace("guid-nan", "guid-106")

        def fetch_dos(url):
            if "anchor.fm" in url:
                return rss_dos_de_mafia.encode("utf-8")
            return fake_fetch(url)

        with patch("check_new_episodes.fetch", side_effect=fetch_dos), \
             patch.object(sys, "argv", ["check_new_episodes.py"]):
            (code,), _ = silent(lambda: (cne.main(),))

        nuevo_texto = self.series_data.read_text(encoding="utf-8")
        series_final = cne.series_names_in_data(nuevo_texto)
        # ninguna serie desaparecida ni fusionada con otra
        self.assertEqual(len(series_final), 14)
        bloque_mafia = nuevo_texto[nuevo_texto.index('name: "La Mafia"'):
                                    nuevo_texto.index('] },', nuevo_texto.index('name: "La Mafia"'))]
        self.assertIn("#105", bloque_mafia)
        self.assertIn("#106", bloque_mafia)

    def test_cada_fuente_se_descarga_una_sola_vez_aunque_haya_varios_episodios_nuevos(self):
        # el hallazgo de la revisión de rendimiento: Apple/YouTube/iVoox
        # devuelven siempre su listado completo más reciente sin importar
        # qué episodio se busque, así que con 2 episodios nuevos en el
        # mismo lote antes se pedían 2 veces cada una — ahora debe ser 1.
        rss_dos_de_mafia = RSS_FIXTURE.replace(
            "Sin numero de episodio, se debe ignorar",
            "Black Mango #106 - LA MAFIA HOLANDESA | segundo caso de prueba",
        ).replace("guid-nan", "guid-106")

        llamadas = []

        def fetch_contador(url):
            llamadas.append(url)
            if "anchor.fm" in url:
                return rss_dos_de_mafia.encode("utf-8")
            return fake_fetch(url)

        with patch("check_new_episodes.fetch", side_effect=fetch_contador), \
             patch.object(sys, "argv", ["check_new_episodes.py"]):
            (code,), _ = silent(lambda: (cne.main(),))

        def veces(substr):
            return sum(1 for u in llamadas if substr in u)

        self.assertEqual(veces("itunes.apple.com"), 1)
        self.assertEqual(veces("youtube.com/feeds"), 1)
        self.assertEqual(veces("ivoox.com"), 1)
        self.assertEqual(veces("anchor.fm"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
