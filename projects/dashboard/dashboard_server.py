
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI()
STATUS_FILE = "/Users/leo/Desktop/leohermes/status.json"

def get_status():
    if not os.path.exists(STATUS_FILE):
        return {"agents": {"Hermes": "Idle", "CEO": "Idle", "Daidai": "Idle", "Chacha": "Idle"}, "pipeline": "Idle", "progress": 0, "metrics": {"usdt": "0.00", "tools": "0"}}
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

@app.get("/")
async def index():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/status")
async def status():
    return get_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
