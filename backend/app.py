import asyncio
import json
import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.central_controller.gc_core import gc
from backend.config import PORT, HOST, SIMULATION_INTERVAL_SEC

# Import the AI Agent
try:
    from backend.agent import run_agent_on_simulator_metrics, run_agent_cycle, load_memory
    AI_AGENT_AVAILABLE = True
except Exception as e:
    print(f"AI Agent import error: {e}")
    AI_AGENT_AVAILABLE = False

app = FastAPI()

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history for the dashboard
history_logs = []

class AnomalyRequest(BaseModel):
    type: str

class ModeRequest(BaseModel):
    mode: str

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/mode")
async def get_mode():
    """Get current system mode"""
    return {
        "mode": gc.get_mode(),
        "available_modes": ["real_time", "historical_csv"]
    }

@app.post("/api/mode")
async def set_mode(request: ModeRequest):
    """Set system mode (real_time or historical_csv)"""
    result = gc.set_mode(request.mode)
    return result

@app.get("/api/policies")
async def get_policies():
    """Get learned policies from agent memory"""
    return {"policies": gc.get_learned_policies()}

@app.post("/api/policies/clear")
async def clear_policies():
    """Clear learned policies"""
    return gc.clear_memory()

@app.get("/api/history")
async def get_history():
    return history_logs[-50:]

@app.post("/api/inject")
async def inject_anomaly(request: AnomalyRequest):
    # Trigger the anomaly in the simulation
    result = gc.inject_anomaly(request.type)
    return {"status": "success", "injected": request.type, "details": result}

# AI Agent Endpoints
@app.get("/api/agent/status")
async def agent_status():
    """Check if AI agent is available"""
    return {
        "available": AI_AGENT_AVAILABLE,
        "memory": load_memory() if AI_AGENT_AVAILABLE else []
    }

@app.post("/api/agent/run")
async def run_agent():
    """Run the AI agent cycle"""
    if not AI_AGENT_AVAILABLE:
        return {"error": "AI Agent not available"}
    
    try:
        result = run_agent_cycle(max_anomalies=3)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/agent/memory")
async def get_agent_memory():
    """Get agent memory/history"""
    if not AI_AGENT_AVAILABLE:
        return {"error": "AI Agent not available"}
    return {"memory": load_memory()}

# WebSocket for real-time telemetry
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Just keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to run the simulation loop
async def simulation_loop():
    while True:
        try:
            # Run a cycle of the global controller (includes AI analysis)
            result = gc.run_cycle()
            
            # Store the report in history
            history_logs.append(result["report"])
            if len(history_logs) > 100:
                history_logs.pop(0)
                
            # Broadcast the result to all connected clients
            await manager.broadcast(json.dumps(result))
            
        except Exception as e:
            print(f"Simulation Error: {e}")
            
        await asyncio.sleep(SIMULATION_INTERVAL_SEC)

@app.on_event("startup")
async def startup_event():
    # Start the simulation loop in the background
    asyncio.create_task(simulation_loop())

# Serve static files from the frontend build directory
# This assumes the frontend is built into /dist
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
