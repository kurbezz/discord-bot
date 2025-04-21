from fastapi.staticfiles import StaticFiles

from starlette.responses import Response
from starlette.exceptions import HTTPException


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException:
            if path.startswith("/api"):
                raise

            return await super().get_response("index.html", scope)
