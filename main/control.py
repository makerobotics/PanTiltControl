#!/usr/bin/env python
#from inputs import get_gamepad
from inputs import devices
import socket    #for sockets
import time
import logging
import configparser
from threading import Thread
#import RPi.GPIO as GPIO
import sense
import data
import udp
import json
import math

#AUTO_DISABLE = True
AUTO_DISABLE = False
GAMEPAD = True
#GAMEPAD = False
GAMEPAD_FACTOR = 50

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class control(Thread):

    TRACE = 0

    def __init__(self):
        Thread.__init__(self)
        self.tracefile = None
        self.traceline = 0
        self.traceData = {}
        self.lastFrameTimestamp = time.time()
        self.cycleTime = 0
        self._running = True
        if(self.TRACE == 1):
            self.initTrace()
        self.udp = udp.udp()

    def handleGamepad(self):
        global GAMEPAD_FACTOR

        pan = "0"
        tilt = "0"
        active = True
        #events = get_gamepad() # removed as blocking the thread
        events = devices.gamepads[0]._do_iter()
        if events is not None:
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
                    res = self.udp.sendUDP_managed('4 6 '+str(int(active))) # set mode follow
                    logger.debug(res)
                    
                if(gamepad_actuated):    
                    logger.debug(event.code+": "+str(event.state))
                    res = self.udp.sendUDP_managed('4 1 '+pan+' '+tilt) # set mode follow
                    logger.debug(res)
                    res = self.udp.sendUDP_managed('5 4') # get position
                    print(res, end = '        \r')

    def initTrace(self):
        if(self.TRACE == 1):
            self.tracefile = open("trace.csv","w+")
            header = "timestamp;"
            for k, v in self.traceData.iteritems():
                header += k+";"
            header += "\r\n"
            self.tracefile.write(header)

    def writeTrace(self):
        if (self.TRACE == 1):
            if self.traceline == 0:
                self.initTrace()
                self.traceline = 1
            filestring = str(time.time())+";"
            displaystring = ""
            for k, v in self.traceData.iteritems():
                displaystring += k+": "+str(v)+", "
                filestring += str(v)+";"
            filestring += "\r\n"
            #logger.debug(displaystring)
            self.tracefile.write(filestring)

    def terminate(self): 
        self._running = False

    def close(self):
        logger.debug("Closing control thread")
        if self.TRACE == 1 and self.tracefile != None:
            self.tracefile.close()

    def idleTask(self):
        pass
        #print("."),

    def runCommand(self, cmd):
        res = ""
        if "{" in cmd:
            try:
                #logger.debug(cmd)
                command = json.loads(cmd)
                #logger.debug(command)
                return "ok"
            except:
                logger.error("Command syntax not valid: "+cmd)
                return "nok"
        else:
            logger.debug("Control thread received command: " + cmd)
            res = self.udp.sendUDP_managed(cmd)
            logger.debug("Control thread received answer: " + res)
            return res

    def run(self):
        global GAMEPAD_FACTOR
        logger.debug('Control thread running')
        
        logger.debug("set mode to follow")
        res = self.udp.sendUDP_managed('4 5 4') # set mode follow
        #logger.info(res)
        logger.debug("set enable pin")
        res = self.udp.sendUDP_managed('4 6 1') # set enable pin
        #logger.info(res)

        try:
            while self._running:
                #time.sleep(0.05)
                self.handleGamepad()
        except:
            logger.warning("No gamepad connected.")

        while self._running:
            time.sleep(0.05)
            ### Wait for command (call of runCommand by rpibot.py)
            self.idleTask()
            #self.handleGamepad()
        # Signal termination
        logger.info("Reset enable")
        res = self.udp.sendUDP_managed('4 6 0') # reset enable
        #logger.info(res)
        logger.info("Set mode to STOP")
        res = self.udp.sendUDP_managed('4 5 2') # reset mode to stop
        #logger.info(res)
        print("")

        self.close()
        logger.debug('Control thread terminating')

    def stop(self, reason):
        logger.info("Stopped by "+reason)

# Run this if standalone (test purpose)
if __name__ == '__main__':

    try:
        logger.info("Started main")
        #s = sense.sense()
        #s.start()
        #myudp = udp()
        c = control()
        c.start()
        time.sleep(2)
        c.stop("Test")
    except KeyboardInterrupt:
        # Signal termination
        logger.info("Keyboard interrupt. Terminate thread")
    finally:
        c.terminate()
        #s.terminate()
        logger.debug("Thread terminated")

        # Wait for actual termination (if needed)
        c.join()
        #s.join()
        logger.debug("Thread finished")
