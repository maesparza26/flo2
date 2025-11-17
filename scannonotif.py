import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
TEMP_UUID = "4cdffd9d-8787-4dd3-88da-8a0309152a09"

async def main():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)

    esp_device = None
    for d in devices:
        print(f"Found: {d.name} ({d.address})")
        if d.name == "ESP32BLE":
            esp_device = d
            break

    if not esp_device:
        print("ESP32 BLE device not found")
        return

    print(f"Connecting to ESP32 at {esp_device.address}...")

    async with BleakClient(esp_device.address) as client:
        if not client.is_connected:
            print("Failed to connect")
            return

        print("Connected!")

        # 🔹 NO NOTIFICATIONS YET – just read & write

        # Read initial value
        try:
            value = await client.read_gatt_char(TEMP_UUID)
            print("Initial value from ESP32:",
                  value.decode("utf-8", errors="ignore"))
        except Exception as e:
            print("Error reading characteristic:", e)

        # Write something to ESP32
        msg = "Hello from PC!"
        try:
            print("Writing:", msg)
            await client.write_gatt_char(TEMP_UUID, msg.encode("utf-8"))
            print("Write done.")
        except Exception as e:
            print("Error writing characteristic:", e)

        print("Staying connected for 5 seconds...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
