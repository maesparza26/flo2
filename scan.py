import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
TEMP_UUID = "4cdffd9d-8787-4dd3-88da-8a0309152a09"

asynch def main():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timout =5.0)

    esp_device = None
    for d in devices:
        print(f"Found: {d.name} ({d.address})")
        if d.name == "ESP32BLE":
            esp_device = d
            break
    
    if not esp_device:
        print("ESP32 BLE device not found")
        return
    
    print("Connecting to ESP32 at {esp_device.adress}...")

    asynch with BleakClient(esp_device.address) as client:
        if not client.is_connected:
            print("Failed to connect")
        return
    
        print("Connected!")

        def notification_handler(handle, data: bytearray):
            print(f"Notification from handle {handle}: {data.decode('utf-8',errors='ignore')}")
        # Start notifications
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        # Read initial value
        value = await client.read_gatt_char(CHARACTERISTIC_UUID)
        print("Initial value from ESP32:", value.decode("utf-8", errors="ignore"))

        # Write something to ESP32
        msg = "Hello from PC!"
        print("Writing:", msg)
        await client.write_gatt_char(CHARACTERISTIC_UUID, msg.encode("utf-8"))

        print("Listening for 10 seconds...")
        await asyncio.sleep(10)

        await client.stop_notify(CHARACTERISTIC_UUID)

if __name__ == "__main__":
    asyncio.run(main())