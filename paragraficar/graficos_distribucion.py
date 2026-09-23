"""
Distribucion del tiempo de llenado del avion para las 5 politicas de embarque,
comparando 10, 100 y 1000 simulaciones.

Genera un unico grafico (3 paneles, uno por cantidad de iteraciones) usando una
paleta segura para daltonismo (protanopia / deuteranopia / tritanopia).

Uso:  python graficos_distribucion.py
"""

import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# ---------------------------------------------------------------------------
# Parametros del modelo (identicos a eltrabajoencuestion.py)
# ---------------------------------------------------------------------------

FILAS = 25
VELOCIDAD_NORMAL = 3
VELOCIDAD_CARRYON = 6
MAX_EN_PASILLO = None  # None = sin tope; el pasillo se llena hasta donde da la puerta

SEMILLA = 2026
P_CARRYON = 0.5  # escenario base, el mismo que analisis_carryon.py y analisis_prioritario.py
ITERACIONES = [10, 100, 1000]
POLITICAS = ["Steffen", "WILMA", "RANDOM", "BackToFront", "BackToFrontUltimate"]


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------

def simular(politica, rng, p_carryon):
    """Corre una simulacion completa de embarque y devuelve el tiempo (segundos)."""

    avion = [[0, 0, 0, 0, 0] for _ in range(FILAS)]
    asientos = set(range(FILAS * 4))
    asientosVentanas = {i for i in range(FILAS * 4) if i % 4 == 0 or i % 4 == 3}

    # BackToFront arranca por la ultima fila y va hacia adelante
    fila_actual = FILAS - 1
    libres = [-2, -1, 1, 2]

    # Cola de Steffen: ventanas pares, ventanas impares, pasillos pares, pasillos impares
    ventanaIzq = [4 * fila for fila in reversed(range(FILAS))]
    pasilloIzq = [4 * fila + 1 for fila in reversed(range(FILAS))]
    pasilloDer = [4 * fila + 2 for fila in reversed(range(FILAS))]
    ventanaDer = [4 * fila + 3 for fila in reversed(range(FILAS))]

    colaSteffen = []
    colaSteffen += [a for a in ventanaIzq if (a // 4) % 2 == 0]
    colaSteffen += [a for a in ventanaDer if (a // 4) % 2 == 0]
    colaSteffen += [a for a in ventanaIzq if (a // 4) % 2 == 1]
    colaSteffen += [a for a in ventanaDer if (a // 4) % 2 == 1]
    colaSteffen += [a for a in pasilloIzq if (a // 4) % 2 == 0]
    colaSteffen += [a for a in pasilloDer if (a // 4) % 2 == 0]
    colaSteffen += [a for a in pasilloIzq if (a // 4) % 2 == 1]
    colaSteffen += [a for a in pasilloDer if (a // 4) % 2 == 1]

    def nuevo(fila, columna):
        return {
            "posActual": (0, 0),
            "dest": (int(fila), int(columna)),
            "carryon": rng.random() < p_carryon,
            "esperar": 0,
            "bajando": 0,
            "sentando": 0,
        }

    def a_columna(asiento):
        columna = asiento % 4
        return columna - 2 if columna <= 1 else columna - 1

    def RANDOM():
        asiento = int(rng.choice(list(asientos)))
        asientos.remove(asiento)
        asientosVentanas.discard(asiento)
        return nuevo(asiento // 4, a_columna(asiento))

    def WILMA():
        if asientosVentanas:
            asiento = int(rng.choice(list(asientosVentanas)))
            asientosVentanas.remove(asiento)
        else:
            asiento = int(rng.choice(list(asientos)))
        asientos.remove(asiento)
        return nuevo(asiento // 4, a_columna(asiento))

    def BackToFrontUltimate():
        ultimos = sorted(asientos)[-20:]
        asiento = int(rng.choice(ultimos))
        asientos.remove(asiento)
        asientosVentanas.discard(asiento)
        return nuevo(asiento // 4, a_columna(asiento))

    def BackToFront():
        nonlocal fila_actual, libres
        if len(libres) == 0:
            libres = [-2, -1, 1, 2]
            fila_actual -= 1
        columna = int(rng.choice(libres))
        libres.remove(columna)
        asiento = fila_actual * 4 + (columna + 1 if columna > 0 else columna + 2)
        asientos.remove(asiento)
        asientosVentanas.discard(asiento)
        return nuevo(fila_actual, columna)

    def Steffen():
        asiento = colaSteffen.pop(0)
        asientos.remove(asiento)
        asientosVentanas.discard(asiento)
        return nuevo(asiento // 4, a_columna(asiento))

    generar = {
        "RANDOM": RANDOM,
        "WILMA": WILMA,
        "BackToFront": BackToFront,
        "BackToFrontUltimate": BackToFrontUltimate,
        "Steffen": Steffen,
    }[politica]

    pasajeros = []
    t = 0

    while len(asientos) > 0 or (t > 0 and len(pasajeros) > 0):
        t += 1  # cada iteracion = un segundo

        hayLugarEnPasillo = MAX_EN_PASILLO is None or len(pasajeros) < MAX_EN_PASILLO
        if avion[0][2] == 0 and len(asientos) > 0 and hayLugarEnPasillo:
            pasajeros.append(generar())

        for pasajero in pasajeros:
            fila, col = pasajero["posActual"]
            avion[fila][col + 2] = 1

            if pasajero["esperar"] > 0:
                pasajero["esperar"] -= 1
                if fila + 1 < FILAS and avion[fila + 1][2] != 0:
                    pasajero["esperar"] = 3
                continue

            if pasajero["bajando"] > 0:
                pasajero["bajando"] -= 1
                if pasajero["bajando"] == 0:
                    avion[fila][col + 2] = 0
                    pasajero["posActual"] = (fila + 1, 0)
                    avion[fila + 1][2] = 1
                continue

            if pasajero["sentando"] > 0:
                pasajero["sentando"] -= 1
                if pasajero["sentando"] == 0:
                    avion[fila][col + 2] = 0
                    pasajero["posActual"] = pasajero["dest"]
                    avion[pasajero["dest"][0]][pasajero["dest"][1] + 2] = 1
                continue

            if fila == pasajero["dest"][0]:
                # llegue a mi fila: primero el carry on, despues me siento
                if pasajero["carryon"]:
                    pasajero["esperar"] = int(rng.integers(7, 15))
                    pasajero["carryon"] = False
                    continue

                destCol = pasajero["dest"][1]
                bloqueado = (destCol == 2 and avion[pasajero["dest"][0]][3] != 0) or (
                    destCol == -2 and avion[pasajero["dest"][0]][1] != 0
                )
                pasajero["sentando"] = int(rng.integers(20, 26)) if bloqueado else 5
            else:
                if avion[fila + 1][2] != 0:
                    pasajero["esperar"] = 3  # tengo que esperar a que se mueva
                else:
                    pasajero["bajando"] = (
                        VELOCIDAD_CARRYON if pasajero["carryon"] else VELOCIDAD_NORMAL
                    )

        pasajeros = [p for p in pasajeros if p["posActual"] != p["dest"]]

    return t


# ---------------------------------------------------------------------------
# Estilo del grafico  (paleta validada para daltonismo)
# ---------------------------------------------------------------------------

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SEC = "#52514e"
TINTA_TENUE = "#898781"
GRILLA = "#e1e0d9"

# Paleta categorica CVD-safe: peor par adyacente dE 9.1 (protan) / 19.6 (vision normal)
COLORES = {
    "Steffen": "#2a78d6",              # azul
    "WILMA": "#eb6834",                # naranja
    "RANDOM": "#1baf7a",               # aqua
    "BackToFront": "#eda100",          # amarillo
    "BackToFrontUltimate": "#e87ba4",  # magenta
}

# Marcador distinto por politica: segunda codificacion ademas del color
MARCADORES = {
    "Steffen": "o",
    "WILMA": "s",
    "RANDOM": "^",
    "BackToFront": "D",
    "BackToFrontUltimate": "v",
}


def _oscurecer(hexcolor, factor=0.62):
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def graficar(resultados, salida):
    """resultados[n][politica] = lista de tiempos."""

    fig, axes = plt.subplots(
        1, len(ITERACIONES), figsize=(14.5, 6.2), sharey=True, facecolor=SUPERFICIE
    )

    todos = [t for por_n in resultados.values() for ts in por_n.values() for t in ts]
    ymin, ymax = min(todos), max(todos)
    margen = (ymax - ymin) * 0.10
    posiciones = np.arange(len(POLITICAS))

    for ax, n in zip(axes, ITERACIONES):
        ax.set_facecolor(SUPERFICIE)
        datos = [resultados[n][pol] for pol in POLITICAS]

        cajas = ax.boxplot(
            datos,
            positions=posiciones,
            widths=0.58,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color=TINTA, linewidth=2),
            whiskerprops=dict(color=TINTA_SEC, linewidth=1.2),
            capprops=dict(color=TINTA_SEC, linewidth=1.2),
        )

        for caja, pol in zip(cajas["boxes"], POLITICAS):
            color = COLORES[pol]
            caja.set_facecolor(color)
            caja.set_alpha(0.32)
            caja.set_edgecolor(_oscurecer(color))
            caja.set_linewidth(1.8)

        # nube de puntos: cada simulacion individual
        alpha = 0.70 if n <= 10 else (0.30 if n <= 100 else 0.07)
        tam = 34 if n <= 10 else (16 if n <= 100 else 7)
        jitter = np.random.default_rng(7)
        for x, pol in zip(posiciones, POLITICAS):
            ts = resultados[n][pol]
            xs = x + jitter.normal(0, 0.075, len(ts))
            ax.scatter(
                xs, ts,
                s=tam, marker=MARCADORES[pol],
                facecolor=COLORES[pol], edgecolor=SUPERFICIE,
                linewidth=0.5, alpha=alpha, zorder=3,
            )

        # media, etiquetada directamente sobre cada politica
        for x, pol in zip(posiciones, POLITICAS):
            media = float(np.mean(resultados[n][pol]))
            ax.plot([x - 0.29, x + 0.29], [media, media],
                    color=_oscurecer(COLORES[pol]), linewidth=2.2,
                    linestyle=(0, (3, 2)), zorder=4)
            ax.annotate(f"{media:.0f}", (x + 0.31, media), xytext=(2, 0),
                        textcoords="offset points", ha="left", va="center",
                        fontsize=8.5, color=TINTA_SEC, zorder=5)

        ax.set_title(f"{n} simulaciones", fontsize=12, color=TINTA, pad=12)
        ax.set_xticks(posiciones)
        ax.set_xticklabels(
            ["Steffen", "WILMA", "RANDOM", "Back to\nFront", "Back to Front\nUltimate"],
            fontsize=9, color=TINTA_SEC,
        )
        ax.set_xlim(-0.55, len(POLITICAS) - 0.10)
        ax.set_ylim(ymin - margen, ymax + margen)
        ax.grid(axis="y", color=GRILLA, linewidth=0.8)
        ax.set_axisbelow(True)
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(axis="y", colors=TINTA_TENUE, length=0, labelsize=9)
        ax.tick_params(axis="x", colors=TINTA_TENUE, length=0)

    axes[0].set_ylabel("Tiempo de llenado (segundos)", fontsize=10, color=TINTA_SEC)

    fig.suptitle(
        "Distribucion del tiempo de llenado segun la politica de embarque",
        fontsize=15, color=TINTA, x=0.055, ha="left", y=0.972,
    )
    fig.text(
        0.055, 0.905,
        "Caja = cuartiles 1 a 3, linea llena = mediana, linea punteada = media. "
        f"Cada punto es una simulacion. Probabilidad de carry-on = {P_CARRYON}.",
        fontsize=9.5, color=TINTA_SEC, ha="left",
    )

    handles = [
        Patch(facecolor=COLORES[p], edgecolor=_oscurecer(COLORES[p]), alpha=0.55, label=p)
        for p in POLITICAS
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=5, frameon=False,
        fontsize=9.5, labelcolor=TINTA_SEC, bbox_to_anchor=(0.5, 0.005),
    )

    fig.tight_layout(rect=(0.01, 0.055, 0.99, 0.925))
    fig.savefig(salida, dpi=200, facecolor=SUPERFICIE)
    print(f"\nGrafico guardado en: {salida}")


# ---------------------------------------------------------------------------

def main():
    rng = np.random.default_rng(SEMILLA)
    p_carryon = P_CARRYON
    print(f"Probabilidad de carry on: {p_carryon}  (semilla {SEMILLA})\n")

    maximo = max(ITERACIONES)
    resultados = {n: {} for n in ITERACIONES}

    for pol in POLITICAS:
        tiempos = []
        for i in range(maximo):
            tiempos.append(simular(pol, rng, p_carryon))
            if (i + 1) % 100 == 0 or i + 1 == maximo:
                print(f"  {pol}: {i + 1}/{maximo}")
        # los primeros n de la misma corrida: muestra las tres cantidades anidadas
        for n in ITERACIONES:
            resultados[n][pol] = tiempos[:n]

    # Tabla resumen (tambien sirve como lectura alternativa al color)
    ancho = 30
    print(f"\n{'Politica':<22}" + "".join(f"{'n=' + str(n):>{ancho}}" for n in ITERACIONES))
    print("-" * (22 + ancho * len(ITERACIONES)))
    for pol in POLITICAS:
        fila = f"{pol:<22}"
        for n in ITERACIONES:
            ts = np.array(resultados[n][pol])
            desvio = ts.std(ddof=1)             # desvio muestral: estima el de la poblacion
            error_media = desvio / np.sqrt(n)   # error estandar de la media
            fila += f"{ts.mean():>12.1f} ±{error_media:>5.1f}  sd {desvio:>5.1f}"
        print(fila)
    print("\n(media ± error estandar de la media, y desvio estandar muestral; en segundos)")

    # graficos/ esta en la raiz del repo, al lado de los otros graficos
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(raiz, "graficos")
    os.makedirs(carpeta, exist_ok=True)
    graficar(resultados, os.path.join(carpeta, "distribucion_tiempos.png"))


if __name__ == "__main__":
    main()
