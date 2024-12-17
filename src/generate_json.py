import json
import csv
from urllib.request import urlopen

# Import the geopy library for Haversine calculations
from geopy.distance import geodesic

# Fetch the airport coordinates data only once
url = "https://raw.githubusercontent.com/cowtool-llc/ac-sqd/refs/heads/main/src/main/resources/airports.csv"
response = urlopen(url)
reader = csv.reader(response.read().decode('utf-8').splitlines())
next(reader)  # Skip the header row

airport_coordinates = {}
for row in reader:
    try:
        airport_coordinates[row[0]] = (float(row[2]), float(row[3]))
    except (IndexError, ValueError):
        pass  # Handle potential errors in the CSV data


def get_airport_coordinates(airport_code):
    """
    Retrieves airport coordinates from the pre-fetched data.
    """
    return airport_coordinates.get(airport_code)


def generate_json(nodes_file, distances_file, output_file):
    """
    Generates a JSON object with nodes and edges based on the input files.

    Args:
      nodes_file: Path to the nodes.csv.json file.
      distances_file: Path to the aeroplan_distances.csv.json file.
      output_file: Path to the output JSON file.
    """

    with open(nodes_file, 'r') as f:
        nodes_data = json.load(f)

    with open(distances_file, 'r') as f:
        distances_data = json.load(f)

    edges = []
    for node in nodes_data:
        if node['TYPE'] == 'DESTINATION':
            distance = 0
            source = "geopy"
            for dist in distances_data:
                if (dist['origin'] == 'YUL' or dist['destination'] == 'YUL') and \
                        (dist['destination'] == node['ID'] or dist['origin'] == node['ID']):
                    distance = int(dist.get('distance') or dist.get('old_distance') or 0)
                    source = "file"
                    break

            if distance == 0:
                yul_coords = get_airport_coordinates("YUL")
                dest_coords = get_airport_coordinates(node['ID'])
                if yul_coords and dest_coords:
                    # Use geopy to calculate the distance
                    distance = int(geodesic(yul_coords, dest_coords).km)

            edges.append({
                'source': 'YUL',
                'target': node['ID'],
                'distance': distance,
                'distance_source': source
            })

    output_data = {
        'nodes': nodes_data,
        'edges': edges
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

generate_json('nodes.csv.json', '../../ref/aeroplan_distances.csv.json', 'nodes_edges_distances.json')