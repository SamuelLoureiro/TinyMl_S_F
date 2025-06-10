#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>


BLEService imuService("12345678-1234-5678-1234-56789abcdef0");
BLECharacteristic imuChar("abcdefab-1234-5678-1234-56789abcdef0", BLENotify, 60);


#define FREQUENCIA_HZ 5 
const unsigned long BLE_SEND_INTERVAL_MS = 1000 / FREQUENCIA_HZ;
unsigned long lastDataSentMillis = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 5000); 

  Serial.println("Iniciando IMU...");
  if (!IMU.begin()) {
    Serial.println("ERRO: IMU não detectado ou falha na inicialização");
    while (1);
  }

  Serial.println("IMU OK!");

  Serial.println("Iniciando BLE...");
  if (!BLE.begin()) {
    Serial.println("ERRO: Falha ao iniciar BLE!");
    while (1);
  }
  Serial.println("BLE OK!");

  BLE.setLocalName("IMU-Vaca");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuChar);
  BLE.addService(imuService);

  BLE.advertise();
  Serial.println("Anunciando como IMU-Vaca");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado a: ");
    Serial.println(central.address());

    while (central.connected()) {
      unsigned long currentMillis = millis();

      if (currentMillis - lastDataSentMillis >= BLE_SEND_INTERVAL_MS) {
        lastDataSentMillis += BLE_SEND_INTERVAL_MS;

        float ax, ay, az, gx, gy, gz;

        if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
          IMU.readAcceleration(ax, ay, az);
          IMU.readGyroscope(gx, gy, gz);

          char dados[60];
          snprintf(dados, sizeof(dados), "%.2f,%.2f,%.2f,%.2f,%.2f,%.2f",
                   ax, ay, az, gx, gy, gz);

          imuChar.writeValue((const uint8_t*)dados, strlen(dados)); 
          Serial.println(dados);
        }
      }
    }
    
    Serial.print("Desconectado de: ");
    Serial.println(central.address());
  } else {
    if (!BLE.advertise()) {
        Serial.println("Anunciando novamente como IMU-Vaca");
        BLE.advertise();
    }
    delay(100);
  }
}