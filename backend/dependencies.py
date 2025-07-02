from functools import lru_cache

from backend.storage.base import BaseLogStorage
from backend.storage.memory import InMemoryLogStorage
from src.database.models import DatabaseManager

# Use lru_cache to ensure a singleton instance of the storage
# across the application lifetime when using FastAPI's dependency injection.


@lru_cache()
def get_log_storage() -> BaseLogStorage:
    """Dependency function to get the singleton log storage instance."""
    return InMemoryLogStorage()


@lru_cache()
def get_database_manager() -> DatabaseManager:
    """Dependency function to get the singleton database manager instance."""
    return DatabaseManager()
