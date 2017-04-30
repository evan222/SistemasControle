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

flag_controle = 0 #comeca com controle direto

flag_malha = 0  # 0 = malha aberta / 1  = malha fechada
flag_signal = 1
## "1 - Degrau\n"
## "2 - Onda Senoidal\n"
## "3 - Onda Quadrada\n"
## "4 - Onda tipo dente de serra\n"	
## "5 - Sinal Aleatorio\n"
flag_pid = 0
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

valor_entrada = 0
periodo = 1
offset = 0
tensao_max = 4
tensao_min = -4

# Variaveis do controlador PID
Derivator = 0.0
Integrator = 0.0
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

##variaveis de controle da interface/sistema
Start = False
lista_saida = [(0, 0)]
lista_entrada = [(0, 0)]
lista_setpoint = [(0, 0)]
lista_altura = [(0, 0)]
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
#Variaveis do tempo de subida
tempo_final = 0.0
tempo_inicial = 0.0



##-------------------------------------------
def readSensor(channel):
    global conn
    return conn.readAD(channel)


def getAltura(channel):
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


def atualizaListas(tempo, tensao_saida, tensao_sensor, altura, set_point):
    global contador, lista_saida, lista_entrada, lista_altura, lista_setpoint
    if ( contador >=10):
        lista_saida.append((tempo, tensao_saida))
        lista_entrada.append((tempo, tensao_sensor))
        lista_altura.append((tempo, altura))
        lista_setpoint.append((tempo, set_point))
        contador = 0
    else:
        contador = contador + 1


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

def atualizaTempos(t):
    global flag_mudou_setPoint, flag, tempo_inicial
    if(flag_mudou_setPoint):
        tempo_inicial = t
        flag_mudou_setPoint = False
        flag = False


##CONTROLE:

class Controle(threading.Thread):
    def __int__(self):
        self._stop = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        global x_axis_range, Start, nivel_tanque, channel, overshoot, overshootPercentual
        global flag_malha, flag_signal, periodo, offset, conn, valor_entrada, flag_pid, Kp, Ki, Kd, taud, taui, PID

        tensao = 0.0
        read = 0.0
        t_init = time.time()
        PID = 0.0

        ##planta:
        ##startConnection('10.13.99.69',20081)
        ##servidor:
        startConnection('localhost', 20074)
        while (Start):
            t = float(time.time() - t_init)
            if (flag_malha == 0):
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
                altura = float(getAltura(channel))
                tensao = writeTensao(0, set_point)
                v = float(quanser.getTension())
                read = float(readSensor(channel))
                nivel_tanque = altura  # atualiza o nivel do tanque
                x_axis_range = float(t)  # atualiza o range do grafico
                atualizaListas(t, v, read, altura, set_point) #atualiza os valores plotados
            elif (flag_malha == 1):
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
                altura = float(getAltura(channel))
                saida = controlePID_K(set_point, altura, Kp, Kd, Ki)
                tensao = writeTensao(0, saida)
                v = float(quanser.getTension())
                read = float(readSensor(channel))
                nivel_tanque = altura  # atualiza o nivel do tanque
                x_axis_range = float(t)  # atualiza o range do grafico
                atualizaListas(t, v, read, altura, set_point) #atualiza os valores plotados
                calculaOvershoot(set_point, altura)
                atualizaTempos(t)
                calculaTempoSubida(set_point, altura, t)
                calculaTempoAcomodacao(set_point, altura, t)

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
        self.plotsetpoint2 = MeshLinePlot(color=[0, 0, 1, 1])
        self.plotaltura = MeshLinePlot(color=[0, 128, 0, 1])

    # graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=5,x_ticks_major=25, y_ticks_major=1, y_grid_label=True, x_grid_label=True, 		#padding=5, x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-1, ymax=1)


    ##FUNCOES DOS BOTOES:

    ##SUGESTOES:
    ## 1) Retirar as funoces de malha e substituir pelas funcoes de controle abaixo.

##A FUNCAO ABAIXO SE TORNOU OBSOLETA (malha):
    ##MALHA
    def MA(self):
        global flag_malha
        flag_malha = 0
        self.ids.malha.text = "Malha Aberta"
    def MF(self):
        global flag_malha
        flag_malha = 1
        self.ids.malha.text = "Malha Fechada"

    ##CONTROLE
    def CD(self):
        global flag_controle
        flag_controle = 0
    def CC(self):
        global flag_controle
        flag_controle = 1

##ESTA FUNCAO TAMBEM TORNOU-SE OBSOLETA (tanques):
    ##TANQUES
    def tanque1(self):
        global channel
        channel = 0
    def tanque2(self):
        global channel
        channel = 1

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

    ##ATUALIZAR VALORES
    def atualiza(self):
        global tensao_min, tensao_max, offset, valor_entrada, periodo
        global Kp, Ki, Kd, taui, taud
        global flag, flag_subida, flag_acomodacao, flag_overshoot, flag_mudou_setPoint, antigo_setPoint, flag_verifica_overshoot
        global tempo_subida, tempo_acomodacao, overshootPercentual
        if((valor_entrada!=float(self.ids.tensaoentrada.text)) or (offset!=float(self.ids.offset.text))):
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
        ##        print "kp: ", Kp
        ##        print "kd: ", Ki
        ##        print "ki: ", Kd
        ##        print "taud: ", taui
        ##        print "taui: ", taud


    ##RETIREI A FUNCAO KP_IN POIS ELA TORNOU-SE OBSOLETA (E ESTA BUGANDO OS VALORES DOS TAUS)

    ##FUNCOES QUE ATUALIZA K'S E TAUS
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

    ##BOTOES QUE SELECIONAM K'S OU TAUS
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



    ##FUNCOES PARA CONTROLE DA INTERFACE E CHAMADA DO PROGRAMA DE CONTROLE:

    def startsaida(self):
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
        self.ids.graphsaida.add_plot(self.plotsetpoint)
        self.ids.graphentrada.add_plot(self.plotentrada)
        self.ids.graphentrada.add_plot(self.plotsetpoint2)
        self.ids.graphentrada.add_plot(self.plotaltura)
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
        self.plotsetpoint.points = [i for i in lista_setpoint]

    def get_valueentrada(self, dt):
        self.plotentrada.points = [i for i in lista_entrada]
        self.plotsetpoint2.points = [i for i in lista_setpoint]
        self.plotaltura.points = [i for i in lista_altura]



    def stop(self):
        global Start, lista_entrada, lista_saida, lista_setpoint, lista_altura
        global overshoot, overshootPercentual, antigo_setPoint
        global tempo_subida, tempo_acomodacao, tempo_acomodacao_inicial, tempo_final, tempo_inicial
        self.clockSaida.cancel()
        self.clockEntrada.cancel()
        self.clockUpdateX.cancel()
        self.clockNivel.cancel()
        Start = False
        self.ids.graphsaida.remove_plot(self.plotsaida)
        self.ids.graphentrada.remove_plot(self.plotentrada)
        self.ids.graphsaida.remove_plot(self.plotsetpoint)
        self.ids.graphentrada.remove_plot(self.plotsetpoint2)
        self.ids.graphentrada.remove_plot(self.plotaltura)
        self.ids.graphsaida._clear_buffer()
        self.ids.graphentrada._clear_buffer()
        while len(lista_entrada) > 0: lista_entrada.pop()
        while len(lista_saida) > 0: lista_saida.pop()
        while len(lista_setpoint) > 0: lista_setpoint.pop()
        while len(lista_altura) > 0: lista_altura.pop()
        lista_entrada = [(0, 0)]
        lista_saida = [(0, 0)]
        lista_setpoint = [(0, 0)]
        lista_altura = [(0, 0)]
        overshootPercentual = 0.0
        overshoot = 0.0
        antigo_setPoint = 0.0
        self.ids.overshoot.text = "-"
        self.ids.nivel_tanque1.value = 0.0
        self.ids.tempo_subida.text = "-"
        self.ids.tempo_acomodacao.text = "-"
        tempo_subida = 0.0
        tempo_acomodacao = 0.0
        tempo_acomodacao_inicial = 0.0
        tempo_final = 0.0
        tempo_inicial = 0.0


    ##-----------------------------------------------------------------------------

class ControleApp(App):
    def build(self):
        return Builder.load_file("Controle.kv")


if __name__ == '__main__':
    ControleApp().run()
