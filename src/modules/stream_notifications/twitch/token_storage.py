from core.mongo import mongo_manager


class TokenStorage:
    COLLECTION_NAME = "secrets"
    OBJECT_ID = "twitch_tokens"

    @staticmethod
    async def save(acceess_token: str, refresh_token: str):
        data = {"access_token": acceess_token, "refresh_token": refresh_token}

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

            return data["access_token"], data["refresh_token"]
