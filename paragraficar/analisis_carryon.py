"""
Cuanto pesa el carry-on: el avion lleno con p = 0 contra el avion lleno con p = 1.

El enunciado pregunta como cambian las respuestas si TODOS los pasajeros llevan
carry-on y si NINGUNO lo lleva. Este script responde esas dos preguntas y, de
paso, barre los valores intermedios de p para mostrar la forma de la curva.

Reusa el simulador de eltrabajoencuestion.py sin tocarlo: solo pisa la constante
global PROBABILIDAD_CARRYON antes de cada tanda, que es lo que leen las cinco
funciones de politica cuando sortean si el pasajero trae valija.

Uso:  python analisis_carryon.py
Salidas: capturas/07_carryon_barrido.png
         capturas/08_carryon_0_vs_1.png
         capturas/resultados_carryon.csv
         y tres tablas por consola listas para pegar en la presentacion.
"""

import csv
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import eltrabajoencuestion as E


# ---------------------------------------------------------------------------
# Parametros del experimento
# ---------------------------------------------------------------------------

ITERACIONES = 1000             # simulaciones por (politica, p)
SEMILLA = 2026

# Los dos casos que pide el enunciado, mas los intermedios para ver la curva.
P_BARRIDO = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
P_NINGUNO = 0.0
P_TODOS = 1.0

POLITICAS = ["Steffen", "WILMA", "RANDOM", "BackToFrontUltimate", "BackToFront"]

FUNCIONES = {
    "Steffen": E.Steffen,
    "WILMA": E.WILMA,
    "RANDOM": E.RANDOM,
    "BackToFront": E.BackToFront,
    "BackToFrontUltimate": E.BackToFrontUltimate,
}

# Misma paleta y marcadores que graficos_distribucion.py y analisis_prioritario.py.
# Validada para daltonismo: peor par adyacente dE 9.1 (protanopia) / 19.6 (vision
# normal). El color nunca va solo: cada politica tiene ademas su marcador propio y
# su etiqueta escrita al lado de la linea.
COLORES = {
    "Steffen": "#2a78d6",
    "WILMA": "#eb6834",
    "RANDOM": "#1baf7a",
    "BackToFront": "#eda100",
    "BackToFrontUltimate": "#e87ba4",
}
MARCADORES = {
    "Steffen": "o", "WILMA": "s", "RANDOM": "^",
    "BackToFront": "D", "BackToFrontUltimate": "v",
}
ETIQUETA = {
    "Steffen": "Steffen", "WILMA": "WILMA", "RANDOM": "RANDOM",
    "BackToFront": "Back to Front", "BackToFrontUltimate": "Back to Front Ultimate",
}

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SEC = "#52514e"
TINTA_TENUE = "#898781"
GRILLA = "#e1e0d9"
CRITICO = "#d03b3b"


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------

def correr(nombre_politica, p, iteraciones=None):
    """Tiempos de llenado de `iteraciones` embarques con probabilidad de carry-on p.

    El default se resuelve adentro y no en la firma, asi bajar ITERACIONES desde
    afuera (para una prueba rapida) realmente achica la corrida.
    """
    iteraciones = ITERACIONES if iteraciones is None else iteraciones
    E.PROBABILIDAD_CARRYON = p
    fn = FUNCIONES[nombre_politica]
    return np.array([E.simular_una_vez(fn) for _ in range(iteraciones)], dtype=float)


def resumen(tiempos):
    """Media, desvio muestral (ddof=1) y errores de ambos estimadores.

    El error de la media es sd/sqrt(n). El del desvio es sd/sqrt(2n), que es la
    aproximacion asintotica valida bajo normalidad de los tiempos; con n = 1000
    el TCL la sostiene de sobra.
    """
    n = len(tiempos)
    media = float(tiempos.mean())
    sd = float(tiempos.std(ddof=1))
    return {
        "n": n,
        "media": media,
        "sd": sd,
        "se_media": sd / np.sqrt(n),
        "se_sd": sd / np.sqrt(2 * n),
    }


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

def tabla_caso(res, p, titulo):
    """Una fila por politica para un valor fijo de p."""
    print(f"\n{titulo}")
    print(f"{'Politica':<24}{'Media (s)':>11}{'Media (min)':>13}{'IC 95% de la media':>24}"
          f"{'Desvio (s)':>12}{'EE desvio':>11}")
    print("-" * 95)
    for pol in POLITICAS:
        r = res[pol][p]
        lo = r["media"] - 1.96 * r["se_media"]
        hi = r["media"] + 1.96 * r["se_media"]
        print(f"{ETIQUETA[pol]:<24}{r['media']:>11.1f}{r['media'] / 60:>13.2f}"
              f"{f'[{lo:.1f} ; {hi:.1f}]':>24}{r['sd']:>12.1f}{r['se_sd']:>11.1f}")
    print(f"(n = {res[POLITICAS[0]][p]['n']} simulaciones por politica)")


def tabla_comparacion(res):
    """El delta entre los dos casos extremos: es la respuesta al enunciado."""
    print(f"\nCuanto cuesta el carry-on: pasar de p = 0 a p = 1")
    print(f"{'Politica':<24}{'p = 0 (min)':>13}{'p = 1 (min)':>13}{'Delta (min)':>13}"
          f"{'Penalidad':>11}{'Ranking':>18}")
    print("-" * 92)
    orden_cero = sorted(POLITICAS, key=lambda q: res[q][P_NINGUNO]["media"])
    orden_uno = sorted(POLITICAS, key=lambda q: res[q][P_TODOS]["media"])
    for pol in POLITICAS:
        m0 = res[pol][P_NINGUNO]["media"]
        m1 = res[pol][P_TODOS]["media"]
        salto = f"{orden_cero.index(pol) + 1} -> {orden_uno.index(pol) + 1}"
        print(f"{ETIQUETA[pol]:<24}{m0 / 60:>13.2f}{m1 / 60:>13.2f}{(m1 - m0) / 60:>13.2f}"
              f"{100 * (m1 - m0) / m0:>10.0f}%{salto:>18}")
    print("(Ranking = puesto con p = 0 -> puesto con p = 1; 1 es el mas rapido)")


def guardar_csv(res, ruta):
    """Todo el barrido crudo, para que los numeros de las slides sean auditables."""
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Politica", "P_Carryon", "N", "Media_Segundos",
                    "Desvio_Segundos", "EE_Media", "EE_Desvio"])
        for pol in POLITICAS:
            for p in P_BARRIDO:
                r = res[pol][p]
                w.writerow([pol, p, r["n"], round(r["media"], 2), round(r["sd"], 2),
                            round(r["se_media"], 3), round(r["se_sd"], 3)])
    return ruta


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------

def _eje(ax):
    ax.set_facecolor(SUPERFICIE)
    ax.grid(axis="y", color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=TINTA_TENUE, length=0, labelsize=9)


def _encabezado(fig, titulo, subtitulo, y_titulo=0.965, y_sub=0.905):
    fig.suptitle(titulo, fontsize=15, color=TINTA, x=0.055, ha="left", y=y_titulo)
    fig.text(0.055, y_sub, subtitulo, fontsize=9.5, color=TINTA_SEC, ha="left")


def _etiquetas_directas(ax, x, puntos, hueco=0.042):
    """Escribe el nombre de cada serie al final de su linea, sin que se pisen.

    `puntos` es [(y, texto), ...]. Cuando dos lineas terminan muy juntas (pasa
    con RANDOM y Back to Front Ultimate) se separan las etiquetas lo minimo
    necesario y se deja una guia gris hasta el punto real, asi la etiqueta sigue
    apuntando a su linea. `hueco` va en fraccion del alto del eje.
    """
    lo, hi = ax.get_ylim()
    minimo = (hi - lo) * hueco

    ordenados = sorted(puntos, key=lambda par: par[0])
    ys = [y for y, _ in ordenados]
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < minimo:
            ys[i] = ys[i - 1] + minimo
    desborde = ys[-1] - (hi - minimo * 0.5)
    if desborde > 0:
        ys = [y - desborde for y in ys]

    for y_etiqueta, (y_real, texto) in zip(ys, ordenados):
        if abs(y_etiqueta - y_real) > minimo * 0.25:
            ax.annotate("", xy=(x, y_real), xytext=(x, y_etiqueta),
                        arrowprops=dict(arrowstyle="-", color=GRILLA, linewidth=0.9),
                        annotation_clip=False, zorder=1)
        ax.annotate(texto, (x, y_etiqueta), xytext=(7, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=8.5, color=TINTA_SEC,
                    annotation_clip=False, zorder=5)


def grafico_barrido(res, carpeta):
    """Dos paneles: como cambian la media y el desvio a medida que sube p.

    Van en paneles separados y no en un eje doble a proposito: son dos magnitudes
    de escala distinta y superponerlas invita a leer cruces que no existen.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 6.2), facecolor=SUPERFICIE)

    for ax, clave, etiqueta_y, titulo_panel in (
        (ax1, "media", "Tiempo medio de llenado (minutos)", "Cuánto tarda"),
        (ax2, "sd", "Desvío estándar del tiempo (segundos)", "Cuánto varía"),
    ):
        _eje(ax)
        finales = []
        for pol in POLITICAS:
            ys = np.array([res[pol][p][clave] for p in P_BARRIDO])
            if clave == "media":
                ys = ys / 60.0
                errores = np.array([res[pol][p]["se_media"] * 1.96 / 60.0 for p in P_BARRIDO])
            else:
                errores = np.array([res[pol][p]["se_sd"] * 1.96 for p in P_BARRIDO])
            ax.plot(P_BARRIDO, ys, "-", color=COLORES[pol], linewidth=2,
                    marker=MARCADORES[pol], markersize=6, markeredgecolor=SUPERFICIE,
                    markeredgewidth=1.2, label=ETIQUETA[pol], zorder=3)
            ax.fill_between(P_BARRIDO, ys - errores, ys + errores,
                            color=COLORES[pol], alpha=0.14, linewidth=0, zorder=2)
            finales.append((float(ys[-1]), ETIQUETA[pol]))

        ax.set_title(titulo_panel, fontsize=11.5, color=TINTA, loc="left", pad=10)
        ax.set_xlabel("Probabilidad de que un pasajero lleve carry-on", fontsize=10,
                      color=TINTA_SEC)
        ax.set_ylabel(etiqueta_y, fontsize=10, color=TINTA_SEC)
        ax.set_xticks(P_BARRIDO)
        ax.set_xticklabels([f"{p:.0%}" for p in P_BARRIDO])
        ax.set_xlim(-0.04, 1.34)
        # Etiqueta directa al final de cada linea: la identidad nunca depende solo
        # del color (la paleta no llega a 3:1 de contraste contra el fondo).
        _etiquetas_directas(ax, P_BARRIDO[-1], finales)

    # Steffen con p = 0 no tiene ninguna fuente de azar: cola fija, sin valijas y
    # sin bloqueos ventana-pasillo. El desvio da 0.0 exacto y conviene sen~alarlo.
    ax2.annotate("con p = 0 Steffen es determinista:\ndesvío exactamente 0 s",
                 xy=(0.0, 0.0), xycoords="data", xytext=(0.10, 0.20),
                 textcoords="axes fraction", fontsize=8.5, color=TINTA_SEC,
                 ha="left", va="bottom",
                 arrowprops=dict(arrowstyle="->", color=TINTA_TENUE, linewidth=0.9,
                                 connectionstyle="arc3,rad=0.25"))

    _encabezado(fig, "El carry-on no castiga a todas las políticas por igual",
                "Tiempo de llenado de un avión lleno (100 pasajeros) según qué fracción lleva equipaje de mano. "
                f"Banda = IC 95%, {ITERACIONES} simulaciones por punto.")
    fig.tight_layout(rect=(0.01, 0.02, 0.99, 0.89))
    ruta = os.path.join(carpeta, "07_carryon_barrido.png")
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


def grafico_extremos(res, carpeta):
    """Las dos preguntas del enunciado, una al lado de la otra.

    Un punto por caso y una barra que los une: lo que se quiere leer es el largo
    de la barra, o sea cuanto empeora cada politica al pasar de 0 a 100%.
    """
    orden = sorted(POLITICAS, key=lambda q: res[q][P_TODOS]["media"], reverse=True)
    ys = np.arange(len(orden))

    fig, ax = plt.subplots(figsize=(12.5, 6.0), facecolor=SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    ax.grid(axis="x", color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=TINTA_TENUE, length=0, labelsize=9)

    for y, pol in zip(ys, orden):
        m0 = res[pol][P_NINGUNO]["media"] / 60.0
        m1 = res[pol][P_TODOS]["media"] / 60.0
        color = COLORES[pol]
        ax.plot([m0, m1], [y, y], "-", color=color, linewidth=6, alpha=0.30,
                solid_capstyle="round", zorder=2)
        # Anillo del color del fondo en cada punta: separa las marcas cuando se
        # acercan y las despega de la barra.
        ax.scatter([m0], [y], s=105, marker=MARCADORES[pol], facecolor=SUPERFICIE,
                   edgecolor=color, linewidth=2.2, zorder=4)
        ax.scatter([m1], [y], s=115, marker=MARCADORES[pol], facecolor=color,
                   edgecolor=SUPERFICIE, linewidth=2.0, zorder=4)
        ax.annotate(f"{m0:.1f}", (m0, y), xytext=(-9, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=9, color=TINTA_SEC)
        ax.annotate(f"{m1:.1f}", (m1, y), xytext=(10, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9.5, color=TINTA, fontweight="bold")
        penalidad = 100 * (m1 - m0) / m0
        ax.annotate(f"+{penalidad:.0f}%", ((m0 + m1) / 2, y), xytext=(0, 11),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=9.5, color=color, fontweight="bold")

    ax.set_yticks(ys)
    ax.set_yticklabels([ETIQUETA[p] for p in orden], fontsize=10.5, color=TINTA)
    ax.set_ylim(-0.7, len(orden) - 0.3)
    ax.set_xlabel("Tiempo de llenado del avión (minutos)", fontsize=10, color=TINTA_SEC)
    ax.set_xlim(13, 51)

    # Leyenda de forma, no de color: que significa cada punta de la barra. Va al
    # pie de la figura y no dentro del eje para que no tape la barra mas larga.
    ax.scatter([], [], s=105, marker="o", facecolor=SUPERFICIE, edgecolor=TINTA_SEC,
               linewidth=2.2, label="Ninguno lleva carry-on  ·  p = 0")
    ax.scatter([], [], s=115, marker="o", facecolor=TINTA_SEC, edgecolor=SUPERFICIE,
               linewidth=2.0, label="Todos llevan carry-on  ·  p = 1")
    fig.legend(loc="lower center", ncol=2, frameon=False, fontsize=9.5,
               labelcolor=TINTA_SEC, bbox_to_anchor=(0.5, 0.005))

    _encabezado(fig, "Con todos los pasajeros cargando valija, Back to Front se hunde",
                "Tiempo de llenado en los dos extremos que pide el enunciado. La barra mide el costo del carry-on; "
                f"el porcentaje, cuánto empeora cada política. {ITERACIONES} simulaciones por punto.")
    fig.tight_layout(rect=(0.01, 0.06, 0.99, 0.88))
    ruta = os.path.join(carpeta, "08_carryon_0_vs_1.png")
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


# ---------------------------------------------------------------------------

def main():
    np.random.seed(SEMILLA)
    carpeta = os.path.join(RAIZ, "capturas")
    os.makedirs(carpeta, exist_ok=True)

    print(f"Efecto del carry-on · {ITERACIONES} simulaciones por punto · "
          f"semilla {SEMILLA} · avión lleno (100 pasajeros)")

    res = {}
    for pol in POLITICAS:
        res[pol] = {}
        for p in P_BARRIDO:
            res[pol][p] = resumen(correr(pol, p))
        print(f"  {ETIQUETA[pol]:<24} p=0 {res[pol][P_NINGUNO]['media']:7.1f} s   "
              f"p=1 {res[pol][P_TODOS]['media']:7.1f} s")

    E.PROBABILIDAD_CARRYON = 0.5   # deja el modulo como estaba

    tabla_caso(res, P_NINGUNO, "CASO A · Ningún pasajero lleva carry-on  (p = 0)")
    tabla_caso(res, P_TODOS, "CASO B · Todos los pasajeros llevan carry-on  (p = 1)")
    tabla_comparacion(res)

    print(f"\nDatos crudos en: {guardar_csv(res, os.path.join(carpeta, 'resultados_carryon.csv'))}")
    for ruta in (grafico_barrido(res, carpeta), grafico_extremos(res, carpeta)):
        print(f"Gráfico guardado en: {ruta}")


if __name__ == "__main__":
    main()
