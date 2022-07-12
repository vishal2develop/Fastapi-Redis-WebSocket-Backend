from email import message
from time import sleep
from typing import List
import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
r = redis.Redis(host='localhost', port=6379, db=0)
print(r)
connections = r.lrange('active_connections',0,-1)
while len(connections)<=0:
    r.pop('active_connections')
    

res = r.rpush("active_connections", "")
connections = r.lrange('active_connections',0,-1)
print(len(connections))



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        r.rpush("active_connections", websocket)
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        r.lrem("active_connections",1,websocket)
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        connections = r.lrange('active_connections',0,-1)
        for connection in connections:
            await connection.send_text(message)
        # for connection in self.active_connections:
        #     await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return "Welcome Home"

@app.get("/assign/{client_id}")
async def get(client_id:int):
    print('Inside assign')
    # bus logic
    sleep(10)
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    data='Assigned to '+str(client_id)
    print('data: ',data)
    message = {"time":current_time,"user":client_id,"message":data}
    await manager.broadcast(json.dumps(message))
    return "Assigned Successfully"

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    print('Accepting')
    await manager.connect(websocket)
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    try:
        while True:
            data = await websocket.receive_text()
            print('Data: ',data)
            
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            message = {"time":current_time,"user":client_id,"message":data}
            print('message: ',message)
            await manager.broadcast(json.dumps(message))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"time":current_time,"user":client_id,"message":"Offline"}
        print('message3:',message)
        await manager.broadcast(json.dumps(message))