#!/usr/bin/env python3
"""Test de regresión para classify() y el escapado de check_new_episodes.py.

Sin framework (consistente con el resto del proyecto: cero dependencias).
Uso: python3 scripts/test_classify.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_new_episodes import classify, js_string, warn_uncovered_series  # noqa: E402

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
    sin_cubrir_sim = warn_uncovered_series(simulado)
    if sin_cubrir_sim != ["Una Serie De Prueba Sin Keyword"]:
        fallos += 1
        print(f"FALLO: warn_uncovered_series no detectó bien el caso simulado: {sin_cubrir_sim}")

    if fallos:
        print(f"\n{fallos} fallo(s).")
        return 1
    print(f"OK: {len(CASOS_SERIE)} casos de serie + {len(CASOS_REVISION)} de revisión + escapado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
