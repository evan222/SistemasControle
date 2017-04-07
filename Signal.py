flag = False
init_time = 0.0
periodo = 0.0
amplitude = 0.0

import random
import math

def sign(x):
    if(x<=0.0):
        return 0.0
    elif(x>0):
        return 1.0

# onda degrau
def waveStep(amplitude, offset):
    return float(amplitude+offset)


# onda senoidal
def waveSine(amplitude, period, offset, time):
    phase = 0
    angle = ((2*math.pi*time)/period) + phase
    return float(amplitude*math.sin(angle) + offset)


# onda quadrada
def waveSquare(amplitude, period, offset, time):
    phase = 0;
    angle = ((2*math.pi*time)/period) + phase
    return float(amplitude*sign(math.sin(angle)) + offset)


# onda dente de serra
def waveSawtooth(amplitude, period, offset, time):
    return float(amplitude*(time%period)/period + offset)

# onda aleatorio
def waveRandom(amp_max, per_max, offset, time):
    global flag, init_time, periodo, amplitude
    if(not flag):
        random.seed()
        init_time = time;
        amplitude = random.randrange(-amp_max,amp_max+1,1)
        periodo = random.randrange(per_max)
        flag = True
    elif (time >= init_time+periodo):
        flag = False
    return float(amplitude + offset)