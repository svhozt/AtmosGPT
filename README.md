
# AtmosGPT

## Overview

AtmosGPT is a comprehensive project dedicated to monitoring and analyzing air quality. By integrating cutting-edge technologies such as PostgreSQL with PostGIS and pgRouting, Neo4j for graph database management, MQTT for IoT data handling, and GeoServer for geospatial data visualization, AtmosGPT offers a robust solution for environmental data assessment and visualization.

## Features

- **Real-Time Air Quality Monitoring:** Collects data continuously from IoT devices to provide up-to-date air quality metrics.
- **Advanced Data Analysis:** Employs PostgreSQL and Neo4j databases for efficient data storage and complex querying capabilities.
- **Geospatial Data Handling:** Uses PostGIS for spatial data analysis and pgRouting for mapping and route planning.
- **Interactive Data Visualization:** Features data visualization capabilities, including map-based representations, through GeoServer.

## Prerequisites

Before starting, ensure you have:
- Docker and Docker Compose installed on your machine.
- Fundamental knowledge of Docker, PostgreSQL, Neo4j, MQTT protocol, and GeoServer.

## Installation

To install AtmosGPT, follow these steps:

1. **Clone the Repository:**
   ```
   git clone https://github.com/svhozt/AtmosGPT.git
   cd AtmosGPT
   ```

2. **Environment Variables Setup:**
   - Copy `.env.sample` to a new file named `.env`.
   - Complete the `.env` file with your specific configuration values.

3. **Build and Launch Docker Containers:**
   ```
   docker-compose up --build
   ```

## Usage

Upon successful setup, you can access the services as follows:

- **PostgreSQL Database:** Available at `localhost:5435` (or the configured port in your `.env` file).
- **Neo4j Database:** Access the web interface at `http://localhost:7474`.
- **GeoServer:** Visit `http://localhost:8080/geoserver` for geospatial data visualization.
- **MQTT Server:** Connect your IoT devices through the configured MQTT server.

## Contributing

To contribute to AtmosGPT, please follow these steps:

1. Fork this repository.
2. Create a new branch: `git checkout -b <branch_name>`.
3. Make your changes and commit them: `git commit -m '<commit_message>'`.
4. Push to the original branch: `git push origin <project_name>/<location>`.
5. Create a pull request.

For more information on creating a pull request, refer to the [GitHub documentation](https://help.github.com/articles/creating-a-pull-request/).


## Contact

For inquiries, reach out at `nasvimukthi23@gmail.com`.

## License

This project is under the [MIT License](<link_to_license>).

---
