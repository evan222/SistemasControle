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

#from kivy.properties import NumericProperty
import quanser
import threading
import sys
import Signal
import time


#para o grafico:
from math import sin
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
from threading import Thread



##VARIAVEIS GLOBAIS:
flag_malha = 0 #0 = malha aberta / 1  = malha fechada
flag_signal = 1
## "1 - Degrau\n"
## "2 - Onda Senoidal\n"
## "3 - Onda Quadrada\n"
## "4 - Onda tipo dente de serra\n"	
## "5 - Sinal Aleatorio\n"

valor_entrada = 5
periodo = 1
offset = 0
tensao_max = 4
tensao_min = -4

Start = False
lista_saida = [(0,0)]
lista_entrada = [(0,0)]

cont = 0

##-------------------------------------------
def readSensor(channel):
    global conn
    return conn.readAD(channel)
 
def getAltura(channel):
    tensao = readSensor(channel)
    return tensao*6.25
 
def getTensao(amp):
    tensao = amp/6.25
    return tensao

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
        volts = 2
    elif altura >= 30 and volts > 3:
        volts = 2

    conn.writeDA(channel, volts)
    return volts

class Controle(threading.Thread):
	def __int__(self):
		self._stop = threading.Event()
		threading.Thread.__init__(self)
	def run(self):
		# "1 - Degrau"
		# "2 - Onda Senoidal"
		# "3 - Onda Quadrada"
		# "4 - Onda tipo dente de serra"	
		# "5 - Sinal Aleatorio"
		tensao = 0
		channel = 0
		read = 0
		t_init = time.time()
		global flag_malha, flag_signal, periodo, offset, conn, valor_entrada, Start, lista_saida, lista_entrada, cont
		#startConnection('10.13.99.69',20081)
		startConnection('localhost',20074)
		while(Start):
			t = time.time() - t_init
			if(flag_malha == 0):
				if(flag_signal == 1):
					volts = Signal.waveStep(valor_entrada)
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
				print "Tensao: ", v
				lista_saida.append((t, v))
				read = readSensor(channel)
				print "Sensor: ", read
				lista_entrada.append((t, read))
				print "Altura: ", getAltura(read)
				cont = t
			elif(flag_malha == 1):
				amp_volts =  getTensao(valor_entrada)
				if(flag_signal == 1):
					volts = Signal.waveStep(amp_volts)
				elif(flag_signal == 2):
					volts = Signal.waveSine(amp_volts,periodo,offset,t)
				elif(flag_signal == 3):
					volts = Signal.waveSquare(amp_volts,periodo,offset,t)
				elif(flag_signal == 4):
					volts = Signal.waveSawtooth(amp_volts,periodo,offset,t)
				elif(flag_signal == 5):
					volts = Signal.waveRandom(amp_volts,periodo,offset,t)
				volts = volts + (amp_volts - read)
				tensao = writeTensao(channel, volts)
				v =  quanser.getTension()
				print "Tensao: ", v
				lista_saida.append((t, v))
				read = readSensor(channel)
				lista_entrada.append((t, read))
				print "Sensor: ", read
				print "Altura: ", getAltura(read)
				cont = t
		endConnection(channel)
		sys.exit()



##-------------------------------------------

class Interface(BoxLayout):
    def __init__(self,):
        super(Interface, self).__init__()

##        self.cont= 0
        
        self.plotsaida = MeshLinePlot(color=[1,0,0,1])
        self.plotentrada = MeshLinePlot(color=[1,0,0,1])
        #graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=5,x_ticks_major=25, y_ticks_major=1, y_grid_label=True, x_grid_label=True, padding=5, x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-1, ymax=1)

        
##falta edidat os botoes e tensao/cm entrada
    def MA(self):
        global flag_malha
        flag_malha = 0
        self.ids.malha.text = "Malha Aberta"
        
    def MF(self):
        global flag_malha
        flag_malha = 1
        self.ids.malha.text = "Malha Fechada"


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

##    def minus_tensao_min(self):
##        global tensao_min
##        tensao_min = - tensao_min
##        print (tensao_min)
##    def minus_tensao_max(self):
##        global tensao_max
##        tensao_max = - tensao_max
##        print (tensao_max)
##    def minus_offset(self):
##        global offset
##        offset = - offset
##        print (offset)
##    def minus_tensaoentrada(self):
##        global valor_entrada
##        valor_entrada = - valor_entrada
##        print (valor_entrada)
##    def minus_periodo(self):
##        global periodo
##        periodo = - periodo
##        print (periodo)
    
    def degrau(self):
        global flag_signal
        flag_signal = 1
    def quadrada(self):
        global flag_signal
        flag_signal = 3
    def senoide(self):
        global flag_signal
        flag_signal = 2
    def denteserra(self):
        global flag_signal
        flag_signal = 4
    def aleatoria(self):
        global flag_signal
        flag_signal = 5
        
    def startsaida(self):
        global Start
        Start = True
        control = Controle()
        control.start()
        self.ids.graphsaida.add_plot(self.plotsaida)
        self.ids.graphentrada.add_plot(self.plotentrada)
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

        
## funcao para teste real time plot:  
##    def update_points(self, *args):
##        global lista, volts
##        lista.append((time.clock(), volts))

    def get_valuesaida(self, dt):
        self.plotsaida.points = [i for i in lista_saida]
##        self.cont = self.cont + 1

    def get_valueentrada(self, dt):
        self.plotentrada.points = [i for i in lista_entrada]

    def stop(self):
        global Start, lista_entrada, lista_saida
        self.clockSaida.cancel()
        self.clockEntrada.cancel()
        Start = False
        self.ids.graphsaida.remove_plot(self.plotsaida)
        self.ids.graphentrada.remove_plot(self.plotentrada)
        self.ids.graphsaida._clear_buffer()
        self.ids.graphentrada._clear_buffer()
        while len(lista_entrada) > 0 : lista_entrada.pop()
        while len(lista_saida) > 0 : lista_saida.pop()
        lista_entrada = [(0,0)]
        lista_saida = [(0,0)]
##        self.cont = 0


class ControleApp(App):
    def build(self):
        return Builder.load_file("Controle.kv")



if __name__ == '__main__':
    ControleApp().run()
