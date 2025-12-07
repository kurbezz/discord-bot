from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from core.config import config


async def get_client() -> Client:
    return await Client.connect(
        config.TEMPOLAR_URL, namespace="default", data_converter=pydantic_data_converter
    )
