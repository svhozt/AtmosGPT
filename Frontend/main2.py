import dash
from dash import html
import dash_bootstrap_components as dbc

# Define the GeoServer WMS URL and Layer Name
geoserver_wms_url = "http://localhost:8080/geoserver"
wms_layer_name = "bremen:highway-bremen"

# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "GeoServer Map Viewer"

# Define the layout of the app
app.layout = html.Div([
    dbc.NavbarSimple(
        brand="GeoServer Map Viewer",
        brand_href="#",
        color="primary",
        dark=True,
    ),
    html.Div([
        html.H1("Bremen Air Quality Map", style={'textAlign': 'center'}),
        html.Iframe(
            srcDoc=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Leaflet WMS Layer</title>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            </head>
            <body>
                <div id="map" style="width: 100%; height: 600px;"></div>
                <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
                <script>
                    var map = L.map('map').setView([53.0793, 8.8017], 12);
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        maxZoom: 20
                    }}).addTo(map);
                    var wmsLayer = L.tileLayer.wms("{geoserver_wms_url}/wms", {{
                        layers: '{wms_layer_name}',
                        format: 'image/png',
                        transparent: true,
                        version: '1.1.1'
                    }}).addTo(map);
                </script>
            </body>
            </html>
            """,

            style={'width': '100%', 'height': '600px', 'border': 'none'}
        )
    ], style={'textAlign': 'center'})
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
