import paho.mqtt.client as mqtt
import mysql.connector
import json
import time
import ssl

# Local MQTT Configuration (NodeMCU to Gateway)
local_mqtt_broker = "mosquito"
local_mqtt_port = 1883
local_mqtt_topic = "DATA/LOCAL/SENSOR/PANEL_1"
local_client_id = "gateway"

# Remote MQTT Configuration (Gateway to Server)
remote_mqtt_broker = "5de3065f0ebb48d986135895199984d6.s2.eu.hivemq.cloud"
remote_mqtt_port = 8883
remote_client_id = "gateway1"
remote_username = "embedded_test"
remote_password = "Ravelware1402"
remote_topic = "DATA/ONLINE/SENSOR/PANEL_1"

# MySQL Configuration
db_config = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'host': 'localhost',
    'database': 'your_db_name'
}

# Connect to MySQL Database
db_connection = mysql.connector.connect(**db_config)
cursor = db_connection.cursor()

# Create table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        voltage FLOAT,
        current FLOAT,
        power FLOAT,
        temperature FLOAT,
        fan_status VARCHAR(3),
        timestamp DATETIME
    )
""")
db_connection.commit()

# MQTT Callback functions
def on_connect_local(client, userdata, flags, rc):
    print(f"Connected to local MQTT with result code {rc}")
    client.subscribe(local_mqtt_topic)

def on_message_local(client, userdata, msg):
    print(f"Message received from local MQTT: {msg.payload.decode()}")
    data = json.loads(msg.payload.decode())

    status = data.get("status")
    device_id = data.get("deviceID")
    sensor_data = data.get("data")
    
    voltage = sensor_data.get("v")
    current = sensor_data.get("i")
    power = sensor_data.get("pa")
    temperature = sensor_data.get("temp")
    fan_status = sensor_data.get("fan")
    timestamp = sensor_data.get("time")

    save_to_database(voltage, current, power, temperature, fan_status, timestamp)
    send_to_remote_mqtt(voltage, current, power, temperature, fan_status, timestamp)

def save_to_database(voltage, current, power, temperature, fan_status, timestamp):
    cursor.execute("""
        INSERT INTO sensor_data (voltage, current, power, temperature, fan_status, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (voltage, current, power, temperature, fan_status, timestamp))
    db_connection.commit()

def send_to_remote_mqtt(voltage, current, power, temperature, fan_status, timestamp):
    json_payload = {
        "status": "OK",
        "deviceID": "yourname",
        "data": {
            "v": voltage,
            "i": current,
            "pa": power,
            "temp": temperature,
            "fan": fan_status,
            "time": timestamp
        }
    }
    payload = json.dumps(json_payload)
    remote_client.publish(remote_topic, payload)
    print(f"Data sent to remote MQTT: {payload}")

# Setup Local MQTT Client
local_client = mqtt.Client(local_client_id)
local_client.on_connect = on_connect_local
local_client.on_message = on_message_local

local_client.connect(local_mqtt_broker, local_mqtt_port, 60)

# Setup Remote MQTT Client
remote_client = mqtt.Client(remote_client_id)
remote_client.username_pw_set(remote_username, remote_password)
remote_client.tls_set_context(ssl.create_default_context())
remote_client.connect(remote_mqtt_broker, remote_mqtt_port, 60)

# Start MQTT loops
local_client.loop_start()
remote_client.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    cursor.close()
    db_connection.close()
    local_client.loop_stop()
    remote_client.loop_stop()
    local_client.disconnect()
    remote_client.disconnect()
