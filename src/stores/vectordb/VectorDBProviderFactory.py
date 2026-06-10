from .VectorDBEnums import VectorDBEnums
from .providers import QdrantDBProvider

class VectorDBProviderFactory:

    def __init__(self, config: dict):
        self.config = config

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            return QdrantDBProvider(
                db_url=self.config.VECTOR_DB_URL,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD
            )
        
        return None