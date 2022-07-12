from datetime import datetime
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from api.manager.connection_manager import ConnectionManager

# from ..main import get_app
# from fastapi import Request

# app = Request.app

manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    try:
        while True:
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
            message = {"time":current_time,"clientId":client_id,"message":data}
            await manager.broadcast(json.dumps(message))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"time":current_time,"clientId":client_id,"message":"Offline"}
        # await manager.broadcast(f"Client #{client_id} left the chat")
        await manager.broadcast(json.dumps(message))
