from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.mongo import mongo_manager
from core.redis import redis_manager
from core.broker import broker

from .auth.authx import auth
from .views import routes


def get_app() -> FastAPI:
    app = FastAPI()

    app.mount(
        "/",
        StaticFiles(
            directory="modules/web_app/frontend",
            html=True
        ),
        name="frontend"
    )

    auth.handle_errors(app)

    for route in routes:
        app.include_router(route)

    @app.on_event("startup")
    async def startup_event():
        await mongo_manager.init()
        await redis_manager.init()

        if not broker.is_worker_process:
            await broker.startup()

    return app


app = get_app()
