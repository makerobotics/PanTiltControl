#include "Arduino.h"
#include <Preferences.h>
#include "wifi_store.h"
#include "WiFi.h"

#define WIFI_TIMEOUT  10
#define BLUE_LED       2 // D4 pin

wifi_store::wifi_store(){
  pinMode(BLUE_LED, OUTPUT);    // led pin as output
  digitalWrite (BLUE_LED, HIGH);
}

/* Try to connect. If not possible, ask for credentials and try to connect */
void wifi_store::manage_credentials(void){
  bool connected = false;  
  // Try to read credentials and connect
  if (!begin()){
    Serial.println("\nEnter ssid and password");
    while(!connected){
      if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        int delimiter_pos = command.indexOf(',');
        String ssid = command.substring(0, delimiter_pos);
        String password = command.substring(delimiter_pos + 1);
        Serial.println(ssid);
        Serial.println(password);
        write_credentials(ssid, password);
        connected = connect();
        if(!connected) ESP.restart(); // restart as disconnect is not working as expected
      }
    }
  }
}

/* Read credentials in persistent memory and try to connect */
bool wifi_store::begin(void){
  if(has_credentials()){
    if (connect()) return true;
  }
  return false;
}

/* Check for credentials in persistent memory */
bool wifi_store::has_credentials(void){
  Serial.println("Reading credentials");
  
  preferences.begin("credentials", false);
  ssid = preferences.getString("ssid", ""); 
  password = preferences.getString("password", "");
  preferences.end();

  if (ssid == "" || password == ""){
    Serial.println("No values saved for ssid or password");
    return false;
  }
  else {
    Serial.print("ssid: ");Serial.println(ssid);
    Serial.print("password: ");Serial.println(password);
    return true;  
  }
}

void wifi_store::write_credentials(String new_ssid, String new_pwd){
  Serial.println("Writing credentials");
  preferences.begin("credentials", false);
  preferences.putString("ssid", new_ssid);
  preferences.putString("password", new_pwd);
  preferences.end();
}

bool wifi_store::connect(){
  int count = 0;

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(); // not working
  WiFi.begin(ssid.c_str(), password.c_str());
  Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
    if(count > WIFI_TIMEOUT) return false;
    count++;
  }
  Serial.println(WiFi.localIP());
  digitalWrite (BLUE_LED, LOW);
  return true;
}
