from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.models import Channels, UserChannels, User, Role

router = APIRouter(
    prefix="/channel_search",
    tags=["ChannelSearch"]
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/")
async def websocket_endpoint_search(websocket: WebSocket, session: AsyncSession = Depends(get_async_session)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            search = "%{}%".format(data)

            query = select(Channels).join(UserChannels, Channels.id == UserChannels.channel_id) \
                .join(User, User.id == UserChannels.user_id) \
                .join(Role, Role.id == UserChannels.role_id) \
                .filter(or_(Channels.title.like(search),
                            User.full_name.like(search))) \
                .filter(Role.name == "owner")
            result = await session.execute(query)
            channels = result.fetchall()
            await websocket.send_json(data=[channel[0].as_dict() for channel in channels])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
