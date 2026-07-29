#!/usr/bin/env python3
"""Test de regresión para classify() y el escapado de check_new_episodes.py.

Sin framework (consistente con el resto del proyecto: cero dependencias).
Uso: python3 scripts/test_classify.py
"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_new_episodes import (  # noqa: E402
    classify,
    js_episode_entry,
    js_string,
    series_names_in_data,
    insert_into_series,
    warn_uncovered_series,
)

CASOS_SERIE = [
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
    ('Black Mango #1 - Indonesia', None),
    ('Black Mango #104 - CIVILIZACIONES PERDIDAS | Los mayores misterios', None),
]

CASOS_REVISION = [
    'Black Mango #110 - ASESINATOS EN EL METAVERSO 1 | Un caso real',
    'Black Mango #111 - EL ARTE DEL ENGAÑO 2 | Estafas legendarias',
]


def main():
    fallos = 0

    for title, esperado in CASOS_SERIE:
        serie, review, _ = classify(title)
        if serie != esperado or review:
            fallos += 1
            print(f"FALLO: {title!r} -> serie={serie!r} review={review} (esperado {esperado!r})")

    for title in CASOS_REVISION:
        serie, review, reason = classify(title)
        if not review:
            fallos += 1
            print(f"FALLO: {title!r} debería marcarse para revisión y no lo hizo")

    # el escapado debe producir un literal de string valido de verdad,
    # no solo "parecer" bien a ojo
    import json
    peligroso = 'Título con "comillas", barra\\ y <script>alert(1)</script>'
    literal = js_string(peligroso)
    if json.loads(literal) != peligroso:
        fallos += 1
        print("FALLO: js_string no produce un literal reversible")

    # SERIES_KEYWORDS vive aparte de SERIES: si una serie real se queda sin
    # cobertura, debe avisar; si una serie de prueba sin keyword aparece, debe
    # detectarla (y no marcar como "sin cubrir" una que sí tiene keyword)
    real = Path(__file__).parent.parent / "assets" / "series-data.js"
    sin_cubrir_real = warn_uncovered_series(real.read_text(encoding="utf-8"))
    if sin_cubrir_real:
        fallos += 1
        print(f"FALLO: hay series reales sin keyword: {sin_cubrir_real}")

    simulado = (
        '{ name: "Los Terribles", episodes: [] },\n'
        '{ name: "Una Serie De Prueba Sin Keyword", episodes: [] },'
    )
    # este caso es deliberadamente falso (solo para probar la detección) —
    # se silencia su AVISO por stdout para no ensuciar el log real del
    # workflow con algo que parece (pero no es) un problema de verdad.
    # Se vio pasar exactamente eso en la primera ejecución real en Actions.
    with contextlib.redirect_stdout(io.StringIO()):
        sin_cubrir_sim = warn_uncovered_series(simulado)
    if sin_cubrir_sim != ["Una Serie De Prueba Sin Keyword"]:
        fallos += 1
        print(f"FALLO: warn_uncovered_series no detectó bien el caso simulado: {sin_cubrir_sim}")

    # Regresión: dos episodios NUEVOS de la MISMA serie existente en un
    # mismo run. Encontrado por inspección real de logs — insert_into_series
    # reconstruía el cierre "] }" con un espacio de más, así que la 2ª
    # llamada no reconocía el cierre de la 1ª y fusionaba esa serie con la
    # siguiente completa. Se prueba contra los datos reales (solo lectura).
    original = real.read_text(encoding="utf-8")
    series_antes = series_names_in_data(original)
    idx_mafia = series_antes.index("La Mafia")
    siguiente_serie = series_antes[idx_mafia + 1]

    t = original
    e1 = js_episode_entry(901, "Black Mango #901 - LA MAFIA DE PRUEBA UNO | test", "https://s/1", "", "")
    e2 = js_episode_entry(902, "Black Mango #902 - LA MAFIA DE PRUEBA DOS | test", "https://s/2", "", "")
    t = insert_into_series(t, "La Mafia", e1)
    t = insert_into_series(t, "La Mafia", e2)

    series_despues = series_names_in_data(t)
    if series_despues != series_antes:
        fallos += 1
        print(f"FALLO: insertar 2 episodios en 'La Mafia' alteró la lista de series: {series_despues}")

    bloque_mafia = t[t.index('name: "La Mafia"'): t.index(f'name: "{siguiente_serie}"')]
    if "#901" not in bloque_mafia or "#902" not in bloque_mafia:
        fallos += 1
        print("FALLO: los dos episodios nuevos no quedaron ambos dentro del bloque de 'La Mafia'")

    if fallos:
        print(f"\n{fallos} fallo(s).")
        return 1
    print(f"OK: {len(CASOS_SERIE)} casos de serie + {len(CASOS_REVISION)} de revisión + "
          f"escapado + cobertura de keywords + 2 episodios misma serie en un run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
