# -*- coding: utf-8 -*-
#
#   Driver de acesso a tanques Quanser
#   Arquivo: quanser.py
#   Autor: Allan David Garcia
#   Mail: allan.garcia@gmail.com
#   License: GPLv2
#
##############################################################################

import socket
# Variaveis globais para voltagem maxima e minima suportada pela bomba
# O valor das variáveis voltMax e voltMin vao variar de acordo com o que o usuário colocar a interface
# Deve ser tratado na interface que o usuario nao possa digitar/escolhar algo > 4 ou < -4
voltMax = 4.0
voltMin = -4.0
tension = 0.0

class Quanser:
    """
    Classe de comunicacao com a planta dos tanques de segunda ordem
    
    Exemplo:
    import quanser
    conn = quanser.Quanser("10.13.97.81", 20081)
    """

    def __init__(self, host, port):
        """
        Construtor do driver de conexao com a planta
        """
        self.connectServer(host, port)

    def connectServer(self, host, port):
        """
        Realiza a conexao com o servidor da planta
        """
        try:
            self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            self.soc.connect((host, port))
        except Exception:
            return False
        return True

    def closeServer(self):
        """
        Fecha a conexao com o servidor da planta
        """
        try:
            self.soc.close()
        except Exception:
            return False
        return True

    def __receiveData(self):
        """
        Recebe os dados do buffer do servidor
        """
        data = ''
        chunk = ''
        while (len(data) < 1) or (chunk != '\n'):
            chunk = self.soc.recv(1)
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            data = data + chunk
        return data

    def __sendData(self, data):
        """
        Envia dados para o servidor
        """
        try:
            self.soc.sendall(data)
        except Exception:
            return False
        return True

    def writeDA(self, channel, volt):
    	global voltMax, voltMin, tension
        """
        Escreve um valor em Volt no canal da planta
        """
        if(volt > voltMax):
        	volt = voltMax
        elif(volt < voltMin):
        	volt = voltMin
		
        aux = volt
        tension = aux
		
        string = 'WRITE %d %d\n' % (channel, volt)
        self.__sendData(string)
        string = self.__receiveData()
        if "ACK" in string:
            return True
        return False

    def readAD(self, channel):
        """
        Le um valor em Volt do canal da planta
        """
        string = 'READ %d\n' % (channel)
        self.__sendData(string)
        string = self.__receiveData()
        return float(string)

def getTension():
    global tension
    return tension