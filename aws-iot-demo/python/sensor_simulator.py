import json
import random
import time
import os
from datetime import datetime, timezone
import threading
import sys

from awscrt import mqtt
from awsiot import mqtt_connection_builder

ENDPOINT = os.environ["IOT_ENDPOINT"]
DEVICE_ID = os.environ["DEVICE_ID"]
CERT_PATH = os.environ["CERT_PATH"]
PRIVATE_KEY_PATH = os.environ["PRIVATE_KEY_PATH"]
ROOT_CA_PATH = os.environ["ROOT_CA_PATH"]

TOPIC = f"sensors/temperature/{DEVICE_ID}"

SENSOR_TYPE = "environment"
LOCATION = "office-tokyo"

mode = "normal"  # normal / alert

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=CERT_PATH,
    pri_key_filepath=PRIVATE_KEY_PATH,
    ca_filepath=ROOT_CA_PATH,
    client_id=DEVICE_ID
)

# 初期設定値
INIT_TEMPERATURE = 24.0
INIT_HUMIDITY = 55.0
INIT_CO2 = 600
INIT_BATTERY = 100.0

temperature = INIT_TEMPERATURE
humidity = INIT_HUMIDITY
co2 = INIT_CO2
battery = INIT_BATTERY

# 異常判定閾値
TEMP_ALERT_THRESHOLD = 35.0
CO2_ALERT_THRESHOLD = 1000
BATTERY_ALERT_THRESHOLD = 20.0

#TTL設定
ttl = int(time.time()) + 60 * 60 * 24  # 24時間後

def input_listener():
    global mode
    print(
    "Input mode:\n"
    "0=Reset(normal)\n"
    "1=normal\n"
    "2=high temperature\n"
    "3=high CO2\n"
    "4=low battery\n"
    "5=all alerts\n"
    "6=Random"
    )

    #手動モード設定
    while True:
        key = sys.stdin.read(1)
        if key == "0":
            print("Mode -> RESET(NORMAL)")
            reset_sensor_values()
        elif key == "1":
            mode = "normal"
            print("Mode -> NORMAL")
        elif key == "2":
            mode = "temp"
            print("Mode -> TEMP_ALERT")
        elif key == "3":
            mode = "co2"
            print("Mode -> CO2_ALERT")
        elif key == "4":
            mode = "battery"
            print("Mode -> BATTERY_ALERT")
        elif key == "5":
            mode = "all"
            print("Mode -> ALL_ALERT")
        elif key == "6":
            print("Mode -> RANDOM")
            mode = "random"

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def reset_sensor_values():
    global temperature, humidity, co2, battery, mode

    temperature = INIT_TEMPERATURE
    humidity = INIT_HUMIDITY
    co2 = INIT_CO2
    battery = INIT_BATTERY
    mode = "normal"

def generate_sensor_data():
    global temperature, humidity, co2, battery, mode

    temperature += random.uniform(-0.3, 0.3)
    humidity += random.uniform(-1.0, 1.0)
    co2 += random.randint(-20, 20)

    status = "normal"
    alert_reasons = []

    #手動モード異常設定動作
    if mode == "temp":
        temperature += random.uniform(5.0, 8.0)

    if mode == "co2":
        co2 += random.randint(800, 1200)

    if mode == "battery":
        battery = clamp(battery - random.uniform(5.0, 10.0), 0.0, 100.0)

    if mode == "all":
        temperature += random.uniform(5.0, 8.0)
        co2 += random.randint(800, 1200)
        battery = clamp(battery - random.uniform(5.0, 10.0), 0.0, 100.0)

    if mode == "random":
        temperature = random.uniform(20.0, 40.0)
        humidity = random.uniform(30.0, 80.0)
        co2 = random.randint(400, 2000)
        battery = random.uniform(10.0, 100.0)

    #clamp関数呼び出し(あり得ない値にならない範囲制限)
    temperature = clamp(temperature, -10.0, 50.0)
    humidity = clamp(humidity, 0.0, 100.0)
    co2 = clamp(co2, 400, 5000)
    battery = clamp(battery - random.uniform(0.01, 0.05), 0.0, 100.0)

    # 異常判定
    if temperature > TEMP_ALERT_THRESHOLD:
        alert_reasons.append("high_temperature")

    if co2 > CO2_ALERT_THRESHOLD:
        alert_reasons.append("high_co2")

    if battery < BATTERY_ALERT_THRESHOLD:
        alert_reasons.append("low_battery")

    status = "alert" if alert_reasons else "normal"

    return {
        "deviceId": DEVICE_ID,
        "sensorType": SENSOR_TYPE,
        "location": LOCATION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ttl": ttl,
        "metrics": {
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "co2": int(co2)
        },
        "battery": round(battery, 1),
        "status": status,
        "alertReasons": alert_reasons
    }

if __name__ == "__main__":
    mqtt_connection.connect().result()
    print("Connected to AWS IoT")
    threading.Thread(target=input_listener, daemon=True).start()

    while True:
        data = generate_sensor_data()

        mqtt_connection.publish(
            topic=TOPIC,
            payload=json.dumps(data),
            qos=mqtt.QoS.AT_LEAST_ONCE
        )

        time.sleep(30)
