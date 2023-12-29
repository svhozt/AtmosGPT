import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import folium
import psycopg2
import networkx as nx
from shapely.geometry import Point, MultiPoint, LineString
from shapely.ops import nearest_points, linemerge
import geopandas as gpd
from shapely.geometry import MultiLineString
from geopy.geocoders import Nominatim
from datetime import datetime


# Initialize the geolocator
geolocator = Nominatim(user_agent="sahanNishshanka")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "GeoServer Map Viewer"


# Function to fetch road data from the database
def fetch_roads_data():
    conn = psycopg2.connect(
        dbname="bremengeo",
        user="postgres",
        password="12Wuw4Bbi8",
        host="localhost",
        port="5433"
    )
    sql = 'SELECT * FROM "highway-bremen";'
    return gpd.read_postgis(sql, conn, geom_col='geom')


# Function to create a graph from road data
def create_graph_from_roads(roads_data):
    G = nx.Graph()
    for index, road in roads_data.iterrows():
        geom = road['geom']
        if isinstance(geom, MultiLineString):
            geom = linemerge(geom)
        if isinstance(geom, LineString):
            coords = list(geom.coords)
            for i in range(len(coords)-1):
                G.add_edge(
                    coords[i], coords[i+1], weight=calculate_weight(road))
        else:
            print(f"Skipping invalid geometry at index {index}")
    return G


# Function to calculate weight based on air quality level
def calculate_weight(road_segment):
    return 1 / max(
        road_segment['air_quality_level'], 1)  # Avoid division by zero


# Function to find the closest graph node to a given coordinate
def get_closest_node(coord, graph):
    point = Point(coord)
    all_nodes = [data['coord'] for _, data in graph.nodes(data=True)]

    # Check if all_nodes is populated correctly
    print("Number of nodes to check:", len(all_nodes))
    if not all_nodes:
        print("No nodes in graph.")
        return None

    # Convert node coordinates to Points for spatial comparison
    all_points = [Point(node_coord) for node_coord in all_nodes]

    # Find the nearest point and corresponding node
    closest_point = nearest_points(point, MultiPoint(all_points))[1]
    closest_node = [node for node, data in graph.nodes(data='coord') if data == closest_point.coords[0]][0]

    # Debug output
    print("Closest node to", coord, "is", closest_node)

    return closest_node


# Function to find the best route based on air quality
def find_route(start_coords, end_coords, G):
    # Get closest nodes to start and end coordinates
    start_node = get_closest_node(start_coords, G)
    end_node = get_closest_node(end_coords, G)

    print("Start Node:", start_node)
    print("End Node:", end_node)

    # Check if start and end nodes are valid
    if start_node not in G or end_node not in G:
        print("Invalid start or end node.")
        return []

    # Find shortest path
    try:
        route = nx.shortest_path(G, start_node, end_node)
        return route
    except nx.NetworkXNoPath:
        print("No path found.")
        return []


app.layout = html.Div([
    dbc.NavbarSimple(
        brand="GeoServer Map Viewer",
        brand_href="#",
        color="primary",
        dark=True,
    ),
    html.Div([
        dcc.Input(id='start-location', type='text', placeholder='Start Location', style={"marginRight": "10px"}),
        dcc.Input(id='end-location', type='text', placeholder='End Location', style={"marginRight": "10px"}),
        html.Button('Calculate Route', id='calculate-route-btn'),
        html.Div(id='route-map-container'),
        html.Div(id='route-map-container')
    ], style={'textAlign': 'center', 'padding': '20px'})
])


@app.callback(
    Output('route-map-container', 'children'),
    [Input('calculate-route-btn', 'n_clicks')],
    [Input('start-location', 'value'), Input('end-location', 'value')]
)
def update_map(n_clicks, start_location, end_location):
    if n_clicks is None or not all([start_location, end_location]):
        return None

    start_geo = geolocator.geocode(start_location)
    end_geo = geolocator.geocode(end_location)
    if not start_geo or not end_geo:
        return "Unable to find locations."

    # Fetch road data and create a graph
    roads_data = fetch_roads_data()
    G = create_graph_from_roads(roads_data)
    print("Hii")

    # Add coordinates as node attributes for all nodes in the graph
    for node in G.nodes:
        G.nodes[node]['coord'] = node

    print("start:", datetime.now().strftime("%M:%S"))
    # Calculate the route
    route = find_route((start_geo.longitude, start_geo.latitude), (end_geo.longitude, end_geo.latitude), G)
    if not route:
        return "No route found."
    print("end:", datetime.now().strftime("%M:%S"))

    # Create a map centered at the start of the route
    route_map = folium.Map(location=[route[0][1], route[0][0]], zoom_start=14)

    # Add markers for the start and end points
    folium.Marker([route[0][1], route[0][0]], popup='Start', icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker([route[-1][1], route[-1][0]], popup='End', icon=folium.Icon(color='red')).add_to(route_map)

    # Add lines for the route
    folium.PolyLine([(point[1], point[0]) for point in route], color='blue').add_to(route_map)

    # Save map to an HTML file
    route_map.save('route_map.html')
    return html.Iframe(srcDoc=open('route_map.html', 'r').read(), style={'width': '100%', 'height': '600px'})


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
