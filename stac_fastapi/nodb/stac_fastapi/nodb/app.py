"""FastAPI application."""
from stac_fastapi.api.app import StacApi
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.nodb.config import Tile38Settings
from stac_fastapi.nodb.core import CoreCrudClient
from stac_fastapi.nodb.session import Session
from stac_fastapi.nodb.transactions import (
    # BulkTransactionsClient,
    TransactionsClient,
)
from stac_fastapi.extensions.core import (
    ContextExtension,
    FieldsExtension,
    SortExtension,
    TokenPaginationExtension,
    TransactionExtension,
)
# from stac_fastapi.extensions.third_party import BulkTransactionExtension

settings = Tile38Settings()
session = Session.create_from_settings(settings)

extensions = [
    TransactionExtension(client=TransactionsClient(session=session), settings=settings),
    # BulkTransactionExtension(client=BulkTransactionsClient(session=session)),
    FieldsExtension(),
    SortExtension(),
    TokenPaginationExtension(),
    ContextExtension(),
]

post_request_model = create_post_request_model(extensions)

api = StacApi(
    settings=settings,
    extensions=extensions,
    client=CoreCrudClient(session=session, post_request_model=post_request_model),
    search_get_request_model=create_get_request_model(extensions),
    search_post_request_model=post_request_model,
)
app = api.app


def run():
    """Run app from command line using uvicorn if available."""
    try:
        import uvicorn

        uvicorn.run(
            "stac_fastapi.nodb.app:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level="info",
            reload=settings.reload,
        )
    except ImportError:
        raise RuntimeError("Uvicorn must be installed in order to use command")


if __name__ == "__main__":
    run()


def create_handler(app):
    """Create a handler to use with AWS Lambda if mangum available."""
    try:
        from mangum import Mangum

        return Mangum(app)
    except ImportError:
        return None


handler = create_handler(app)
