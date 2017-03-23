import quanser
import threading
import sys
import Signal
import time

# "1 - Degrau"
# "2 - Onda Senoidal"
# "3 - Onda Quadrada"
# "4 - Onda tipo dente de serra"	
# "5 - Sinal Aleatorio"
# 0 para malha aberta, e 1 para malha fechada
flag_malha = 1
flag_signal = 1
flag_pid = 1
valor_entrada = 15
periodo = 10 
offset = 0
tensao_max = 4.0
tensao_min = -4.0
#Constantes do Controlador PID
taud=0.0
taui=0.0
Kd=0.01
Kp=0.1
Ki=0.5
PID=0.0
#Variaveis do controlador PID
Derivator=0.0
Integrator=0.0
Integrator_max=500
Integrator_min=-500
# flag_modo==0 - K
# flag_modo==1 - tau
flag_modo=0

def readSensor(channel):
    global conn
    return conn.readAD(channel)
 
def getAltura(channel):
    tensao = readSensor(channel)
    return tensao*6.25

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
 
    if altura <= 3 and volts < 0:
        volts = 0
    elif altura >= 28 and altura < 30 and volts > 3:
        volts = 2
    elif altura >= 30 and volts > 3:
        volts = 2
 
    conn.writeDA(channel, volts)
    return volts

def calculaTauD(Kp,Kd):
	return	float(Kd/Kp)
def calculaKD(taud,Kp):
	return float(taud*Kp)
def calculaTauI(Kp,Ki):
	return	float(Kp/Ki)
def calculaKI(taui,Ki):
	return float(Kp/taui)


"""
flag_pid=0 -> controle P
flag_pid=1 -> controle PD
flag_pid=2 -> controle PI
flag_pid=3 -> controle PID
flag_pid=4 -> controle PI-D
"""
def controlePID_K(set_point,current_value,Kp,Kd,Ki):
	#Declaracoes das variaveis globais
	global Derivator, Integrator, Integrator_max, Integrator_min, flag_pid,PID
	h=0.1

	error = set_point - current_value

	if(flag_pid==0 or flag_pid==1):
		Integrator=0
	if(flag_pid==0 or flag_pid==2):
		Derivator=0
	if(flag_pid==0 or flag_pid==1 or flag_pid==2 or flag_pid==3 or flag_pid==4):
		P_value = Kp*error
		PID = PID + P_value
	if(flag_pid==1 or flag_pid==3):
		D_value = Kd*((error - Derivator)/h)
		Derivator = error
		PID = PID + D_value
	if(flag_pid==4):
		D_value = Kd*((current_value - Derivator)/h)
		Derivator = current_value
		PID = PID + D_value
	if(flag_pid==2 or flag_pid==3 or flag_pid==4):
		Integrator = Integrator + (Ki*error*h)
		if Integrator > Integrator_max:
			Integrator = Integrator_max
		elif Integrator < Integrator_min:
			Integrator = Integrator_min
		I_value = Integrator
		PID = PID + I_value
	return PID

def controlePID_TAU(set_point,current_value,Kp,Td,Ti):
	#Declaracoes das variaveis globais
	global Integrator_max, Integrator_min, flag_pid, PID
	h=0.1

	error = set_point - current_value

	if(flag_pid==0 or flag_pid==1):
		Integrator=0
		I_value=0
	if(flag_pid==0 or flag_pid==2):
		Derivator=0
		D_value=0
	if(flag_pid==0 or flag_pid==1 or flag_pid==2 or flag_pid==3 or flag_pid==4):
		P_value = Kp*error
		PID = PID + P_value
	if(flag_pid==1 or flag_pid==3):
		D_value = Kp*Td*((error - Derivator)/h)
		Derivator = error
		PID = PID + D_value
	if(flag_pid==4):
		D_value = Kp*Td*((current_value - Derivator)/h)
		Derivator = current_value
		PID = PID + D_value
	if(flag_pid==2 or flag_pid==3 or flag_pid==4):
		Integrator = Integrator + ((Kp/Ti)*error*h)
		if Integrator > Integrator_max:
			Integrator = Integrator_max
		elif Integrator < Integrator_min:
			Integrator = Integrator_min
		I_value = Integrator
		PID = PID + I_value
	return PID

class Controle(threading.Thread):
	def __int__(self):
		self._stop = threading.Event()
		threading.Thread.__init__(self)
	def run(self):
		cont=0
		tensao = 0.0
		channel = 0
		read = 0.0
		t_init = time.time()
		global flag_malha, flag_signal, periodo, offset, conn, valor_entrada, flag_pid, Kp, Ki, Kd,taud, taui, flag_modo

		#startConnection('10.13.99.69',20081)
		startConnection('localhost',20074)
		while(True):
			t = time.time() - t_init
			if(flag_malha == 0):
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
				tensao = writeTensao(channel, volts)
				v =  quanser.getTension()
				print "Tensao: ", v
				read = readSensor(channel)
				print "Sensor: ", read
				print "Altura: ", getAltura(channel)
				cont += 1
				if(cont>1000):
					print 'terminou de executar!'
					break
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
				if flag_modo==0:
					saida = controlePID_K(valor_entrada,altura,Kp,Kd,Ki)
				elif flag_modo==1:
					saida = controlePID_TAU(valor_entrada,altura,Kp,taud,taui)
				tensao = writeTensao(channel, saida)
				v = quanser.getTension()
				print "Tensao: ", v
				read = readSensor(channel)
				print "Sensor: ", read
				print "Altura: ", altura
				cont += 1
				time.sleep(0.1)
				if(cont>1000):
					print 'terminou de executar!'
					break
		endConnection(channel)
		sys.exit()

#Criacao das threads
control = Controle()

# Start na thread de leitura e escrita
control.start()