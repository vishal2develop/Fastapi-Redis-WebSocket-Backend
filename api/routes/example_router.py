from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import APIRouter
# from ..main import get_app
from ..controllers import example_controller

router = APIRouter()

# @router.get('/{client_id}')
# async def get(client_id: int):
#     return {'data': 'example1 data', 'client': client_id}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    return example_controller.websocket_endpoint(websocket, client_id)

