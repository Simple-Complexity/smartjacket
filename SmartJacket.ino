

#include <Seeed_ws2812.h>

#include <BreakoutSDK.h>
#include <Ultrasonic.h>


static const char *device_purpose = "SmartJacket";
static const char *psk_key = "ff7283f9befc3b7432c61107b46efdf3";
Breakout *breakout = &Breakout::getInstance();

#define ULTRASONIC_PIN  (38)
#define INTERVAL        (1000)
#define BUTTON_PIN  20
Ultrasonic UltrasonicRanger(ULTRASONIC_PIN);
WS2812 strip = WS2812(1, RGB_LED_PIN);
long distance=-1;
bool updateServer= true;
long delta=10;
String state = ""; //State of jacket according to weather, calender, location and schedule of owner

void enableLed() {
  pinMode(RGB_LED_PWR_PIN, OUTPUT);
  //digitalWrite(RGB_LED_PWR_PIN, HIGH);
  strip.begin();
  strip.brightness = 5;
}



/**
 * Setting up the Arduino platform. This is executed once, at reset.
 */
void setup() {
  //owl_LOG_set_level(L_INFO);
  //LOG(L_WARN, "Arduino setup() starting up\r\n");
  pinMode(38, INPUT);  //ultrasonic
  enableLed();
  pinMode(20, INPUT);

  // Set the Breakout SDK parameters
  breakout->setPurpose(device_purpose);
  breakout->setPSKKey(psk_key);
  breakout->setPollingInterval(1);  // Read every second

  // Powering the modem and starting up the SDK
  //LOG(L_WARN, "Powering on module and registering...");
  breakout->powerModuleOn();

  //LOG(L_WARN, "... done powering on and registering.\r\n");
  //LOG(L_WARN, "Arduino loop() starting up\r\n");
}


/**
*Smart Jacket gets the priodic update from server based on weather on owner's schedule and calender
 */
void SmartJacket() {
  if (breakout->hasWaitingCommand()) {
    // Check if there is a command waiting and take action based on command
    char command[141];
    size_t commandLen = 0;
    bool isBinary     = false;
    // Read a command
    command_status_code_e code = breakout->receiveCommand(140, command, &commandLen, &isBinary);
    switch (code) {
      case COMMAND_STATUS_OK:
        //LOG(L_INFO, "Rx-Command [%.*s]\r\n", commandLen, command);
   
        if(String(command).indexOf("STATE")>-1){
          state=String(command);
        }
        break;
      case COMMAND_STATUS_ERROR:
        //LOG(L_INFO, "Rx-Command ERROR\r\n");
        break;
      case COMMAND_STATUS_BUFFER_TOO_SMALL:
        //LOG(L_INFO, "Rx-Command BUFFER_TOO_SMALL\r\n");
        break;
      case COMMAND_STATUS_NO_COMMAND_WAITING:
        //LOG(L_INFO, "Rx-Command NO_COMMAND_WAITING\r\n");
        break;
      default:
        break;
        //LOG(L_INFO, "Rx-Command ERROR %d\r\n", code);
    }
  }
}

//SmartJacket will use sensor to detect if it has been moved and inform the server
void JacketPicked(){
   
  if (updateServer) {
        long newDistance;
        newDistance = UltrasonicRanger.MeasureInCentimeters();
        if (newDistance>100){
          return;
        }
        
        //LOG(L_INFO, "Distance %ld  New Distance %ld \r\n",distance, newDistance);
        //LOG(L_INFO, "Jacket State %s \r\n",state.c_str());
        if(distance ==-1){
          distance= newDistance;
          return;
        } else if (abs(distance-newDistance) > delta && state.length()>0){ //When Jacket is picked
          
           if( state.indexOf("GREEN")>-1) {
            // Set RGB-LED to green
             digitalWrite(RGB_LED_PWR_PIN, HIGH);
             strip.begin();
             strip.brightness = 5;
             strip.WS2812SetRGB(0, 0x00, 0x40, 0x00);
             strip.WS2812Send();
           }else if ( state.indexOf("YELLOW")>-1){
             //Set RGB-LED to yellow
             digitalWrite(RGB_LED_PWR_PIN, HIGH);
             strip.begin();
             strip.brightness = 5;
             strip.WS2812SetRGB(0, 0x20, 0x20, 0x00);
             strip.WS2812Send();
           }else if ( state.indexOf("RED")>-1){
               // Set RGB-LED to Red
                digitalWrite(RGB_LED_PWR_PIN, HIGH);
                strip.begin();
                strip.brightness = 5;
                strip.WS2812SetRGB(0, 0x40, 0x00, 0x00);
                strip.WS2812Send();
           }
      
               if (breakout->sendTextCommand(state.c_str()) == COMMAND_STATUS_OK) {
                  //LOG(L_INFO, "Tx-Command [%s]\r\n", state.c_str());
                } else {
                  //LOG(L_INFO, "Tx-Command ERROR\r\n");
                }
                
                  //LOG(L_INFO, "Jacket was picked \r\n");
           distance =-1; 
           updateServer=false;    
        } else {
          distance=newDistance;
          //LOG(L_INFO, "Jacket is not picked\r\n" );
        }
  }

}

//reset button can return the jacket to hanging position
void resetButton(){
  int buttonState = digitalRead(BUTTON_PIN);
   if (buttonState){
     updateServer = true;
     digitalWrite(RGB_LED_PWR_PIN, LOW);
     //LOG(L_INFO, "Ready to send message to server\r\n");
   }
}

void loop() {
  SmartJacket();
  JacketPicked();
  resetButton();
  // The Breakout SDK checking things and doing the work
  breakout->spin();

  delay(INTERVAL);
}
