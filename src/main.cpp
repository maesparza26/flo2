// arduiono files are used for BLE 
#include <Arduino.h>
// initialization, advertisting & creating services
#include <BLEDevice.h>

#include <BLEUtils.h>

#include <BLEServer.h>

// Custom UUID
    // a service groups MULTIPLE characteristics
#define SERVICE_UUID "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
    // important to note that every sensor needs its own uuid & characteristic
    // characeristic represents a single piece of data
#define TEMP_UUID "4cdffd9d-8787-4dd3-88da-8a0309152a09"

// pointer to BLE GATT server
BLEServer* pServer = nullptr;
// pointer to temperature characteristic 
BLECharacteristic* TempChar = nullptr;

// will be used to check if BLE client is connected 
bool deviceConnected = false;

// checks to see if device is connected, when it is then deviceConnected = true
class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) override {
        deviceConnected = true;
        // print for logic check to know when it is connected
        Serial.println("device Connected");
    }
    void onDisconnect(BLEServer* pServer) override {
        deviceConnected = false;
        Serial.println("Disconnected");
        pServer->getAdvertising()->start();
    }
};

class MyCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic){
        std::string rxValue = pCharacteristic->getValue();
        if (rxValue.length() > 0) {
            Serial.print("Received from central: ");
            for (int i = 0; i < rxValue.length(); i++) {
                Serial.print(rxValue[1]);
            }
            Serial.println();
        }
    }
};

void setup() {
    // start serial for debugging
    Serial.begin(115200);
    delay(1000);
    Serial.println("Starting Bluetooth Low Energy");

    //Initialize BLE with device name
    BLEDevice::init("ESP32BLE");

    //Creation of BLE server (GATT server)
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());

    //Create Service (container for characteristics)
    BLEService* Service = pServer->createService(SERVICE_UUID);

    //Create Temperature Characteristic
    TempChar = Service->createCharacteristic(
        TEMP_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_WRITE |
        BLECharacteristic::PROPERTY_NOTIFY |   
        BLECharacteristic:: PROPERTY_INDICATE
    );
    // add descriptor, client must receive notify permission
        //BLE2902 is the client characeristic configuration descriptor
        //required if you want notifications
    
    TempChar->setCallbacks(new MyCallbacks());
    TempChar->setValue("Hello from ESP32 BLE!");

    //start service
    Service->start();

    //start advertisting esp32 and temperature service
    BLEAdvertising* Advertise = BLEDevice::getAdvertising();
    Advertise->addServiceUUID(SERVICE_UUID);
    Advertise->setScanResponse(true);
    BLEDevice::startAdvertising();
    Serial.println("BLE advertising started!");
}

void loop() {
     if (deviceConnected) {
        //read internal temperature sensor
        // standard value of 40 - 60 celsius
        // data via BLE is sent as bye not float 
        float tempC = temperatureRead();

        //packs float into 4 bytes
        uint8_t data[4];
        memcpy(data, &tempC, sizeof(float));

        //updates char value & notify
        TempChar->setValue(data,sizeof(data));
        TempChar->notify();
        // maybe look into better ways to print to terminal instead
        Serial.println("Temp:");
        Serial.println(tempC);
        Serial.println("C");
    }
    //1 Hz delay
    delay(1000);
}