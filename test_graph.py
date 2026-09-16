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

# lat, lon = calc_dest(1.3774, 103.7649, 1000, 90)
# print(f"https://www.google.com/maps?q={lat},{lon}")
# print(f"https://www.google.com/maps?q=1.3774,103.7649")

G = ox.load_graphml("singapore_filtered.graphml")
print(f"Loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

# orig = ox.distance.nearest_nodes(G, X=103.7649, Y=1.3774)
# dest = ox.distance.nearest_nodes(G, X=103.8198, Y=1.3644)

# route = ox.shortest_path(G, orig, dest, weight="length")
# print(f"Route has {len(route)} nodes")

# length_m = nx.path_weight(G, route, weight="length")
# print(f"Route length: {length_m:.0f} m ({length_m/1000:.2f} km)")

start_lat, start_long = 1.4405417727572356, 103.79203761808662
distance = 1000 * 10
start = ox.distance.nearest_nodes(G, X=start_long, Y=start_lat)

candidates = []

TOLERANCE_M = 1000

for attempt in range(20):
    n_dir = 4
    radius_factor = attempt * 0.01 + 0.05
    
    turn_nodes = calc_turn_nodes(G, start_lat, start_long, distance * radius_factor, n_dir=n_dir)
    
    path_nodes = [start] + turn_nodes + [start]
    path = calc_simple_route(G, path_nodes)
    
    if path:
        path = trim_dead_ends(path)
        total_length = nx.path_weight(G, path, weight="length")
        diff = abs(total_length - distance)
        if diff <= TOLERANCE_M:
            candidates.append((path, total_length, diff))
        print(radius_factor, total_length)

print(f"{len(candidates)} candidates within tolerance")

candidates.sort(key=lambda c: c[2])
top_5 = candidates[:5]

for candidate in top_5:
    path = candidate[0]
    # print(path)
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

# node_colors = ['red' if n in nodes else 'gray' for n in G.nodes]
# node_sizes = [30 if n in nodes else 0 for n in G.nodes]
# ox.plot_graph(G, node_color=node_colors, node_size=node_sizes, bbox=bbox)