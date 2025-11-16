#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

// Custom UUID

#define SERVICE_UUID "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
#define CHARACTERISTIC UUID "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"

BLEServer * pServer = nullptr;
BLECharacteristic *pTemCharacteristic = nullptr;

bool deviceConnected = false;


