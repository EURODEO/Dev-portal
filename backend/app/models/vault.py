""""
Vault models
"""

from pydantic import BaseModel
from app.config import settings

config = settings()

if config.apisix.key_name != "auth_key":
    raise ValueError(
        "Configuration mismatch: Key name used in APISix does not match the one used in Vault"
    )


class VaultUser(BaseModel):
    """
    Representing an Vault user.

    Attributes:
        auth_key (str): The key name used for api key.
        date (str): The date user was created.
    """

    auth_key: str
    date: str
