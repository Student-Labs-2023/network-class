import json
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select, or_, and_
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
            try:
                data = await websocket.receive_text()
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    if json_data.get("filter") and json_data.get("search_string"):
                        filter_string = json_data.get("filter")
                        search_string = json_data.get("search_string")
                        search = "%{}%".format(search_string)

                        query = select(Channels).join(UserChannels, Channels.id == UserChannels.channel_id) \
                            .join(User, User.id == UserChannels.user_id) \
                            .join(Role, Role.id == UserChannels.role_id)

                        if search_string:
                            query = query.filter(or_(Channels.title.like(search),
                                                     User.full_name.like(search)))
                        if filter_string == "my":
                            user_email = json_data.get("user_email")
                            query = query.filter(and_(Role.name == "owner", User.email == user_email))
                        elif filter_string == "access":
                            user_email = json_data.get("user_email")
                            query = query.filter(User.email == user_email)
                        else:
                            pass
                        result = await session.execute(query)
                        channels = result.unique().fetchall()
                        response_list = []
                        for channel in channels:
                            query = select(UserChannels).where(
                                and_(UserChannels.channel_id == channel[0].id, UserChannels.role_id == 1))
                            result = await session.execute(query)
                            user_id = result.first()

                            query = select(User).where(User.id == user_id[0].user_id)
                            result = await session.execute(query)
                            user_info = result.first()
                            channel_dict = channel[0].as_dict()
                            channel_dict["owner_fullname"] = user_info[0].full_name
                            channel_dict["owner_email"] = user_info[0].email
                            response_list.append(channel_dict)
                        await websocket.send_json(data=response_list)
            except Exception as error:
                print(error)
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket)
