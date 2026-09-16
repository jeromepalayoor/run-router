import osmnx as ox
import networkx as nx
import math

def calc_dest(lat, long, distance, angle):
    angle = math.radians(angle)
    lat = math.radians(lat)
    long = math.radians(long)
    angular = distance / 6371000

    dest_lat = math.asin(math.sin(lat) * math.cos(angular) +
                         math.cos(lat) * math.sin(angular) * math.cos(angle))
    dest_long = long + math.atan2(math.sin(angle) * math.sin(angular) * math.cos(lat),
                                  math.cos(angular) - math.sin(lat) * math.sin(dest_lat))

    return math.degrees(dest_lat), math.degrees(dest_long)

def calc_turn_nodes(G, start_lat, start_long, distance, n_dir=8):
    node_bearings = []
    seen = set()
    for i in range(n_dir):
        bearing = i * (360 / n_dir)
        node_lat, node_long = calc_dest(start_lat, start_long, distance, bearing)
        node = ox.distance.nearest_nodes(G, X=node_long, Y=node_lat)
        if node not in seen:
            seen.add(node)
            node_bearings.append((bearing, node))
    node_bearings.sort(key=lambda x: x[0])
    return [n for _, n in node_bearings]

def trim_dead_ends(path):
    stack = [path[0]]
    for node in path[1:]:
        if len(stack) >= 2 and stack[-2] == node:
            stack.pop()
        else:
            stack.append(node)
    return stack

def calc_simple_route(G, nodes):
    total_path = [nodes[0]]
    for i in range(len(nodes)-1):
        path = ox.shortest_path(G, nodes[i], nodes[i+1], weight="length", cpus=16)
        if not path:
            return None
        total_path += path[1:]
    return total_path

def generate_routes(G, start_lat, start_long, target_distance_m, tolerance_m=1000, num_candidates=5):
    start = ox.distance.nearest_nodes(G, X=start_long, Y=start_lat)
    candidates = []

    for attempt in range(20):
        n_dir = 4
        radius_factor = attempt * 0.01 + 0.05

        turn_nodes = calc_turn_nodes(G, start_lat, start_long, target_distance_m * radius_factor, n_dir=n_dir)
        path_nodes = [start] + turn_nodes + [start]
        path = calc_simple_route(G, path_nodes)

        if path:
            path = trim_dead_ends(path)
            total_length = nx.path_weight(G, path, weight="length")
            diff = abs(total_length - target_distance_m)
            if diff <= tolerance_m:
                candidates.append((path, total_length, diff))

    candidates.sort(key=lambda c: c[2])
    return candidates[:num_candidates]

def path_to_coords(G, path):
    return [[G.nodes[n]['x'], G.nodes[n]['y']] for n in path]