from neo4j import GraphDatabase
import os

# Load environment variables
uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', 'default_password')

# Neo4j connection settings
neo4j_driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))


def find_nearest_node(driver, latitude, longitude):
    with driver.session() as session:
        result = session.run(
            "WITH point({latitude: $latitude, longitude: $longitude}) AS inputPoint "
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


def generate_google_maps_navigation_link(path):
    if not path or len(path) < 2:
        return None

    start_point = path[0]
    end_point = path[-1]
    waypoints = path[1:-1]

    base_url = "https://www.google.com/maps/dir/?api=1"
    origin_param = f"origin={start_point[1]},{start_point[0]}"
    destination_param = f"destination={end_point[1]},{end_point[0]}"
    waypoints_param = "&waypoints=" + '|'.join([f"{lat},{lng}" for lng, lat in waypoints])

    url = f"{base_url}&{origin_param}&{destination_param}&{waypoints_param}&travelmode=driving"
    return url


if __name__ == "__main__":
    start_latitude = 8.776387
    start_longitude = 53.098774
    end_latitude = 8.782535
    end_longitude = 53.104376

    start_node_id = find_nearest_node(driver, start_latitude, start_longitude)
    end_node_id = find_nearest_node(driver, end_latitude, end_longitude)

    path_info = find_shortest_path(driver, start_node_id, end_node_id)
    print("Path info:", path_info)

    if path_info:
        google_maps_link = generate_google_maps_navigation_link(path_info)
        if google_maps_link:
            print("Google Maps Navigation Link:", google_maps_link)
        else:
            print("Error: Unable to generate Google Maps link.")
