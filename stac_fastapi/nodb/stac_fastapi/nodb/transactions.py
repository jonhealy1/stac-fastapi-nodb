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
    client = settings.create_tile_38_client
    redis_client = settings.create_redis_client

    def create_item(self, model: stac_types.Item, **kwargs):
        """Create item."""
        pass
    #     base_url = str(kwargs["request"].base_url)
    #     self._create_item_index()

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

    #     # If a single item is posted
    #     if not self.client.exists(index="stac_collections", id=model["collection"]):
    #         raise ForeignKeyError(f"Collection {model['collection']} does not exist")

    #     if self.client.exists(index="stac_items", id=model["id"]):
    #         raise ConflictError(
    #             f"Item {model['id']} in collection {model['collection']} already exists"
    #         )

    #     data = ItemSerializer.stac_to_db(model, base_url)

    #     self.client.index(
    #         index="stac_items", doc_type="_doc", id=model["id"], document=data
    #     )
    #     return ItemSerializer.db_to_stac(model, base_url)

    # async example for tile38 client
    async def jset_collection(self, model: stac_types.Collection):
        # await self.client.jset('collections', 1, 'id', 'model["id')
        # return self.client.jget('collections', 1)

        # self.client.set('user', 902).object(model).exec()
        # return await self.client.get('user', 902).asStringObject()

        await self.redis_client.execute_command('SET', 'hello', 'world')

        return await self.redis_client.execute_command('GET', 'hello')

    def create_collection(self, model: stac_types.Collection, **kwargs):
        """Create collection."""
        base_url = str(kwargs["request"].base_url)
        collection_links = CollectionLinks(
            collection_id=model["id"], base_url=base_url
        ).create_links()
        model["links"] = collection_links

        # for collection in COLLECTIONS:
        #     if collection["id"] == model["id"]:
        #         raise ConflictError(f"Collection {model['id']} already exists")
      
        ### tile 38
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # coroutine = self.jset_collection(model)
        # response = loop.run_until_complete(coroutine)
        # return str(response)

        self.redis_client.json().set(model["id"], Path.rootPath(), model)

        collection = self.redis_client.json().get(model["id"])
        return CollectionSerializer.db_to_stac(collection, base_url)

    def update_item(self, model: stac_types.Item, **kwargs):
        """Update item."""
        pass
#         base_url = str(kwargs["request"].base_url)
#         now = datetime.utcnow().strftime(DATETIME_RFC339)
#         model["properties"]["updated"] = str(now)

#         if not self.client.exists(index="stac_collections", id=model["collection"]):
#             raise ForeignKeyError(f"Collection {model['collection']} does not exist")
#         if not self.client.exists(index="stac_items", id=model["id"]):
#             raise NotFoundError(
#                 f"Item {model['id']} in collection {model['collection']} doesn't exist"
#             )
#         self.delete_item(model["id"], model["collection"])
#         self.create_item(model, **kwargs)
#         # self.client.update(index="stac_items",doc_type='_doc',id=model["id"],
#         #         body=model)
#         return ItemSerializer.db_to_stac(model, base_url)

    def update_collection(self, model: stac_types.Collection, **kwargs):
        """Update collection."""
        pass
#         base_url = str(kwargs["request"].base_url)
#         try:
#             _ = self.client.get(index="stac_collections", id=model["id"])
#         except elasticsearch.exceptions.NotFoundError:
#             raise NotFoundError(f"Collection {model['id']} not found")
#         self.delete_collection(model["id"])
#         self.create_collection(model, **kwargs)

#         return CollectionSerializer.db_to_stac(model, base_url)

    def delete_item(self, item_id: str, collection_id: str, **kwargs):
        """Delete item."""
        pass
#         try:
#             _ = self.client.get(index="stac_items", id=item_id)
#         except elasticsearch.exceptions.NotFoundError:
#             raise NotFoundError(f"Item {item_id} not found")
#         self.client.delete(index="stac_items", doc_type="_doc", id=item_id)

    def delete_collection(self, collection_id: str, **kwargs):
        """Delete collection."""
        pass
#         try:
#             _ = self.client.get(index="stac_collections", id=collection_id)
#         except elasticsearch.exceptions.NotFoundError:
#             raise NotFoundError(f"Collection {collection_id} not found")
#         self.client.delete(index="stac_collections", doc_type="_doc", id=collection_id)


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
