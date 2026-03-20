from pymongo import MongoClient
from .config import settings


_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client


def get_db():
    return get_client()[settings.mongo_db_name]


def get_collection():
    return get_db()[settings.mongo_collection]
