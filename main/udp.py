#!/usr/bin/env python
import socket    #for sockets
import sys    #for exit
import os
import time
import logging
import json

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.WARNING)

class udp():

    def __init__(self):
        self.host = '192.168.2.40';
        self.port = 4210;
        self.busy = False

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            logger.error('Failed to create socket')
        #self.readConfig()
        logger.debug("Started udp class")

    def sendUDP_managed(self, msg):
        while (self.busy):
            time.sleep(0.05)
        return self.sendUDP(msg)

    def sendUDP(self, msg):
        res = "error"
        if(not self.busy):
            self.busy = True
            try:
                frame = msg.split()
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
        myudp.sendUDP("Welcome")
        time.sleep(0.5)
    except KeyboardInterrupt:
        # Signal termination
        logger.info("Keyboard interrupt. Terminate thread")
    finally:
        myudp.close()
        logger.debug("Thread terminated")
