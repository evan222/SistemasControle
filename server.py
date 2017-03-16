
from socket import * # sockets
import math
import thread
import time

serverName = '' # ip do servidor (em branco)
serverPort = 20074 # porta a se conectar
serverSocket = socket(AF_INET,SOCK_STREAM) # criacao do socket TCP
serverSocket.bind((serverName,serverPort)) # bind do ip do servidor com a porta
serverSocket.listen(1) # socket pronto para "ouvir" conexoes

print "Servidor TCP esperando conexoes na porta %d ..." % (serverPort)


lastRecv= "0,0 \n"

# h'= -k*sqrt(h)+k*U

h1= 0.0
h2= 0.0
h10= 0.0
u10= 0.0
h20= 0.0
u20= 0.0
a= math.pi*pow((0.56*math.pow(10,-2))/2,2)
A= math.pi*pow((4.45*math.pow(10,-2))/2,2)
c1= math.sqrt(2*9.81)*a/A
c2= 2.1*math.pow(10,-5)/A
parar= False

def simulacao(threadName, delay):
    global h1, h2, h10, u10, h20, u20, c1, c2
    while not parar:
        h1= h10+(c2*u10-c1*math.sqrt(h10))*delay
        h2= h20+(c1*math.sqrt(h10)-c1*math.sqrt(h20))*delay
        if h1 < 0:
            h1= 0
        if h2 < 0:
            h2= 0
        h10= h1
        h20= h2
        time.sleep(delay)

while 1:
    h1= 0.0
    h2= 0.0
    h10= 0.0
    u10= 0.0
    h20= 0.0
    u20= 0.0
    parar= False
    thread.start_new_thread(simulacao, ("simulacao", 0.01,))
    connectionSocket, addr = serverSocket.accept() # aceita as conexoes dos clientes
    while 1:
        sentence = connectionSocket.recv(1024) # recebe dados do cliente
        if sentence == "":
            break
        if "READ" in sentence:
            if sentence[5] == "0":
                #print h1*100/6.1
                toSend= str(h1*100/6.1)+" \n"
                #toSend= toSend.replace(".", ",")
                connectionSocket.send(toSend)
            elif sentence[5] == "1":
                #print h2*100/6.1
                toSend= str(h2*100/6.1)+" \n"
                #toSend= toSend.replace(".", ",")
                connectionSocket.send(toSend)
            else:
                #print h1*100/6.1
                toSend= str(h1*100/6.1)+" \n"
                #toSend= toSend.replace(".", ",")
                connectionSocket.send(toSend)

        else:
            #print sentence
            u10= float(sentence.split(' ')[2])
            lastRecv= sentence.split(' ')[2]+" \n"
            #lastRecv= lastRecv.replace(".", ",")
            connectionSocket.send("ACK\n")
    parar= True

    connectionSocket.close() # encerra o socket com o cliente
serverSocket.close() # encerra o socket do servidor
