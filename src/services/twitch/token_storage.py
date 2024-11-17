from asyncio import Lock
import json

import aiofiles

from core.config import config
from core.mongo import mongo_manager


class TokenStorage:
    COLLECTION_NAME = "secrets"
    OBJECT_ID = "twitch_tokens"

    lock = Lock()

    @staticmethod
    async def save(acceess_token: str, refresh_token: str):
        data = {"access_token": acceess_token, "refresh_token": refresh_token}

        async with TokenStorage.lock:
            async with aiofiles.open(config.SECRETS_FILE_PATH, "w") as f:
                await f.write(json.dumps(data))

        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[TokenStorage.COLLECTION_NAME]

            await collection.update_one(
                {"_id": TokenStorage.OBJECT_ID},
                {"$set": data},
                upsert=True
            )

    @staticmethod
    async def get() -> tuple[str, str]:
        async with mongo_manager.connect() as client:
            db = client.get_default_database()
            collection = db[TokenStorage.COLLECTION_NAME]

            data = await collection.find_one({"_id": TokenStorage.OBJECT_ID})
            if data is not None:
                return data["access_token"], data["refresh_token"]

        async with TokenStorage.lock:
            async with aiofiles.open(config.SECRETS_FILE_PATH, "r") as f:
                data_str = await f.read()

        data = json.loads(data_str)

        await TokenStorage.save(data["access_token"], data["refresh_token"])

        return data["access_token"], data["refresh_token"]
