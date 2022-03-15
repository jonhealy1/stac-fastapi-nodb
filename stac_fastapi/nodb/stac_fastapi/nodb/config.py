"""API configuration."""
import os
from typing import Set

from stac_fastapi.types.config import ApiSettings

from pyle38 import Tile38

DOMAIN = os.getenv("38_HOST")
PORT = os.getenv("38_PORT")


class Tile38Settings(ApiSettings):
    """API settings."""

    # Fields which are defined by STAC but not included in the database model
    forbidden_fields: Set[str] = {"type"}

    # Fields which are item properties but indexed as distinct fields in the database model
    indexed_fields: Set[str] = {"datetime"}

    @property
    def create_client(self):
        """Create tile38 client."""
        # try:
        client = Tile38(url=f"redis://{str(DOMAIN)}:{str(PORT)}", follower_url="redis://{str(DOMAIN)}:{str(PORT)}")
        return client
