"""transactions extension client."""

import logging
import asyncio
import json
from datetime import datetime
import redis
from redis.commands.json.path import Path


import attr
from stac_pydantic.shared import DATETIME_RFC339

from stac_fastapi.nodb.config import Tile38Settings
from stac_fastapi.nodb.serializers import CollectionSerializer, ItemSerializer
from stac_fastapi.nodb.session import Session
from stac_fastapi.extensions.third_party.bulk_transactions import (
    BaseBulkTransactionsClient,
    Items,
)
from stac_fastapi.types import stac as stac_types
from stac_fastapi.types.core import BaseTransactionsClient
from stac_fastapi.types.errors import ConflictError, ForeignKeyError, NotFoundError
from stac_fastapi.types.links import CollectionLinks

logger = logging.getLogger(__name__)

COLLECTIONS = []

@attr.s
class TransactionsClient(BaseTransactionsClient):
    """Transactions extension specific CRUD operations."""

    session: Session = attr.ib(default=attr.Factory(Session.create_from_env))
    settings = Tile38Settings()
    tile38_client = settings.create_tile_38_client
    redis_client = settings.create_redis_client

    def create_item(self, model: stac_types.Item, **kwargs):
        """Create item."""
        base_url = str(kwargs["request"].base_url)

    ##### implement after bulk sync post request
    #     # If a feature collection is posted
    #     if model["type"] == "FeatureCollection":
    #         bulk_client = BulkTransactionsClient()
    #         processed_items = [
    #             bulk_client._preprocess_item(item, base_url)
    #             for item in model["features"]
    #         ]
    #         return_msg = f"Successfully added {len(processed_items)} items."
    #         bulk_client.bulk_sync(processed_items)

    #         return return_msg

        # If a single item is posted
        self.check_collection_not_exists(model)

        if self.redis_client.json().get(model["id"]):
            raise ConflictError(
                f"Item {model['id']} in collection {model['collection']} already exists"
            )

        data = ItemSerializer.stac_to_db(model, base_url)

        self.redis_client.json().set(model["id"], Path.rootPath(), data)

        ### run async code for tile38 client
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coroutine = self.create_geojson_object(data)
        loop.run_until_complete(coroutine)

        return ItemSerializer.db_to_stac(data, base_url)

    # async example for tile38 client
    async def create_geojson_object(self, item: stac_types.Item):
        ### tile 38 def function
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # coroutine = self.jset_collection(model)
        # response = loop.run_until_complete(coroutine)
        # return str(response)

        await self.tile38_client.set("items", item["id"]).object(item["geometry"]).exec()
        # response = await self.tile38_client.get("items", item["id"]).asObject()

        # return response.object

    def create_collection(self, model: stac_types.Collection, **kwargs):
        """Create collection."""
        base_url = str(kwargs["request"].base_url)
        collection_links = CollectionLinks(
            collection_id=model["id"], base_url=base_url
        ).create_links()
        model["links"] = collection_links

        if self.redis_client.json().get(model["id"]):
            raise ConflictError(f"Collection {model['id']} already exists")

        self.redis_client.json().set(model["id"], Path.rootPath(), model)
        self.redis_client.sadd("collections", model["id"])

        collection = self.redis_client.json().get(model["id"])
        return CollectionSerializer.db_to_stac(collection, base_url)

    def check_collection_not_exists(self, model):
        if not self.redis_client.json().get(model["collection"]):
            raise ForeignKeyError(f"Collection {model['collection']} does not exist")

    def check_collection_not_found(self, collection_id):
        if not self.redis_client.json().get(collection_id):
            raise NotFoundError(f"Collection {collection_id} not found")

    def check_item_not_exists(self, item_id, collection_id):
        if not self.redis_client.json().get(item_id):
            raise NotFoundError(
                f"Item {item_id} in collection {collection_id} doesn't exist"
            )

    def update_item(self, item: stac_types.Item, **kwargs):
        """Update item."""
        base_url = str(kwargs["request"].base_url)
        now = datetime.utcnow().strftime(DATETIME_RFC339)
        item["properties"]["updated"] = str(now)
        self.check_collection_not_exists(item)
        self.check_item_not_exists(item["id"], item["collection"])
        self.delete_item(item["id"], item["collection"])
        self.create_item(item, **kwargs)

        return ItemSerializer.db_to_stac(item, base_url)

    def update_collection(self, model: stac_types.Collection, **kwargs):
        """Update collection."""
        base_url = str(kwargs["request"].base_url)
        self.check_collection_not_found(model["id"])
        self.delete_collection(model["id"])
        self.create_collection(model, **kwargs)

        return CollectionSerializer.db_to_stac(model, base_url)

    def delete_item(self, item_id: str, collection_id: str, **kwargs):
        """Delete item."""
        self.check_item_not_exists(item_id, collection_id)
        self.redis_client.json().delete(item_id, Path.rootPath())

    def delete_collection(self, collection_id: str, **kwargs):
        """Delete collection."""
        self.check_collection_not_found(collection_id)
        self.redis_client.json().delete(collection_id, Path.rootPath())
        self.redis_client.srem("collections", collection_id


# @attr.s
# class BulkTransactionsClient(BaseBulkTransactionsClient):
#     """Postgres bulk transactions."""

#     session: Session = attr.ib(default=attr.Factory(Session.create_from_env))

#     def __attrs_post_init__(self):
#         """Create es engine."""
#         settings = ElasticsearchSettings()
#         self.client = settings.create_client

#     def _preprocess_item(self, model: stac_types.Item, base_url) -> stac_types.Item:
#         """Preprocess items to match data model."""
#         if not self.client.exists(index="stac_collections", id=model["collection"]):
#             raise ForeignKeyError(f"Collection {model['collection']} does not exist")

#         if self.client.exists(index="stac_items", id=model["id"]):
#             raise ConflictError(
#                 f"Item {model['id']} in collection {model['collection']} already exists"
#             )

#         item = ItemSerializer.stac_to_db(model, base_url)
#         return item

#     def bulk_sync(self, processed_items):
#         """Elasticsearch bulk insertion."""
#         actions = [
#             {"_index": "stac_items", "_source": item} for item in processed_items
#         ]
#         helpers.bulk(self.client, actions)

#     def bulk_item_insert(self, items: Items, **kwargs) -> str:
#         """Bulk item insertion using es."""
#         transactions_client = TransactionsClient()
#         transactions_client._create_item_index()
#         try:
#             base_url = str(kwargs["request"].base_url)
#         except Exception:
#             base_url = ""
#         processed_items = [
#             self._preprocess_item(item, base_url) for item in items.items.values()
#         ]
#         return_msg = f"Successfully added {len(processed_items)} items."

#         self.bulk_sync(processed_items)

#         return return_msg
