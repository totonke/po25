#include <Wire.h> //I2C
#include <math.h>
#include <DS1307.h> //時計
#include "rgb_lcd.h" //lcd
#include <SD.h>
#include "Arduino.h"
#include "LoRa_E220.h"

#define ADT7410_ADDR 0x48  // ADT7410のI2Cアドレス 温度計
#define LIGHT_PIN A0
#define ENABLE_RSSI true
#define ROTARY_ANGLE_SENSOR A3
#define ADC_REF 5.0
#define SW 8

LoRa_E220 e220ttl(4, 5, 3, 7, 6); // Arduino RX <-- e220 TX, Arduino TX --> e220 RX AUX M0 M1

const int chipSelect = 9; //SDのピン

// LoRa 設定の定数を定義します
// const uint8_t DEST_ADDH = 0x00; // 宛先アドレス上位バイト
// const uint8_t DEST_ADDL = 0x01; // 宛先アドレス下位バイト
// const uint8_t CHANNEL_NUM = 0x07; // 通信チャンネル（受信側と一致させる必要があります）

//平野さん班の宛先
const uint8_t DEST_ADDH = 0x00; 
const uint8_t DEST_ADDL = 0x06; 
const uint8_t CHANNEL_NUM = 0x01;


int lightValue;

//時間カウント部分
unsigned long lastSaveTime = 0;
const unsigned long saveIntervalMs = 300000; // 5 minutes
// int cnt = 0;
// int interval = 720; //120が5分

float temperature;

File myFile;
DS1307 clock;  // RTCオブジェクト
rgb_lcd lcd;

boolean saveFlg = false;
boolean sdAvailable = false;


//cnt count
void updateTimer(void){
  unsigned long now = millis();
    if (now - lastSaveTime >= saveIntervalMs) {
        saveFlg = true;
        lastSaveTime = now;
    }

  // cnt++;
  // if(cnt > interval){
  //   saveFlg = true;
  // }
}

// 温度を取得する関数
float readTemperature() {
  Wire.beginTransmission(ADT7410_ADDR);
  Wire.write(0x00);  // 温度レジスタ指定
  Wire.endTransmission();

  Wire.requestFrom(ADT7410_ADDR, 2); // 2バイト要求
  if (Wire.available() >= 2) {
    byte msb = Wire.read();
    byte lsb = Wire.read();

    int16_t raw = ((int16_t)msb << 8) | lsb;
    raw >>= 3; // 13bitモード
    return raw * 0.0625;
  }
  return NAN;  // 読み取れなかった場合
}

//時間print
void getTimeString(char* buf, size_t len){
    clock.getTime();
    snprintf(buf, len, "%04d/%02d/%02d %02d:%02d:%02d",
             clock.year + 2000,
             clock.month,
             clock.dayOfMonth,
             clock.hour,
             clock.minute,
             clock.second);
}

//取得した値達の確定
void updateSensors(){
  lightValue = analogRead(LIGHT_PIN);
  temperature = readTemperature();
}

void initSD(void){
  Serial.print("Initializing SD card...");
  if (SD.begin(chipSelect)) { 
    Serial.println("initialization done.");
    lcd.clear();
    lcd.println("SD OKAY");
    sdAvailable = true ;
    delay(1500);
    lcd.clear();
  }else{
      Serial.println("initialization failed - skipping SD logging.");
      lcd.clear();
      lcd.println("SD HAITTENAIYO");
      sdAvailable = false;
      delay(1500);
      lcd.clear();
  }
  
}


void printLCD(void) {
  char timeBuf[25];
  getTimeString(timeBuf, sizeof(timeBuf));

  lcd.setCursor(0, 0);
  lcd.print(timeBuf);
  delay(50);
  lcd.setCursor(0, 1);
  // print the number of seconds since reset:
  lcd.print(temperature);
  lcd.print("C ");
  lcd.print(lightValue);
  lcd.print(" lx");
  delay(50);
}

void saveToSD(void){
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SD SAVING");
  myFile = SD.open("log.csv", FILE_WRITE); //該当ファイルを開く

  // if the file opened okay, write to it:
  if (myFile) {                             //ファイルが開けていれば
    if (myFile.size() == 0) {
      myFile.println("Timestamp,Temperature,Light");
    }
    // myFile.print("time:");    //ファイルに書き込む
    char timeBuf[25];
    getTimeString(timeBuf, sizeof(timeBuf));

    myFile.print(timeBuf); 
    myFile.print(",");
    myFile.print(temperature); 
    myFile.print(",");
    myFile.println(lightValue); 
    // myFile.println(" lx"); 
    // close the file:
    myFile.close();                         //ファイルを閉じる
    Serial.println("done.");
  } else {
    lcd.clear();
    lcd.print("SD HAITTENAIYO");
    // if the file didn't open, print an error:
    Serial.println("error opening log.csv");
    sdAvailable = false;
  }
// lcd.clear();
}

void checkSDflg(){
  if(saveFlg == true && sdAvailable == true){
    //このフラグがたったタイミングでSDカードに書き込み
    saveToSD();
    delay(3000);
    // cnt = 0;
    saveFlg = false;
  }else if(saveFlg == true){
    initSD();
    // cnt = 0;
    saveFlg = false;
  }

}


// void buildMessage(char* out, size_t len) {

//   char tempBuf[10];  
//   dtostrf(temperature, 4, 2, tempBuf);  // float → char[]

//   // char timeBuf[25];
//   // getTimeString(timeBuf, sizeof(timeBuf));
//     // snprintf(out, len,
//   //         "device1,%s,%d,%s\n",
//   //         tempBuf,
//   //         lightValue,
//   //         timeBuf);
  
//   snprintf(out, len,
//           "dvc1,%s,%d\n",
//           tempBuf,
//           lightValue);

// //     snprintf(out, len,
// //              "device1,%.2f,%d,%s\n",
// //              temperature,
// //              lightValue,             
// //              timeBuf);
// }

void buildMessage(char* out, size_t len) {

  char tempBuf[10];
  dtostrf(temperature, 4, 2, tempBuf);

  // Remove leading spaces (E220 becomes unstable otherwise)
  for (int i = 0; i < 10; i++) {
      if (tempBuf[i] == ' ') {
          tempBuf[i] = '0';
      }
  }

  // Add extra dummy field to keep length stable
  snprintf(out, len,
           "dvc1,%s,%d,00\n",
           tempBuf,
           lightValue);
}


void sending(){
  char msg[150];
  buildMessage(msg, sizeof(msg));

  // delay(500);
  Serial.print("msg_check:");
  Serial.println(msg);

 ResponseStatus rs = e220ttl.sendFixedMessage(DEST_ADDH,DEST_ADDL,CHANNEL_NUM,msg);
  Serial.println(rs.getResponseDescription());

}



// デバッグ出力関数
void printDebugInfo(void) {
  //時間表示
  char timeBuf[25];
  getTimeString(timeBuf, sizeof(timeBuf));

  Serial.print("Time: ");
  Serial.print(timeBuf);


//デバッグ
  Serial.print(" Temperature: ");
  Serial.print(temperature);
  Serial.print(" ℃");

  Serial.print(" Light: ");
  Serial.print(lightValue);

  Serial.print(" sdAvailable: ");
  Serial.print(sdAvailable);

  Serial.print(" saveFlg: ");
  Serial.println(saveFlg);

}



void setup() {
 Serial.begin(9600);//serialスタート
 Wire.begin(); //12c
  delay(100);
 clock.begin();//
  delay(100);
 lcd.begin(16, 2);          // 16文字×2行のLCDを初期化
 lcd.setRGB(255, 255, 255);     // バックライトを緑に設定
  delay(100);
 initSD();
  delay(100);

  //addsetup1117
  //sw
  pinMode(SW, INPUT); 
  // Startup all pins and UART
  e220ttl.begin();
  //rotary
  pinMode(ROTARY_ANGLE_SENSOR,INPUT);

  //MUDA
  Serial.println("Hi, I'm going to send message!");
  // Send message
  ResponseStatus rs = e220ttl.sendMessage("NIHAOMA?");
  // Check If there is some problem of succesfully send
  Serial.println(rs.getResponseDescription());
  delay(100);

}

void loop() {

  updateSensors();
  updateTimer();
  // デバッグ出力関数を呼び出す
  delay(100);

  // printDebugInfo();
  printLCD();
  delay(1000);

  sending();

  // String msg = buildMessage();
  // ResponseStatus rs = e220ttl.sendMessage(msg);
  // Serial.println(rs.getResponseDescription());
  // delay(500);
  // Serial.println(msg);

  checkSDflg();
  // if(saveFlg == true && sdAvailable == true){
  //   //このフラグがたったタイミングでSDカードに書き込み
  //   saveToSD();
  //   delay(3000);
  //   cnt = 0;
  //   saveFlg = false;
  // }else if(saveFlg == true){
  //   initSD();
  //   cnt = 0;
  //   saveFlg = false;
  // }

  delay(1000);

}
