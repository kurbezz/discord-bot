from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter


async def get_client() -> Client:
    return await Client.connect(
        "temporal:7233",
        namespace="default",
        data_converter=pydantic_data_converter
    )
