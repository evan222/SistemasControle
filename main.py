import kivy
kivy.require('1.9.1') # replace with your current kivy version !

from kivy.app import App

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle

from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image

#para o grafico:
from math import sin
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
from threading import Thread

import quanser
import threading
import sys
import Signal
import time



##VARIAVEIS GLOBAIS:
flag_malha = 0 #0 = malha aberta / 1  = malha fechada
flag_signal = 1
## "1 - Degrau\n"
## "2 - Onda Senoidal\n"
## "3 - Onda Quadrada\n"
## "4 - Onda tipo dente de serra\n"	
## "5 - Sinal Aleatorio\n"
flag_pid = 0
"""
flag_pid=0 -> controle P
flag_pid=1 -> controle PD
flag_pid=2 -> controle PI
flag_pid=3 -> controle PID
flag_pid=4 -> controle PI-D
"""
flag_modo=0
##flag_modo = 0 -> Ki e Kd
##flag_modo = 1 -> taui e taud


valor_entrada = 0
periodo = 1
offset = 0
tensao_max = 4
tensao_min = -4

#Variaveis do controlador PID
Derivator=0.0
Integrator=0.0
Integrator_max=500
Integrator_min=-500
last_time = 0

#Constantes do Controlador PID
taud=0.0
taui=0.0
Kd=0.0
Kp=0.0
Ki=0.0
PID=0.0

##variaveis de controle da interface/sistema
Start = False
lista_saida = [(0,0)]
lista_entrada = [(0,0)]
lista_setpoint = [(0,0)]
lista_altura = [(0,0)]

cont = 0
nivel_tanque = 0

##-------------------------------------------
def readSensor(channel):
    global conn
    return conn.readAD(channel)
 
def getAltura(channel):
    tensao = readSensor(channel)
    return float(tensao*6.25)

def startConnection(IP, porta):
    global conn
    try:
        conn = quanser.Quanser(IP, porta)
        #print "aqui"
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
def calculaTauD(Kp,Kd):
    return  float(Kd)/float(Kp)
def calculaKD(taud,Kp):
    return float(taud)*float(Kp)
def calculaTauI(Kp,Ki):
    return  float(Kp)/float(Ki)
def calculaKI(taui,Ki):
    return float(Kp)/float(taui)

##Calculo controle PID:
def controlePID_K(set_point,current_value,Kp,Kd,Ki):
    #Declaracoes das variaveis globais
    global Derivator, Integrator, Integrator_max, Integrator_min, flag_pid, PID, last_time

    #h=0.1

    h = time.time() - last_time  #dt

    error = set_point - current_value

    Integrator=0
    Derivator=0
    P_value = Kp*error
    D_value = 0
    I_value = 0

    if(flag_pid==1 or flag_pid==3): 
        D_value = Kd*((error - Derivator)/h)
        Derivator = error
    if(flag_pid==4):
        D_value = Kd*((current_value - Derivator)/h)
        Derivator = current_value
    if(flag_pid==2 or flag_pid==3 or flag_pid==4):
        Integrator = Integrator + (Ki*error*h)
        if Integrator > Integrator_max:
            Integrator = Integrator_max
        elif Integrator < Integrator_min:
            Integrator = Integrator_min
        I_value = Integrator

    PID = PID + P_value + D_value + I_value
    print "PID:" , PID
    last_time  = time.time()
    return PID


##CONTROLE:

class Controle(threading.Thread):
	def __int__(self):
		self._stop = threading.Event()
		threading.Thread.__init__(self)

	def run(self):	
		global lista_saida, lista_entrada, lista_setpoint, cont, Start, nivel_tanque
		global flag_malha, flag_signal, periodo, offset, conn, valor_entrada, flag_pid, Kp, Ki, Kd,taud, taui, flag_modo,PID, last_time
		
		tensao = 0.0
		channel = 0
		read = 0.0
		t_init = time.time()
		last_time = time.time()
		PID=0.0

		##planta:
		##startConnection('10.13.99.69',20081)
		##servidor:
		startConnection('localhost',20074)
		while(Start):
			t = time.time() - t_init
			if(flag_malha == 0):
				if(flag_signal == 1):
					volts = Signal.waveStep(valor_entrada, offset)
				elif(flag_signal == 2):
					volts = Signal.waveSine(valor_entrada,periodo,offset,t)
				elif(flag_signal == 3):
					volts = Signal.waveSquare(valor_entrada,periodo,offset,t)
				elif(flag_signal == 4):
					volts = Signal.waveSawtooth(valor_entrada,periodo,offset,t)
				elif(flag_signal == 5):
					volts = Signal.waveRandom(valor_entrada,periodo,offset,t)
				tensao = writeTensao(channel, volts)
				v =  quanser.getTension()
				#print "Tensao: ", v
				lista_saida.append((t, v))
				read = readSensor(channel)
				lista_entrada.append((t, read))
				#altura = getAltura(read)
				lista_altura.append((t, altura))
				#print "Sensor: ", read
				#print "Altura: ", altura
				#nivel_tanque = altura
				lista_setpoint.append((t, volts))
				cont = t
			elif(flag_malha == 1):
				if(flag_signal == 1):
					volts = Signal.waveStep(valor_entrada,offset)
				elif(flag_signal == 2):
					volts = Signal.waveSine(valor_entrada,periodo,offset,t)
				elif(flag_signal == 3):
					volts = Signal.waveSquare(valor_entrada,periodo,offset,t)
				elif(flag_signal == 4):
					volts = Signal.waveSawtooth(valor_entrada,periodo,offset,t)
				elif(flag_signal == 5):
					volts = Signal.waveRandom(valor_entrada,periodo,offset,t)
				altura = getAltura(channel)
				
				saida = controlePID_K(volts,altura,Kp,Kd,Ki)

				tensao = writeTensao(channel, saida)
				v =  quanser.getTension()
				#print "Tensao: ", v
				lista_saida.append((t, v))
				read = readSensor(channel)
				lista_entrada.append((t, read))
				#altura = getAltura(read)
				lista_altura.append((t, altura))
				#print "Sensor: ", read
				#print "Altura: ", altura
				#nivel_tanque = altura
				lista_setpoint.append((t, volts))
				cont = t
			#time.sleep(0.01)
		endConnection(channel)
		sys.exit()



##-------------------------------------------

class Interface(BoxLayout):
    def __init__(self,):
        super(Interface, self).__init__()

        
        self.plotsaida = MeshLinePlot(color=[1,0,0,1])
        self.plotentrada = MeshLinePlot(color=[1,0,0,1])
        self.plotsetpoint = MeshLinePlot(color=[0,0,1,1])
        self.plotsetpoint2 = MeshLinePlot(color=[0,0,1,1])
        self.plotaltura = MeshLinePlot(color=[0,128,0,1])
        	#graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=5,x_ticks_major=25, y_ticks_major=1, y_grid_label=True, x_grid_label=True, 		#padding=5, x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-1, ymax=1)

        
##FUNCOES DOS BOTOES:
        
    def MA(self):
        global flag_malha
        flag_malha = 0
        self.ids.malha.text = "Malha Aberta"
        
    def MF(self):
        global flag_malha
        flag_malha = 1
        self.ids.malha.text = "Malha Fechada"

        
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


    def tensao_min(self,value):
        global tensao_min
        tensao_min = float(value)
    def tensao_max(self,value):
        global tensao_max
        tensao_max = float(value)
    def offset(self,value):
        global offset
        offset = float(value)
    def tensaoentrada(self,value):
        global valor_entrada
        valor_entrada = float(value)
    def periodo(self,value):
        global periodo
        periodo = float(value)


    def do_p(self):
        self.ids.ki.disabled = True
        self.ids.kd.disabled = True
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 0
    def do_pd(self):
        self.ids.ki.disabled = True
        self.ids.kd.disabled = False
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 1
    def do_pi(self):
        self.ids.ki.disabled = False
        self.ids.kd.disabled = True
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 2
    def do_pid(self):
        self.ids.ki.disabled = False
        self.ids.kd.disabled = False
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 3
    def do_pi_d(self):
        self.ids.ki.disabled = False
        self.ids.kd.disabled = False
        self.ids.taui.disabled = True
        self.ids.taud.disabled = True
        flag_pid = 4


    def kp_in(self, value):
        global Kp, Ki, Kd, taui, taud
        try:
            Kp = float(value)
        except:
            Kp = 0.0
        try:
            taui = calculaTauI(Kp, Ki)
            taud = calculaTauD(Kp, Kd)
            self.ids.taui.text = str(taui)
            self.ids.taud.text = str(taud)
        except:
            pass
    def kd_in(self, value):
        global  Kp, Kd, taud#, flag_modo
        try:
            Kd = float(value)
        except:
            Kd = 0.0
            #flag_modo = 0
        try:
            taud = calculaTauD(Kp, Kd)
            self.ids.taud.text = str(taud)
        except:
            self.ids.taud.text = "0.0"
    def ki_in(self, value):
        global Kp, taui, Ki#, flag_modo
        try:
            Ki = float(value)
        except:
            Ki = 0.0
            #flag_modo = 0
        try:
            taui = calculaTauI(Kp, Ki)
            self.ids.taui.text = str(taui)
        except:
            self.ids.taui.text = "0.0"
    def taud_in(self, value):
        global Kp, Kd, taud#, flag_modo
        try:
            taud = float(value)
        except:
            taud = 0.0
            #flag_modo = 1
        try:
            Kd = calculaKD(taud, Kp)
            self.ids.kd.text = str(Kd)
        except:
            self.ids.kd.text = "0.0"
    def taui_in(self, value):
        global Kp, Ki, taui#, flag_modo
        try:
            taui = float(value)
        except:
            taui = 0.0
            #flag_modo = 1
        try:
            Ki = calculaKI(taui, Kp)
            self.ids.ki.text = str(Ki)
        except:
            self.ids.ki.text = "0.0"


    def pressKD(self):
        #global flag_modo
        #flag_modo = 0
        self.ids.kd.disabled = False
        self.ids.taud.disabled = True
    def pressKI(self):
        #global flag_modo
        #flag_modo = 0
        self.ids.ki.disabled = False
        self.ids.taui.disabled = True
    def pressTD(self):
        #global flag_modo
        #flag_modo = 0
        self.ids.kd.disabled = True
        self.ids.taud.disabled = False
    def pressTI(self):
        #global flag_modo
        #flag_modo = 0
        self.ids.ki.disabled = True
        self.ids.taui.disabled = False



##def calculaTauD(Kp,Kd):
##    return  float(Kd/Kp)
##def calculaKD(taud,Kp):
##    return float(taud*Kp)
##def calculaTauI(Kp,Ki):
##    return  float(Kp/Ki)
##def calculaKI(taui,Ki):
##    return float(Kp/taui)        


##FUNCOES PARA CONTROLE DA INTERFACE E CHAMADA DO PROGRAMA DE CONTROLE:

    def startsaida(self):
        global Start
        Start = True
        control = Controle()
        control.start()
        self.ids.graphsaida.add_plot(self.plotsaida)
        self.ids.graphsaida.add_plot(self.plotsetpoint)
        self.ids.graphentrada.add_plot(self.plotentrada)
        self.ids.graphentrada.add_plot(self.plotsetpoint2)
        self.ids.graphentrada.add_plot(self.plotaltura)
        self.clockSaida = Clock.schedule_interval(self.get_valuesaida,0.001)
        self.clockEntrada = Clock.schedule_interval(self.get_valueentrada,0.001)
        Clock.schedule_interval(self.update_xaxis, 0.001)


##funcao caso queira adequar os ranges de x:       
    def update_xaxis(self, *args):
        global cont
        if (cont > 80):
            self.ids.graphsaida.xmin = cont - 80
            self.ids.graphsaida.xmax = cont + 20
            self.ids.graphentrada.xmin = cont - 80
            self.ids.graphentrada.xmax = cont + 20


    def get_valuesaida(self, dt):
        self.plotsaida.points = [i for i in lista_saida]
        self.plotsetpoint.points = [i for i in lista_setpoint]

    def get_valueentrada(self, dt):
        self.plotentrada.points = [i for i in lista_entrada]
        self.plotsetpoint2.points = [i for i in lista_setpoint]
        self.plotaltura.points = [i for i in lista_altura]
        #self.ids.tanque.size_hint = (0.2, 1)


    def stop(self):
        global Start, lista_entrada, lista_saida, lista_setpoint, lista_altura
        self.clockSaida.cancel()
        self.clockEntrada.cancel()
        Start = False
        self.ids.graphsaida.remove_plot(self.plotsaida)
        self.ids.graphentrada.remove_plot(self.plotentrada)
        self.ids.graphsaida.remove_plot(self.plotsetpoint)
        self.ids.graphentrada.remove_plot(self.plotsetpoint2)
        self.ids.graphentrada.remove_plot(self.plotaltura)
        self.ids.graphsaida._clear_buffer()
        self.ids.graphentrada._clear_buffer()
        while len(lista_entrada) > 0 : lista_entrada.pop()
        while len(lista_saida) > 0 : lista_saida.pop()
        while len(lista_setpoint) > 0 : lista_setpoint.pop()
        while len(lista_altura) > 0 : lista_altura.pop()
        lista_entrada = [(0,0)]
        lista_saida = [(0,0)]
        lista_setpoint = [(0,0)]
        lista_altura = [(0,0)]


##-----------------------------------------------------------------------------

class ControleApp(App):
    def build(self):
        return Builder.load_file("Controle.kv")



if __name__ == '__main__':
	ControleApp().run()
