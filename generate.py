import osmnx as ox
import networkx as nx
import math
import time
import random

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

def calc_fan_nodes(G, start_lat, start_long, base_angle, angle_offset, leg1_distance, leg2_distance):
    point1_lat, point1_long = calc_dest(start_lat, start_long, leg1_distance, base_angle)
    point2_lat, point2_long = calc_dest(start_lat, start_long, leg2_distance, base_angle + angle_offset)

    node1 = ox.distance.nearest_nodes(G, X=point1_long, Y=point1_lat)
    node2 = ox.distance.nearest_nodes(G, X=point2_long, Y=point2_lat)
    return [node1, node2]


def trim_dead_ends(path):
    stack = [path[0]]
    for node in path[1:]:
        if len(stack) >= 2 and stack[-2] == node:
            stack.pop()
        else:
            stack.append(node)
    return stack

def path_edge_set(path):
    return set(frozenset((path[i], path[i + 1])) for i in range(len(path) - 1))

def is_similar(new_edges, existing_edges, threshold=0.9):
    if not new_edges or not existing_edges:
        return False
    overlap = len(new_edges & existing_edges)
    smaller = min(len(new_edges), len(existing_edges))
    return (overlap / smaller) >= threshold

def calc_simple_route(G, nodes):
    total_path = [nodes[0]]
    for i in range(len(nodes) - 1):
        path = ox.shortest_path(G, nodes[i], nodes[i+1], weight="length", cpus=16)
        if not path:
            return None
        total_path += path[1:]
    return total_path

def path_to_coords(G, path):
    coords = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G.get_edge_data(u, v)
        best_key = min(edge_data, key=lambda k: edge_data[k].get('length', float('inf')))
        data = edge_data[best_key]

        if 'geometry' in data:
            seg_coords = [[x, y] for x, y in data['geometry'].coords]
            if (seg_coords[0][0], seg_coords[0][1]) != (G.nodes[u]['x'], G.nodes[u]['y']):
                seg_coords = seg_coords[::-1]
        else:
            seg_coords = [
                [G.nodes[u]['x'], G.nodes[u]['y']],
                [G.nodes[v]['x'], G.nodes[v]['y']],
            ]

        if coords:
            coords.extend(seg_coords[1:])
        else:
            coords.extend(seg_coords)

    return coords

def random_fan_params(target_distance_m):
    base_angle = random.uniform(0, 360)
    angle_offset = random.uniform(50, 90)

    leg_distance = target_distance_m / 3
    leg1_distance = leg_distance * random.uniform(0.8, 1.2)
    leg2_distance = leg_distance * random.uniform(0.8, 1.2)

    return base_angle, angle_offset, leg1_distance, leg2_distance

def generate_routes(G, start_lat, start_long, target_distance_m, tolerance_m=1000, num_candidates=5, max_attempts=15, similarity_threshold=0.9):
    t_start = time.time()
    start = ox.distance.nearest_nodes(G, X=start_long, Y=start_lat)
    candidates = []
    accepted_edge_sets = []

    for _ in range(max_attempts):
        base_angle, angle_offset, leg1_distance, leg2_distance = random_fan_params(target_distance_m)
        fan_nodes = calc_fan_nodes(G, start_lat, start_long, base_angle, angle_offset, leg1_distance, leg2_distance)

        path_nodes = [start] + fan_nodes + [start]
        path = calc_simple_route(G, path_nodes)

        if path:
            path = trim_dead_ends(path)
            new_edges = path_edge_set(path)

            if any(is_similar(new_edges, existing, similarity_threshold) for existing in accepted_edge_sets):
                continue

            total_length = nx.path_weight(G, path, weight="length")
            diff = abs(total_length - target_distance_m)
            if diff <= tolerance_m:
                candidates.append((path, total_length, diff))
                accepted_edge_sets.append(new_edges)

        if len(candidates) >= num_candidates * 2:
            break

    candidates.sort(key=lambda c: c[2])
    print(f"Total generate_routes time: {time.time() - t_start:.2f}s")
    return candidates[:num_candidates]

def generate_routes_stream(G, start_lat, start_long, target_distance_m, tolerance_m=1000, num_candidates=5, max_attempts=15, similarity_threshold=0.9):
    start = ox.distance.nearest_nodes(G, X=start_long, Y=start_lat)
    found = 0
    accepted_edge_sets = []

    for _ in range(max_attempts):
        base_angle, angle_offset, leg1_distance, leg2_distance = random_fan_params(target_distance_m)
        fan_nodes = calc_fan_nodes(G, start_lat, start_long, base_angle, angle_offset, leg1_distance, leg2_distance)

        path_nodes = [start] + fan_nodes + [start]
        path = calc_simple_route(G, path_nodes)

        if path:
            path = trim_dead_ends(path)
            new_edges = path_edge_set(path)

            if any(is_similar(new_edges, existing, similarity_threshold) for existing in accepted_edge_sets):
                continue

            total_length = nx.path_weight(G, path, weight="length")
            diff = abs(total_length - target_distance_m)
            if diff <= tolerance_m:
                found += 1
                accepted_edge_sets.append(new_edges)
                yield {
                    "type": "route",
                    "coordinates": path_to_coords(G, path),
                    "distance_m": total_length,
                    "diff_m": diff,
                }

        if found >= num_candidates * 2:
            break

    yield {"type": "done", "count": found}

if __name__ == "__main__":
    start_lat, start_long = 1.4405417727572356, 103.79203761808662
    distance = 1000 * 10

    G = ox.load_graphml("singapore_filtered.graphml")
    print(f"Loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

    candidates = generate_routes(G, start_lat, start_long, distance)

    for candidate in candidates:
        path = candidate[0]
        lats = [G.nodes[n]['y'] for n in path]
        lons = [G.nodes[n]['x'] for n in path]
        padding = 0.002
        bbox = (
            min(lons) - padding,
            min(lats) - padding,
            max(lons) + padding,
            max(lats) + padding,
        )

        total_length = candidate[1]
        print(f"Loop length: {total_length:.0f} m ({total_length/1000:.2f} km)")
        ox.plot_graph_route(G, path, route_color='red', route_linewidth=3, node_size=0, bbox=bbox)