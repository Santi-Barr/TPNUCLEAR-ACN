import numpy as np
import time
import os


VELOCIDAD_NORMAL = 3
VELOCIDAD_CARRYON = 6
PROBABILIDAD_CARRYON = .5 #defini vos marcos


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
    ultimos = list(asientos)[-20::]    
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
    if(fila_actual>=0):
        if(len(libres) == 0): 
            libres = [-2,-1,1,2]
            fila_actual -= 1
        columna = np.random.choice(libres)
        libres.remove(columna)
        if(columna > 0):
            asientos.remove((fila_actual)*4 + columna+1)
        else:
            asientos.remove((fila_actual)*4 + columna+2)


    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])
    
    return {"posActual" : (0, 0), "dest" : (int(fila_actual), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def reset():
    global ventanaIzq, pasilloIzq, pasilloDer, ventanaDer, colaSteffen, t, pasajeros, avion, asientos, asientosVentanas

    pasajeros = []
    t = 0

    avion = [[0, 0, 0, 0, 0] for _ in range(25)]

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
lineas_menu = [f"[{k}] {fn.__name__}" for k, fn in opciones.items()]
opc = ""
while(opc not in opciones.keys()):
    opc = input("Seleccione una opcion para simular:\n" + "\n".join(lineas_menu) + "\n")

funcion_seleccionada = opciones.get(opc)
iteraciones = ""
while(not iteraciones.isnumeric()):
    iteraciones = input("Ingrese la cantidad de iteraciones que desea simular: ")

tiempos = []
iteraciones = int(iteraciones)
for iteracion in range(iteraciones):
    
    reset()


    for i in range(25*4):
        if(i%4 == 3 or i%4 == 0):
            asientosVentanas.add(i)
        asientos.add(i)


    while(len(asientos) > 0 or (t>0 and len(pasajeros) > 0)):
        t+=1
        # Cada Iteracion = Un segundo

        #Esto depende de la politca (random)

        if(avion[0][2] == 0 and len(asientos) > 0 and len(pasajeros) < 4):
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
                    pasajero["esperar"] = int(np.random.randint(5,11))
                    pasajero["carryon"] = False
                    continue

                # if estoy en la ventana y no hay chabon en medio, hay chabon en medio
                if((pasajero["dest"][1] == 2 and avion[pasajero["dest"][0]][3] != 0) or (pasajero["dest"][1] == -2 and avion[pasajero["dest"][0]][1] != 0)):
                    pasajero["sentando"] = 15
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

    print(f"Iteracion {iteracion+1} terminada.")

    tiempos.append(t)


# 1. Calcular el promedio
promedio = sum(tiempos) / iteraciones

# 2. Sumar las diferencias al cuadrado
suma_diferencias_cuadrado = 0
for ti in tiempos:
    suma_diferencias_cuadrado += (ti - promedio) ** 2

# 3. Calcular la varianza
varianza = suma_diferencias_cuadrado / iteraciones
std = varianza ** 0.5


print(f"Promedio: {promedio:.4f} s")
print(f"Desviación Estándar (std): {std:.4f} s")


