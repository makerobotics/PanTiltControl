#!/usr/bin/env python
from inputs import get_gamepad
import socket    #for sockets
import sys    #for exit
import os
import time
import logging
import json

#AUTO_DISABLE = True
AUTO_DISABLE = False
GAMEPAD = True
#GAMEPAD = False
GAMEPAD_FACTOR = 50

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

class udp():

    def __init__(self):
        self.host = '192.168.2.165';
        self.port = 4210;
        self.busy = False

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            logger.error('Failed to create socket')
        #self.readConfig()
        logger.debug("Started udp class")

    def sendUDP(self, msg):
        res = "error"
        if(not self.busy):
            self.busy = True
            try:
                frame = msg.split()
                # turn angle in deg
                if("turn" in frame[0]):
                    msg = "1 "+str(round(float(frame[1])*22.575))+" "+str(round(float(frame[1])*(-22.575)))
                # move distance in cm
                if("move" in frame[0]):
                    msg = "1 "+str(round(float(frame[1])*21.558*10))+" "+str(round(float(frame[1])*(21.558*10)))
                logger.info("UDP class received: "+msg)
                try :
                    #Set the whole string
                    self.s.sendto(msg.encode(), (self.host, self.port))
                    self.s.settimeout(1)
                    
                    # receive data from client (data, addr)
                    d = self.s.recvfrom(1024)
                    reply = d[0]
                    addr = d[1]
                    
                    logger.info('Server reply : ' + reply.decode().strip())
                    res = reply.decode().strip()
                except socket.timeout:
                    logger.error("UDP Timeout")
                except socket.error:
                    logger.error('Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            except:
                logger.info("closing socket")
                self.s.close()
            self.busy = False
        else:
            res = "busy"
        return res

    def close(self):
        self.s.close()
        logger.info("Closed udp")

    def isMoving(self):
        res = self.sendUDP("5 5")
        logger.debug("Mode: "+res)
        try:
            if(int(res) == 0):
                return False
            else:
                return True
        except:
            logger.warning("is Moving reply: "+str(res))
            return True

def handleGamepad():
    global GAMEPAD_FACTOR
    logger.info("change mode to follow")
    res = myudp.sendUDP('4 5 4') # set mode follow
    logger.info(res)
    logger.debug("set enable pin")
    res = myudp.sendUDP('4 6 1') # set enable pin
    logger.info(res)
    pan = "0"
    tilt = "0"
    active = True
    while 1:
        try:
            events = get_gamepad()
            for event in events:
                gamepad_actuated = False
                if("ABS_Y" in event.code):
                    pan = str(int(event.state/GAMEPAD_FACTOR))
                    gamepad_actuated = True
                elif("ABS_X" in event.code):
                    tilt = str(int(-event.state/GAMEPAD_FACTOR))
                    gamepad_actuated = True
                elif("BTN_WEST" in event.code):
                    GAMEPAD_FACTOR = 10
                elif("BTN_NORTH" in event.code):
                    GAMEPAD_FACTOR = 100
                elif("BTN_SOUTH" in event.code):
                    GAMEPAD_FACTOR = 1000
                elif(("BTN_EAST" in event.code) and (event.state == 1)):
                    active = not(active)
                    logger.debug("Active: "+str(active))
                    res = myudp.sendUDP('4 6 '+str(int(active))) # set mode follow
                    logger.debug(res)
                    
                if(gamepad_actuated):    
                    logger.debug(event.code+": "+str(event.state))
                    res = myudp.sendUDP('4 1 '+pan+' '+tilt) # set mode follow
                    logger.debug(res)
                    res = myudp.sendUDP('5 4') # get position
                    print(res, end = '\r')
        except KeyboardInterrupt:
            # Signal termination
            logger.info("Reset enable")
            res = myudp.sendUDP('4 6 0') # reset enable
            logger.info(res)
            logger.info("Set mode to STOP")
            res = myudp.sendUDP('4 5 2') # reset mode to stop
            logger.info(res)
            print("")
            break

def handleManual(message):
    result = ""
    if(message.split()[0] == "1"):
        logger.debug("Enable driver")
        result = myudp.sendUDP('4 6 1')
        logger.debug("Response: "+str(result))
    if(not "error" in result):
        result = myudp.sendUDP(message)
        print("Response: "+str(result))
        if((AUTO_DISABLE == True) and (message.split()[0] == "1")):
            while(myudp.isMoving()):
                time.sleep(0.2)
            logger.debug("Disable driver")
            result = myudp.sendUDP('4 6 0')
            logger.debug("Response: "+str(result))

# Run this if standalone (test purpose)
if __name__ == '__main__':
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)

    try:
        logger.info("Started main")
        myudp = udp()

        while(1) :
            try:
                msg = input('Enter command : ')
                res = ""
                frame = msg.split()
                if("gp" in frame[0]):
                    handleGamepad()
                else:
                    handleManual(msg)
            except KeyboardInterrupt:
                # Signal termination
                logger.info("Keyboard interrupt. Terminate thread")
                print("")
                break
    finally:
        myudp.close()
        logger.info("Thread terminated")
