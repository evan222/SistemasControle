import kivy

kivy.require('1.9.1')  # replace with your current kivy version !

from kivy.app import App

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle

from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
# from kivy.uix.switch import Switch

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel
# from kivy.uix.image import Image

# para o grafico:
from math import sin
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
from threading import Thread
from kivy.garden.bar import Bar

import quanser
import threading
import sys
import Signal
import time

##VARIAVEIS GLOBAIS:

flag_controle = 1 #comeca com controle direto

flag_malha = 1  # 0 = malha aberta / 1  = malha fechada
flag_signal = 1
## "1 - Degrau\n"
## "2 - Onda Senoidal\n"
## "3 - Onda Quadrada\n"
## "4 - Onda tipo dente de serra\n"	
## "5 - Sinal Aleatorio\n"
flag_pid = 0   ##USADA APENAS PRA NAO DAR ERRO
T1_flag_pid = 0
T2_flag_pid = 0
##"""
##flag_pid=0 -> controle P
##flag_pid=1 -> controle PD
##flag_pid=2 -> controle PI
##flag_pid=3 -> controle PID
##flag_pid=4 -> controle PI-D
##"""
flag = True # flag do tempo de subida
flag_subida = True
flag_overshoot = True # flag do overshoot
flag_overshoot_subida = True
flag_mudou_setPoint =  False
flag_acomodacao = True
flag_verifica_overshoot = True
##Para controle simples: tipo_controle = 0
##Para controle em cascata: tipo_controle = 1
tipo_controle = 1

valor_entrada = 0
periodo = 1
offset = 0
tensao_max = 3
tensao_min = -3
setpoint_ME = 0.0

# Variaveis do controlador PID
Derivator = 0.0
Integrator = 0.0
T1_Derivator = 0.0
T1_Integrator = 0.0
T2_Derivator = 0.0
T2_Integrator = 0.0
Integrator_max = 100
Integrator_min = -100
last_time = 0

# Constantes do Controlador PID
taud = 0.0
taui = 0.0
Kd = 0.0
Kp = 0.0
Ki = 0.0
PID = 0.0
T1_taud = 0.0
T1_taui = 0.0
T1_Kd = 0.0
T1_Kp = 0.0
T1_Ki = 0.0
T2_taud = 0.0
T2_taui = 0.0
T2_Kd = 0.0
T2_Kp = 0.0
T2_Ki = 0.0

##variaveis de controle da interface/sistema
Start = False
lista_saida = [(0, 0)]
lista_tensao = [(0, 0)]
lista_setpoint = [(0, 0)]
lista_setpoint_ME = [(0, 0)]
lista_altura_tanque1 = [(0, 0)]
lista_altura_tanque2 = [(0, 0)]
contador = 0

x_axis_range = 0.0
nivel_tanque = 0.0
channel = 0

##Variaveis de resposta do Sistema
overshoot = 0.0
overshootPercentual = 0.0
antigo_setPoint = 0.0
tempo_subida = 0.0
tempo_acomodacao = 0.0
tempo_acomodacao_inicial = 0.0
valor_passado = 0.0

##Tanque 1 resposta do Sistema
T1_overshoot = 0.0
T1_overshootPercentual = 0.0
T1_antigo_setPoint = 0.0
T1_tempo_subida = 0.0
T1_tempo_acomodacao = 0.0
T1_tempo_acomodacao_inicial = 0.0
T1_valor_passado = 0.0

##Tanque 2 resposta do Sistema
T2_overshoot = 0.0
T2_overshootPercentual = 0.0
T2_antigo_setPoint = 0.0
T2_tempo_subida = 0.0
T2_tempo_acomodacao = 0.0
T2_tempo_acomodacao_inicial = 0.0
T2_valor_passado = 0.0

#Variaveis do tempo de subida
tempo_final = 0.0
tempo_inicial = 0.0

##Tanque 1 tempo de subida
T1_tempo_final = 0.0
T1_tempo_inicial = 0.0

##Tanque 2 tempo de subida
T2_tempo_final = 0.0
T2_tempo_inicial = 0.0

##flags do tanque 1
T1_flag = True # flag do tempo de subida
T1_flag_subida = True
T1_flag_overshoot = True # flag do overshoot
T1_flag_overshoot_subida = True
T1_flag_mudou_setPoint =  False
T1_flag_acomodacao = True
T1_flag_verifica_overshoot = True

##flags do tanque 2
T2_flag = True # flag do tempo de subida
T2_flag_subida = True
T2_flag_overshoot = True # flag do overshoot
T2_flag_overshoot_subida = True
T2_flag_mudou_setPoint =  False
T2_flag_acomodacao = True
T2_flag_verifica_overshoot = True

##-------------------------------------------
def readSensor(channel):
    global conn
    return conn.readAD(channel)


def getAltura(channel):
    global conn
    tensao = readSensor(channel)
    return float(tensao * 6.25)


def startConnection(IP, porta):
    global conn
    try:
        conn = quanser.Quanser(IP, porta)
        # print "aqui"
        print "Conectado!"
    except:
        print 'Nao conectou!'


def endConnection(channel):
    global conn
    try:
        conn.writeDA(channel, 0)
        print("WriteDA")
        conn.closeServer()
    except:
        print 'Nao encerrou!'


def writeTensao(channel, volts):
    global conn, tensao_max, tensao_min
    if volts > tensao_max:
        volts = tensao_max
    elif volts < tensao_min:
        volts = tensao_min

    altura = getAltura(channel)

    if altura <= 2 and volts < 0:
        volts = 0
    elif altura >= 28 and altura < 30 and volts > 3:
        volts = 3
    elif altura >= 30 and volts > 3:
        volts = 3

    conn.writeDA(channel, volts)
    print("WriteDA volts: ", volts)
    return volts


##Calculo das variaveis de controle PID:
def calculaTauD(Kp, Kd):
    return float(Kd) / float(Kp)
def calculaKD(taud, Kp):
    return float(taud) * float(Kp)
def calculaTauI(Kp, Ki):
    return float(Kp) / float(Ki)
def calculaKI(taui, Ki):
    return float(Kp) / float(taui)


##Calculo controle PID:
def controlePID_K(set_point, current_value, Kp, Kd, Ki):
    # Declaracoes das variaveis globais
    global Derivator, Integrator, Integrator_max, Integrator_min, flag_pid, PID

    b = 1  # filtro na acao derivativa
    h = 0.1

    I_value = 0
    D_value = 0

    error = set_point - current_value
    margem = abs((set_point - current_value) / set_point)

    # print "error", error

    P_value = Kp * error
    if (flag_pid == 0 or flag_pid == 1):
        Integrator = 0
        I_value = 0
    if (flag_pid == 0 or flag_pid == 2):
        Derivator = 0
        D_value = 0

    if (flag_pid == 1 or flag_pid == 3):
        if (margem <= 0.03):
            b = 0.0
        D_value = Kd * ((error - Derivator) / h) * b
        Derivator = error
    if (flag_pid == 4):
        if (margem <= 0.03):
            b = 0.0
        D_value = Kd * ((current_value - Derivator) / h) * b
        Derivator = current_value
    if (flag_pid == 2 or flag_pid == 3 or flag_pid == 4):
        Integrator = Integrator + (Ki * error * h)
        # print "integrador", Integrator
        if Integrator > Integrator_max:
            Integrator = Integrator_max
        elif Integrator < Integrator_min:
            Integrator = Integrator_min
        I_value = Integrator

    PID = P_value + D_value + I_value
    # print "PID:" , PID
    return PID

##Calculo controle PID no modelo Cascata:
##tipo_malha = 0, se trata da malha externa
##tipo_malha = 1, se trata da malha interna
def controlePID_K_Cascata(set_point, current_value, Kp, Kd, Ki, tipo_malha):
    # Declaracoes das variaveis globais
    global T1_Derivator, T1_Integrator, T2_Derivator, T2_Integrator, Integrator_max, Integrator_min, T1_flag_pid, T2_flag_pid, PID

    h = 0.1

    I_value = 0
    D_value = 0

    error = set_point - current_value
    margem = abs((set_point - current_value) / set_point)

    # print "error", error

    P_value = Kp * error
    ##Controle tanque 2 em cascata
    if((T2_flag_pid == 0 or T2_flag_pid == 1) and tipo_malha == 0):
        T2_Integrator = 0
        I_value = 0
    if((T2_flag_pid == 0 or T2_flag_pid == 2) and tipo_malha==0):
        T2_Derivator = 0
        D_value = 0
    if((T2_flag_pid == 1 or T2_flag_pid == 3) and tipo_malha==0):
        D_value = Kd * ((error - T2_Derivator) / h)
        T2_Derivator = error
    if(T2_flag_pid == 4 and tipo_malha==0):
        D_value = Kd * ((current_value - T2_Derivator) / h)
        T2_Derivator = current_value
    if((T2_flag_pid == 2 or T2_flag_pid == 3 or T2_flag_pid == 4) and tipo_malha==0):
        T2_Integrator = T2_Integrator + (Ki * error * h)
        if T2_Integrator > Integrator_max:
            T2_Integrator = Integrator_max
        elif T2_Integrator < Integrator_min:
            T2_Integrator = Integrator_min
        I_value = T2_Integrator

    ##Controle tanque 1 em cascata
    if ((T1_flag_pid == 0 or T1_flag_pid == 1) and tipo_malha == 1):
        T1_Integrator = 0
        I_value = 0
    if ((T1_flag_pid == 0 or T1_flag_pid == 2) and tipo_malha == 1):
        T1_Derivator = 0
        D_value = 0
    if ((T1_flag_pid == 1 or T1_flag_pid == 3) and tipo_malha == 1):
        D_value = Kd * ((error - T1_Derivator) / h)
        T1_Derivator = error
    if (T1_flag_pid == 4 and tipo_malha == 0):
        D_value = Kd * ((current_value - T1_Derivator) / h)
        T2_Derivator = current_value
    if ((T1_flag_pid == 2 or T1_flag_pid == 3 or T1_flag_pid == 4) and tipo_malha == 1):
        T1_Integrator = T1_Integrator + (Ki * error * h)
        if T1_Integrator > Integrator_max:
            T1_Integrator = Integrator_max
        elif T1_Integrator < Integrator_min:
            T1_Integrator = Integrator_min
        I_value = T1_Integrator

    PID = P_value + D_value + I_value
    return PID


def calculaOvershoot(set_point,current_value):
    global overshoot, overshootPercentual, antigo_setPoint, flag_overshoot_subida, flag_overshoot, flag_verifica_overshoot, valor_passado
    if(flag_verifica_overshoot):
        valor_passado = current_value
        flag_verifica_overshoot = False

    if(current_value-valor_passado>0 and flag_overshoot and not(flag_verifica_overshoot)):
        flag_overshoot_subida = True
        if(current_value>overshoot):
            overshoot = current_value
            if(current_value>set_point):
                if(set_point!=antigo_setPoint):
                    overshootPercentual = round(abs(((current_value-set_point)/(set_point - antigo_setPoint))*100), 2)
                else:
                    overshootPercentual = round(abs(((current_value-set_point)/(set_point))*100), 2)
                    flag_overshoot_subida = True
    if(current_value-valor_passado<0 and flag_overshoot and not(flag_verifica_overshoot)):
        flag_overshoot_subida = False
        if(current_value<overshoot):
            overshoot = current_value
            if(current_value<set_point):
                if(set_point!=antigo_setPoint):
                    overshootPercentual = round(abs(((current_value-set_point)/(set_point - antigo_setPoint))*100), 2)
                    flag_overshoot_subida = False
                else:
                    overshootPercentual = round(abs(((current_value-set_point)/(set_point))*100), 2)
                    flag_overshoot_subida = False

def calculaOvershoot_Cascata(set_point,current_value,tipo_malha):
    global T1_overshoot, T1_overshootPercentual, T1_antigo_setPoint, T1_flag_overshoot_subida, T1_flag_overshoot, T1_flag_verifica_overshoot, T1_valor_passado
    global T2_overshoot, T2_overshootPercentual, T2_antigo_setPoint, T2_flag_overshoot_subida, T2_flag_overshoot, T2_flag_verifica_overshoot, T2_valor_passado

    if (T1_flag_verifica_overshoot and tipo_malha==1):
        T1_valor_passado = current_value
        T1_flag_verifica_overshoot = False
    if ((current_value - T1_valor_passado > 0 and T1_flag_overshoot and not (T1_flag_verifica_overshoot)) and tipo_malha==1):
        T1_flag_overshoot_subida = True
        if(current_value > T1_overshoot):
            T1_overshoot = current_value
            if (current_value > set_point):
                if (set_point != T1_antigo_setPoint):
                    T1_overshootPercentual = round(abs(((current_value - set_point) / (set_point - T1_antigo_setPoint)) * 100), 2)
                else:
                    T1_overshootPercentual = round(abs(((current_value - set_point) / (set_point)) * 100), 2)
                    T1_flag_overshoot_subida = True
    if ((current_value - T1_valor_passado < 0 and T1_flag_overshoot and not (T1_flag_verifica_overshoot)) and tipo_malha==1):
        T1_flag_overshoot_subida = False
        if (current_value < T1_overshoot):
            T1_overshoot = current_value
            if (current_value < set_point):
                if (set_point != T1_antigo_setPoint):
                    T1_overshootPercentual = round(abs(((current_value - set_point) / (set_point - T1_antigo_setPoint)) * 100), 2)
                    T1_flag_overshoot_subida = False
                else:
                    T1_overshootPercentual = round(abs(((current_value - set_point) / (set_point)) * 100), 2)
                    T1_flag_overshoot_subida = False

    if(T2_flag_verifica_overshoot and tipo_malha==0):
        T2_valor_passado = current_value
        T2_flag_verifica_overshoot = False
    if((current_value-T2_valor_passado>0 and T2_flag_overshoot and not(T2_flag_verifica_overshoot)) and tipo_malha==0):
        T2_flag_overshoot_subida = True
        if(current_value>T2_overshoot):
            T2_overshoot = current_value
            if(current_value>set_point):
                if(set_point!=T2_antigo_setPoint):
                    T2_overshootPercentual = round(abs(((current_value-set_point)/(set_point - T2_antigo_setPoint))*100), 2)
                else:
                    T2_overshootPercentual = round(abs(((current_value-set_point)/(set_point))*100), 2)
                    T2_flag_overshoot_subida = True
    if((current_value-T2_valor_passado<0 and T2_flag_overshoot and not(T2_flag_verifica_overshoot)) and tipo_malha==0):
        T2_flag_overshoot_subida = False
        if(current_value<T2_overshoot):
            T2_overshoot = current_value
            if(current_value<set_point):
                if(set_point!=T2_antigo_setPoint):
                    T2_overshootPercentual = round(abs(((current_value-set_point)/(set_point - T2_antigo_setPoint))*100), 2)
                    T2_flag_overshoot_subida = False
                else:
                    T2_overshootPercentual = round(abs(((current_value-set_point)/(set_point))*100), 2)
                    T2_flag_overshoot_subida = False

def calculaTempoSubida(set_point, current_value, t):
    global flag, tempo_subida, tempo_final, tempo_inicial, flag_subida, flag_overshoot_subida, flag_overshoot
    if(flag_overshoot_subida):
        if(current_value<set_point and current_value>(set_point-set_point*0.05) and flag_subida):
            tempo_final = t
            tempo_aux = tempo_final - tempo_inicial
            if(tempo_aux != 0.0):
                tempo_subida = tempo_aux
                flag_subida = False
                flag_overshoot = True
        elif(current_value>(set_point*0.05) and flag):
            tempo_inicial=t
            flag=False
    elif(not(flag_overshoot_subida)):
        if(current_value>set_point and current_value<(set_point+set_point*0.05) and flag_subida):
            tempo_final = t
            tempo_aux = tempo_final - tempo_inicial
            if(tempo_aux != 0.0):
                tempo_subida = tempo_aux
                flag_subida = False
                flag_overshoot = True
        elif(current_value>(set_point*0.05) and flag):
            tempo_inicial=t
            flag=False

def calculaTempoSubida_Cascata(set_point, current_value, t, tipo_malha):
    global T1_flag, T1_tempo_subida, T1_tempo_final, T1_tempo_inicial, T1_flag_subida, T1_flag_overshoot_subida, T1_flag_overshoot
    global T2_flag, T2_tempo_subida, T2_tempo_final, T2_tempo_inicial, T2_flag_subida, T2_flag_overshoot_subida, T2_flag_overshoot

    if (T1_flag_overshoot_subida and tipo_malha==1):
        if (current_value < set_point and current_value > (set_point - set_point * 0.05) and T1_flag_subida):
            T1_tempo_final = t
            tempo_aux = T1_tempo_final - T1_tempo_inicial
            if (tempo_aux != 0.0):
                T1_tempo_subida = tempo_aux
                T1_flag_subida = False
                T1_flag_overshoot = True
        elif (current_value > (set_point * 0.05) and T1_flag):
            T1_tempo_inicial = t
            T1_flag = False
    elif(not (T1_flag_overshoot_subida)):
        if (current_value > set_point and current_value < (set_point + set_point * 0.05) and T1_flag_subida):
            T1_tempo_final = t
            tempo_aux = T1_tempo_final - T1_tempo_inicial
            if (tempo_aux != 0.0):
                T1_tempo_subida = tempo_aux
                T1_flag_subida = False
                T1_flag_overshoot = True
        elif (current_value > (set_point * 0.05) and T1_flag):
            T1_tempo_inicial = t
            T1_flag = False

    if(T2_flag_overshoot_subida and tipo_malha==0):
        if(current_value<set_point and current_value>(set_point-set_point*0.05) and T2_flag_subida):
            T2_tempo_final = t
            tempo_aux = T2_tempo_final - T2_tempo_inicial
            if(tempo_aux != 0.0):
                T2_tempo_subida = tempo_aux
                T2_flag_subida = False
                T2_flag_overshoot = True
        elif(current_value>(set_point*0.05) and T2_flag):
            T2_tempo_inicial=t
            T2_flag=False
    elif(not(T2_flag_overshoot_subida)):
        if(current_value>set_point and current_value<(set_point+set_point*0.05) and T2_flag_subida):
            T2_tempo_final = t
            tempo_aux = T2_tempo_final - T2_tempo_inicial
            if(tempo_aux != 0.0):
                T2_tempo_subida = tempo_aux
                T2_flag_subida = False
                T2_flag_overshoot = True
        elif(current_value>(set_point*0.05) and T2_flag):
            T2_tempo_inicial=t
            T2_flag=False

def calculaTempoAcomodacao(set_point, current_value, t):
    global flag_subida, tempo_acomodacao, tempo_inicial, tempo_final, flag_overshoot, flag_acomodacao, tempo_acomodacao_inicial
    if((current_value>(set_point-set_point*0.05) and current_value<(set_point+set_point*0.05)) and flag_acomodacao):
        flag_acomodacao = False
        tempo_acomodacao_inicial = t - tempo_inicial
    if((current_value<(set_point-set_point*0.05) or current_value>(set_point+set_point*0.05)) and not(flag_acomodacao)):
        flag_acomodacao = True
        tempo_acomodacao_inicial = 0.0
    if((current_value>(set_point-set_point*0.05) and current_value<(set_point+set_point*0.05)) and abs((t-tempo_inicial) - tempo_acomodacao_inicial)>2.0):
        tempo_acomodacao =  tempo_acomodacao_inicial
        flag_overshoot = False
        flag_acomodacao = False

def calculaTempoAcomodacao_Cascata(set_point, current_value, t, tipo_malha):
    global T1_flag_subida, T1_tempo_acomodacao, T1_tempo_inicial, T1_tempo_final, T1_flag_overshoot, T1_flag_acomodacao, T1_tempo_acomodacao_inicial
    global T2_flag_subida, T2_tempo_acomodacao, T2_tempo_inicial, T2_tempo_final, T2_flag_overshoot, T2_flag_acomodacao, T2_tempo_acomodacao_inicial

    if((current_value>(set_point-set_point*0.05) and current_value<(set_point+set_point*0.05)) and T1_flag_acomodacao and tipo_malha==1):
        T1_flag_acomodacao = False
        T1_tempo_acomodacao_inicial = t - T1_tempo_inicial
    if((current_value<(set_point-set_point*0.05) or current_value>(set_point+set_point*0.05)) and not(T1_flag_acomodacao) and tipo_malha==1):
        T1_flag_acomodacao = True
        T1_tempo_acomodacao_inicial = 0.0
    if((current_value>(set_point-set_point*0.05) and current_value<(set_point+set_point*0.05)) and abs((t-T1_tempo_inicial) - T1_tempo_acomodacao_inicial)>2.0 and tipo_malha==1):
        T1_tempo_acomodacao =  T1_tempo_acomodacao_inicial
        T1_flag_overshoot = False
        T1_flag_acomodacao = False

    if ((current_value > (set_point - set_point * 0.05) and current_value < (set_point + set_point * 0.05)) and T2_flag_acomodacao and tipo_malha == 1):
        T2_flag_acomodacao = False
        T2_tempo_acomodacao_inicial = t - T2_tempo_inicial
    if ((current_value < (set_point - set_point * 0.05) or current_value > (set_point + set_point * 0.05)) and not (T2_flag_acomodacao) and tipo_malha == 1):
        T2_flag_acomodacao = True
        T2_tempo_acomodacao_inicial = 0.0
    if ((current_value > (set_point - set_point * 0.05) and current_value < (set_point + set_point * 0.05)) and abs((t - T2_tempo_inicial) - T2_tempo_acomodacao_inicial) > 2.0 and tipo_malha == 1):
        T2_tempo_acomodacao = T2_tempo_acomodacao_inicial
        T2_flag_overshoot = False
        T2_flag_acomodacao = False

def atualizaTempos(t):
    global flag_mudou_setPoint, flag, tempo_inicial
    if(flag_mudou_setPoint):
        tempo_inicial = t
        flag_mudou_setPoint = False
        flag = False

def setTipoControle(tipo):
	global tipo_controle
	if(tipo==0 or tipo==1):
		tipo_controle = tipo


def atualizaListas(tempo, tensao_saida, tensao_sensor, altura_tanque1, altura_tanque2, set_point, set_point_ME):
    global contador, lista_saida, tensao, lista_altura_tanque1, lista_altura_tanque2, lista_setpoint, lista_setpoint_ME
    if (contador >= 10):
        lista_saida.append((tempo, tensao_saida))
        lista_tensao.append((tempo, tensao_sensor))
        lista_altura_tanque1.append((tempo, altura_tanque1))
        lista_altura_tanque2.append((tempo, altura_tanque2))
        lista_setpoint.append((tempo, set_point))
        lista_setpoint_ME.append((tempo, set_point_ME))
        contador = 0
    else:
        contador = contador + 1


##CONTROLE:

class Controle(threading.Thread):
    def __int__(self):
        self._stop = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        global x_axis_range, Start, nivel_tanque, channel, overshoot, overshootPercentual
        global flag_malha, flag_signal, periodo, offset, conn, valor_entrada, flag_pid
        global Kp, Ki, Kd, taud, taui, PID, setpoint_ME

        tensao = 0.0
        read = 0.0
        t_init = time.time()
        PID = 0.0

        ##planta:
        ##startConnection('10.13.99.69',20081)
        ##servidor:
        startConnection('localhost', 20081)
        altura = float(getAltura(channel))
        altura_tanque1 = float(getAltura(0))
        altura_tanque2 = float(getAltura(1))
        while (Start):
            t = float(time.time() - t_init)
            # if (flag_malha == 0):
            #     if (flag_signal == 1):
            #         set_point = Signal.waveStep(valor_entrada, offset)
            #     elif (flag_signal == 2):
            #         set_point = Signal.waveSine(valor_entrada, periodo, offset, t)
            #     elif (flag_signal == 3):
            #         set_point = Signal.waveSquare(valor_entrada, periodo, offset, t)
            #     elif (flag_signal == 4):
            #         set_point = Signal.waveSawtooth(valor_entrada, periodo, offset, t)
            #     elif (flag_signal == 5):
            #         set_point = Signal.waveRandom(valor_entrada, periodo, offset, t)
            #     altura = float(getAltura(channel))
            #     tensao = writeTensao(0, set_point)
            #     v = float(quanser.getTension())
            #     read = float(readSensor(channel))
            #     nivel_tanque = altura  # atualiza o nivel do tanque
            #     x_axis_range = float(t)  # atualiza o range do grafico
            #     atualizaListas(t, saida, tensao, altura_tanque1, altura_tanque2, set_point, setpoint_ME) #atualiza os valores plotados
            if (flag_malha == 1):
                if (flag_signal == 1):
                    set_point = Signal.waveStep(valor_entrada, offset)
                elif (flag_signal == 2):
                    set_point = Signal.waveSine(valor_entrada, periodo, offset, t)
                elif (flag_signal == 3):
                    set_point = Signal.waveSquare(valor_entrada, periodo, offset, t)
                elif (flag_signal == 4):
                    set_point = Signal.waveSawtooth(valor_entrada, periodo, offset, t)
                elif (flag_signal == 5):
                    set_point = Signal.waveRandom(valor_entrada, periodo, offset, t)
                if(tipo_controle==0):
                    altura = float(getAltura(channel))
                    saida = controlePID_K(set_point, altura, Kp, Kd, Ki)
                    calculaOvershoot(set_point, altura)
                    calculaTempoSubida(set_point, altura, t)
                    calculaTempoAcomodacao(set_point, altura, t)
                elif(tipo_controle==1):
                    altura_tanque1 = float(getAltura(0))
                    altura_tanque2 = float(getAltura(1))
                    setpoint_ME = controlePID_K_Cascata(set_point, altura_tanque2, T2_Kp, T2_Kd, T2_Ki, 0)
                    saida = controlePID_K_Cascata(setpoint_ME, altura_tanque1, T1_Kp, T1_Kd, T1_Ki, 1)
                    calculaOvershoot_Cascata(set_point, altura_tanque2, 0)
                    calculaTempoSubida_Cascata(set_point, altura_tanque2, t, 0)
                    calculaTempoAcomodacao_Cascata(set_point, altura_tanque2, t, 0)
                    calculaOvershoot_Cascata(setpoint_ME, altura_tanque1, 1)
                    calculaTempoSubida_Cascata(setpoint_ME, altura_tanque1, t, 1)
                    calculaTempoAcomodacao_Cascata(setpoint_ME, altura_tanque1, t, 1)
                print "Tensao: ", tensao
                tensao = writeTensao(0, saida)
                print "Write tensao saida: ", saida
                v = float(quanser.getTension())
                read = float(readSensor(channel))
                nivel_tanque = altura  # atualiza o nivel do tanque
                x_axis_range = float(t)  # atualiza o range do grafico
                atualizaListas(t, saida, tensao, altura_tanque1, altura_tanque2, set_point, setpoint_ME) #atualiza os valores plotados
                atualizaTempos(t)

        endConnection(channel)
        sys.exit()

    ##-------------------------------------------
    ##OBSERVACOES:
    ##PARA USAR OS CAMPOS DE OVERSHOOT E TEMPOS, FAZER, DENTRO DA CLASSE INTERFACE:
    ##self.ids.overshoot.text = ""
    ##self.ids.tempo_subida.text = ""
    ##self.ids.tempo_acomodacao.text = ""
    ##IR NA FUNCAO update_nivel EM Interface PARA AJUSTAR OS VALORES NA INTERFACE


class Interface(BoxLayout):
    def __init__(self, ):
        super(Interface, self).__init__()

        self.contador = 0

        self.plotsaida = MeshLinePlot(color=[1, 0, 0, 1])
        self.plotentrada = MeshLinePlot(color=[1, 0, 0, 1])
        self.plotsetpoint = MeshLinePlot(color=[0, 0, 1, 1])
        self.plotsetpointME = MeshLinePlot(color=[0, 0, 1, 1])
        self.plotaltura1 = MeshLinePlot(color=[0, 128, 0, 1])
        self.plotaltura2 = MeshLinePlot(color=[0, 128, 0, 1])

    # graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=5,x_ticks_major=25, y_ticks_major=1, y_grid_label=True, x_grid_label=True, 		#padding=5, x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-1, ymax=1)


    ##FUNCOES DOS BOTOES:

    ##SUGESTOES:
    ## 1) Retirar as funoces de malha e substituir pelas funcoes de controle abaixo.

    ##CONTROLE
    def CD(self):
        print("Clicou CD")
        global flag_controle
        flag_controle = 0
    def CC(self):
        print("Clicou CC")
        global flag_controle
        flag_controle = 1

    ##ONDAS
    def degrau(self):
        global flag_signal
        flag_signal = 1
        self.ids.periodo.disabled = True
    def quadrada(self):
        global flag_signal
        flag_signal = 3
        self.ids.periodo.disabled = False
    def senoide(self):
        global flag_signal
        flag_signal = 2
        self.ids.periodo.disabled = False
    def denteserra(self):
        global flag_signal
        flag_signal = 4
        self.ids.periodo.disabled = False
    def aleatoria(self):
        global flag_signal
        flag_signal = 5
        self.ids.periodo.disabled = False

    ##CONTROLE
    ##CONTROLE CASCATA
    def do_p(self):
        global flag_pid
        self.ids.ki.disabled = True
        self.ids.kd.disabled = True
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 0

    def do_pd(self):
        global flag_pid
        self.ids.ki.disabled = True
        self.ids.kd.disabled = False
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 1

    def do_pi(self):
        global flag_pid
        self.ids.ki.disabled = False
        self.ids.kd.disabled = True
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 2

    def do_pid(self):
        global flag_pid
        self.ids.ki.disabled = False
        self.ids.kd.disabled = False
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 3

    def do_pi_d(self):
        global flag_pid
        self.ids.ki.disabled = False
        self.ids.kd.disabled = False
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 4
    ##TANQUE 1
    def T1_do_p(self):
        global T1_flag_pid
        self.ids.T1_ki.disabled = True
        self.ids.T1_kd.disabled = True
        self.ids.T1_taui.disabled = True
        self.ids.T1_taud.disabled = True
        T1_flag_pid = 0
    def T1_do_pd(self):
        global T1_flag_pid
        self.ids.T1_ki.disabled = True
        self.ids.T1_kd.disabled = False
        self.ids.T1_taui.disabled = True
        self.ids.T1_taud.disabled = True
        T1_flag_pid = 1
    def T1_do_pi(self):
        global T1_flag_pid
        self.ids.T1_ki.disabled = False
        self.ids.T1_kd.disabled = True
        self.ids.T1_taui.disabled = True
        self.ids.T1_taud.disabled = True
        T1_flag_pid = 2
    def T1_do_pid(self):
        global T1_flag_pid
        self.ids.T1_ki.disabled = False
        self.ids.T1_kd.disabled = False
        self.ids.T1_taui.disabled = True
        self.ids.T1_taud.disabled = True
        T1_flag_pid = 3
    def T1_do_pi_d(self):
        global T1_flag_pid
        self.ids.T1_ki.disabled = False
        self.ids.T1_kd.disabled = False
        self.ids.T1_taui.disabled = True
        self.ids.T1_taud.disabled = True
        T1_flag_pid = 4
    ##TANQUE 2
    def T2_do_p(self):
        global T2_flag_pid
        self.ids.T2_ki.disabled = True
        self.ids.T2_kd.disabled = True
        self.ids.T2_taui.disabled = True
        self.ids.T2_taud.disabled = True
        T2_flag_pid = 0

    def T2_do_pd(self):
        global T2_flag_pid
        self.ids.T2_ki.disabled = True
        self.ids.T2_kd.disabled = False
        self.ids.T2_taui.disabled = True
        self.ids.T2_taud.disabled = True
        T2_flag_pid = 1

    def T2_do_pi(self):
        global T2_flag_pid
        self.ids.T2_ki.disabled = False
        self.ids.T2_kd.disabled = True
        self.ids.T2_taui.disabled = True
        self.ids.T2_taud.disabled = True
        T2_flag_pid = 2

    def T2_do_pid(self):
        global T2_flag_pid
        self.ids.T2_ki.disabled = False
        self.ids.T2_kd.disabled = False
        self.ids.T2_taui.disabled = True
        self.ids.T2_taud.disabled = True
        T2_flag_pid = 3

    def T2_do_pi_d(self):
        global T2_flag_pid
        self.ids.T2_ki.disabled = False
        self.ids.T2_kd.disabled = False
        self.ids.T2_taui.disabled = True
        self.ids.T2_taud.disabled = True
        T2_flag_pid = 4



    ##ATUALIZAR VALORES
    def atualiza(self):
        global tensao_min, tensao_max, offset, valor_entrada, periodo
        global Kp, Ki, Kd, taui, taud
        global T1_Kp, T1_Ki, T1_Kd, T1_taui, T1_taud, T2_Kp, T2_Ki, T2_Kd, T2_taui, T2_taud
        global flag, flag_subida, flag_acomodacao, flag_overshoot, flag_mudou_setPoint, antigo_setPoint, flag_verifica_overshoot
        global tempo_subida, tempo_acomodacao, overshootPercentual
        global T1_flag, T1_flag_subida, T1_flag_acomodacao, T1_flag_overshoot, T1_flag_mudou_setPoint, T1_antigo_setPoint, T1_flag_verifica_overshoot
        global T1_tempo_subida, T1_tempo_acomodacao, T1_overshootPercentual
        global T2_flag, T2_flag_subida, T2_flag_acomodacao, T2_flag_overshoot, T2_flag_mudou_setPoint, T2_antigo_setPoint, T2_flag_verifica_overshoot
        global T2_tempo_subida, T2_tempo_acomodacao, T2_overshootPercentual
        if((valor_entrada!=float(self.ids.tensaoentrada.text)) or (offset!=float(self.ids.offset.text))):
            ##Controle direto
            flag = True
            flag_subida = True
            flag_acomodacao = True
            flag_overshoot = True
            flag_mudou_setPoint = True
            flag_verifica_overshoot = True
            antigo_setPoint = valor_entrada+offset
            tempo_subida = 0.0
            tempo_acomodacao = 0.0
            overshootPercentual = 0.0
            ##Controle cascata tanque 1
            T1_flag = True
            T1_flag_subida = True
            T1_flag_acomodacao = True
            T1_flag_overshoot = True
            T1_flag_mudou_setPoint = True
            T1_flag_verifica_overshoot = True
            T1_antigo_setPoint = valor_entrada + offset
            T1_tempo_subida = 0.0
            T1_tempo_acomodacao = 0.0
            T1_overshootPercentual = 0.0
            ##Controle cascata tanque 2
            T2_flag = True
            T2_flag_subida = True
            T2_flag_acomodacao = True
            T2_flag_overshoot = True
            T2_flag_mudou_setPoint = True
            T2_flag_verifica_overshoot = True
            T2_antigo_setPoint = valor_entrada + offset
            T2_tempo_subida = 0.0
            T2_tempo_acomodacao = 0.0
            T2_overshootPercentual = 0.0
        tensao_min = float(self.ids.tensaomin.text)
        tensao_max = float(self.ids.tensaomax.text)
        offset = float(self.ids.offset.text)
        valor_entrada = float(self.ids.tensaoentrada.text)
        periodo = float(self.ids.periodo.text)
        ##        print "tensaomax: ", tensao_max
        ##        print "tensaomin: ", tensao_min
        ##        print "offset: ", offset
        ##        print "entrada: ", valor_entrada
        ##        print "periodo: ", periodo
        ##ATE AQUI OK
        Kp = float(self.ids.kp.text)
        Kd = float(self.ids.kd.text)
        Ki = float(self.ids.ki.text)
        taui = float(self.ids.taui.text)
        taud = float(self.ids.taud.text)
        T1_Kp = float(self.ids.T1_kp.text)
        T1_Kd = float(self.ids.T1_kd.text)
        T1_Ki = float(self.ids.T1_ki.text)
        T1_taui = float(self.ids.T1_taui.text)
        T1_taud = float(self.ids.T1_taud.text)
        T2_Kp = float(self.ids.T2_kp.text)
        T2_Kd = float(self.ids.T2_kd.text)
        T2_Ki = float(self.ids.T2_ki.text)
        T2_taui = float(self.ids.T2_taui.text)
        T2_taud = float(self.ids.T2_taud.text)
        self.ids.overshoot.text = "-"
        self.ids.tempo_subida.text = "-"
        self.ids.tempo_acomodacao.text = "-"

        if (self.ids.kd_label.state == 'down'):
            self.kd_in()
        if (self.ids.ki_label.state == 'down'):
            self.ki_in()
        if (self.ids.taud_label.state == 'down'):
            self.taud_in()
        if (self.ids.taui_label.state == 'down'):
            self.taui_in()
        if (self.ids.T1_kd_label.state == 'down'):
            self.T1_kd_in()
        if (self.ids.T1_ki_label.state == 'down'):
            self.T1_ki_in()
        if (self.ids.T1_taud_label.state == 'down'):
            self.T1_taud_in()
        if (self.ids.T1_taui_label.state == 'down'):
            self.T1_taui_in()
        if (self.ids.T2_kd_label.state == 'down'):
            self.T2_kd_in()
        if (self.ids.T2_ki_label.state == 'down'):
            self.T2_ki_in()
        if (self.ids.T2_taud_label.state == 'down'):
            self.T2_taud_in()
        if (self.ids.T2_taui_label.state == 'down'):
            self.T2_taui_in()
        ##        print "kp: ", Kp
        ##        print "kd: ", Ki
        ##        print "ki: ", Kd
        ##        print "taud: ", taui
        ##        print "taui: ", taud


    ##RETIREI A FUNCAO KP_IN POIS ELA TORNOU-SE OBSOLETA (E ESTA BUGANDO OS VALORES DOS TAUS)

    ##FUNCOES QUE ATUALIZA K'S E TAUS

    ##CASCATA
    def kd_in(self):
        global Kp, Kd, taud
        try:
            Kd = float(self.ids.kd.text)
        except:
            Kd = 0.0
        try:
            taud = calculaTauD(Kp, Kd)
            self.ids.taud.text = str(taud)
        except:
            self.ids.taud.text = "0.0"

    def ki_in(self):
        global Kp, taui, Ki
        try:
            Ki = float(self.ids.ki.text)
        except:
            Ki = 0.0
        try:
            taui = calculaTauI(Kp, Ki)
            self.ids.taui.text = str(taui)
        except:
            self.ids.taui.text = "0.0"

    def taud_in(self):
        global Kp, Kd, taud
        try:
            taud = float(self.ids.taud.text)
        except:
            taud = 0.0
        try:
            Kd = calculaKD(taud, Kp)
            self.ids.kd.text = str(Kd)
        except:
            self.ids.kd.text = "0.0"

    def taui_in(self):
        global Kp, Ki, taui
        try:
            taui = float(self.ids.taui.text)
        except:
            taui = 0.0
        try:
            Ki = calculaKI(taui, Kp)
            self.ids.ki.text = str(Ki)
        except:
            self.ids.ki.text = "0.0"

    ##TANQUE 1
    def T1_kd_in(self):
        global T1_Kp, T1_Kd, T1_taud
        try:
            T1_Kd = float(self.ids.T1_kd.text)
        except:
            T1_Kd = 0.0
        try:
            T1_taud = calculaTauD(T1_Kp, T1_Kd)
            self.ids.T1_taud.text = str(T1_taud)
        except:
            self.ids.T1_taud.text = "0.0"

    def T1_ki_in(self):
        global T1_Kp, T1_taui, T1_Ki
        try:
            T1_Ki = float(self.ids.T1_ki.text)
        except:
            T1_Ki = 0.0
        try:
            T1_taui = calculaTauI(T1_Kp, T1_Ki)
            self.ids.T1_taui.text = str(T1_taui)
        except:
            self.ids.T1_taui.text = "0.0"

    def T1_taud_in(self):
        global T1_Kp, T1_Kd, T1_taud
        try:
            T1_taud = float(self.ids.T1_taud.text)
        except:
            T1_taud = 0.0
        try:
            T1_Kd = calculaKD(T1_taud, T1_Kp)
            self.ids.T1_kd.text = str(T1_Kd)
        except:
            self.ids.T1_kd.text = "0.0"

    def T1_taui_in(self):
        global T1_Kp, T1_Ki, T1_taui
        try:
            T1_taui = float(self.ids.T1_taui.text)
        except:
            T1_taui = 0.0
        try:
            T1_Ki = calculaKI(T1_taui, T1_Kp)
            self.ids.T1_ki.text = str(T1_Ki)
        except:
            self.ids.T1_ki.text = "0.0"

    ##TANQUE 2
    def T2_kd_in(self):
        global T2_Kp, T2_Kd, T2_taud
        try:
            T2_Kd = float(self.ids.T2_kd.text)
        except:
            T2_Kd = 0.0
        try:
            T2_taud = calculaTauD(T2_Kp, T2_Kd)
            self.ids.T2_taud.text = str(T2_taud)
        except:
            self.ids.T2_taud.text = "0.0"

    def T2_ki_in(self):
        global T2_Kp, T2_taui, T2_Ki
        try:
            T2_Ki = float(self.ids.T2_ki.text)
        except:
            T2_Ki = 0.0
        try:
            T2_taui = calculaTauI(T2_Kp, T2_Ki)
            self.ids.T2_taui.text = str(T2_taui)
        except:
            self.ids.T2_taui.text = "0.0"

    def T2_taud_in(self):
        global T2_Kp, T2_Kd, T2_taud
        try:
            T2_taud = float(self.ids.T2_taud.text)
        except:
            T2_taud = 0.0
        try:
            T2_Kd = calculaKD(T2_taud, T2_Kp)
            self.ids.T2_kd.text = str(T2_Kd)
        except:
            self.ids.T2_kd.text = "0.0"

    def T2_taui_in(self):
        global T2_Kp, T2_Ki, T2_taui
        try:
            T2_taui = float(self.ids.T2_taui.text)
        except:
            T2_taui = 0.0
        try:
            T2_Ki = calculaKI(T2_taui, T2_Kp)
            self.ids.T2_ki.text = str(T2_Ki)
        except:
            self.ids.T2_ki.text = "0.0"


    ##BOTOES QUE SELECIONAM K'S OU TAUS
        ##CASCATA
        def pressKD(self):
            global flag_pid
            if (flag_pid == 1 or flag_pid == 3 or flag_pid == 4):
                self.ids.kd.disabled = False
                self.ids.taud.disabled = True

        def pressKI(self):
            global flag_pid
            if (flag_pid == 2 or flag_pid == 3 or flag_pid == 4):
                self.ids.ki.disabled = False
                self.ids.taui.disabled = True

        def pressTD(self):
            global flag_pid
            if (flag_pid == 1 or flag_pid == 3 or flag_pid == 4):
                self.ids.kd.disabled = True
                self.ids.taud.disabled = False

        def pressTI(self):
            global flag_pid
            if (flag_pid == 2 or flag_pid == 3 or flag_pid == 4):
                self.ids.ki.disabled = True
                self.ids.taui.disabled = False

    ##TANQUE 1
    def T1_pressKD(self):
        global T1_flag_pid
        if (T1_flag_pid == 1 or T1_flag_pid == 3 or T1_flag_pid == 4):
            self.ids.T1_kd.disabled = False
            self.ids.T1_taud.disabled = True
    def T1_pressKI(self):
        global T1_flag_pid
        if (T1_flag_pid == 2 or T1_flag_pid == 3 or T1_flag_pid == 4):
            self.ids.T1_ki.disabled = False
            self.ids.T1_taui.disabled = True
    def T1_pressTD(self):
        global T1_flag_pid
        if (T1_flag_pid == 1 or T1_flag_pid == 3 or T1_flag_pid == 4):
            self.ids.T1_kd.disabled = True
            self.ids.T1_taud.disabled = False
    def T1_pressTI(self):
        global T1_flag_pid
        if (T1_flag_pid == 2 or T1_flag_pid == 3 or T1_flag_pid == 4):
            self.ids.T1_ki.disabled = True
            self.ids.T1_taui.disabled = False
    ##TANQUE 2
    def T2_pressKD(self):
        global T2_flag_pid
        if (T2_flag_pid == 1 or T2_flag_pid == 3 or T2_flag_pid == 4):
            self.ids.T2_kd.disabled = False
            self.ids.T2_taud.disabled = True
    def T2_pressKI(self):
        global T2_flag_pid
        if (T2_flag_pid == 2 or T2_flag_pid == 3 or T2_flag_pid == 4):
            self.ids.T2_ki.disabled = False
            self.ids.T2_taui.disabled = True
    def T2_pressTD(self):
        global T2_flag_pid
        if (T2_flag_pid == 1 or T2_flag_pid == 3 or T2_flag_pid == 4):
            self.ids.T2_kd.disabled = True
            self.ids.T2_taud.disabled = False

    def T2_pressTI(self):
        global T2_flag_pid
        if (T2_flag_pid == 2 or T2_flag_pid == 3 or T2_flag_pid == 4):
            self.ids.T2_ki.disabled = True
            self.ids.T2_taui.disabled = False

    ##FUNCOES PARA CONTROLE DA INTERFACE E CHAMADA DO PROGRAMA DE CONTROLE:

    def startsaida(self):
        print("Clicou Start")
        global Start, flag, flag_subida, flag_acomodacao, flag_overshoot, flag_verifica_overshoot
        flag = True
        flag_subida = True
        flag_acomodacao = True
        flag_overshoot = True
        flag_verifica_overshoot = True
        Start = True
        self.atualiza()
        control = Controle()
        control.start()
        self.ids.graphsaida.add_plot(self.plotsaida)
        self.ids.graphsaida.add_plot(self.plotentrada)
        self.ids.graphsaida.add_plot(self.plotsetpointME)
        self.ids.graphentrada.add_plot(self.plotsetpointME)
        self.ids.graphentrada.add_plot(self.plotsetpoint)
        self.ids.graphentrada.add_plot(self.plotaltura1)
        self.ids.graphentrada.add_plot(self.plotaltura2)
        self.clockSaida = Clock.schedule_interval(self.get_valuesaida, 0.001)
        self.clockEntrada = Clock.schedule_interval(self.get_valueentrada, 0.001)
        self.clockUpdateX = Clock.schedule_interval(self.update_xaxis, 0.001)
        self.clockNivel = Clock.schedule_interval(self.update_nivel, 1)


    ##ATUALIZAR OVERSHOOT E TEMPOS AQUI
    ##usar essa funcao com timer para fazer update dos itens junto com a imagem do tanque
    def update_nivel(self, *args):
        global nivel_tanque, overshoot, overshootPercentual, tempo_subida, tempo_acomodacao
        nivel = (nivel_tanque / 30) * 100
        if(nivel>100):
            nivel=100.0
        if(nivel<0):
            nivel=0.0
        self.ids.nivel_tanque1.value = nivel

        overshootPercentual = round(overshootPercentual, 2)
        self.ids.overshoot.text = str(overshootPercentual)
        self.ids.tempo_subida.text = str(round(tempo_subida,3))
        self.ids.tempo_acomodacao.text = str(round(tempo_acomodacao,3))


    ##funcao caso queira adequar os ranges de x:
    def update_xaxis(self, *args):
        global x_axis_range
        if (x_axis_range > 80):
            self.ids.graphsaida.xmin = x_axis_range - 80
            self.ids.graphsaida.xmax = x_axis_range + 20
            self.ids.graphentrada.xmin = x_axis_range - 80
            self.ids.graphentrada.xmax = x_axis_range + 20

    def get_valuesaida(self, dt):
        self.plotsaida.points = [i for i in lista_saida]
        self.plotentrada.points = [i for i in lista_tensao]
        self.plotsetpointME.points = [i for i in lista_setpoint_ME]

    def get_valueentrada(self, dt):
        self.plotsetpoint.points = [i for i in lista_setpoint]
        self.plotsetpointME.points = [i for i in lista_setpoint_ME]
        self.plotaltura1.points = [i for i in lista_altura_tanque1]
        self.plotaltura2.points = [i for i in lista_altura_tanque2]



    def stop(self):
        global Start, tensao, lista_saida, lista_setpoint, lista_altura_tanque1
        global overshoot, overshootPercentual, antigo_setPoint
        global tempo_subida, tempo_acomodacao, tempo_acomodacao_inicial, tempo_final, tempo_inicial
        global T1_overshoot, T1_overshootPercentual, T1_antigo_setPoint
        global T1_tempo_subida, T1_tempo_acomodacao, T1_tempo_acomodacao_inicial, T1_tempo_final, T1_tempo_inicial
        global T2_overshoot, T2_overshootPercentual, T2_antigo_setPoint
        global T2_tempo_subida, T2_tempo_acomodacao, T2_tempo_acomodacao_inicial, T2_tempo_final, T2_tempo_inicial
        self.clockSaida.cancel()
        self.clockEntrada.cancel()
        self.clockUpdateX.cancel()
        self.clockNivel.cancel()
        Start = False
        self.ids.graphsaida.remove_plot(self.plotsaida)
        self.ids.graphentrada.remove_plot(self.plotentrada)
        self.ids.graphsaida.remove_plot(self.plotsetpoint)
        self.ids.graphentrada.remove_plot(self.plotsetpointME)
        self.ids.graphentrada.remove_plot(self.plotaltura)
        self.ids.graphsaida._clear_buffer()
        self.ids.graphentrada._clear_buffer()
        while len(tensao) > 0: tensao.pop()
        while len(lista_saida) > 0: lista_saida.pop()
        while len(lista_setpoint) > 0: lista_setpoint.pop()
        while len(lista_altura_tanque1) > 0: lista_altura_tanque1.pop()
        tensao = [(0, 0)]
        lista_saida = [(0, 0)]
        lista_setpoint = [(0, 0)]
        lista_altura_tanque1 = [(0, 0)]
        overshootPercentual = 0.0
        overshoot = 0.0
        antigo_setPoint = 0.0
        ##Verificar os campos para T1 e T2 em cascata e colocar a mesma alteracao
        self.ids.overshoot.text = "-"
        self.ids.nivel_tanque1.value = 0.0
        self.ids.tempo_subida.text = "-"
        self.ids.tempo_acomodacao.text = "-"
        tempo_subida = 0.0
        tempo_acomodacao = 0.0
        tempo_acomodacao_inicial = 0.0
        tempo_final = 0.0
        tempo_inicial = 0.0
        ##Cascata tanque 1
        T1_overshootPercentual = 0.0
        T1_overshoot = 0.0
        T1_antigo_setPoint = 0.0
        T1_tempo_subida = 0.0
        T1_tempo_acomodacao = 0.0
        T1_tempo_acomodacao_inicial = 0.0
        T1_tempo_final = 0.0
        T1_tempo_inicial = 0.0
        ##Cascata tanque 2
        T2_overshootPercentual = 0.0
        T2_overshoot = 0.0
        T2_antigo_setPoint = 0.0
        T2_tempo_subida = 0.0
        T2_tempo_acomodacao = 0.0
        T2_tempo_acomodacao_inicial = 0.0
        T2_tempo_final = 0.0
        T2_tempo_inicial = 0.0


    ##-----------------------------------------------------------------------------

class ControleApp(App):
    def build(self):
        return Builder.load_file("Controle.kv")


if __name__ == '__main__':
    ControleApp().run()