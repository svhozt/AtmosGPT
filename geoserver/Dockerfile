# Use the latest GeoServer image as the base
FROM docker.osgeo.org/geoserver:2.25.x

# Copy the "bremen" workspace folder into the GeoServer data directory inside the container
# Adjust the '/path/to/geoserver_data/workspaces' to the correct path if different
COPY GeoServer/ /opt/geoserver_data/


# The base image likely includes an ENTRYPOINT or CMD to start GeoServer
# No need to change if you don't have a custom startup script
