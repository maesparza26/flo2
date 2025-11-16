// arduiono files are used for BLE 
#include <Arduino.h>
// initialization, advertisting & creating services
#include <NimBLEDevice.h>

// Custom UUID
    // a service groups MULTIPLE characteristics
#define SERVICE_UUID "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
    // important to note that every sensor needs its own uuid & characteristic
    // characeristic represents a single piece of data
#define TEMP_UUID "4cdffd9d-8787-4dd3-88da-8a0309152a09"

// pointer to BLE GATT server
NimBLEServer* pServer = nullptr;
// pointer to temperature characteristic 
NimBLECharacteristic* TempChar = nullptr;

// will be used to check if BLE client is connected 
bool deviceConnected = false;

// checks to see if device is connected, when it is then deviceConnected = true
class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
        deviceConnected = true;
        // print for logic check to know when it is connected
        Serial.println("device Connected");
    }
    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
        deviceConnected = false;
        Serial.println("Disconnected");
        NimBLEDevice::startAdvertising();
    }
};

void setup() {
    // start serial for debugging
    Serial.begin(115200);
    Serial.println("Starting Bluetooth Low Energy");

    //Initialize BLE with device name
    NimBLEDevice::init("ESP32-BLE");

    //Creation of BLE server (GATT server)
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());

    //Create Service (container for characteristics)
    NimBLEService* Service = pServer->createService(SERVICE_UUID);

    //Create Temperature Characteristic
    TempChar = Service->createCharacteristic(
        TEMP_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY:: NOTIFY

        // without nim
        // // read -> clients can read the value once
        // BLECharacteristic::PROPERTY_READ |
        // // notify -> esp32 can push data automatically
        // BLECharacteristic::PROPERTY_NOTIFY
    );
    // add descriptor, client must receive notify permission
        //BLE2902 is the client characeristic configuration descriptor
        //required if you want notifications
    
    //start service
    Service->start();

    //start advertisting esp32 and temperature service
    NimBLEAdvertising* Advertise = NimBLEDevice::getAdvertising();
    Advertise->addServiceUUID(SERVICE_UUID);
    NimBLEDevice::startAdvertising();
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