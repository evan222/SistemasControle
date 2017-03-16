import quanser
import threading
import sys
import Signal
import time

# 0 para malha aberta, e 1 para malha fechada
flag_malha = 0
flag_signal = 1
valor_entrada = 5
periodo = 1
offset = 0
tensao_max = 6
tensao_min = -4

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
    global conn
    if volts >= tensao_max:
        volts = tensao_max
    elif volts <= tensao_min:
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
		cont=0
		tensao = 0
		channel = 0
		read = 0
		t_init = time.time()
		global flag_malha, flag_signal, periodo, offset, conn, valor_entrada
		#startConnection('10.13.99.69',20081)
		startConnection('localhost',20074)
		while(True):
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
				read = readSensor(channel)
				print "Sensor: ", read
				print "Altura: ", getAltura(read)
				time.sleep(0.01)
				cont += 1
				if(cont>1000):
					print 'terminou de executar!'
					break
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
				print "Tensao: ", quanser.getTension()
				read = readSensor(channel)
				print "Sensor: ", read
				print "Altura: ", getAltura(read)
				cont += 1
				if(cont>1000):
					print 'terminou de executar!'
					break
		endConnection(channel)
		sys.exit()

#Criacao das threads
control = Controle()

# Start na thread de leitura e escrita
control.start()