import osmnx as ox
ox.settings.overpass_url = "https://overpass.kumi.systems/api/interpreter"
print("Downloading Singapore road networks")
G = ox.graph_from_place("Singapore", network_type="walk")
ox.save_graphml(G, "singapore.graphml")
print(f"Done. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")