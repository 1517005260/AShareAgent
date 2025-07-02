from functools import lru_cache

from .storage.base import BaseLogStorage
from .storage.memory import InMemoryLogStorage

# Use lru_cache to ensure a singleton instance of the storage
# across the application lifetime when using FastAPI's dependency injection.


@lru_cache()
def get_log_storage() -> BaseLogStorage:
    """Dependency function to get the singleton log storage instance."""
    return InMemoryLogStorage()
