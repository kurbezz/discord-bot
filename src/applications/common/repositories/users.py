from applications.common.domain.users import CreateUser, User

from .base import BaseRepository


class UserRepository(BaseRepository):
    COLLECTION_NAME = "users"

    @classmethod
    async def get(cls, user_id: str) -> User:
        async with cls.connect() as collection:
            user = await collection.find_one({"_id": user_id})

        return User(
            id=str(user["_id"]),
            oauths=user["oauths"],
            is_admin=user["is_admin"],
        )

    @classmethod
    async def get_or_create_user(cls, new_user: CreateUser) -> User:
        filter_data = {}

        for provider, data in new_user.oauths.items():
            filter_data[f"oauths.{provider}.id"] = data.id

        async with cls.connect() as collection:
            await collection.update_one(
                filter_data,
                {
                    "$setOnInsert": {
                        **new_user.model_dump(),
                    }
                },
                upsert=True,
            )

            user = await collection.find_one(filter_data)

        return User(
            id=str(user["_id"]),
            oauths=user["oauths"],
            is_admin=user["is_admin"],
        )
