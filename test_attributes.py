import osmnx as ox
from collections import Counter

G = ox.load_graphml("singapore.graphml")
print(f"Loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

highway_types = []
for u, v, key, data in G.edges(keys=True, data=True):
    h = data.get('highway', 'unknown')
    if isinstance(h, list):
        h = h[0]
    highway_types.append(h)

counts = Counter(highway_types)
print("\nHighway type counts:")
for htype, count in counts.most_common():
    print(f"  {htype}: {count}")

start_lat, start_long = 1.4405417727572356, 103.79203761808662
buffer_deg = 0.03
bbox = (
    start_long - buffer_deg,
    start_lat - buffer_deg,
    start_long + buffer_deg,
    start_lat + buffer_deg,
)

for htype in counts:
    edge_colors = []
    edge_linewidths = []
    for u, v, key, data in G.edges(keys=True, data=True):
        h = data.get('highway', 'unknown')
        if isinstance(h, list):
            h = h[0]
        if h == htype:
            edge_colors.append('red')
            edge_linewidths.append(2)
        else:
            edge_colors.append('#333333')
            edge_linewidths.append(0.5)

    print(f"\nPlotting: {htype} ({counts[htype]} edges)")
    ox.plot_graph(
        G,
        edge_color=edge_colors,
        edge_linewidth=edge_linewidths,
        node_size=0,
        bbox=bbox,
        show=True,
        close=True,
    )