import numpy as np
import time
import os


VELOCIDAD_NORMAL = 3
VELOCIDAD_CARRYON = 6
PROBABILIDAD_CARRYON = .5 #defini vos marcos
np.random.uniform()


avion = [[0, 0, 0, 0, 0] for _ in range(25)]

asientos = set()
asientosVentanas = set()

stevens = [[]*8]


for i in range(25*4):
    if(i%4 == 3 or i%4 == 0):
        asientosVentanas.add(i)
        if(i%4 == 3):

            stevens[0].append(i)
        else:
            stevens[0]
    asientos.add(i)
fila_actual = 24
libres = [-2,-1,1,2]


def entraUnPajeroRandom():
    nuevoPasajero = np.random.choice(list(asientos))
    fila = (nuevoPasajero//4)
    columna = (nuevoPasajero%4)
    if(columna <=1): columna-=2
    elif(columna >=2): columna-=1
    asientos.remove(nuevoPasajero)
    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])

    return {"posActual" : (0, 0), "dest" : (int(fila), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def entraUnPajeroWILMA():
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

def entraUnPajeroB2FUltimate():
    ultimos = list(asientos)[-20::]    
    nuevoPasajero = np.random.choice(ultimos)
    fila = nuevoPasajero//4
    columna = nuevoPasajero%4
    if(columna <=1): columna-=2
    else: columna-=1
    asientos.remove(nuevoPasajero)
    tieneCarryOn = bool(np.random.binomial(n=1, p=PROBABILIDAD_CARRYON, size=1)[0])
    
    return {"posActual" : (0, 0), "dest" : (int(fila), int(columna)), "carryon" : tieneCarryOn, "esperar" : 0, "bajando" : 0, "sentando" : 0}

def entraUnPajeroB2F():
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

def entraEstiven():

    pass


pajeros = []

t = 0
while(len(asientos) > 0 or (t>0 and len(pajeros) > 0)):
    t+=1
    # Cada Iteracion = Un segundo

    print(pajeros)
    #Esto depende de la politca (random)

    if(avion[0][2] == 0 and len(asientos) > 0 and len(pajeros) < 4):
        pajeros.append(entraUnPajeroB2FUltimate())
        
    # print(pajeros)
    for pajero in pajeros:
        avion[pajero["posActual"][0]][pajero["posActual"][1]+ 2] = 1


        if(pajero["esperar"] > 0):
            pajero["esperar"]-=1
            #problema de indexacion
            if (pajero["posActual"][0] + 1 < len(avion) and avion[pajero["posActual"][0] + 1][2] != 0):
                #tengo que esperar a que mueva
                pajero["esperar"] = 3
            continue
        if(pajero["bajando"] > 0):
            pajero["bajando"]-=1
            if(pajero["bajando"] == 0):
                avion[pajero["posActual"][0]][pajero["posActual"][1] + 2] = 0
                pajero["posActual"] = (pajero["posActual"][0]+1, 0)
                avion[pajero["posActual"][0]][pajero["posActual"][1] + 2] = 1
            continue

        if(pajero["sentando"] > 0):
            pajero["sentando"]-=1
            if(pajero["sentando"] == 0):
                avion[pajero["posActual"][0]][pajero["posActual"][1] + 2] = 0
                pajero["posActual"] = (pajero["dest"][0],pajero["dest"][1])
                avion[pajero["posActual"][0]][pajero["posActual"][1] + 2] = 1
            continue
    
        # llegue?
        if(pajero["posActual"][0] == pajero["dest"][0]):
            # llegue a mi fila, ahora tengo que entrar
            if(pajero["carryon"]):
                pajero["esperar"] = int(np.random.random_integers(low=5, high=11))
                pajero["carryon"] = False
                continue

            # if estoy en la ventana y no hay chabon en medio, hay chabon en medio
            if((pajero["dest"][1] == 2 and avion[pajero["dest"][0]][3] != 0) or (pajero["dest"][1] == -2 and avion[pajero["dest"][0]][1] != 0)):
                pajero["sentando"] = 15
            else:
                pajero["sentando"] = 5
        else:
            if (avion[pajero["posActual"][0] + 1][2] != 0):
                #tengo que esperar a que mueva
                pajero["esperar"] = 3
            else:
                #bajo no?
                if(pajero["carryon"]):
                    pajero["bajando"] = VELOCIDAD_CARRYON
                else:
                    pajero["bajando"] = VELOCIDAD_NORMAL
                pass

        pass

    pajeros = [p for p in pajeros if p["posActual"] != p["dest"]]

    os.system('cls')
    for fila in avion:
        print(fila)

    print()

    time.sleep(.025)



    pass




