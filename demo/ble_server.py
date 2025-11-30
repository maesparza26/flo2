import asyncio
from bleak import BleakScanner, BleakClient
from flask import Flask, jsonify
import threading
import struct

SERVICE_UUID = "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
TEMP_UUID = "4cdffd9d-8787-4dd3-88da-8a0309152a09"
TARGET_NAME = "ESP32BLE"

latest_temp = "NONE"

#Bluetooth Low Energy

async def ble_task():
    global temp_value

    print("Scanning for BLE devices...")
    device = None
    devices = await BleakScanner.discover()
    for d in devices:
        print("Found:", d.name, d.address)
        if d.name and TARGET_NAME.lower() in d.name.lower():
            device = d
            break
    
    if device is None:
        print("Target device not found")
        return 
    
    print("Connecting to", device.name, device.address)
    async with BleakClient(device) as client:
        print("Connected:", client.is_connected)

        print("Starting loop to read data...")
        try:
            while True:
                try:
                    #reading temp characteristic
                    data = await client.read_gatt_char(TEMP_UUID)

                    #data is being sent in 4 bytes 
                    if len(data) >= 4:
                        temp = struct.unpack('<f',data[0:4])[0]
                        temp_value = f"{temp: .2f}"
                        print("Temperature Reading:",temp_value)
                    else:
                        print("Unexpected data length:", len(data),data)
                except Exception as e:
                    print("Error reading temperature characteristic:",e)

                await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            print("Task cancelled")

# ---------- FLASK HTTP SERVER ----------

app = Flask(__name__)

@app.get("/temp")
def get_temp():
    return jsonify({"temp": temp_value})

def run_flask():
    # host="0.0.0.0" so emulator can reach it via 10.0.2.2
    app.run(host="0.0.0.0", port=8000, debug=False)


# ---------- MAIN ----------

if __name__ == "__main__":
    # run Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # run BLE loop
    asyncio.run(ble_task())