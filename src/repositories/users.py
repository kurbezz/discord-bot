from domain.users import CreateUser, User

from .base import BaseRepository


class UserRepository(BaseRepository):
    COLLECTION_NAME = "users"

    @classmethod
    async def get_or_create_user(cls, newUser: CreateUser) -> User:
        filter_data = {}

        for provider, data in newUser.oauths.items():
            filter_data[f"oauths.{provider}.id"] = data.id

        async with cls.connect() as collection:
            await collection.update_one(
                filter_data,
                {
                    "$setOnInsert": {
                        **newUser.model_dump(),
                    }
                },
                upsert=True,
            )

            user = await collection.find_one(filter_data)

        return User(**user)
