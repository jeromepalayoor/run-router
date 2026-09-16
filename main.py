from fastapi import FastAPI
from pydantic import BaseModel
from generate import *

G = ox.load_graphml("singapore_filtered.graphml")
print(f"Loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

app = FastAPI()

class RouteRequest(BaseModel):
    lat: float
    lon: float
    distance_km: float

@app.post("/routes")
def get_routes(req: RouteRequest):
    target_distance_m = req.distance_km * 1000
    routes = generate_routes(G, req.lat, req.lon, target_distance_m)

    return {
        "routes": [
            {
                "coordinates": path_to_coords(G, path),
                "distance_m": total_length,
            }
            for path, total_length, diff in routes
        ]
    }