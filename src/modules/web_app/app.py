from fastapi import FastAPI

from .views import routes


async def get_app() -> FastAPI:
    app = FastAPI()

    for route in routes:
        app.include_router(route)

    return app
