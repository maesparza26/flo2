import asyncio
from bleak import BleakScanner, BleakClient
from flask import Flask, jsonify
import threading

SERVICE_UUID = "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
TEMP_UUID = "4cdffd9d-8787-4dd3-88da-8a0309152a09"
TARGET_NAME = "ESP32BLE"

latest_temp = "NONE"

#Bluetooth Low Energy

async def ble_task():
    global latest_temp

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
        print("Connected:", await client.is_connected())

        def notification_handler(_, data: bytearray):
            global latest_temp
            # assuming ESP32 sends ASCII like "23.45"
            latest = data.decode(errors="ignore").strip()
            print("Temp:", latest)
            latest_temp = latest

        await client.start_notify(TEMP_UUID, notification_handler)

        print("Listening for notifications. Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

# ---------- FLASK HTTP SERVER ----------

app = Flask(__name__)

@app.get("/temp")
def get_temp():
    return jsonify({"temp": latest_temp})

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