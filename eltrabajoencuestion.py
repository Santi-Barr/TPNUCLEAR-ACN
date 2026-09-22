import numpy as np
import time
import os
import csv


VELOCIDAD_NORMAL = 3
VELOCIDAD_CARRYON = 6
PROBABILIDAD_CARRYON = np.random.uniform(.4,.6) 
MAX_EN_PASILLO = None  # None = sin tope; el pasillo se llena hasta donde da la puerta


avion = [[0, 0, 0, 0, 0] for _ in range(25)]

asientos = set()
asientosVentanas = set()

for i in range(25*4):
    if(i%4 == 3 or i%4 == 0):
        asientosVentanas.add(i)
    asientos.add(i)

def RANDOM():
    nuevoPasajero = np.random.choice(list(asientos))
    fila = (nuevoPasajero//4)
    columna = (nuevoPasajero%4)
    if(columna <=1): columna-=2
    elif(columna >=2): columna-=1
    asientos.remove(nuevoPasajero)
    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])

    return {"posActual" : (0, 0), "dest" : (int(fila), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def WILMA():
    nuevoPasajero = -1
    if len(asientosVentanas) > 0:
        nuevoPasajero = np.random.choice(list(asientosVentanas))
        asientosVentanas.remove(nuevoPasajero)
    else:
        nuevoPasajero = np.random.choice(list(asientos))
    fila = nuevoPasajero//4
    columna = nuevoPasajero%4
    if(columna <=1): columna-=2
    else: columna-=1
    asientos.remove(nuevoPasajero)
    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])

    return {"posActual" : (0, 0), "dest" : (int(fila), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def BackToFrontUltimate():
    ultimos = sorted(asientos)[-20::]
    nuevoPasajero = np.random.choice(ultimos)
    fila = nuevoPasajero//4
    columna = nuevoPasajero%4
    if(columna <=1): columna-=2
    else: columna-=1
    asientos.remove(nuevoPasajero)
    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])
    
    return {"posActual" : (0, 0), "dest" : (int(fila), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def BackToFront():
    global fila_actual, libres
    # Avanza de atras hacia adelante salteando los asientos que no se vendieron.
    while True:
        if(len(libres) == 0):
            libres = [-2,-1,1,2]
            fila_actual -= 1
        if(fila_actual < 0):
            # Red de seguridad: no deberia pasar, pero evita un loop infinito.
            asiento = min(asientos)
            fila_actual = asiento//4
            columna = (asiento % 4) - 2 if (asiento % 4) <= 1 else (asiento % 4) - 1
            asientos.remove(asiento)
            break
        columna = np.random.choice(libres)
        libres.remove(columna)
        asiento = (fila_actual)*4 + (columna+1 if columna > 0 else columna+2)
        if(asiento in asientos):
            asientos.remove(asiento)
            break

    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])

    return {"posActual" : (0, 0), "dest" : (int(fila_actual), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def reset():
    global ventanaIzq, pasilloIzq, pasilloDer, ventanaDer, colaSteffen, t, pasajeros, avion, asientos, asientosVentanas, fila_actual, libres

    pasajeros = []
    t = 0

    avion = [[0, 0, 0, 0, 0] for _ in range(25)]

    # BackToFront arranca por la ultima fila y va hacia adelante
    fila_actual = len(avion) - 1
    libres = [-2,-1,1,2]

    asientos = set()
    asientosVentanas = set()
    #aca arranca la magia de estiven
    ventanaIzq = [4*fila for fila in reversed(range(25))]
    pasilloIzq = [4*fila + 1 for fila in reversed(range(25))]
    pasilloDer = [4*fila + 2 for fila in reversed(range(25))]
    ventanaDer = [4*fila + 3 for fila in reversed(range(25))]

    colaSteffen = []
    colaSteffen += [asiento for asiento in ventanaIzq if (asiento//4) % 2 == 0]  
    colaSteffen += [asiento for asiento in ventanaDer if (asiento//4) % 2 == 0]  
    colaSteffen += [asiento for asiento in ventanaIzq if (asiento//4) % 2 == 1]  
    colaSteffen += [asiento for asiento in ventanaDer if (asiento//4) % 2 == 1]  
    colaSteffen += [asiento for asiento in pasilloIzq if (asiento//4) % 2 == 0]  
    colaSteffen += [asiento for asiento in pasilloDer if (asiento//4) % 2 == 0]  
    colaSteffen += [asiento for asiento in pasilloIzq if (asiento//4) % 2 == 1]  
    colaSteffen += [asiento for asiento in pasilloDer if (asiento//4) % 2 == 1]  

def Steffen():
    nuevoEstiven = colaSteffen.pop(0)
    fila = nuevoEstiven//4 
    columna = nuevoEstiven%4 
    if(columna<=1): columna -=2
    else: columna -=1
    asientos.remove(nuevoEstiven)
    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])
        
    return {"posActual" : (0, 0), "dest" : (int(fila), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

#y funciona re piola mal


opciones = {
    '1' : Steffen,
    '2' : WILMA,
    '3' : RANDOM,
    '4' : BackToFront,
    '5' : BackToFrontUltimate,
}


def simular_una_vez(funcion_seleccionada, bloqueados=frozenset()):
    """Corre un embarque completo y devuelve cuantos segundos tardo.

    `bloqueados` es el conjunto de asientos que no se vendieron: nadie los
    ocupa, asi que ningun pasajero camina hasta ellos ni obliga a levantarse
    al vecino. Vacio = avion lleno (100 pasajeros)."""
    global t, pasajeros

    reset()


    for i in range(25*4):
        if(i in bloqueados):
            continue
        if(i%4 == 3 or i%4 == 0):
            asientosVentanas.add(i)
        asientos.add(i)

    # La cola de Steffen se arma en reset() con el avion lleno: hay que sacarle
    # los asientos bloqueados o intentaria sentar gente que no existe.
    colaSteffen[:] = [asiento for asiento in colaSteffen if asiento not in bloqueados]


    while(len(asientos) > 0 or (t>0 and len(pasajeros) > 0)):
        t+=1
        # Cada Iteracion = Un segundo

        #Esto depende de la politca (random)

        hayLugarEnPasillo = (MAX_EN_PASILLO is None or len(pasajeros) < MAX_EN_PASILLO)
        if(avion[0][2] == 0 and len(asientos) > 0 and hayLugarEnPasillo):
            pasajeros.append(funcion_seleccionada())
            
        # print(pasajeros)
        for pasajero in pasajeros:
            avion[pasajero["posActual"][0]][pasajero["posActual"][1]+ 2] = 1


            if(pasajero["esperar"] > 0):
                pasajero["esperar"]-=1
                #problema de indexacion
                if (pasajero["posActual"][0] + 1 < len(avion) and avion[pasajero["posActual"][0] + 1][2] != 0):
                    #tengo que esperar a que mueva
                    pasajero["esperar"] = 3
                continue
            if(pasajero["bajando"] > 0):
                pasajero["bajando"]-=1
                if(pasajero["bajando"] == 0):
                    avion[pasajero["posActual"][0]][pasajero["posActual"][1] + 2] = 0
                    pasajero["posActual"] = (pasajero["posActual"][0]+1, 0)
                    avion[pasajero["posActual"][0]][pasajero["posActual"][1] + 2] = 1
                continue

            if(pasajero["sentando"] > 0):
                pasajero["sentando"]-=1
                if(pasajero["sentando"] == 0):
                    avion[pasajero["posActual"][0]][pasajero["posActual"][1] + 2] = 0
                    pasajero["posActual"] = (pasajero["dest"][0],pasajero["dest"][1])
                    avion[pasajero["posActual"][0]][pasajero["posActual"][1] + 2] = 1
                continue
        
            # llegue?
            if(pasajero["posActual"][0] == pasajero["dest"][0]):
                # llegue a mi fila, ahora tengo que entrar
                if(pasajero["carryon"]):
                    pasajero["esperar"] = int(np.random.randint(7,15))
                    pasajero["carryon"] = False
                    continue

                # if estoy en la ventana y no hay chabon en medio, hay chabon en medio
                if((pasajero["dest"][1] == 2 and avion[pasajero["dest"][0]][3] != 0) or (pasajero["dest"][1] == -2 and avion[pasajero["dest"][0]][1] != 0)):
                    pasajero["sentando"] = int(np.random.randint(20,26))
                else:
                    pasajero["sentando"] = 5
            else:
                if (avion[pasajero["posActual"][0] + 1][2] != 0):
                    #tengo que esperar a que mueva
                    pasajero["esperar"] = 3
                else:
                    #bajo no?
                    if(pasajero["carryon"]):
                        pasajero["bajando"] = VELOCIDAD_CARRYON
                    else:
                        pasajero["bajando"] = VELOCIDAD_NORMAL
                    pass

            pass

        pasajeros = [p for p in pasajeros if p["posActual"] != p["dest"]]

        # os.system('clear')
        # for fila in avion:
        #     print(fila)

        # print()

        # time.sleep(.025)

    return t


def correr(funcion_seleccionada, iteraciones, mostrar_progreso=True, bloqueados=frozenset()):
    """Repite la simulacion N veces y devuelve la lista de tiempos."""
    tiempos = []
    for iteracion in range(iteraciones):
        tiempos.append(simular_una_vez(funcion_seleccionada, bloqueados))
        if(mostrar_progreso):
            print(f"Iteracion {iteracion+1} terminada.")
    return tiempos


def estadisticas(tiempos):
    iteraciones = len(tiempos)

    # 1. Calcular el promedio
    promedio = sum(tiempos) / iteraciones

    # 2. Sumar las diferencias al cuadrado
    suma_diferencias_cuadrado = 0
    for ti in tiempos:
        suma_diferencias_cuadrado += (ti - promedio) ** 2

    # 3. Calcular la varianza
    varianza = suma_diferencias_cuadrado / iteraciones
    std = varianza ** 0.5

    return promedio, std


def guardar_csv(resultados, nombre_archivo="resultados_simulacion.csv"):
    """Vuelca {politica: [tiempos]} a un CSV al lado de este script."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_archivo)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["Politica", "Tiempo_Total"])
        for politica, tiempos in resultados.items():
            for ti in tiempos:
                escritor.writerow([politica, ti])
    return ruta


if __name__ == "__main__":
    lineas_menu = [f"[{k}] {fn.__name__}" for k, fn in opciones.items()]
    lineas_menu.append("[T] Todas las politicas (guarda resultados_simulacion.csv)")

    opc = ""
    validas = list(opciones.keys()) + ['T']
    while(opc not in validas):
        opc = input("Seleccione una opcion para simular:\n" + "\n".join(lineas_menu) + "\n").strip().upper()

    iteraciones = ""
    while(not iteraciones.isnumeric()):
        iteraciones = input("Ingrese la cantidad de iteraciones que desea simular: ")
    iteraciones = int(iteraciones)

    if(opc == 'T'):
        # Una corrida por politica, todo a un mismo CSV para el analisis de costos.
        resultados = {}
        for fn in opciones.values():
            print(f"\nSimulando {fn.__name__}...")
            resultados[fn.__name__] = correr(fn, iteraciones, mostrar_progreso=False)
            promedio, std = estadisticas(resultados[fn.__name__])
            print(f"{fn.__name__}: promedio {promedio:.4f} s | std {std:.4f} s")

        ruta = guardar_csv(resultados)
        print(f"\nGuardado en: {ruta}")
    else:
        funcion_seleccionada = opciones.get(opc)
        tiempos = correr(funcion_seleccionada, iteraciones)
        promedio, std = estadisticas(tiempos)
        error_media = std / np.sqrt(len(tiempos))
        error_desvio = std / np.sqrt(2*len(tiempos))
        print(f"Promedio: {promedio:.4f} s")
        print(f"Desviación Estándar (std): {std:.4f} s")
        print(f"Error del desviación Estándar (std): {error_desvio:.4f} s")


