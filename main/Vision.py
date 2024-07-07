#!/usr/bin/env python

import time
import logging
import picamera
import picamera.array
import cv2
from fractions import Fraction
from threading import Thread
import numpy as np
import random as rng

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
rng.seed(12345)

class Vision(Thread):

    def __init__(self, cam = None):
        Thread.__init__(self)
        self._running = True
        self.processing = False

        if cam is None:
            #self.camera = picamera.PiCamera(resolution=(1280, 720), framerate=Fraction(1, 6), sensor_mode=3)
            self.camera = picamera.PiCamera(resolution=(640, 480))
            #self.camera = picamera.PiCamera(resolution=(640, 480), sensor_mode=3)
            #self.camera.rotation = 180
            self.camera.start_preview()
            # Camera warm-up time
            time.sleep(2)
            #self.camera.shutter_speed = 6000000
            #self.camera.shutter_speed = 600000
            self.camera.iso = 800
            # Give the camera a good long time to set gains and
            # measure AWB (you may wish to use fixed AWB instead)
            #sleep(30)
            #self.camera.exposure_mode = 'off'
            # Finally, capture an image with a 6s exposure. Due
            # to mode switching on the still port, this will take
            # longer than 6 seconds
            #self.camera.capture('dark.jpg')
        else:
            self.camera = cam
        self.image = None
        self.blurred = None

    def terminate(self):
        self._running = False

    def run(self):
        logger.debug('Vision thread running')
        while self._running:
            ### Wait for command (call of runCommand by rpibot.py)
            if(self.processing == True):
                self.capture()
                #self.prepareImage()
                self.process()
                self.processing = False
            #else:
            #    self.idleTask()
            time.sleep(0.05)
        self.close()
        logger.debug('Vision thread terminating')

    def close(self):
        self.camera.close()
        self.camera = None

    def parameter(self, par_array):
        print(par_array[1:5])

    def capture(self):
        rawCapture = picamera.array.PiRGBArray(self.camera)
        self.camera.capture(rawCapture, format="bgr")
        self.image = rawCapture.array

    def prepareImage(self, filename="blurred.jpg"):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        #gray = cv2.equalizeHist(gray)
        self.blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        #self.saveImage(self.blurred, "blurred.jpg")

    def edgeDetectionCanny(self, filename="canny.jpg"):
        output = cv2.Canny(self.blurred, 10, 200)
        self.saveImage(output, filename)

    def findCont(self, img):
        AREA_THRESHOLD = 200
        # Find contours
        image, contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Draw contours
        drawing = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
        for i in range(len(contours)):
            area = cv2.contourArea(contours[i])
            #leftmost = tuple(contours[i][contours[i][:,:,0].argmin()][0])
            #rightmost = tuple(contours[i][contours[i][:,:,0].argmax()][0])
            #topmost = tuple(contours[i][contours[i][:,:,1].argmin()][0])
            bottommost = tuple(contours[i][contours[i][:,:,1].argmax()][0])
            if area > AREA_THRESHOLD:
                color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
                cv2.drawContours(self.image, contours, i, color, 2, cv2.LINE_8, hierarchy, 0)
        self.saveImage(self.image, "contours.jpg")

    def edgeDetectionSobel(self, filename="sobel.jpg"):
        # main treatment
        #sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)  # x
        output = cv2.Sobel(self.blurred,cv2.CV_64F,0,1,ksize=5)  # y
        # result output
        self.saveImage(output, filename)

    def snapshot(self):
        self.camera.capture('foo.jpg')
        # raspistill -ss 6000000 -t 3000 -ex night -ISO 800 -o still.jpg

    def process(self, algo=4):
        if(algo == 1):
            self.prepareImage()
            self.algo_1()
        elif(algo == 2):
            self.algo_2()
        elif(algo == 3):
            self.algo_3()
        elif(algo == 4):
            self.algo_4()

    def algo_1(self, filename="test.jpg"):
        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv2.bitwise_not(self.blurred)
        bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
        #self.saveImage(bw, "bw.jpg")
        # Create the images that will use to extract the horizontal and vertical lines
        horizontal = np.copy(bw)
        vertical = np.copy(bw)
        # [horiz]
        # Specify size on horizontal axis
        cols = horizontal.shape[1]
        horizontal_size = cols // 30
        # Create structure element for extracting horizontal lines through morphology operations
        horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
        # Apply morphology operations
        horizontal = cv2.erode(horizontal, horizontalStructure)
        horizontal = cv2.dilate(horizontal, horizontalStructure)

        # [vert]
        # Specify size on vertical axis
        rows = vertical.shape[0]
        verticalsize = rows // 30
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
        # Apply morphology operations
        vertical = cv2.erode(vertical, verticalStructure)
        vertical = cv2.dilate(vertical, verticalStructure)

        # result output
        #self.saveImage(horizontal, "horizontal.jpg")
        #self.saveImage(vertical, "vertical.jpg")

        or_horiz_vert = cv2.bitwise_or(horizontal, vertical)
        #self.saveImage(or_horiz_vert, "mix.jpg")
        self.findCont(or_horiz_vert)

    def algo_2(self, filename="test.jpg"):
        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv2.bitwise_not(self.blurred)
        bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
        #self.saveImage(bw, "bw.jpg")
        # Create the images that will use to extract the horizontal and vertical lines
        horizontal = np.copy(bw)
        vertical = np.copy(bw)
        # [horiz]
        # Specify size on horizontal axis
        cols = horizontal.shape[1]
        horizontal_size = cols // 30
        # Create structure element for extracting horizontal lines through morphology operations
        horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
        # Apply morphology operations
        horizontal = cv2.erode(horizontal, horizontalStructure)
        horizontal = cv2.dilate(horizontal, horizontalStructure)

        # [vert]
        # Specify size on vertical axis
        rows = vertical.shape[0]
        verticalsize = rows // 30
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
        # Apply morphology operations
        vertical = cv2.erode(vertical, verticalStructure)
        vertical = cv2.dilate(vertical, verticalStructure)

        # result output
        #self.saveImage(horizontal, "horizontal.jpg")
        #self.saveImage(vertical, "vertical.jpg")

        or_horiz_vert = cv2.bitwise_or(horizontal, vertical)
        #self.saveImage(or_horiz_vert, "mix.jpg")
        self.findCont(or_horiz_vert)

    def algo_3(self, filename="test.jpg"):
        # Object detection from Stable camera
        object_detector = cv2.createBackgroundSubtractorMOG2()
        while True:
            ret, frame = cap.read()
        
            # 1. Object Detection
            mask = object_detector.apply(frame)
            _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 255, 0), 3)

    def algo_4(self, filename="test.jpg"):
        # Convert to HSV
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        # Define brown color range
        lower_brown = np.array([150, 160, 60])
        upper_brown = np.array([200, 255, 200])

        # Threshold the image
        mask = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # Find contours
        _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        index = 0
        # Draw bounding boxes (optional)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            surf = cv2.contourArea(contour)
            peri = cv2.arcLength(contour, True)
            #approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if(surf > 10000):
                index += 1
                label = f"Contour {index}"
                # Draw the bounding box
                cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                # Draw the contour on the image
                cv2.drawContours(self.image, [contour], -1, (0, 255, 0), 2)  # Green color, thickness 2
                #cv2.drawContours(roi, [approx], -1, (0, 255, 0), 2)  # Green color, thickness 2
                # Draw the label near the contour
                cv2.putText(self.image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

                # compute the center of the contour
                M = cv2.moments(contour)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv2.circle(self.image, (cX, cY), 7, (255, 255, 255), -1)
                cv2.putText(self.image, f"center ({cX}, {cY})", (cX - 20, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    def saveImage(self, output, filename):
        cv2.imwrite(filename, output)

    def imageProcessing(self):
        self.processing = True

# Run this if standalone (test purpose)
if __name__ == '__main__':
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)

    try:
        logger.info("Start image processing")
        v = Vision()
        logger.info("Created image processing thread")
        v.start()
        logger.info("Started image processing thread")
        v.imageProcessing()
        logger.info("Started image processing")
        while v.processing == True:
            time.sleep(0.1)
            #print("waiting...")
        logger.info("camera closed")
    except KeyboardInterrupt:
        # Signal termination 
        logger.info("Keyboard interrupt. Terminate thread")
    finally:
        logger.info("Image processing finished")
        v.terminate()
        logger.debug("Thread terminated")

        # Wait for actual termination (if needed)
        v.join()
        logger.debug("Thread finished")
