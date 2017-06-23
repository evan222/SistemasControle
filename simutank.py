# -*- coding: utf-8 -*-
#!/usr/bin/python

##
#  Simulator for Quanser's Coupled Tanks
#  Copyright (C) 2015-2017, Augusto Damasceno
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import thread
import time
import socket
import re
import math
import signal
import os

############# CONFIGURE SIMULATOR ###########################

# Configure ip and port   
ip = '127.0.0.1'
port = 20081

# Max connections using the simulator
maxClients = 2

# Configure log
# If log is enabled, logInput and logOuputs
# can be enabled independently 
log = True
logInput = True
logOutputs = True
logIn = [0.0]
logOut1 = [0]
logOut2 = [0]

# Prints enabled/disabled
DEBUG_MODE = True
DEBUG_MODE_SOCKET = False
DEBUG_MODE_SOCKET_DATA = False

# Lock communication before exit
# DO NOT EDIT THIS VARIABLE
LOCK = False

# Model
readChannel = [0.0,0.0]
writeChannel = 0.0
amplifyWriteCh = 1.0
timeInterval = 0.05

# Read Channel 0 Noise
# Probability and maximum value
noiseProbCh0 = 0.00
noiseMaxCh0 = 3.0

# Read Channel 1 Noise
# Probability and maximum value
noiseProbCh1 = 0.00
noiseMaxCh1 = 3.0

############################################################

def noise(noiseProb,noiseMax):
    if int(os.urandom(1).encode('hex'),16)/255. < noiseProb:    
        i = int(os.urandom(4).encode('hex'),16) % noiseMax
        f = float(int(os.urandom(6).encode('hex'),16))
        f =  f/10000.0 - float(int(f/10000.0))
        return i+f
    else:
        return 0

def model():
###
# Model reference from:
#
# Júnior, Francisco G. F.; Maitelli, André L.; 
# Lopes, José S. B.;Araújo, Fabio M. U.
# Oliveira, Luiz A. H. G. 
# IMPLEMENTAÇÃO DE CONTROLADORES PID UTILIZANDO
# LÓGICA FUZZY E INSTRUMENTAÇÃO INDUSTRIAL
# VII Simpósio Brasileiro de Automação Inteligente.
# São Luís, setembro de 2005
#
    global readChannel, writeChannel,logIn,logOut1,logOut2
    global noiseProbCh0,noiseProbCh1,noiseMaxCh0,noiseMaxCh1

############# CONFIGURE MODEL PARAMETERS ###################

    # Tank orifice diameter    (cm^2)
    a1 = 0.48
    a2 = a1
    # Tank base area (cm^2)
    A1 = 15.518
    A2 = A1
    # Gravitational acceleration (m/s^2)
    g = 9.81
    # Pump flow constant ((cm^3)/sV)
    km = 3.3

############################################################

    # Operating Points 5cm and 25cm
    # Equation 1 (LaTeX):
    # \dot{L_{1}} = -\frac{a_{1}}{A_{1}}\sqrt{2gL_{1}}
    # +\frac{K_{m}}{A_{1}}V_{p}
    # Equation 2 (LaTeX):
    #  \dot{L_{2}} = -\frac{a_{2}}{A_{2}}\sqrt{2gL_{2}}
    # +\frac{a_{1}}{A_{2}}\sqrt{2gL_{1}}

    # State space
    A11 = (-1.0*a1/A1)*math.sqrt(2.0*g)
    A12 = 0.0
    A21 = (a1/A2)*math.sqrt(2.0*g)
    A22 = (-1.0*a2/A2)*math.sqrt(2.0*g)
    B1 = (km/A1)
    B2 = 0.0
    x1 = 0.0    
    x2 = 0.0
    
    while 1:
        x1sqrt = math.sqrt(x1)
        x2sqrt = math.sqrt(x2)

        Ax1 = (A11*x1sqrt)+(A12*x2sqrt)
        Ax2 = (A21*x1sqrt)+(A22*x2sqrt)
        u = writeChannel*amplifyWriteCh
        Bu1 = B1*u
        Bu2 = B2*u

        # x* = Ax+Bu        
        x1 = x1 + (Ax1+Bu1)*timeInterval
        x2 = x2 + (Ax2+Bu2)*timeInterval

        # Prevent negative level and overflow
        if x1 < 0.0:
            x1 = 0.0
        if x2 < 0.0:
            x2 = 0.0
        if x1 > 30.0:
            x1 = 30.0
        if x2 > 30.0:
            x2 = 30.0

        # Convert cm to sensor data
        readChannel[0] = x1/6.25 + noise(noiseProbCh0,noiseMaxCh0)
        readChannel[1] = x2/6.25 + noise(noiseProbCh1,noiseMaxCh1)

        if log:
            if logInput:
                logIn.append(writeChannel)
            if logOutputs:
                logOut1.append(readChannel[0])
                logOut2.append(readChannel[1])
        if DEBUG_MODE:
            print '\nPump: %.4fV' %  (writeChannel*amplifyWriteCh)
            print 'Level 1: %.4fcm' % x1
            print 'Level 2: %.4fcm' % x2
            if amplifyWriteCh <> 1.0:
                print 'Input Amplification Actived!'
        time.sleep(timeInterval)

def connectionAcc(conn, addr):
    global readChannel,writeChannel,clients

    if DEBUG_MODE_SOCKET:
        print 'Connected with: ', addr
    
    clients = clients + 1

    if DEBUG_MODE_SOCKET:
        print 'Client ' + str(clients)
        if (clients >= maxClients):
            print 'Max number of clients reached!'

    while(1):
        if LOCK:
            break
        
        try:
            data = conn.recv(64)
        except socket.error, (value,message):
            sock.close()
            print "Error socket receiving. " + message
            connected = False
            break

        if not data:
            connected = False
            break
        
        if DEBUG_MODE_SOCKET_DATA:
            print "Received: ", data

        if "WRITE" in data:
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+",data)
            if len(numbers) < 2:
                conn.send("WRG\n")
            else:   
                if int(numbers[0]) == 0:
                    writeChannel = float(numbers[1])
                    if DEBUG_MODE_SOCKET_DATA:
                        print "Wrote to channel %d, voltage %f\n" \
                            % (int(numbers[0]),float(numbers[1]))
                    conn.send("ACK\n")
                else:
                    conn.send("WRG\n")
        elif "READ" in data:
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+",data)
            if len(numbers) > 0 & \
                (int(numbers[0]) == 0 | int(numbers[0]) == 1):
                readChannelstr = str(readChannel[int(numbers[0])]) 
                readChannelstr = readChannelstr + '\n'
                if DEBUG_MODE_SOCKET_DATA:
                    print "Read from channel %d, level: %f\n" \
                        % (int(numbers[0]),readChannel[int(numbers[0])])
                conn.send(readChannelstr)
            else:
                conn.send("WRG\n")
        else:
                conn.send("WRG\n")

    conn.close() 
    clients = clients - 1

# Save logs, lock connections and exit
def handler(signum, frame):
    global logIn, logOut1, logOut2,LOCK
    LOCK = True
    if log:
        if logInput:
            filelog = open('logInput', 'w');
            for i in range(len(logIn)):
                filelog.write(str(logIn[i])+'\n')
            filelog.close()
        if logOutputs:
            filelog = open('logOutput1', 'w');
            for i in range(len(logOut1)):
                filelog.write(str(logOut1[i])+'\n')
            filelog.close()
            filelog = open('logOutput2', 'w');
            for i in range(len(logOut2)):
                filelog.write(str(logOut2[i])+'\n')
            filelog.close()
        print "\n\nLog saved!\n"

signal.signal(signal.SIGINT, handler)

# Create model thread
try:
   thread.start_new_thread( model, () )
except:
    print "Model Thread Error!"
    sys.exit(-1)

# Run server
try:
    # Socket  
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(1)
except socket.error, (value,message):
    sock.close()
    print "Error opening socket. " + message

clients = 0
locked = False
while(1):
    if ((clients+1) < maxClients) | \
        (locked & (clients < maxClients)):
        locked = False
        # Accept connection and create connection thread
        conn, addr = sock.accept()
        try:
            thread.start_new_thread(connectionAcc, (conn,addr,) )
        except:
            print "Connecction Accepted Thread Error!"
    else:
        if DEBUG_MODE_SOCKET:
            print 'Connections locked!'
        time.sleep(1)
        locked = True

