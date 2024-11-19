from fastapi import APIRouter

from .auth import auth_router


routes: list[APIRouter] = [
    auth_router,
]


__all__ = ["routes"]
