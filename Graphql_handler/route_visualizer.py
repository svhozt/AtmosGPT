from neo4j import GraphDatabase
import folium

uri = "neo4j://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "12Wuw4Bbi8"))


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


def visualize_path(path):
    if not path:
        print("No path to visualize.")
        return

    # Create the map centered on the first point of the path
    folium_map = folium.Map(location=path[0][::-1], zoom_start=14)

    # Add markers for start and end points
    folium.Marker(location=path[0][::-1], popup='Start', icon=folium.Icon(color='green')).add_to(folium_map)
    folium.Marker(location=path[-1][::-1], popup='End', icon=folium.Icon(color='red')).add_to(folium_map)

    # Add a line for the path
    folium.PolyLine([point[::-1] for point in path], color='blue').add_to(folium_map)

    # Display the map
    folium_map.save("path_map.html")
    print("Map saved as path_map.html")


if __name__ == "__main__":
    start_latitude = 8.776387
    start_longitude = 53.098774
    end_latitude = 8.782535
    end_longitude = 53.104376

    start_node_id = find_nearest_node(driver, start_latitude, start_longitude)
    end_node_id = find_nearest_node(driver, end_latitude, end_longitude)

    path_info = find_shortest_path(driver, start_node_id, end_node_id)
    print("Path info:", path_info)

    visualize_path(path_info)
