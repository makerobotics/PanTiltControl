#include <stdio.h>  // sscanf
#include <stdlib.h> // atoi
#include <string.h> // strlen
#include <WiFi.h>
#include <WiFiUdp.h>

// sketch worked again after adding these includes...

#include <WiFi.h>
#include <WiFiAP.h>
#include <WiFiClient.h>
#include <WiFiGeneric.h>
#include <WiFiMulti.h>
#include <WiFiSTA.h>
#include <WiFiScan.h>
#include <WiFiServer.h>
#include <WiFiType.h>
#include <WiFiUdp.h>

#include <EEPROM.h>

#include "wifi_store.h"

/*
PROPERTIES
----------
Steps per revolution: 200
Step control: half step
Full turn steps: 
Steps per deg: 8127/360 = 22,575 /deg
*/

// Include the AccelStepper library:
#include <AccelStepper.h>
// http://www.airspayce.com/mikem/arduino/AccelStepper/classAccelStepper.html

// UPD client:
// nc -u 192.168.2.164 4210
#define UDP_PORT          4210

#define INIT_MAX_SPEED    1500 // max
#define INIT_ACCEL        600

#define CMD_GOTO          1 // 1 33 44 [move stepper to 33 and 44]
#define CMD_STOP          2 // 2 [stop stepper]
#define CMD_MODE          3
#define CMD_SET           4 // 4 2 400 400 [set max speed to 400]
#define CMD_GET           5 // 5 4
#define CMD_EE_READ       6 // 6 0
#define CMD_EE_WRITE      7 // 7 0 55
#define CMD_SCAN          8 // 8
//#define CMD_FOLLOW        9 // 9

#define CMD_SUB_SPEED     1
#define CMD_SUB_MAX_SPEED 2
#define CMD_SUB_ACCEL     3
#define CMD_SUB_POS       4
#define CMD_SUB_MOD       5 // 5 5 (get mode)
#define CMD_SUB_ENABLE    6 // 4 6 0 (0: Disable, 1: Enable)
#define CMD_SUB_MOTION    7 // 4 7 0 (0:REL, 1:ABS)

#define POS_COMMAND       0
#define POS_SUB_COMMAND   1
#define POS_CMD_PARAM_1   2
#define POS_CMD_PARAM_2   3
#define POS_RESP_PARAM_1  0
#define POS_RESP_PARAM_2  1

#define POS_MODE          1
#define POS_TARGET_LEFT   1
#define POS_TARGET_RIGHT  2
#define POS_SET_PARAM_L   2
#define POS_SET_PARAM_R   3
#define POS_SET_ENABLE    2
#define POS_SET_MOTION    2
#define POS_SET_MODE      2
#define POS_EE_ADR        1
#define POS_EE_VAL        2

#define MODE_STB          0
#define MODE_START        1
#define MODE_STOP         2
#define MODE_RUN          3
#define MODE_FOLLOW       4

#define MOTION_REL        0
#define MOTION_ABS        1

#define dirPin  17
#define stepPin 16
#define enable  19

#define dirPin2  21
#define stepPin2 22
#define enable2  23

// Define the AccelStepper interface type; 
// DRIVER mode:
#define MotorInterfaceType 1

wifi_store ws;

int stepCounter;
int steps = 200;

struct Frame {
    char rawData[50];
    int data[10];
    int length = 0;
    int newCommand = 0;
};

// UDP
WiFiUDP UDP;
char packet[255];
char response[255] = "ok\n";
char reply[] = "Packet received!";
struct Frame frame;

AccelStepper stepperL = AccelStepper(MotorInterfaceType, stepPin, dirPin);
AccelStepper stepperR = AccelStepper(MotorInterfaceType, stepPin2, dirPin2);

struct { 
  unsigned int val = 0;
} eepromdata;
int addr = 0; // only 1 address used to store the random list index

int mode = MODE_STB;
int motion = MOTION_ABS;

long targetLeft = 0, targetRight = 0;
long currentLeft = 0, currentRight = 0;

void setup() {
  // Configure serial line
  Serial.begin(115200);
  Serial.println("Starting...");
  // flush serial line
  while(Serial.available() > 0) {
    char t = Serial.read();
  }

  // Begin WiFi
  ws.manage_credentials();
 
  // Begin listening to UDP port
  UDP.begin(UDP_PORT);
  Serial.print("Listening on UDP port ");  Serial.println(UDP_PORT);

  // Enable pin configured and set to LOW  (not enabled)
  pinMode(enable, OUTPUT);
  pinMode(enable2, OUTPUT);
  digitalWrite(enable, HIGH); // Sets enable pins to ground
  digitalWrite(enable2, HIGH);// Sets enable pins to ground
  
  // Init EEPROM
  EEPROM.begin(4);  //Initialize EEPROM
  // Set the maximum steps per second:
  stepperL.setMaxSpeed(INIT_MAX_SPEED);
  stepperR.setMaxSpeed(INIT_MAX_SPEED);
  // Set the maximum acceleration in steps per second^2:
  stepperL.setAcceleration(INIT_ACCEL);
  stepperR.setAcceleration(INIT_ACCEL);
}

void loop() {
  // Receive serial frame if available
  receiveSerialFrame();
  // Receive UDP frame if available
  receiveUDPFrame();
  // Decode command and set variables
  decodeCommand();
  // Handle command received before for motion
  runCommand();
}

void runCommand(){
  int stepL, stepR;
  
  if(mode == MODE_START){
    if(motion == MOTION_REL){
      stepperR.move(targetRight);
      stepperL.move(targetLeft);
    }
    else{
      stepperR.moveTo(targetRight);
      stepperL.moveTo(targetLeft);
    }
    Serial.println("Start.");
    mode = MODE_RUN;
  }
  else if(mode == MODE_RUN){
    stepL = stepperL.run();
    stepR = stepperR.run();
    
    if((stepL == false) and (stepR == false)) mode = MODE_STOP;
  }
  else if(mode == MODE_FOLLOW){
    stepL = stepperL.runSpeed();
    stepR = stepperR.runSpeed();
  }
  else if(mode == MODE_STOP){
    stepperR.stop();
    stepperL.stop();
    Serial.println("Stop.");
    mode = MODE_STB;
  }
  else if(mode == MODE_STB){
    stepperL.disableOutputs();
    stepperR.disableOutputs();
  }
}

void receiveUDPFrame(){
  int packetSize = UDP.parsePacket();
  char delimiter[] = ",; ";
  char *ptr;
  int i = 0;
  // If packet received...
  if (packetSize) {
    Serial.print("UDP: Received packet! Size: "); Serial.println(packetSize);

    frame.length = UDP.read(frame.rawData, 255);
    if (frame.length > 0) frame.rawData[frame.length] = '\0';
    frame.newCommand = 1;

    Serial.print("UDP: Packet received: "); Serial.println(frame.rawData);

    // Convert string raw frame to int array
    ptr = strtok(frame.rawData, delimiter);
    while(ptr != NULL) {
      frame.data[i] = atoi(ptr);
      ptr = strtok(NULL, delimiter);
      i++;
    }
    frame.length = i;
  }
}

void decodeCommand(){
  // If a new frame was received
  if(frame.newCommand == 1){
    //Serial.println("New command received");
    //Serial.println("Frame length ok.");
    // Handle data in frame depending on command
    if(frame.data[POS_COMMAND] == CMD_GOTO){
      Serial.println("Goto.");
      targetLeft = frame.data[POS_TARGET_LEFT];
      targetRight = frame.data[POS_TARGET_RIGHT];
      mode = MODE_START;
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_STOP){
      Serial.println("Stop");
      mode = MODE_STOP;
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_MODE){
      Serial.print("MODE: ");
      Serial.println(frame.data[POS_MODE]);
      mode = frame.data[POS_MODE];
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_EE_READ){
      Serial.print("EEPROM value: ");
      EEPROM.get(frame.data[POS_EE_ADR], eepromdata);
      Serial.println(eepromdata.val);
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_EE_WRITE){
      Serial.print("Writing EEPROM value: ");
      Serial.print(frame.data[POS_EE_VAL]);
      Serial.print(" at adr: ");
      Serial.println(frame.data[POS_EE_ADR]);
      eepromdata.val = frame.data[POS_EE_VAL];
      EEPROM.put(frame.data[POS_EE_ADR], eepromdata);
      EEPROM.commit();    //Store data to EEPROM
      delay(100);
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_SET){
      if(frame.data[POS_SUB_COMMAND] == CMD_SUB_SPEED){
        Serial.print("set speed");
        stepperL.setSpeed(frame.data[POS_SET_PARAM_L]);
        stepperR.setSpeed(frame.data[POS_SET_PARAM_R]);
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_MAX_SPEED){
        Serial.print("set max speed");
        stepperL.setMaxSpeed(frame.data[POS_SET_PARAM_L]);
        stepperR.setMaxSpeed(frame.data[POS_SET_PARAM_R]);
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_ACCEL){
        Serial.print("set acceleration");
        stepperL.setAcceleration(frame.data[POS_SET_PARAM_L]);
        stepperR.setAcceleration(frame.data[POS_SET_PARAM_R]);
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_ENABLE){
        Serial.print("set enable");
        digitalWrite(enable, int(not(frame.data[POS_SET_ENABLE])));
        digitalWrite(enable2, int(not(frame.data[POS_SET_ENABLE])));
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_MOTION){
        Serial.print("set motion");
        motion = int(frame.data[POS_SET_MOTION]);
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_MOD){
        Serial.print("set mode");
        mode = int(frame.data[POS_SET_MODE]);
        sendUDP("ok\n");
      }
    }
    else if(frame.data[POS_COMMAND] == CMD_GET){
      if(frame.data[POS_SUB_COMMAND] == CMD_SUB_POS){
        sprintf(response, "%d %d\n", stepperL.currentPosition(), stepperR.currentPosition());
        Serial.println(response);
        sendUDP(response);
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_MOD){
        sprintf(response, "%d\n", mode);
        Serial.println(response);
        sendUDP(response);
      }
    }
    else{
      Serial.println("Unknown command.");
      sendUDP("NOK");
    }
  }
  // reset new command flag
  frame.newCommand = 0;
}

/* Test useless box components */
void receiveSerialFrame(){
  // if there's any serial available, read it:
  while (Serial.available() > 0) {
    
    // look for the next valid integer in the incoming serial stream:
    frame.data[frame.length] = Serial.parseInt();
    frame.length++;
    
    // look for the newline. That's the end of your sentence:
    if (Serial.read() == '\n') {
      frame.newCommand = 1;
      frame.length = 0;
    }
  }
}

void sendUDP(char * buffer){
  // Send return packet
  UDP.beginPacket(UDP.remoteIP(), UDP.remotePort());
  UDP.write((uint8_t*)buffer, strlen(buffer));
  UDP.endPacket();
  Serial.print("UDP Tx: "); Serial.println(buffer);
}

