import asyncio
import logging
import aioredis
from aioredis.client import PubSub, Redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""
@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket('/ws')
async def ws_voting_endpoint(websocket: WebSocket):
    await websocket.accept()
    await redis_connector(websocket)


async def redis_connector(websocket: WebSocket):
    async def consumer_handler(conn: Redis, ws: WebSocket):
        print('Inside consumer')
        try:
            while True:
                message = await ws.receive_text()
                print('received text',message)
                if message:
                    await conn.publish("chat:c", message)
        except WebSocketDisconnect as exc:
            # TODO this needs handling better
            print('Consumer error',exc.reason)
            logger.error(exc)

    async def producer_handler(pubsub: PubSub, ws: WebSocket):
        print('subscribing')
        await pubsub.subscribe("chat:c")
        # assert isinstance(channel, PubSub)
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                
                # print('subscribed msg',message)
                if message:
                    print('subscribed msg',message)
                    await ws.send_text(message.get('data'))
        except Exception as exc:
            # TODO this needs handling better
            print('Producer error',exc.reason)
            
            logger.error(exc)

    conn = await get_redis_pool()
    print('redis pool',conn)
    pubsub = conn.pubsub()
    print('pubsub',pubsub)

    consumer_task = consumer_handler(conn=conn, ws=websocket)
    producer_task = producer_handler(pubsub=pubsub, ws=websocket)
    done, pending = await asyncio.wait(
        [consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED,
    )
    logger.debug(f"Done task: {done}")
    for task in pending:
        logger.debug(f"Canceling task: {task}")
        task.cancel()


async def get_redis_pool():
    return await aioredis.from_url(f'redis://localhost', encoding="utf-8", decode_responses=True)