from datetime import datetime

from pydantic import BaseModel


class State(BaseModel):
    title: str
    category: str

    last_live_at: datetime
