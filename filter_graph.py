import osmnx as ox
import networkx as nx

G = ox.load_graphml("singapore.graphml")
print(f"Loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

EXCLUDE_TYPES = {"service", "steps", "bridleway", "bus_stop", "corridor", "track"}

def get_highway(data):
    h = data.get('highway', 'unknown')
    return h[0] if isinstance(h, list) else h

edges_to_remove = [
    (u, v, k) for u, v, k, data in G.edges(keys=True, data=True)
    if get_highway(data) in EXCLUDE_TYPES
]
G.remove_edges_from(edges_to_remove)
print(f"After edge filter: Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

isolated = list(nx.isolates(G))
G.remove_nodes_from(isolated)
print(f"Removed {len(isolated)} isolated nodes")
print(f"After isolated-node removal: Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

before = len(G.nodes)
G = ox.truncate.largest_component(G, strongly=True)
print(f"Removed {before - len(G.nodes)} nodes not in the largest connected component")
print(f"After largest-component filter: Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

if not G.graph.get('simplified', False):
    G = ox.simplification.simplify_graph(G)
    print(f"After simplification: Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
else:
    print("Graph already simplified, skipping")

ox.plot_graph(
    G,
    node_size=0,
    edge_color='red',
    edge_linewidth=0.5,
    show=True,
    close=False,
    figsize=(20, 12),
)

ox.save_graphml(G, "singapore_filtered.graphml")
print("Saved filtered graph to singapore_filtered.graphml")