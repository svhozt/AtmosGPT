import psycopg2
import logging
import time
import networkx as nx
import geopy.distance
import geopandas as gpd
import pickle
from shapely.geometry import MultiLineString
from neo4j import GraphDatabase
import os

# Database initialization
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db_name = os.getenv('DB_NAME', 'default_db_name')
db_user = os.getenv('DB_USER', 'default_user')
db_password = os.getenv('DB_PASSWORD', 'default_password')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')


neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', 'default_password')


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

def build_network(conn):
    G = nx.Graph()
    sql = 'SELECT gid, geom FROM "highway-bremen";'
    df = gpd.read_postgis(sql, conn, geom_col='geom')
    for index, row in df.iterrows():
        geom = row.geom
        if isinstance(geom, MultiLineString):
            for line in geom.geoms:
                add_edges_from_line(G, line)
        else:
            add_edges_from_line(G, geom)
    return G

def add_edges_from_line(G, line):
    coords = list(line.coords)
    for i in range(len(coords) - 1):
        point1 = coords[i]
        point2 = coords[i + 1]
        distance = geopy.distance.distance(point1, point2).km
        G.add_edge(point1, point2, weight=distance)

def save_graph(graph, filename='network_graph.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(graph, f)

def load_graph(filename='network_graph.pkl'):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def connect_to_neo4j(uri, user, password):
    return GraphDatabase.driver(uri, auth=(user, password))

def create_node(tx, node_id, latitude, longitude):
    query = (
        "MERGE (n:Node {id: $node_id}) "
        "ON CREATE SET n.latitude = $latitude, n.longitude = $longitude"
    )
    tx.run(query, node_id=node_id, latitude=latitude, longitude=longitude)

def create_relationship(tx, node_id_1, node_id_2, distance):
    query = (
        "MATCH (n1:Node {id: $node_id_1}), (n2:Node {id: $node_id_2}) "
        "MERGE (n1)-[:CONNECTS {distance: $distance}]->(n2)"
    )
    tx.run(query, node_id_1=node_id_1, node_id_2=node_id_2, distance=distance)

def transfer_graph_to_neo4j(graph, neo4j_driver):
    with neo4j_driver.session() as session:
        for node in graph.nodes:
            session.write_transaction(create_node, node, node[0], node[1])
        for start_node, end_node, data in graph.edges(data=True):
            session.write_transaction(create_relationship, start_node, end_node, data['weight'])

# Main Execution
if __name__ == "__main__":
    neo4j_driver = connect_to_neo4j(neo4j_uri, neo4j_user, neo4j_password)

    try:
        G = load_graph()  # Load the graph from a file
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        conn = connect_to_database()
        try:
            G = build_network(conn)  # Build the graph
            save_graph(G)  # Save the graph to a file
        finally:
            conn.close()

    # Transfer the graph to Neo4j
    transfer_graph_to_neo4j(G, neo4j_driver)

    neo4j_driver.close()
