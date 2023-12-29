import psycopg2
import logging
import time
import os

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PostgreSQL database credentials
db_name = os.getenv('DB_NAME', 'default_db_name')
db_user = os.getenv('DB_USER', 'default_user')
db_password = os.getenv('DB_PASSWORD', 'default_password')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')


# Thresholds for each pollutant (hypothetical values)
CO_THRESHOLDS = {'Good': 4.4, 'Moderate': 9.4, 'Unhealthy': 12.4, 'Very Unhealthy': 15.0}  # ppm
PM25_THRESHOLDS = {'Good': 12, 'Moderate': 35.4, 'Unhealthy': 55.4, 'Very Unhealthy': 150.0}  # µg/m³
NO2_THRESHOLDS = {'Good': 53, 'Moderate': 100, 'Unhealthy': 360, 'Very Unhealthy': 649}  # ppb
NH3_THRESHOLDS = {'Good': 100, 'Moderate': 200, 'Unhealthy': 400, 'Very Unhealthy': 700}  # hypothetical units


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

            return conn
        except psycopg2.OperationalError as e:
            logging.error(f"Failed to connect to the database: {e}")
            time.sleep(delay)
            attempts -= 1
    raise Exception("Unable to connect to the database ")


def set_initial_levels():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        query = """
        UPDATE "highway-bremen"
        SET co_level = 150,
            pm25_level = 150,
            no2_level = 150,
            nh3_level = 150,
            air_quality_level = 150;
        """

        cursor.execute(query)
        conn.commit()
        logging.info("Initial levels set in highway-bremen table")
    except Exception as e:
        logging.error(f"Error setting initial levels in  table: {e}")
    finally:
        cursor.close()
        conn.close()


def update_highway_bremen():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        query = """
        UPDATE "highway-bremen" AS h
        SET
            co_level = a.co_level,
            pm25_level = a.pm25_level,
            no2_level = a.no2_level,
            nh3_level = a.nh3_level
        FROM air_quality AS a
        WHERE ST_DWithin(h.geom::geography, a.geom::geography, 200);
        """

        cursor.execute(query)
        conn.commit()
        logging.info("highway-bremen table updated successfully")
    except Exception as e:
        logging.error(f"Error updating highway-bremen table: {e}")
    finally:
        cursor.close()
        conn.close()


# Function to classify individual pollutant level
def classify_pollutant_level(value, thresholds):
    for level, threshold in thresholds.items():
        if value <= threshold:
            return level
    return 'Hazardous'


# Function to determine overall air quality level
def determine_air_quality_level(co_level, pm25_level, no2_level, nh3_level):
    # If all levels are 150, do not update air quality level
    if all(level == 150 for level in [co_level, pm25_level, no2_level, nh3_level]):
        return None

    co_quality = classify_pollutant_level(co_level, CO_THRESHOLDS)
    pm25_quality = classify_pollutant_level(pm25_level, PM25_THRESHOLDS)
    no2_quality = classify_pollutant_level(no2_level, NO2_THRESHOLDS)
    nh3_quality = classify_pollutant_level(nh3_level, NH3_THRESHOLDS)

    all_levels = [co_quality, pm25_quality, no2_quality, nh3_quality]

    # Mapping air quality levels to numbers
    level_mapping = {
        'Good': 1,
        'Moderate': 2,
        'Unhealthy': 3,
        'Very Unhealthy': 4,
        'Hazardous': 5
    }

    numeric_levels = [level_mapping[level] for level in all_levels if level in level_mapping]
    return max(numeric_levels) if numeric_levels else None


def update_air_quality_levels():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Select all rows from the table
        cursor.execute("SELECT gid, co_level, pm25_level, no2_level, nh3_level FROM \"highway-bremen\";")
        rows = cursor.fetchall()

        # Iterate over each row and update the air quality level
        for row in rows:
            gid, co_level, pm25_level, no2_level, nh3_level = row
            air_quality_level = determine_air_quality_level(co_level, pm25_level, no2_level, nh3_level)

            if air_quality_level is not None:
                # Update the air_quality_level for the current row
                update_query = """
                    UPDATE "highway-bremen"
                    SET air_quality_level = %s
                    WHERE gid = %s;
                """
                cursor.execute(update_query, (air_quality_level, gid))

        conn.commit()
        logging.info("Air quality levels updated successfully for all rows.")
    except Exception as e:
        logging.error(f"Error updating air quality levels: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    set_initial_levels()  # Set initial levels when the script runs first time
    logging.info("Starting main process")

    # Initialize last_checked with the current max timestamp from air_quality
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(updated_at) FROM air_quality;")
    last_checked = cursor.fetchone()[0]
    logging.info(f"Initial last_checked timestamp: {last_checked}")
    cursor.close()
    conn.close()

    while True:
        # Check if the air_quality table has been updated
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(updated_at) FROM air_quality;")
        last_updated = cursor.fetchone()[0]

        if last_updated != last_checked:
            logging.info(f"Detected update in air_quality table. Last updated at: {last_updated}")
            last_checked = last_updated
            update_highway_bremen()
            update_air_quality_levels()

        cursor.close()
        conn.close()
        time.sleep(5)


if __name__ == "__main__":
    main()
