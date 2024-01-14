import paho.mqtt.client as mqtt
import json
import base64
import psycopg2
import struct
import time
import logging
import os

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PostgreSQL database credentials
db_name = os.getenv('DB_NAME', 'default_db_name')
db_user = os.getenv('DB_USER', 'default_user')
db_password = os.getenv('DB_PASSWORD', 'default_password')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')


def connect_to_database(attempts=5, delay=5):
    while attempts > 0:
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            print("Database connection established")
            logging.info("Database connection established")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Failed to connect to the database: {e}")
            time.sleep(delay)
            attempts -= 1
    raise Exception("Unable to connect to the database after multiple attempts")


# Use the function to connect
conn = connect_to_database()
cursor = conn.cursor()

# MQTT setup
application_id = os.getenv('APPLICATION_ID', 'default_application_id')
tenant_id = os.getenv('TENANT_ID', 'default_tenant_id')
access_key = os.getenv('ACCESS_KEY', 'default_access_key')
mqtt_server = os.getenv('MQTT_SERVER', 'default_mqtt_server')

mqtt_username = f"{application_id}@{tenant_id}"
mqtt_topic = f"v3/{application_id}@{tenant_id}/devices/+/up"


def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code " + str(rc))
    client.subscribe(mqtt_topic)


def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}")
    payload = json.loads(msg.payload)

    device_id = payload['end_device_ids']['device_id']
    time_received = payload['received_at']
    frm_payload = payload['uplink_message']['frm_payload']
    decoded_payload = base64.b64decode(frm_payload)

    print("Length of decoded payload: ", len(decoded_payload))

    if len(decoded_payload) == 56:  # Expected length
        try:
            # Unpack the payload
            air_quality_format = '<24H'  # 6 sets of 4 unsigned shorts (each 2 bytes)
            gps_format = '2f'  # 2 floats for GPS coordinates (each 4 bytes)
            unpacked_data = struct.unpack(air_quality_format + gps_format, decoded_payload)

            # Extract air quality data and GPS coordinates
            air_quality_data = unpacked_data[:24]  # First 24 values (6 sets of 4 values each)
            gps_coords = unpacked_data[24:]  # Last 2 values (latitude, longitude)

            # Process and insert each set of air quality data into the database
            for i in range(0, len(air_quality_data), 4):
                co_level, pm25_level, no2_level, nh3_level = air_quality_data[i:i+4]
                latitude, longitude = gps_coords
                print(f"Device ID: {device_id}, Time: {time_received}, CO: {co_level}, PM2.5: {pm25_level}, NO2: {no2_level}, NH3: {nh3_level}, Lat: {latitude}, Long: {longitude}")
                logging.info(f"Device ID: {device_id}, Time: {time_received}, CO: {co_level}, PM2.5: {pm25_level}, NO2: {no2_level}, NH3: {nh3_level}, Lat: {longitude}, Long: {latitude}")
                # Insert data into the PostgreSQL database
                try:
                    insert_query = "INSERT INTO raw_data_2 (device_id, time_received, co_level, pm25_level, no2_level, nh3_level, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(insert_query, (device_id, time_received, co_level, pm25_level, no2_level, nh3_level, longitude, latitude))
                    conn.commit()
                except Exception as e:
                    print("Error inserting data:", e)
                    conn.rollback()

        except struct.error as e:
            print("Unpacking error:", e)
    else:
        print("Unexpected payload length")


client = mqtt.Client()
client.username_pw_set(mqtt_username, access_key)

client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_server, 1883, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    cursor.close()
    conn.close()
