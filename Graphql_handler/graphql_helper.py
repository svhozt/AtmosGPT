import logging
import time
import psycopg2
import psycopg2.extras
from neo4j import GraphDatabase
import folium
import os

# Database initialization for PostgreSQL
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            return conn
        except psycopg2.OperationalError as e:
            logging.error(f"Failed to connect to the database: {e}")
            time.sleep(delay)
            attempts -= 1
    raise Exception("Unable to connect to the database")


pg_conn = connect_to_database()


# Load environment variables
uri = os.getenv('NEO4J_URI', 'neo4j://neo4j:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', 'default_password')

# Neo4j connection settings
neo4j_driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))


def find_nearest_node(driver, latitude, longitude):
    with driver.session() as session:
        result = session.run(
            "WITH point({latitude: $latitude,longitude: $longitude}) AS inputPoint "
            "MATCH (n:Node) "
            "RETURN n.id AS nodeId, point.distance(point({latitude: n.latitude, longitude: n.longitude}), inputPoint) AS dist "
            "ORDER BY dist "
            "LIMIT 1",
            latitude=latitude, longitude=longitude)
        return result.single()[0]


def find_shortest_path(driver, start_id, end_id):
    with driver.session() as session:
        result = session.run(
            "MATCH (start:Node {id: $start_id}), (end:Node {id: $end_id}) "
            "MATCH path = shortestPath((start)-[:CONNECTS*]-(end)) "
            "RETURN [node in nodes(path) | node.id] AS nodeIds",
            start_id=start_id, end_id=end_id)
        return result.single()[0]


def get_data_from_postgres():
    with pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM raw_data_2 ORDER BY time_received;")
        return cur.fetchall()


def update_air_quality_table(data):
    with pg_conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, """
            INSERT INTO air_quality (co_level,
                                      pm25_level,
                                      no2_level,
                                      nh3_level,
                                      longitude,
                                      latitude, geom)
            VALUES (%s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_Point(%s, %s), 4326));
            """, [(
                row[2],
                row[3],
                row[4],
                row[5],
                row[0],
                row[1],
                row[0],
                row[1]) for row in data])
    pg_conn.commit()


def process_data(raw_data):
    processed_data = []
    number_of_rows_to_leave = len(raw_data) % 6  # Calculate how many rows to leave unprocessed
    rows_to_process = len(raw_data) - number_of_rows_to_leave

    for i in range(0, rows_to_process, 6):
        segment = raw_data[i:i + 6]
        if len(segment) < 6 or i + 6 >= len(raw_data):
            break

        next_point = raw_data[i + 6]

        # Get interpolated points
        start_point = (segment[0]['longitude'], segment[0]['latitude'])
        end_point = (next_point['longitude'], next_point['latitude'])

        start_node_id = find_nearest_node(
            neo4j_driver, start_point[1], start_point[0])
        end_node_id = find_nearest_node(
            neo4j_driver, end_point[1], end_point[0])

        interpolated_points = find_shortest_path(
            neo4j_driver, start_node_id, end_node_id)
        if not interpolated_points:
            continue

        # Determine interval for picking 6 points
        interval = max(len(interpolated_points) // 6, 1)

        # Pick 6 approximately equally spaced points
        selected_points = [interpolated_points[j] for j in range(
            0, min(len(interpolated_points), 6 * interval), interval)]

        for row, point in zip(segment, selected_points):
            processed_data.append((
                point[0],
                point[1],
                row['co_level'],
                row['pm25_level'],
                row['no2_level'],
                row['nh3_level'],
                row['time_received']
            ))

    return processed_data


def visualize_path(data, filename='path_map.html'):
    if not data:
        print("No data to visualize.")
        return

    # Create a map centered on the first point
    folium_map = folium.Map(location=[data[0][1], data[0][0]], zoom_start=14)

    # Create a list of coordinates for the path
    path_coords = [(row[1], row[0]) for row in data]  # (latitude, longitude)

    # Add the path as a line to the map
    folium.PolyLine(
        path_coords, color="blue", weight=2.5, opacity=1).add_to(folium_map)

    # Save the map to an HTML file
    folium_map.save(filename)
    print(f"Map saved as {filename}")


def remove_processed_data(ids):
    with pg_conn.cursor() as cur:
        cur.execute("DELETE FROM raw_data_2 WHERE id = ANY(%s);", (ids,))
    pg_conn.commit()


def main():
    while True:
        try:
            raw_data = get_data_from_postgres()
            total_rows = len(raw_data)
            if total_rows >= 7:  # Check for at least 7 rows
                # Calculate the number of complete sets
                number_of_complete_sets = (total_rows - 1) // 6

                # Process and delete only complete sets, leaving the last set
                rows_to_process = number_of_complete_sets * 6
                processed_data = process_data(raw_data[:rows_to_process])
                visualize_path(processed_data)
                update_air_quality_table(processed_data)

                # Collect IDs of processed rows
                processed_ids = [
                    row['id'] for row in raw_data[:rows_to_process]]
                remove_processed_data(processed_ids)
            else:
                logging.info("Not enough data to process.")

            time.sleep(60)  # Wait for 1 minute
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    main()
