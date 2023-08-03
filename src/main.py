from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.channel.router import router as router_channel
from src.channel_search.router import router as router_channel_search

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

