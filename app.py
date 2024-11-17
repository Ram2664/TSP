import os
from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import folium
from geopy.distance import geodesic
import random
import networkx as nx
from itertools import combinations
from flask_cors import CORS


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST"], "supports_credentials": True}})

# Provided area coordinates
AREA_COORDINATES = {
    "Marathahalli": (12.9568, 77.7019),
    "Sarjapur Road": (12.9057, 77.6825),
    "Electronic City": (12.8440, 77.6630),
    "HSR Layout": (12.9116, 77.6412),
    "Koramangala": (12.9352, 77.6245),
    "Whitefield": (12.9698, 77.7500),
    "BTM Layout": (12.9166, 77.6101),
    "Bellandur": (12.9250, 77.6778),
    "Tin Factory": (13.0121, 77.6606),
    "Banashankari": (12.9255, 77.5466)
}

# Distance matrix calculation
def calculate_distance_matrix():
    locations = list(AREA_COORDINATES.keys())
    num_locations = len(locations)
    distance_matrix = np.zeros((num_locations, num_locations))
    for i, loc1 in enumerate(locations):
        for j, loc2 in enumerate(locations):
            if i != j:
                distance_matrix[i][j] = geodesic(AREA_COORDINATES[loc1], AREA_COORDINATES[loc2]).km
    return distance_matrix, locations

distance_matrix, location_names = calculate_distance_matrix()

# Simulated Annealing Algorithm
def simulated_annealing_tsp(distance_matrix, start=0, initial_temp=100, cooling_rate=0.995, num_iterations=1000):
    def total_distance(tour):
        return sum(distance_matrix[tour[i]][tour[i + 1]] for i in range(len(tour) - 1)) + distance_matrix[tour[-1]][tour[0]]

    num_locations = len(distance_matrix)
    current_tour = list(range(num_locations))
    current_tour.remove(start)
    random.shuffle(current_tour)
    current_tour = [start] + current_tour + [start]
    best_tour, best_distance = list(current_tour), total_distance(current_tour)
    temperature = initial_temp

    for _ in range(num_iterations):
        i, j = sorted(random.sample(range(1, num_locations), 2))
        new_tour = current_tour[:]
        new_tour[i:j] = reversed(new_tour[i:j])
        new_distance = total_distance(new_tour)
        if new_distance < best_distance or random.random() < np.exp((best_distance - new_distance) / temperature):
            current_tour, best_distance = new_tour, new_distance
            best_tour = list(new_tour)
        temperature *= cooling_rate

    return best_tour, best_distance

# Ant Colony Optimization Algorithm
def ant_colony_tsp(distance_matrix, num_ants=100, num_iterations=1000, alpha=1, beta=5, evaporation_rate=0.5):
    num_locations = len(distance_matrix)
    pheromone_matrix = np.ones((num_locations, num_locations))
    best_tour, best_distance = None, float('inf')

    def calculate_total_distance(tour):
        return sum(distance_matrix[tour[i]][tour[i + 1]] for i in range(len(tour) - 1)) + distance_matrix[tour[-1]][tour[0]]

    for _ in range(num_iterations):
        all_tours, all_distances = [], []
        for _ in range(num_ants):
            tour = [random.randint(0, num_locations - 1)]
            unvisited = set(range(num_locations)) - set(tour)
            while unvisited:
                current_city = tour[-1]
                probabilities = [pheromone_matrix[current_city][j] ** alpha * (1 / distance_matrix[current_city][j]) ** beta for j in unvisited]
                probabilities /= sum(probabilities)
                next_city = list(unvisited)[np.random.choice(len(unvisited), p=probabilities)]
                tour.append(next_city)
                unvisited.remove(next_city)
            tour.append(tour[0])
            distance = calculate_total_distance(tour)
            all_tours.append(tour)
            all_distances.append(distance)
            if distance < best_distance:
                best_tour, best_distance = tour, distance
        pheromone_matrix *= (1 - evaporation_rate)
        for tour, dist in zip(all_tours, all_distances):
            for i in range(len(tour) - 1):
                pheromone_matrix[tour[i]][tour[i + 1]] += 1 / dist

    return best_tour, best_distance

# Christofides Algorithm
def christofides_tsp(distance_matrix):
    num_locations = len(distance_matrix)
    G = nx.Graph()
    for i, j in combinations(range(num_locations), 2):
        G.add_edge(i, j, weight=distance_matrix[i][j])

    mst = nx.minimum_spanning_tree(G)
    odd_degree_nodes = [node for node, degree in mst.degree() if degree % 2 == 1]
    matching = nx.algorithms.matching.min_weight_matching(G.subgraph(odd_degree_nodes), maxcardinality=True)
    multi_graph = nx.MultiGraph(mst)
    multi_graph.add_edges_from(matching)
    eulerian_circuit = list(nx.eulerian_circuit(multi_graph))

    tour, visited = [], set()
    for u, v in eulerian_circuit:
        if u not in visited:
            tour.append(u)
            visited.add(u)
    tour.append(tour[0])
    total_distance = sum(distance_matrix[tour[i]][tour[i + 1]] for i in range(len(tour) - 1))

    return tour, total_distance

# Admin Dashboard Route
@app.route('/send-consignment', methods=['GET', 'POST'])
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            selected_locations = request.form.getlist('locations')
            location_indexes = [list(AREA_COORDINATES.keys()).index(loc) for loc in selected_locations]

            sa_tour, _ = simulated_annealing_tsp(distance_matrix, start=location_indexes[0])
            aco_tour, _ = ant_colony_tsp(distance_matrix)
            christofides_tour, _ = christofides_tsp(distance_matrix)

            maps = {}
            for name, tour, color in [
                ("Simulated_Annealing", sa_tour, 'blue'),
                ("Ant_Colony", aco_tour, 'green'),
                ("Christofides", christofides_tour, 'red')
            ]:
                start_coord = AREA_COORDINATES[selected_locations[0]]
                map_ = folium.Map(location=start_coord, zoom_start=12)
                tour_coords = [AREA_COORDINATES[list(AREA_COORDINATES.keys())[i]] for i in tour]
                folium.PolyLine(tour_coords, color=color, weight=2.5, opacity=1).add_to(map_)
                if not os.path.exists('static'):
                    os.makedirs('static')
                map_file = f'static/{name}_route_map.html'
                map_.save(map_file)
                maps[name] = map_file

            return render_template('result.html', maps=maps)

        return render_template('admin.html', locations=AREA_COORDINATES.keys())
    return redirect(url_for('login'))

# Route to handle map selection and send to agent
@app.route('/select_map', methods=['POST'])
def select_map():
    if 'role' in session and session['role'] == 'admin':
        selected_map = request.form.get('selected_map')
        session['selected_map'] = selected_map
        return redirect(url_for('agent_dashboard'))
    return redirect(url_for('login'))

# Agent Dashboard to display selected map
@app.route('/agent_dashboard')
def agent_dashboard():
    selected_map = session.get('selected_map', None)
    return render_template('agent.html', map_file=selected_map)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
