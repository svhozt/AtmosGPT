import folium
import pandas as pd

# Load the data
data = pd.read_csv('Sampled_Location.csv')

# Create a map centered around the mean latitude and longitude
mean_lat, mean_lon = data['Latitude (°)'].mean(), data['Longitude (°)'].mean()
map_folium = folium.Map(location=[mean_lat, mean_lon], zoom_start=12)

# Adding markers for each point in the dataset
for idx, row in data.iterrows():
    folium.Marker(
        location=[row['Latitude (°)'], row['Longitude (°)']],
        popup=f"Lat: {row['Latitude (°)']}, Lon: {row['Longitude (°)']}"
    ).add_to(map_folium)

# To display the map in a Jupyter notebook, use: map_folium
# To save the map to an HTML file, use:
map_folium.save('map.html')

map_folium
