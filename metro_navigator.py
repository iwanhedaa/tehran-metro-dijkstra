import json
import math
import heapq

# first Graph Modeling of Tehran Metro 

# Earth's radius in kilometers for Haversine formula
EARTH_RADIUS_KM = 6371

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the haversine (great-circle) distance in kilometers between two points
    on Earth given their latitude and longitude in degrees.
    """
    # Converting degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS_KM * c
    return distance

def build_metro_graph(stations_data, train_speed_kmph=40, line_change_penalty_minutes=4):
    """
    Builds a graph of the Tehran Metro system.
    Each node: a metro station (English name)
    Each edge: a path between two adjacent stations
    Edge weight: travel time in minutes (including line change penalty)
    """
    graph = {}
    station_details = {} # To store station details like coordinates and lines

    # Adding nodes (stations) to the graph
    for station_name_en, data in stations_data.items():
        graph[station_name_en] = {}
        station_details[station_name_en] = {
            'latitude': float(data['latitude']) if 'latitude' in data else None,
            'longitude': float(data['longitude']) if 'longitude' in data else None,
            'lines': data.get('lines', [])
        }

    # Adding edges (paths) to the graph
    for station_name_en, data in stations_data.items():
        if station_details[station_name_en]['latitude'] is None or station_details[station_name_en]['longitude'] is None:
            continue # Cannot calculate distance if coordinates are missing

        for relation_name_en in data.get('relations', []):
            if relation_name_en in stations_data:
                # Calculating distance between two stations
                lat1 = station_details[station_name_en]['latitude']
                lon1 = station_details[station_name_en]['longitude']
                lat2 = station_details[relation_name_en]['latitude']
                lon2 = station_details[relation_name_en]['longitude']

                if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                    continue # Skippingi if coordinates of either station are incomplete

                distance_km = haversine_distance(lat1, lon1, lat2, lon2)
                travel_time_minutes = (distance_km / train_speed_kmph) * 60

                # Checking for line change and apply penalty
                lines_station1 = set(station_details[station_name_en]['lines'])
                lines_station2 = set(station_details[relation_name_en]['lines'])

                # If there are no common lines a line change penalty is applied.
                # This assumes 'relations' only link adjacent stations. -in the assignment required-
                if not (lines_station1.intersection(lines_station2)):
                    travel_time_minutes += line_change_penalty_minutes

                # Adding edge in both directions (metro lines are typically bidirectional)
                graph[station_name_en][relation_name_en] = travel_time_minutes
                graph[relation_name_en][station_name_en] = travel_time_minutes
            
    return graph, station_details

# implementing Dijkstra's Algorithm 

def dijkstra(graph, start_node, end_node, disabled_stations):
    """
    Executeing Dijkstra's algorithm to find the shortest time path.
    :param graph: Dictionary representation of the graph.
    :param start_node: English name of the starting station.
    :param end_node: English name of the destination station.
    :param disabled_stations: List of English names of disabled stations.
    :return: (shortest_time, path) or (None, None) if no path is found.
    """
    distances = {node: float('inf') for node in graph}
    distances[start_node] = 0
    
    # To reconstruct the path
    previous_nodes = {node: None for node in graph}

    # Priority queue (time, node)
    priority_queue = [(0, start_node)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        # to Skip if current node is disabled or already processed with a shorter distance
        if current_node in disabled_stations:
            continue
        
        if current_distance > distances[current_node]:
            continue

        # If destination is reached, reconstruct the path
        if current_node == end_node:
            path = []
            while current_node is not None:
                path.insert(0, current_node)
                current_node = previous_nodes[current_node]
            return distances[end_node], path

        for neighbor, weight in graph[current_node].items():
            if neighbor in disabled_stations:
                continue

            distance = current_distance + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))

    return None, None # No path found

# Main Application 

def main():
    # Loading the station data from the JSON file in the same directory as metro_navigator.py
    try:
        with open('stations.json', 'r', encoding='utf-8') as f:
            stations_data = json.load(f)
        print("Station data loaded successfully.")
    except FileNotFoundError:
        print("Error: 'stations.json' not found. Please ensure the file is in the correct path.")
        return
    except json.JSONDecodeError:
        print("Error: 'stations.json' is not a valid JSON file.")
        return

    # the metro graph
    metro_graph, station_details = build_metro_graph(stations_data)
    print("Metro graph built successfully.")

    # Getting a list of all available station names (English)
    available_stations_en = sorted(list(station_details.keys()))

    print("\nAvailable Stations (English Names):")
    for i, name in enumerate(available_stations_en):
        print(f"{i+1}. {name}")

    while True:
        try:
            start_en = input("\nEnter the starting station name (English): ").strip()
            if start_en not in available_stations_en:
                print("Invalid starting station. Please choose from the list above.")
                continue

            end_en = input("Enter the destination station name (English): ").strip()
            if end_en not in available_stations_en:
                print("Invalid destination station. Please choose from the list above.")
                continue

            disabled_input = input("Enter disabled station names, separated by commas (leave blank if none): ").strip()
            disabled_en_names = [s.strip() for s in disabled_input.split(',') if s.strip()]
            
            # to validate disabled station names
            invalid_disabled_stations = [name for name in disabled_en_names if name not in available_stations_en]
            if invalid_disabled_stations:
                print(f"Warning: Invalid disabled stations found and ignored: {', '.join(invalid_disabled_stations)}")
                disabled_en_names = [name for name in disabled_en_names if name in available_stations_en] # Filter out invalid ones


            if start_en in disabled_en_names:
                print("Starting station is disabled. Please choose another station.")
                continue
            if end_en in disabled_en_names:
                print("Destination station is disabled. Please choose another station.")
                continue
            
            # Executing the Dijkstra's algorithm
            shortest_time, path_en = dijkstra(metro_graph, start_en, end_en, disabled_en_names)

            #  Report 
            if shortest_time is not None:
                print("\n--- Suggested Route ---")
                print(f"Selected Route: {' → '.join(path_en)}")
                print(f"Total Time: {shortest_time:.2f} minutes")
            else:
                print("\nNo path found.")

        except Exception as e:
            print(f"An error occurred: {e}")

        again = input("\nDo you want to find another route? (yes/no): ").strip().lower()
        if again != 'yes':
            break

if __name__ == "__main__":
    main()
