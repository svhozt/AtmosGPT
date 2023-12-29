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


# def find_shortest_path(driver, start_id, end_id):
#     with driver.session() as session:
#         result = session.run(
#             "MATCH (start:Node {id: $start_id}), (end:Node {id: $end_id}) "
#             "CALL gds.alpha.shortestPath.write({ "
#             "  nodeProjection: 'Node', "
#             "  relationshipProjection: { "
#             "    ROAD: { "
#             "      type: 'CONNECTS', "
#             "      properties: 'distance', "
#             "      orientation: 'UNDIRECTED' "
#             "    } "
#             "  }, "
#             "  startNode: start, "
#             "  endNode: end, "
#             "  writeProperty: 'path' "
#             "}) "
#             "YIELD nodeCount, totalCost "
#             "RETURN nodeCount, totalCost",
#             start_id=start_id, end_id=end_id)
#         return result.single()


def find_shortest_path(driver, start_id, end_id):
    with driver.session() as session:
        result = session.run(
            "MATCH (start:Node {id: $start_id}), (end:Node {id: $end_id}) "
            "MATCH path = shortestPath((start)-[:CONNECTS*]-(end)) "
            "RETURN [node in nodes(path) | node.id] AS nodeIds",
            start_id=start_id, end_id=end_id)
        return result.single()[0]


# Example usage
if __name__ == "__main__":
    start_latitude = 8.776387
    start_longitude = 53.098774
    end_latitude = 8.782535
    end_longitude = 53.104376

    start_node_id = find_nearest_node(driver, start_latitude, start_longitude)
    end_node_id = find_nearest_node(driver, end_latitude, end_longitude)

    path_info = find_shortest_path(driver, start_node_id, end_node_id)
    print("Path info:", path_info)
