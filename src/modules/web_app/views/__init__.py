from fastapi import APIRouter

from .auth import auth_router
from .streamer import streamer_router


routes: list[APIRouter] = [
    auth_router,
    streamer_router,
]


__all__ = ["routes"]
