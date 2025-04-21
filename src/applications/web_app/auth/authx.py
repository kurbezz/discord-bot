from authx import AuthX, AuthXConfig

from core.config import config


config = AuthXConfig(
     JWT_ALGORITHM = "HS256",
     JWT_SECRET_KEY = config.SECRET_KEY,
     JWT_TOKEN_LOCATION = ["headers"],
)

auth = AuthX(config=config)
