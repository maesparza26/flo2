import asyncio
from bleak import BleakScanner, BleakClient
from flask import Flask, jsonify
import threading
import struct
from collections import deque
import time

# custom UUID for service and the temperature characteristic
#note: when programming for actual app, multiple characteristics must be used for each sensor reading
SERVICE_UUID = "c64ccea3-eae9-43bf-86cd-7d5d0b7372e4"
TEMP_UUID = "4cdffd9d-8787-4dd3-88da-8a0309152a09"
#name defined in main.cpp file that was uploaded to ESP32 for bluetooth advertisement
TARGET_NAME = "ESP32BLE"

temp_value = "NONE"
# store last 100 readings --> for graphing
temp_history = deque(maxlen = 100)

#Bluetooth Low Energy

async def ble_task():
    global temp_value

    print("Scanning for Bluetooth Devices...")
    device = None
    # scans for bluetooth devices advertisements 
    # for the ESP32 to advertise,main.cpp file must be uploaded to ESP32
    devices = await BleakScanner.discover()
    #printing addresses that are being checked / devices if found
    for d in devices:
        print("Found:", d.name,"Address:", d.address)
        # if the target name mathces one of the names that bleak scanner finds, then esp32 is found
        if d.name and TARGET_NAME.lower() in d.name.lower():
            device = d
            break

    # if device cannot be found after certain time, then program will end 
    if device is None :
        print("Target device not found")
        return 

    #once device is found then it will connect to the client to be able to receive data
    print("Connecting to", device.name, device.address)
    #client interface to connect to the GATT server and communicate with it
    async with BleakClient(device) as client:
        if client.is_connected == True:
            print("Connected Succesfully!")
        else:
            print("Connection Unsucessful :(")

        print("Reading internal temperature from ESP32...")
        try:
            while True:
                try:
                    #reading temp characteristic from GATT server for the temperature custom UUID
                    data = await client.read_gatt_char(TEMP_UUID)

                    #data is being sent in 4 bytes, therfore data must be transformed into a float
                    #assuming little endian for this
                    if len(data) >= 4:
                        temp = struct.unpack('<f',data[0:4])[0]

                        temp_value = f"{temp: .2f}"
                        print("Temperature Reading:",temp_value)

                        #add each point to the history, and keep the 100 most recent readings
                        temp_history.append({
                            #tracks the time of the reading (timestamp)
                            # hour: minute: second format
                            "time": time.strftime("%H:%M:%S"),
                            #only keeps the raw float value and not the one with the string of temp in front
                            "temp": temp 
                        })

                    else:
                        #if data received is not 4 bytes (should always be)
                        print("Unexpected data length:", len(data),data)
                except Exception as e:
                    #any other errors, for debugging purposes
                    print("Error reading temperature characteristic:",e)

                # waits between readings, 1 reading per second
                await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            # this will execute whenever the user CTRL+C to stop the program 
            print("Data reading stopping...")

# ---------- FLASK HTTP SERVER ----------

#creating a flask 'app' objecty type, aka the tiny web server 
app = Flask(__name__)

# web server for temp (only 1 reading)
@app.get("/temp")
def get_temp():
    #this converts the python print into a json string text
    return jsonify({"temp": temp_value})

def run_flask():
    # host="0.0.0.0" so emulator can reach it via 10.0.2.2
    #breakdown:
    #from the PC: http://127.0.0.1:8000/temp
    #from the emulator: http://10.0.2.2:8000/temp
    app.run(host="0.0.0.0", port=8000, debug=False)

#web server for history(last 100 readings)
@app.get("/history")
def get_history():
    history_list = [
        {"time": item["time"], "temp": round(item["temp"],2)}
        for item in list(temp_history)
    ]
    return jsonify(history_list)


# ---------- MAIN ----------

if __name__ == "__main__":
    # run Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # running loop for data to be continously read from the esp32 without stopping 
    asyncio.run(ble_task())