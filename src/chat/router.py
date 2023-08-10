import json
from typing import List, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select, or_, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models import Channels, Chat

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel_id: int):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, channel_id: int):
        self.active_connections[channel_id].remove(websocket)

    async def broadcast(self, room_id: int, data: dict):
        for connection in self.active_connections[room_id]:
            await connection.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/{channel_id}")
async def websocket_endpoint(websocket: WebSocket, channel_id: int, session: AsyncSession = Depends(get_async_session)):
    await manager.connect(websocket, channel_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)
                user_email = json_data.get("email")
                user_id = json_data.get("id")
                user_fullname = json_data.get("fullname")
                user_message = json_data.get("message")

                query_chat = insert(Chat).values(user_id=int(user_id), channel_id=channel_id, value=user_message)
                await session.execute(query_chat)
                await session.commit()

                response_data = {
                    "user_fullname": user_fullname,
                    "message": user_message,
                }
                if user_message is not None and user_fullname is not None:
                    await manager.broadcast(channel_id, response_data)
            except json.JSONDecodeError:
                print("Произошла ошибка при кодировании JSON for chat")
            await manager.broadcast(channel_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)
