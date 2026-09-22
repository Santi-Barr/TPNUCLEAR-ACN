"""
Cuanto vale vender embarque prioritario.

La aerolinea le vende a N pasajeros el derecho a subir primero. Esos N rompen el
orden de la politica: suben antes que todos, en el orden en que llegan (al azar).
Cuantos segundos cuesta cada prioritario, y a partir de que precio conviene venderlo?

Reusa el simulador de eltrabajoencuestion.py sin tocarlo: envuelve a la politica
elegida en una funcion que primero reparte los lugares prioritarios y despues le
pasa la posta a la politica original.

Supuestos economicos: los mismos que el analisis de costos del grupo
(USD 85 por minuto de demora).

Uso:  python analisis_prioritario.py
Salidas: capturas/04_prioritario_tiempo.png
         capturas/05_prioritario_beneficio.png
         capturas/06_prioritario_precio_indiferencia.png
         y una tabla por consola lista para pegar en la presentacion.
"""

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
# Supuestos
# ---------------------------------------------------------------------------

COSTO_POR_MINUTO = 85.0        # USD por minuto de demora (igual que analisis_costos.py)
PRECIO_PRIORITARIO = 15.0      # USD que se le cobra al pasajero por subir primero
P_CARRYON = 0.5                # fija, para que las corridas sean comparables entre si

# Escenario de heterogeneidad: los que pagan prioritario son los que mas valijas
# llevan (por eso pagan: para ganar lugar en el compartimento). Para que el efecto
# sea del ORDEN y no de "hay mas valijas", se compensa bajando la p del resto y
# manteniendo constante la cantidad total de carry-ons del vuelo.
P_CARRYON_PRIORITARIO = 0.8
PRIORITARIOS_SENSIBILIDAD = [0, 10, 20, 40, 60]

ITERACIONES = 400
PRIORITARIOS = [0, 2, 5, 10, 15, 20, 30, 40, 60, 80, 100]
SEMILLA = 2026

PASAJEROS = 100
POLITICAS = ["Steffen", "WILMA", "RANDOM", "BackToFront", "BackToFrontUltimate"]

# Misma paleta y marcadores que graficos_distribucion.py
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
# El mecanismo: prioritarios adelante, el resto segun la politica
# ---------------------------------------------------------------------------

def politica_con_prioritarios(politica, n_prioritarios, p_prioritario=None):
    """Devuelve una funcion de embarque nueva para UNA corrida.

    Los primeros `n_prioritarios` pasajeros suben salteando el orden, con un
    asiento al azar entre los que quedan. Despues sigue la politica original.

    Hay que sacar el asiento de las tres estructuras que usan las politicas
    (asientos, asientosVentanas y la cola de Steffen), igual que hace
    simular_una_vez() con los asientos que no se vendieron.
    """
    quedan = [n_prioritarios]
    p = P_CARRYON if p_prioritario is None else p_prioritario

    def embarcar():
        if quedan[0] <= 0:
            return politica()
        quedan[0] -= 1

        asiento = int(np.random.choice(sorted(E.asientos)))
        E.asientos.remove(asiento)
        E.asientosVentanas.discard(asiento)
        if asiento in E.colaSteffen:
            E.colaSteffen.remove(asiento)

        columna = asiento % 4
        columna = columna - 2 if columna <= 1 else columna - 1
        return {
            "posActual": (0, 0),
            "dest": (asiento // 4, int(columna)),
            "carryon": bool(np.random.binomial(n=1, p=p, size=1)[0]),
            "esperar": 0, "bajando": 0, "sentando": 0,
        }

    return embarcar


def correr(nombre_politica, n_prioritarios, iteraciones, p_prioritario=None, p_resto=None):
    """Tiempos de llenado de `iteraciones` embarques."""
    politica = dict(zip(POLITICAS, [E.Steffen, E.WILMA, E.RANDOM,
                                    E.BackToFront, E.BackToFrontUltimate]))[nombre_politica]
    E.PROBABILIDAD_CARRYON = P_CARRYON if p_resto is None else p_resto
    tiempos = []
    for _ in range(iteraciones):
        tiempos.append(E.simular_una_vez(
            politica_con_prioritarios(politica, n_prioritarios, p_prioritario)))
    E.PROBABILIDAD_CARRYON = P_CARRYON
    return np.array(tiempos, dtype=float)


def resumen(tiempos):
    media = float(tiempos.mean())
    sd = float(tiempos.std(ddof=1))
    return {"media": media, "sd": sd, "se": sd / np.sqrt(len(tiempos))}


# ---------------------------------------------------------------------------
# Economia
# ---------------------------------------------------------------------------

def costo_usd(segundos):
    """Cuanto cuesta, en dolares, una demora de tantos segundos."""
    return segundos / 60.0 * COSTO_POR_MINUTO


def beneficio_neto(delta_segundos, n_prioritarios, precio=PRECIO_PRIORITARIO):
    """Lo que entra por vender prioritarios menos lo que cuesta la demora extra."""
    return n_prioritarios * precio - costo_usd(delta_segundos)


def precio_indiferencia(delta_segundos, n_prioritarios):
    """Precio al que vender el prioritario no suma ni resta."""
    if n_prioritarios == 0:
        return np.nan
    return costo_usd(delta_segundos) / n_prioritarios


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


def _encabezado(fig, titulo, subtitulo):
    fig.suptitle(titulo, fontsize=15, color=TINTA, x=0.055, ha="left", y=0.965)
    fig.text(0.055, 0.905, subtitulo, fontsize=9.5, color=TINTA_SEC, ha="left")


def _leyenda(fig):
    fig.legend(loc="lower center", ncol=5, frameon=False, fontsize=9.5,
               labelcolor=TINTA_SEC, bbox_to_anchor=(0.5, 0.005))


def grafico_tiempo(res, carpeta):
    fig, ax = plt.subplots(figsize=(12.5, 6.0), facecolor=SUPERFICIE)
    _eje(ax)
    for pol in POLITICAS:
        medias = np.array([res[pol][n]["media"] for n in PRIORITARIOS])
        errores = np.array([res[pol][n]["se"] * 1.96 for n in PRIORITARIOS])
        ax.plot(PRIORITARIOS, medias, "-", color=COLORES[pol], linewidth=2,
                marker=MARCADORES[pol], markersize=6, markeredgecolor=SUPERFICIE,
                markeredgewidth=1.2, label=ETIQUETA[pol])
        ax.fill_between(PRIORITARIOS, medias - errores, medias + errores,
                        color=COLORES[pol], alpha=0.14, linewidth=0)

    ax.set_xlabel("Pasajeros con embarque prioritario  ·  de 100", fontsize=10, color=TINTA_SEC)
    ax.set_ylabel("Tiempo de llenado (segundos)", fontsize=10, color=TINTA_SEC)
    ax.set_xticks(PRIORITARIOS)
    ax.annotate("con los 100 prioritarios ya no hay politica:\ntodos suben al azar",
                xy=(100, res["Steffen"][100]["media"]), xycoords="data",
                xytext=(0.60, 0.08), textcoords="axes fraction",
                fontsize=9, color=TINTA_SEC,
                arrowprops=dict(arrowstyle="->", color=TINTA_TENUE, linewidth=0.9))
    _encabezado(fig, "Vender prioritario le saca el orden al embarque",
                "Tiempo de llenado segun cuantos pasajeros suben primero salteando la politica. "
                f"Banda = IC 95% de la media, {ITERACIONES} simulaciones por punto.")
    _leyenda(fig)
    fig.tight_layout(rect=(0.01, 0.055, 0.99, 0.90))
    ruta = os.path.join(carpeta, "04_prioritario_tiempo.png")
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


def grafico_beneficio(res, carpeta):
    fig, ax = plt.subplots(figsize=(12.5, 6.0), facecolor=SUPERFICIE)
    _eje(ax)
    ax.axhline(0, color=CRITICO, linestyle=":", linewidth=1.6)
    ax.annotate("Punto de equilibrio", xy=(0, 0), xytext=(1, 30), fontsize=9.5,
                color=CRITICO, fontweight="bold")

    for pol in POLITICAS:
        base = res[pol][0]["media"]
        ys = [beneficio_neto(res[pol][n]["media"] - base, n) for n in PRIORITARIOS]
        ax.plot(PRIORITARIOS, ys, "-", color=COLORES[pol], linewidth=2,
                marker=MARCADORES[pol], markersize=6, markeredgecolor=SUPERFICIE,
                markeredgewidth=1.2, label=ETIQUETA[pol])
        mejor = int(np.argmax(ys))
        if ys[mejor] > 0:
            ax.annotate(f"{PRIORITARIOS[mejor]}", (PRIORITARIOS[mejor], ys[mejor]),
                        xytext=(0, 9), textcoords="offset points", ha="center",
                        fontsize=9, color=COLORES[pol], fontweight="bold")

    ax.set_xlabel("Pasajeros con embarque prioritario  ·  de 100", fontsize=10, color=TINTA_SEC)
    ax.set_ylabel("Beneficio neto por vuelo (USD)", fontsize=10, color=TINTA_SEC)
    ax.set_xticks(PRIORITARIOS)
    _encabezado(fig, "A USD 15 el prioritario, cuanto deja cada politica",
                f"Lo que entra por vender prioritarios menos el costo de la demora extra, "
                f"a USD {COSTO_POR_MINUTO:.0f} por minuto. El numero marca el optimo de cada politica.")
    _leyenda(fig)
    fig.tight_layout(rect=(0.01, 0.055, 0.99, 0.90))
    ruta = os.path.join(carpeta, "05_prioritario_beneficio.png")
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


def grafico_indiferencia(res, carpeta):
    fig, ax = plt.subplots(figsize=(12.5, 6.0), facecolor=SUPERFICIE)
    _eje(ax)
    ax.axhline(PRECIO_PRIORITARIO, color=CRITICO, linestyle=":", linewidth=1.6)
    ax.annotate(f"Precio real supuesto   USD {PRECIO_PRIORITARIO:.0f}",
                xy=(PRIORITARIOS[-1], PRECIO_PRIORITARIO), xytext=(0, 8),
                textcoords="offset points", ha="right", fontsize=9.5,
                color=CRITICO, fontweight="bold")

    ns = [n for n in PRIORITARIOS if n > 0]
    for pol in POLITICAS:
        base = res[pol][0]["media"]
        ys = [precio_indiferencia(res[pol][n]["media"] - base, n) for n in ns]
        ax.plot(ns, ys, "-", color=COLORES[pol], linewidth=2,
                marker=MARCADORES[pol], markersize=6, markeredgecolor=SUPERFICIE,
                markeredgewidth=1.2, label=ETIQUETA[pol])

    ax.axhline(0, color="#c3c2b7", linewidth=1)
    ax.set_xlabel("Pasajeros con embarque prioritario  ·  de 100", fontsize=10, color=TINTA_SEC)
    ax.set_ylabel("Precio de indiferencia (USD por pasajero)", fontsize=10, color=TINTA_SEC)
    ax.set_xticks(ns)
    _encabezado(fig, "Cuanto hay que cobrar para que vender prioritario no destruya valor",
                "Por debajo de su curva, cada politica pierde plata. Debajo de cero, el prioritario "
                "ademas acelera el embarque: cobrar cualquier cosa conviene.")
    _leyenda(fig)
    fig.tight_layout(rect=(0.01, 0.055, 0.99, 0.90))
    ruta = os.path.join(carpeta, "06_prioritario_precio_indiferencia.png")
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


# ---------------------------------------------------------------------------

def segundos_por_prioritario(res, pol, hasta=20):
    """Pendiente de la recta tiempo ~ prioritarios en el tramo chico."""
    xs = [n for n in PRIORITARIOS if n <= hasta]
    ys = [res[pol][n]["media"] for n in xs]
    return float(np.polyfit(xs, ys, 1)[0])


def main():
    np.random.seed(SEMILLA)
    carpeta = os.path.join(RAIZ, "capturas")      # donde ya viven 01, 02 y 03
    os.makedirs(carpeta, exist_ok=True)

    print(f"Embarque prioritario · {ITERACIONES} simulaciones por punto · "
          f"p(carry-on) = {P_CARRYON} · USD {COSTO_POR_MINUTO:.0f} por minuto\n")

    res = {}
    for pol in POLITICAS:
        res[pol] = {}
        for n in PRIORITARIOS:
            res[pol][n] = resumen(correr(pol, n, ITERACIONES))
        base = res[pol][0]["media"]
        print(f"  {pol:<22} sin prioritarios {base:7.1f} s   "
              f"con 100 {res[pol][100]['media']:7.1f} s")

    # ---- tabla principal ----
    print(f"\n{'Politica':<24}{'s/prioritario':>14}{'USD/prioritario':>17}"
          f"{'Optimo (N)':>12}{'Beneficio max':>15}")
    print("-" * 82)
    for pol in POLITICAS:
        base = res[pol][0]["media"]
        pendiente = segundos_por_prioritario(res, pol)
        beneficios = [beneficio_neto(res[pol][n]["media"] - base, n) for n in PRIORITARIOS]
        mejor = int(np.argmax(beneficios))
        print(f"{pol:<24}{pendiente:>14.1f}{costo_usd(pendiente):>17.2f}"
              f"{PRIORITARIOS[mejor]:>12}{beneficios[mejor]:>14.0f} USD")
    print(f"\n(pendiente estimada con N <= 20; beneficio a USD {PRECIO_PRIORITARIO:.0f} "
          f"por prioritario)")

    # ---- sensibilidad: y si los que pagan son los que mas valijas llevan ----
    print(f"\nSensibilidad: el prioritario lleva carry-on con p = {P_CARRYON_PRIORITARIO}, "
          f"compensando al resto para que el vuelo siga teniendo la misma cantidad de valijas")
    print(f"{'Politica':<24}" + "".join(f"{'N=' + str(n):>12}" for n in PRIORITARIOS_SENSIBILIDAD))
    print("-" * (24 + 12 * len(PRIORITARIOS_SENSIBILIDAD)))
    for pol in POLITICAS:
        fila = f"{pol:<24}"
        for n in PRIORITARIOS_SENSIBILIDAD:
            bolsas_resto = P_CARRYON * PASAJEROS - P_CARRYON_PRIORITARIO * n
            p_resto = max(0.0, min(1.0, bolsas_resto / (PASAJEROS - n))) if n < PASAJEROS else 0.0
            t = resumen(correr(pol, n, max(150, ITERACIONES // 2),
                               p_prioritario=P_CARRYON_PRIORITARIO, p_resto=p_resto))
            fila += f"{t['media']:>12.0f}"
        print(fila)
    print("(segundos de llenado; misma cantidad de valijas en el avion, solo cambia quien las lleva)")

    for ruta in (grafico_tiempo(res, carpeta),
                 grafico_beneficio(res, carpeta),
                 grafico_indiferencia(res, carpeta)):
        print(f"\nGrafico guardado en: {ruta}")


if __name__ == "__main__":
    main()
