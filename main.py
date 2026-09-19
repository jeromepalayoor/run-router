from fastapi import FastAPI
from pydantic import BaseModel
from generate import *
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import StreamingResponse
from generate import generate_routes_stream

G = ox.load_graphml("singapore_filtered.graphml")
print(f"Loaded. Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RouteRequest(BaseModel):
    lat: float
    lon: float
    distance_km: float
    tolerance_m: float = 1000
    max_attempts: int = 15
    num_candidates: int = 5

@app.post("/routes")
def get_routes(req: RouteRequest):
    target_distance_m = req.distance_km * 1000
    routes = generate_routes(G, req.lat, req.lon, target_distance_m, tolerance_m=10000, num_candidates=10, max_attempts=30)

    return {
        "routes": [
            {
                "coordinates": path_to_coords(G, path),
                "distance_m": total_length,
            }
            for path, total_length, diff in routes
        ]
    }

@app.post("/routes/stream")
def get_routes_stream(req: RouteRequest):
    target_distance_m = req.distance_km * 1000

    def event_generator():
        for item in generate_routes_stream(
            G, req.lat, req.lon, target_distance_m,
            tolerance_m=req.tolerance_m,
            num_candidates=req.num_candidates,
            max_attempts=req.max_attempts,
        ):
            yield json.dumps(item) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")