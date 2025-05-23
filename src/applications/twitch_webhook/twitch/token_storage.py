import logging

from core.mongo import mongo_manager

logger = logging.getLogger(__name__)


class TokenStorage:
    COLLECTION_NAME = "secrets"
    TYPE = "twitch_token"

    @staticmethod
    async def save(user: str, acceess_token: str, refresh_token: str):
        data = {"access_token": acceess_token, "refresh_token": refresh_token}

        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[TokenStorage.COLLECTION_NAME]

            await collection.update_one(
                {"type": TokenStorage.TYPE, "twitch_login": user},
                {"$set": data},
                upsert=True
            )

    @staticmethod
    async def get(user: str) -> tuple[str, str]:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[TokenStorage.COLLECTION_NAME]

            data = await collection.find_one({"type": TokenStorage.TYPE, "twitch_login": user})

            if data is None:
                raise RuntimeError(f"Token for user {user} not found")

            return data["access_token"], data["refresh_token"]
