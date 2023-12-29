# Import necessary libraries
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import numpy as np
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


# Sample GeoJSON data for Bremen (replace this with actual GeoJSON data)
bremen_geojson = {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {"name": "Bremen City Center"},
      "geometry": {
        "type": "Point",
        "coordinates": [8.80776, 53.07516]
      }
    },
    {
      "type": "Feature",
      "properties": {"name": "University of Bremen"},
      "geometry": {
        "type": "Point",
        "coordinates": [8.84858, 53.10645]
      }
    },
    {
      "type": "Feature",
      "properties": {"name": "Bremen Airport"},
      "geometry": {
        "type": "Point",
        "coordinates": [8.78667, 53.0475]
      }
    }
  ]
}


# Updated Air quality data for the map
air_quality_data = pd.DataFrame({
    'id': ["Bremen City Center", "University of Bremen", "Bremen Airport"],
    'air_quality': [50, 75, 100]  # Example air quality values for each location
})


# Sample DataFrame for air quality data visualization
df = pd.DataFrame({
    "Date": pd.date_range("2023-01-01", periods=100),
    "Air Quality Index": abs(np.random.randn(100) * 15 + 100),
    "Location": np.random.choice(["City Center", "Suburbs", "Industrial Area"], 100)
})

# Create a Dash application
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app using Bootstrap components
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Map", href="/map")),
            dbc.NavItem(dbc.NavLink("Data Visualization", href="/data-viz")),
        ],
        brand="Air Quality Dashboard",
        brand_href="#",
        color="primary",
        dark=True,
    ),
    html.Div(id='page-content')
])

# Layout for Map page
map_layout = html.Div([
    html.H1("Bremen Air Quality Map"),
    dcc.Graph(id='bremen-map', figure={})
])

# Layout for Data Visualization page
data_viz_layout = html.Div([
    html.H1("Urban Air Quality Monitoring Dashboard"),
    dcc.Graph(id='air-quality-graph'),
    dcc.Dropdown(
        id='location-dropdown',
        options=[{'label': i, 'value': i} for i in df['Location'].unique()],
        value='City Center'
    ),
    html.H2("Air Quality Data Table"),
    dash_table.DataTable(
        id='data-table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
    )
])


# Update page layout based on URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/map':
        return map_layout
    elif pathname == '/data-viz':
        return data_viz_layout
    else:
        return "404 Page Not Found"

bicycle_icon_url = "https://upload.wikimedia.org/wikipedia/commons/3/34/Map_icons_by_Scott_de_Jonge_-_bicycle-store.svg"

# Callback for updating the map
# Callback for updating the map to display points with air quality data
# Callback for updating the map to display points with air quality data
@app.callback(
    Output('bremen-map', 'figure'),
    [Input('bremen-map', 'value')]
)
def update_map(selected_value):
    # Extract latitude, longitude, and names from GeoJSON
    latitudes = [feature['geometry']['coordinates'][1] for feature in bremen_geojson['features']]
    longitudes = [feature['geometry']['coordinates'][0] for feature in bremen_geojson['features']]
    names = [feature['properties']['name'] for feature in bremen_geojson['features']]
    
    # Create a DataFrame for the map with air quality data
    map_data = pd.DataFrame({
        'lat': latitudes,
        'lon': longitudes,
        'name': names,
        'air_quality': air_quality_data['air_quality']
    })

    # Generate random locations for bicycles around Bremen
    np.random.seed(42)  # Seed for reproducibility
    bicycle_lats = np.random.uniform(53.045, 53.095, 20)  # Random latitudes
    bicycle_lons = np.random.uniform(8.775, 8.845, 20)  # Random longitudes

    # Initialize a figure with Mapbox
    fig = go.Figure()

    # Add air quality data to the map
    air_quality_trace = go.Scattermapbox(
        lat=map_data['lat'],
        lon=map_data['lon'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=map_data['air_quality'],
            sizeref=2.*max(map_data['air_quality'])/(40.**2),
            sizemode='area',
            color=map_data['air_quality'],
            colorscale='thermal',
            showscale=True,
            opacity=0.6
        ),
        text=map_data['name']
    )
    fig.add_trace(air_quality_trace)

    # Add bicycles to the map with custom symbols
    bicycle_trace = go.Scattermapbox(
        lat=bicycle_lats,
        lon=bicycle_lons,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=100,  # Size of the bicycle markers
            color='rgb(235, 0, 100)',  # Color of the bicycle markers
            symbol=bicycle_icon_url # Mapbox symbol for bicycle
        ),
        name="bicycle"
    )
    fig.add_trace(bicycle_trace)

    # Set the layout for the map
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=12,
            center={"lat": 53.0793, "lon": 8.8017}
        ),
        height=600,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    return fig





# Callback for updating the data visualization graph
@app.callback(
    Output('air-quality-graph', 'figure'),
    [Input('location-dropdown', 'value')]
)
def update_graph(selected_location):
    filtered_df = df[df.Location == selected_location]
    fig = px.line(
        filtered_df,
        x="Date",
        y="Air Quality Index",
        title="Air Quality Over Time"
    )
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
