from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.channel.router import router as router_channel
from src.channel_search.router import router as router_channel_search
from src.user.router import router as router_user
from src.user_channel.router import router as router_user_channel
from src.chat.router import router as router_chat

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
)

app.include_router(router_channel)
app.include_router(router_channel_search)
app.include_router(router_user)
app.include_router(router_user_channel)
app.include_router(router_chat)
