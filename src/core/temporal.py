from temporalio.client import Client


async def get_client() -> Client:
    return await Client.connect("temporal:7233", namespace="default")
