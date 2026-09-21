"""
Visualizacion con pygame del embarque del avion, politica por politica.

Replica la logica de simulacion de eltrabajoencuestion.py (ese archivo corre su
menu al importarse, asi que aca esta encapsulada en la clase Simulacion) y la
dibuja paso a paso.

Accesibilidad: la paleta es Okabe-Ito, pensada para daltonismo, y ademas ningun
estado se distingue SOLO por color: cada uno tiene su propia forma geometrica,
su etiqueta en la leyenda y su contador en vivo. Con la tecla D se puede simular
protanopia / deuteranopia / tritanopia para verificarlo en pantalla.

Controles
    1-5        elegir politica
    C          vista comparativa (las 5 politicas en paralelo, misma semilla)
    ESPACIO    pausar / reanudar
    -> (der)   avanzar un segundo simulado (en pausa)
    + / -      mas / menos velocidad
    R          reiniciar con semilla nueva
    D          ciclar modo de vision (normal / protanopia / deuteranopia / tritanopia)
    P          guardar captura PNG en ./capturas
    G          exportar un GIF de la corrida completa (de principio a fin)
    V          grabar / cortar un GIF en vivo de lo que se esta viendo
    ESC o Q    salir

Los GIF y las capturas van a ./capturas, listos para meter en la presentacion.
"""

import os
import sys

import numpy as np
import pygame

try:
    from PIL import Image, ImageDraw
    HAY_PIL = True
except ImportError:  # el resto de la visualizacion funciona igual, solo no exporta GIF
    HAY_PIL = False


# ----------------------------------------------------------------------------
# Parametros de la simulacion (mismos que eltrabajoencuestion.py)
# ----------------------------------------------------------------------------

FILAS = 25
VELOCIDAD_NORMAL = 3
VELOCIDAD_CARRYON = 6
MAX_EN_PASILLO = None  # None = sin tope


# ----------------------------------------------------------------------------
# Paleta Okabe-Ito. Validada: banda de luminosidad, piso de croma, separacion
# CVD y piso de vision normal. El unico par ajustado (rosa/verde, dE 7.6 en
# deuteranopia) queda cubierto por la codificacion secundaria: formas distintas
# + etiqueta + contador numerico.
# ----------------------------------------------------------------------------

AZUL      = (0x00, 0x72, 0xB2)   # caminando
NARANJA   = (0xE6, 0x9F, 0x00)   # guardando carry-on
VERDE     = (0x00, 0x9E, 0x73)   # sentado
ROSA      = (0xCC, 0x79, 0xA7)   # maniobra de sentarse
BERMELLON = (0xD5, 0x5E, 0x00)   # bloqueado
CELESTE   = (0x56, 0xB4, 0xE9)   # todavia no entro al avion

FONDO      = (0xFC, 0xFC, 0xFB)
FUSELAJE   = (0xF0, 0xEF, 0xEC)
PASILLO_BG = (0xE4, 0xE3, 0xDE)
ASIENTO_BG = (0xFF, 0xFF, 0xFF)
BORDE      = (0xC2, 0xC0, 0xB8)
TINTA      = (0x1A, 0x1A, 0x1A)
TINTA_2    = (0x5A, 0x58, 0x54)
TINTA_3    = (0x8A, 0x88, 0x84)

# Estados de un pasajero
CAMINANDO = "caminando"
BLOQUEADO = "bloqueado"
EQUIPAJE = "equipaje"
SENTANDO = "sentando"
SENTADO = "sentado"
EN_PUERTA = "en_puerta"

COLOR_ESTADO = {
    CAMINANDO: AZUL,
    BLOQUEADO: BERMELLON,
    EQUIPAJE: NARANJA,
    SENTANDO: ROSA,
    SENTADO: VERDE,
    EN_PUERTA: CELESTE,
}

ETIQUETA_ESTADO = {
    CAMINANDO: "Caminando",
    BLOQUEADO: "Bloqueado",
    EQUIPAJE: "Guardando carry-on",
    SENTANDO: "Sentandose",
    SENTADO: "Sentado",
    EN_PUERTA: "Sin entrar",
}

ORDEN_LEYENDA = [CAMINANDO, BLOQUEADO, EQUIPAJE, SENTANDO, SENTADO, EN_PUERTA]


# ----------------------------------------------------------------------------
# Simulacion de daltonismo: matrices de confusion aplicadas sobre la paleta
# ----------------------------------------------------------------------------

MATRICES_CVD = {
    "normal": None,
    "protanopia": ((0.567, 0.433, 0.000),
                   (0.558, 0.442, 0.000),
                   (0.000, 0.242, 0.758)),
    "deuteranopia": ((0.625, 0.375, 0.000),
                     (0.700, 0.300, 0.000),
                     (0.000, 0.300, 0.700)),
    "tritanopia": ((0.950, 0.050, 0.000),
                   (0.000, 0.433, 0.567),
                   (0.000, 0.475, 0.525)),
}
MODOS_CVD = list(MATRICES_CVD.keys())

_modo_cvd = "normal"
_cache_cvd = {}


def C(rgb):
    """Devuelve el color tal cual lo veria alguien con el tipo de vision activo."""
    if _modo_cvd == "normal":
        return rgb
    clave = (_modo_cvd, rgb)
    if clave not in _cache_cvd:
        m = MATRICES_CVD[_modo_cvd]
        r, g, b = rgb
        _cache_cvd[clave] = tuple(
            max(0, min(255, int(round(f[0] * r + f[1] * g + f[2] * b)))) for f in m
        )
    return _cache_cvd[clave]


# ----------------------------------------------------------------------------
# Simulacion
# ----------------------------------------------------------------------------

class Simulacion:
    """Una corrida de embarque. step() avanza exactamente un segundo simulado."""

    def __init__(self, clave_politica, semilla, p_carryon):
        self.clave = clave_politica
        self.nombre = NOMBRES_POLITICA[clave_politica]
        self.semilla = semilla
        self.p_carryon = p_carryon
        self.reset()

    def reset(self):
        self.rng = np.random.default_rng(self.semilla)
        self.t = 0
        self.pasajeros = []
        self.avion = [[0, 0, 0, 0, 0] for _ in range(FILAS)]
        self.ocupados = {}          # (fila, columna) -> True, para pintar asientos
        self.terminada = False

        self.asientos = set(range(FILAS * 4))
        self.asientosVentanas = {i for i in range(FILAS * 4) if i % 4 in (0, 3)}

        # BackToFront arranca por la ultima fila y va hacia adelante
        self.fila_actual = FILAS - 1
        self.libres = [-2, -1, 1, 2]

        # Cola de Steffen: ventanas pares, ventanas impares, pasillos pares, impares
        ventanaIzq = [4 * f for f in reversed(range(FILAS))]
        pasilloIzq = [4 * f + 1 for f in reversed(range(FILAS))]
        pasilloDer = [4 * f + 2 for f in reversed(range(FILAS))]
        ventanaDer = [4 * f + 3 for f in reversed(range(FILAS))]
        self.colaSteffen = []
        for grupo in (ventanaIzq, ventanaDer):
            self.colaSteffen += [a for a in grupo if (a // 4) % 2 == 0]
        for grupo in (ventanaIzq, ventanaDer):
            self.colaSteffen += [a for a in grupo if (a // 4) % 2 == 1]
        for grupo in (pasilloIzq, pasilloDer):
            self.colaSteffen += [a for a in grupo if (a // 4) % 2 == 0]
        for grupo in (pasilloIzq, pasilloDer):
            self.colaSteffen += [a for a in grupo if (a // 4) % 2 == 1]

        self.politica = {
            '1': self._steffen,
            '2': self._wilma,
            '3': self._random,
            '4': self._back_to_front,
            '5': self._back_to_front_ultimate,
        }[self.clave]

    # -- generadores de pasajero, uno por politica ---------------------------

    def _carryon(self):
        return bool(self.rng.binomial(n=1, p=self.p_carryon))

    def _pasajero(self, fila, columna):
        return {
            "posActual": (0, 0),
            "dest": (int(fila), int(columna)),
            "carryon": self._carryon(),
            "esperar": 0,
            "bajando": 0,
            "sentando": 0,
            "estado": CAMINANDO,
        }

    def _desde_indice(self, idx):
        fila = idx // 4
        columna = idx % 4
        columna = columna - 2 if columna <= 1 else columna - 1
        return self._pasajero(fila, columna)

    def _random(self):
        idx = int(self.rng.choice(sorted(self.asientos)))
        self.asientos.remove(idx)
        self.asientosVentanas.discard(idx)
        return self._desde_indice(idx)

    def _wilma(self):
        if self.asientosVentanas:
            idx = int(self.rng.choice(sorted(self.asientosVentanas)))
            self.asientosVentanas.remove(idx)
        else:
            idx = int(self.rng.choice(sorted(self.asientos)))
        self.asientos.remove(idx)
        return self._desde_indice(idx)

    def _back_to_front_ultimate(self):
        ultimos = sorted(self.asientos)[-20:]
        idx = int(self.rng.choice(ultimos))
        self.asientos.remove(idx)
        self.asientosVentanas.discard(idx)
        return self._desde_indice(idx)

    def _back_to_front(self):
        if len(self.libres) == 0:
            self.libres = [-2, -1, 1, 2]
            self.fila_actual -= 1
        columna = int(self.rng.choice(self.libres))
        self.libres.remove(columna)
        idx = self.fila_actual * 4 + (columna + 1 if columna > 0 else columna + 2)
        self.asientos.remove(idx)
        self.asientosVentanas.discard(idx)
        return self._pasajero(self.fila_actual, columna)

    def _steffen(self):
        idx = self.colaSteffen.pop(0)
        self.asientos.remove(idx)
        self.asientosVentanas.discard(idx)
        return self._desde_indice(idx)

    # -- un segundo de simulacion -------------------------------------------

    def step(self):
        if self.terminada:
            return
        self.t += 1

        hay_lugar = MAX_EN_PASILLO is None or len(self.pasajeros) < MAX_EN_PASILLO
        if self.avion[0][2] == 0 and len(self.asientos) > 0 and hay_lugar:
            self.pasajeros.append(self.politica())

        for p in self.pasajeros:
            self.avion[p["posActual"][0]][p["posActual"][1] + 2] = 1

            if p["esperar"] > 0:
                p["esperar"] -= 1
                # problema de indexacion en la ultima fila
                if (p["posActual"][0] + 1 < FILAS and self.avion[p["posActual"][0] + 1][2] != 0):
                    p["esperar"] = 3
                continue

            if p["bajando"] > 0:
                p["bajando"] -= 1
                if p["bajando"] == 0:
                    self.avion[p["posActual"][0]][p["posActual"][1] + 2] = 0
                    p["posActual"] = (p["posActual"][0] + 1, 0)
                    self.avion[p["posActual"][0]][p["posActual"][1] + 2] = 1
                continue

            if p["sentando"] > 0:
                p["sentando"] -= 1
                if p["sentando"] == 0:
                    self.avion[p["posActual"][0]][p["posActual"][1] + 2] = 0
                    p["posActual"] = (p["dest"][0], p["dest"][1])
                    self.avion[p["posActual"][0]][p["posActual"][1] + 2] = 1
                continue

            if p["posActual"][0] == p["dest"][0]:
                # llegue a mi fila, ahora tengo que entrar
                if p["carryon"]:
                    p["esperar"] = int(self.rng.integers(7, 15))
                    p["carryon"] = False
                    p["estado"] = EQUIPAJE
                    continue
                # si voy a la ventana y ya hay alguien en el medio, tarda mucho mas
                if ((p["dest"][1] == 2 and self.avion[p["dest"][0]][3] != 0)
                        or (p["dest"][1] == -2 and self.avion[p["dest"][0]][1] != 0)):
                    p["sentando"] = int(self.rng.integers(20, 26))
                else:
                    p["sentando"] = 5
                p["estado"] = SENTANDO
            else:
                if self.avion[p["posActual"][0] + 1][2] != 0:
                    p["esperar"] = 3
                    p["estado"] = BLOQUEADO
                else:
                    p["bajando"] = VELOCIDAD_CARRYON if p["carryon"] else VELOCIDAD_NORMAL
                    p["estado"] = CAMINANDO

        for p in self.pasajeros:
            if p["posActual"] == p["dest"]:
                self.ocupados[p["dest"]] = True
        self.pasajeros = [p for p in self.pasajeros if p["posActual"] != p["dest"]]

        if not self.asientos and not self.pasajeros:
            self.terminada = True

    # -- lecturas para el dibujo --------------------------------------------

    def conteos(self):
        c = {e: 0 for e in ORDEN_LEYENDA}
        for p in self.pasajeros:
            c[p["estado"]] += 1
        c[SENTADO] = len(self.ocupados)
        c[EN_PUERTA] = len(self.asientos)
        return c

    @property
    def sentados(self):
        return len(self.ocupados)


NOMBRES_POLITICA = {
    '1': "Steffen",
    '2': "WILMA",
    '3': "Random",
    '4': "BackToFront",
    '5': "BackToFrontUltimate",
}
CLAVES = ['1', '2', '3', '4', '5']


# ----------------------------------------------------------------------------
# Dibujo
# ----------------------------------------------------------------------------

ANCHO, ALTO = 1320, 800
VELOCIDADES = [1, 2, 5, 10, 20, 30, 60, 120, 240]

# Exportacion de GIF. Bajar GIF_ESCALA o GIF_COLORES si el archivo pesa mucho.
GIF_ESCALA = 0.65           # 1320x800 -> 858x520
GIF_FPS = 20                # cuadros por segundo del GIF resultante
GIF_COLORES = 64            # paleta del GIF (la imagen tiene pocos colores planos)
GIF_FRAMES_CORRIDA = 200    # cuadros para el GIF de una corrida completa
GIF_MAX_FRAMES_VIVO = 300   # tope de la grabacion en vivo, para no comerse la RAM
GIF_CADA_N_CUADROS = 3      # en vivo: captura 1 de cada N cuadros dibujados

# carril de pantalla para cada columna logica (-2, -1, pasillo, 1, 2)
CARRIL = {-2: 0, -1: 1, 0: 2, 1: 3, 2: 4}
LETRA_ASIENTO = {0: "A", 1: "B", 3: "C", 4: "D"}


def marca(sup, estado, cx, cy, r):
    """Cada estado tiene forma propia, no solo color: asi se lee sin ver el color."""
    col = C(COLOR_ESTADO[estado])
    oscuro = C(tuple(int(v * 0.55) for v in COLOR_ESTADO[estado]))

    if estado == CAMINANDO:
        pts = [(cx - r * 0.70, cy - r), (cx - r * 0.70, cy + r), (cx + r, cy)]
        pygame.draw.polygon(sup, col, pts)
        pygame.draw.polygon(sup, oscuro, pts, 2)

    elif estado == BLOQUEADO:
        w = max(2, int(r * 0.52))
        for dx in (-r * 0.72, r * 0.20):
            rc = pygame.Rect(int(cx + dx), int(cy - r), w, int(r * 2))
            pygame.draw.rect(sup, col, rc, border_radius=2)
            pygame.draw.rect(sup, oscuro, rc, 2, border_radius=2)

    elif estado == EQUIPAJE:
        cuerpo = pygame.Rect(int(cx - r * 0.85), int(cy - r * 0.50),
                             int(r * 1.70), int(r * 1.35))
        pygame.draw.rect(sup, col, cuerpo, border_radius=3)
        pygame.draw.rect(sup, oscuro, cuerpo, 2, border_radius=3)
        asa = pygame.Rect(int(cx - r * 0.35), int(cy - r * 0.95),
                          int(r * 0.70), int(r * 0.50))
        pygame.draw.rect(sup, oscuro, asa, 2, border_radius=2)

    elif estado == SENTANDO:
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(sup, col, pts)
        pygame.draw.polygon(sup, oscuro, pts, 2)

    elif estado == SENTADO:
        pygame.draw.circle(sup, col, (int(cx), int(cy)), int(r * 0.88))
        pygame.draw.circle(sup, oscuro, (int(cx), int(cy)), int(r * 0.88), 2)

    elif estado == EN_PUERTA:
        pygame.draw.circle(sup, C(FONDO), (int(cx), int(cy)), int(r * 0.88))
        pygame.draw.circle(sup, col, (int(cx), int(cy)), int(r * 0.88), max(2, int(r * 0.38)))


def dibujar_avion(sup, sim, x0, y0, celda, con_etiquetas=True, fuente=None):
    """Dibuja el fuselaje, los asientos y los pasajeros. Fila 0 = puerta (izquierda)."""
    ancho = FILAS * celda
    alto = 5 * celda

    pygame.draw.rect(sup, C(FUSELAJE),
                     pygame.Rect(x0 - 6, y0 - 6, ancho + 12, alto + 12),
                     border_radius=int(celda * 0.8))
    pygame.draw.rect(sup, C(BORDE),
                     pygame.Rect(x0 - 6, y0 - 6, ancho + 12, alto + 12),
                     2, border_radius=int(celda * 0.8))

    # pasillo de fondo
    pygame.draw.rect(sup, C(PASILLO_BG),
                     pygame.Rect(x0, y0 + 2 * celda, ancho, celda))

    pad = max(1, celda // 10)
    for fila in range(FILAS):
        for carril in range(5):
            x = x0 + fila * celda
            y = y0 + carril * celda
            if carril == 2:
                continue  # el pasillo ya esta pintado de fondo
            columna = [-2, -1, 0, 1, 2][carril]
            rc = pygame.Rect(x + pad, y + pad, celda - 2 * pad, celda - 2 * pad)
            ocupado = (fila, columna) in sim.ocupados
            pygame.draw.rect(sup, C(ASIENTO_BG), rc, border_radius=max(2, celda // 6))
            pygame.draw.rect(sup, C(BORDE), rc, 1, border_radius=max(2, celda // 6))
            if ocupado:
                marca(sup, SENTADO, rc.centerx, rc.centery, celda * 0.32)

    # pasajeros que todavia estan en el pasillo
    for p in sim.pasajeros:
        fila, columna = p["posActual"]
        x = x0 + fila * celda + celda / 2
        y = y0 + CARRIL[columna] * celda + celda / 2
        marca(sup, p["estado"], x, y, celda * 0.34)

    if con_etiquetas and fuente is not None:
        for carril in (0, 1, 3, 4):
            txt = fuente.render(LETRA_ASIENTO[carril], True, C(TINTA_3))
            sup.blit(txt, (x0 - 10 - txt.get_width(),
                           y0 + carril * celda + celda / 2 - txt.get_height() / 2))
        for fila in range(0, FILAS, 5):
            txt = fuente.render(str(fila + 1), True, C(TINTA_3))
            sup.blit(txt, (x0 + fila * celda + celda / 2 - txt.get_width() / 2,
                           y0 - 10 - txt.get_height()))
        puerta = fuente.render("puerta", True, C(TINTA_3))
        sup.blit(puerta, (x0 - 10 - puerta.get_width(), y0 + alto + 8))


def barra_progreso(sup, x, y, ancho, alto, fraccion, color):
    pygame.draw.rect(sup, C(PASILLO_BG), pygame.Rect(x, y, ancho, alto),
                     border_radius=alto // 2)
    w = int(ancho * max(0.0, min(1.0, fraccion)))
    if w > 0:
        pygame.draw.rect(sup, C(color), pygame.Rect(x, y, max(w, alto), alto),
                         border_radius=alto // 2)


# ----------------------------------------------------------------------------
# Grabacion de GIF
# ----------------------------------------------------------------------------

class Grabador:
    """Junta cuadros ya escalados y los escribe como un GIF animado."""

    def __init__(self):
        self.cuadros = []
        self.tam = None
        self.grabando = False

    def limpiar(self):
        self.cuadros = []

    def capturar(self, pantalla):
        ancho = int(pantalla.get_width() * GIF_ESCALA)
        alto = int(pantalla.get_height() * GIF_ESCALA)
        chica = pygame.transform.smoothscale(pantalla, (ancho, alto))
        self.tam = (ancho, alto)
        self.cuadros.append(pygame.image.tostring(chica, "RGB"))

    def _paleta_global(self, muestra):
        """
        Paleta unica para todo el GIF.

        Si la saco solo de un cuadro, los colores con poca superficie (el rosa de
        "sentandose", que a veces son dos rombos en toda la pantalla) se pierden
        al cuantizar y salen grises. Asi que le pego abajo una banda con los
        colores de la paleta, para que ocupen area suficiente y cada uno se lleve
        su lugar en los GIF_COLORES.
        """
        criticos = []
        for estado in ORDEN_LEYENDA:
            base = COLOR_ESTADO[estado]
            criticos.append(C(base))
            criticos.append(C(tuple(int(v * 0.55) for v in base)))
        criticos += [C(c) for c in (FONDO, FUSELAJE, PASILLO_BG, ASIENTO_BG,
                                    BORDE, TINTA, TINTA_2, TINTA_3)]

        banda = max(1, muestra.height // 4)
        lienzo = Image.new("RGB", (muestra.width, muestra.height + banda))
        lienzo.paste(muestra, (0, 0))
        dibujo = ImageDraw.Draw(lienzo)
        ancho = muestra.width / len(criticos)
        for i, col in enumerate(criticos):
            dibujo.rectangle([i * ancho, muestra.height,
                              (i + 1) * ancho, lienzo.height], fill=col)
        return lienzo.quantize(colors=GIF_COLORES)

    def guardar(self, ruta):
        """Escribe el GIF y devuelve el mensaje a mostrar en pantalla."""
        if not HAY_PIL:
            return "Falta Pillow para exportar GIF:  pip install Pillow"
        if not self.cuadros:
            return "No hay nada grabado"

        imgs = [Image.frombytes("RGB", self.tam, c) for c in self.cuadros]

        # Una sola paleta para todos los cuadros: evita el parpadeo de color y
        # deja que Pillow comprima por diferencias entre cuadros.
        try:
            sin_dither = Image.Dither.NONE
        except AttributeError:  # Pillow viejo
            sin_dither = Image.NONE
        paleta = self._paleta_global(imgs[len(imgs) // 2])
        indexados = [im.quantize(palette=paleta, dither=sin_dither) for im in imgs]

        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        indexados[0].save(
            ruta,
            save_all=True,
            append_images=indexados[1:],
            duration=int(round(1000 / GIF_FPS)),
            loop=0,
            optimize=True,
            disposal=1,
        )
        mb = os.path.getsize(ruta) / (1024 * 1024)
        n = len(indexados)
        self.limpiar()
        print(f"GIF guardado en {ruta}  ({n} cuadros, {mb:.1f} MB)")
        return f"GIF guardado: {os.path.basename(ruta)}  ({n} cuadros, {mb:.1f} MB)"


# ----------------------------------------------------------------------------
# Aplicacion
# ----------------------------------------------------------------------------

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Embarque del avion - visualizacion por politica")
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()

        self.f_titulo = pygame.font.SysFont("segoe ui,arial", 26, bold=True)
        self.f_sub = pygame.font.SysFont("segoe ui,arial", 15)
        self.f_bold = pygame.font.SysFont("segoe ui,arial", 15, bold=True)
        self.f_num = pygame.font.SysFont("consolas,courier new", 30, bold=True)
        self.f_mini = pygame.font.SysFont("segoe ui,arial", 12)

        self.clave = '1'
        self.vista = "individual"
        self.pausado = False
        self.vel_idx = 4          # 20 pasos por segundo
        self.acumulador = 0.0
        self.resultados = {}      # nombre de politica -> t final
        self.grabador = Grabador()
        self.cuadros_dibujados = 0
        self.mensaje = ""
        self.mensaje_hasta = 0
        self.nueva_corrida()

    # -- estado --------------------------------------------------------------

    def nueva_corrida(self, semilla=None):
        self.semilla = int(np.random.SeedSequence().entropy % 100000) if semilla is None else semilla
        # p(carry-on) se sortea una vez por corrida, igual que en el original
        self.p_carryon = float(np.random.default_rng(self.semilla).uniform(0.4, 0.6))
        self.sim = Simulacion(self.clave, self.semilla, self.p_carryon)
        # misma semilla para las cinco, asi la comparacion es justa
        self.sims = {k: Simulacion(k, self.semilla, self.p_carryon) for k in CLAVES}
        self.acumulador = 0.0

    def cambiar_politica(self, clave):
        self.clave = clave
        self.sim = Simulacion(clave, self.semilla, self.p_carryon)
        self.acumulador = 0.0

    def avanzar_sims(self, n=1):
        """Avanza la simulacion sin tocar el registro de resultados."""
        for _ in range(n):
            if self.vista == "individual":
                self.sim.step()
            else:
                for s in self.sims.values():
                    s.step()

    def avanzar(self, n=1):
        for _ in range(n):
            if self.vista == "individual":
                antes = self.sim.terminada
                self.sim.step()
                if self.sim.terminada and not antes:
                    self.resultados[self.sim.nombre] = self.sim.t
            else:
                for s in self.sims.values():
                    antes = s.terminada
                    s.step()
                    if s.terminada and not antes:
                        self.resultados[s.nombre] = s.t

    # -- dibujo --------------------------------------------------------------

    def texto(self, s, x, y, fuente, color=TINTA, derecha=False, centro=False):
        img = fuente.render(s, True, C(color))
        if derecha:
            x -= img.get_width()
        elif centro:
            x -= img.get_width() / 2
        self.pantalla.blit(img, (x, y))
        return img.get_width()

    def dibujar_leyenda(self, x, y, ancho, conteos):
        paso = ancho / len(ORDEN_LEYENDA)
        for i, estado in enumerate(ORDEN_LEYENDA):
            cx = x + i * paso
            marca(self.pantalla, estado, cx + 13, y + 13, 11)
            self.texto(ETIQUETA_ESTADO[estado], cx + 30, y + 1, self.f_mini, TINTA_2)
            self.texto(str(conteos[estado]), cx + 30, y + 14, self.f_bold, TINTA)

    def dibujar_individual(self):
        sim = self.sim
        conteos = sim.conteos()

        self.texto(f"Embarque  -  {sim.nombre}", 40, 26, self.f_titulo)
        self.texto(f"vision: {_modo_cvd}", ANCHO - 40, 20, self.f_bold, TINTA_2, derecha=True)
        self.texto(f"semilla {self.semilla}   p(carry-on) = {self.p_carryon:.2f}",
                   ANCHO - 40, 40, self.f_mini, TINTA_3, derecha=True)
        estado_txt = ("TERMINADO" if sim.terminada
                      else ("EN PAUSA" if self.pausado else f"x{VELOCIDADES[self.vel_idx]}"))
        self.texto(f"t = {sim.t} s   ({estado_txt})", 40, 58, self.f_sub, TINTA_2)

        celda = 44
        x0 = (ANCHO - FILAS * celda) // 2
        y0 = 140
        dibujar_avion(self.pantalla, sim, x0, y0, celda, True, self.f_mini)

        ancho = FILAS * celda
        barra_progreso(self.pantalla, x0, y0 + 5 * celda + 34, ancho, 14,
                       sim.sentados / (FILAS * 4), VERDE)
        self.texto(f"{sim.sentados} / {FILAS * 4} sentados", x0, y0 + 5 * celda + 54,
                   self.f_mini, TINTA_2)
        self.texto(f"{len(sim.pasajeros)} en el pasillo", x0 + ancho,
                   y0 + 5 * celda + 54, self.f_mini, TINTA_2, derecha=True)

        self.dibujar_leyenda(x0, y0 + 5 * celda + 90, ancho, conteos)

        # tiempos ya medidos, para comparar de un vistazo
        y = y0 + 5 * celda + 150
        self.texto("Tiempos medidos en esta sesion", x0, y, self.f_bold, TINTA_2)
        y += 24
        if not self.resultados:
            self.texto("(todavia ninguna corrida completa)", x0, y, self.f_mini, TINTA_3)
        else:
            peor = max(self.resultados.values())
            for nombre, t in sorted(self.resultados.items(), key=lambda kv: kv[1]):
                self.texto(nombre, x0, y, self.f_sub, TINTA)
                barra_progreso(self.pantalla, x0 + 210, y + 5, 420, 10, t / peor, AZUL)
                self.texto(f"{t} s", x0 + 650, y, self.f_sub, TINTA_2)
                y += 24

        self.pie()

    def dibujar_comparacion(self):
        self.texto("Comparacion de politicas  -  misma semilla, mismo p(carry-on)",
                   40, 26, self.f_titulo)
        self.texto(f"vision: {_modo_cvd}", ANCHO - 40, 20, self.f_bold, TINTA_2, derecha=True)
        self.texto(f"semilla {self.semilla}   p(carry-on) = {self.p_carryon:.2f}",
                   ANCHO - 40, 40, self.f_mini, TINTA_3, derecha=True)

        celda = 20
        x0 = 250
        y = 96
        conteos_totales = {e: 0 for e in ORDEN_LEYENDA}
        for clave in CLAVES:
            s = self.sims[clave]
            c = s.conteos()
            for e in ORDEN_LEYENDA:
                conteos_totales[e] += c[e]

            self.texto(s.nombre, 40, y + 20, self.f_bold, TINTA)
            self.texto(f"t = {s.t} s" + ("  listo" if s.terminada else ""),
                       40, y + 40, self.f_sub, TINTA_2 if not s.terminada else VERDE)
            barra_progreso(self.pantalla, 40, y + 66, 190, 8,
                           s.sentados / (FILAS * 4), VERDE)

            dibujar_avion(self.pantalla, s, x0, y, celda, False)

            dx = x0 + FILAS * celda + 40
            self.texto(f"{s.sentados}/100 sentados", dx, y + 18, self.f_sub, TINTA_2)
            self.texto(f"{len(s.pasajeros)} en pasillo", dx, y + 38, self.f_sub, TINTA_2)
            self.texto(f"{c[BLOQUEADO]} bloqueados", dx, y + 58, self.f_sub, TINTA_2)
            y += 5 * celda + 20

        self.dibujar_leyenda(40, y + 8, ANCHO - 80, conteos_totales)
        self.pie()

    def pie(self):
        ayuda1 = ("1-5 politica   C comparar   ESPACIO pausa   -> paso   +/- velocidad   "
                  "R reiniciar   D vision daltonica")
        ayuda2 = "P captura PNG   G exportar GIF de la corrida   V grabar GIF en vivo   ESC salir"
        self.texto(ayuda1, ANCHO // 2, ALTO - 42, self.f_mini, TINTA_3, centro=True)
        self.texto(ayuda2, ANCHO // 2, ALTO - 26, self.f_mini, TINTA_3, centro=True)

        if self.mensaje and pygame.time.get_ticks() < self.mensaje_hasta:
            self.texto(self.mensaje, ANCHO // 2, ALTO - 66, self.f_bold, TINTA, centro=True)

    def avisar(self, texto, segundos=5):
        self.mensaje = texto
        self.mensaje_hasta = pygame.time.get_ticks() + int(segundos * 1000)

    # -- salidas a archivo ---------------------------------------------------

    def carpeta_salida(self):
        carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capturas")
        os.makedirs(carpeta, exist_ok=True)
        return carpeta

    def nombre_base(self):
        if self.vista == "individual":
            return f"{self.sim.nombre}_semilla{self.semilla}"
        return f"comparacion_semilla{self.semilla}"

    def captura(self):
        t = self.sim.t if self.vista == "individual" else max(s.t for s in self.sims.values())
        ruta = os.path.join(self.carpeta_salida(),
                            f"{self.nombre_base()}_t{t}_{_modo_cvd}.png")
        pygame.image.save(self.pantalla, ruta)
        print(f"captura guardada en {ruta}")
        self.avisar(f"PNG guardado: {os.path.basename(ruta)}")

    def dibujar_vista(self):
        self.pantalla.fill(C(FONDO))
        if self.vista == "individual":
            self.dibujar_individual()
        else:
            self.dibujar_comparacion()

    def pantalla_progreso(self, fraccion, detalle):
        """Mientras se exporta el GIF la ventana no se queda congelada."""
        pygame.event.pump()
        self.pantalla.fill(C(FONDO))
        self.texto("Exportando GIF...", ANCHO // 2, ALTO // 2 - 60, self.f_titulo,
                   TINTA, centro=True)
        barra_progreso(self.pantalla, ANCHO // 2 - 300, ALTO // 2, 600, 16, fraccion, AZUL)
        self.texto(detalle, ANCHO // 2, ALTO // 2 + 28, self.f_sub, TINTA_2, centro=True)
        pygame.display.flip()

    def exportar_corrida(self):
        """
        GIF de la corrida entera, de la puerta vacia al avion lleno.

        Va en dos pasadas sobre la misma semilla: la primera mide cuanto dura el
        embarque, la segunda lo vuelve a correr dibujando un cuadro cada tantos
        segundos simulados. Asi el GIF siempre entra en GIF_FRAMES_CORRIDA
        cuadros, sin importar si la politica tarda 1300 o 2200 segundos, y no
        depende de la velocidad de reproduccion que tuvieras puesta.
        """
        if not HAY_PIL:
            self.avisar("Falta Pillow para exportar GIF:  pip install Pillow", 8)
            return

        claves = [self.clave] if self.vista == "individual" else CLAVES

        # pasada 1: cuanto dura
        total = 0
        for k in claves:
            s = Simulacion(k, self.semilla, self.p_carryon)
            while not s.terminada:
                s.step()
            total = max(total, s.t)
        cada = max(1, total // GIF_FRAMES_CORRIDA)

        # pasada 2: la misma corrida, dibujada
        guardado = (self.sim, self.sims)
        self.sim = Simulacion(self.clave, self.semilla, self.p_carryon)
        self.sims = {k: Simulacion(k, self.semilla, self.p_carryon) for k in CLAVES}
        self.grabador.limpiar()

        t = 0
        while t <= total:
            self.dibujar_vista()
            self.grabador.capturar(self.pantalla)
            if len(self.grabador.cuadros) % 10 == 0:
                self.pantalla_progreso(t / max(total, 1),
                                       f"{len(self.grabador.cuadros)} cuadros   "
                                       f"t = {t} / {total} s simulados")
            for _ in range(cada):
                self.avanzar_sims(1)
            t += cada

        # ultimo cuadro: el avion lleno, que es el que queda congelado al final
        self.dibujar_vista()
        for _ in range(GIF_FPS):  # ~1 segundo de pausa al terminar el loop
            self.grabador.capturar(self.pantalla)

        for k in claves:
            s = self.sim if self.vista == "individual" else self.sims[k]
            self.resultados[s.nombre] = s.t

        self.pantalla_progreso(1.0, "escribiendo el archivo...")
        ruta = os.path.join(self.carpeta_salida(),
                            f"{self.nombre_base()}_{_modo_cvd}.gif")
        msj = self.grabador.guardar(ruta)

        self.sim, self.sims = guardado
        self.avisar(msj, 8)

    def alternar_grabacion_vivo(self):
        if not HAY_PIL:
            self.avisar("Falta Pillow para exportar GIF:  pip install Pillow", 8)
            return
        if self.grabador.grabando:
            self.grabador.grabando = False
            ruta = os.path.join(self.carpeta_salida(),
                                f"{self.nombre_base()}_envivo_{_modo_cvd}.gif")
            self.avisar(self.grabador.guardar(ruta), 8)
        else:
            self.grabador.limpiar()
            self.grabador.grabando = True
            self.avisar("Grabando. V de nuevo para cortar y guardar.", 3)

    def indicador_rec(self):
        n = len(self.grabador.cuadros)
        x, y = ANCHO - 40, 74
        txt = f"REC  {n} / {GIF_MAX_FRAMES_VIVO} cuadros"
        ancho = self.f_bold.size(txt)[0]
        pygame.draw.circle(self.pantalla, C(BERMELLON), (x - ancho - 16, y + 8), 7)
        self.texto(txt, x, y, self.f_bold, BERMELLON, derecha=True)

    # -- loop ----------------------------------------------------------------

    def run(self):
        global _modo_cvd
        corriendo = True
        while corriendo:
            dt = self.reloj.tick(60) / 1000.0

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    corriendo = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                        corriendo = False
                    elif ev.unicode in CLAVES:
                        self.vista = "individual"
                        self.cambiar_politica(ev.unicode)
                    elif ev.key == pygame.K_c:
                        self.vista = "comparar" if self.vista == "individual" else "individual"
                        self.acumulador = 0.0
                    elif ev.key == pygame.K_SPACE:
                        self.pausado = not self.pausado
                    elif ev.key == pygame.K_RIGHT:
                        self.pausado = True
                        self.avanzar(1)
                    elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        self.vel_idx = min(self.vel_idx + 1, len(VELOCIDADES) - 1)
                    elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.vel_idx = max(self.vel_idx - 1, 0)
                    elif ev.key == pygame.K_r:
                        self.resultados.clear()
                        self.nueva_corrida()
                    elif ev.key == pygame.K_d:
                        _modo_cvd = MODOS_CVD[(MODOS_CVD.index(_modo_cvd) + 1) % len(MODOS_CVD)]
                    elif ev.key == pygame.K_p:
                        self.captura()
                    elif ev.key == pygame.K_g:
                        self.exportar_corrida()
                    elif ev.key == pygame.K_v:
                        self.alternar_grabacion_vivo()

            if not self.pausado:
                self.acumulador += dt * VELOCIDADES[self.vel_idx]
                pasos = int(self.acumulador)
                if pasos:
                    self.acumulador -= pasos
                    self.avanzar(min(pasos, 400))

            self.dibujar_vista()

            if self.grabador.grabando:
                self.cuadros_dibujados += 1
                if self.cuadros_dibujados % GIF_CADA_N_CUADROS == 0:
                    self.grabador.capturar(self.pantalla)
                    if len(self.grabador.cuadros) >= GIF_MAX_FRAMES_VIVO:
                        self.alternar_grabacion_vivo()  # llego al tope: corta y guarda
                self.indicador_rec()

            pygame.display.flip()

        if self.grabador.grabando:  # si cerras la ventana grabando, no se pierde
            self.grabador.grabando = False
            self.grabador.guardar(os.path.join(
                self.carpeta_salida(), f"{self.nombre_base()}_envivo_{_modo_cvd}.gif"))

        pygame.quit()
        if self.resultados:
            print("\nTiempos de embarque de esta sesion:")
            for nombre, t in sorted(self.resultados.items(), key=lambda kv: kv[1]):
                print(f"  {nombre:<22} {t} s")


if __name__ == "__main__":
    App().run()
    sys.exit(0)
