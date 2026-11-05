import logging
from typing import Any, Dict, List, Optional

from pymongo import MongoClient

from app.core.config import settings


class MongoKnowledgeRepository:
    def __init__(self, mongo_uri: str, database_name: str, collection_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        logging.info(
            f"Repositorio de Conocimiento Conectado a MongoDB: db='{database_name}', collection='{collection_name}'"
        )
        # El índice vectorial se asume que ya existe en MongoDB Atlas, creado como se describió anteriormente.

    def find_similar_entries(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        custom_filter: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, Any]]:
        """
        Encuentra los documentos (incluyendo text_chunks y metadatos)
        más similares al query_embedding proporcionado, usando búsqueda vectorial en MongoDB Atlas.

        Args:
            query_embedding: El vector de embedding de la consulta del usuario.
            top_k: El número de documentos similares a retornar.
            custom_filter: Un filtro opcional de MongoDB para aplicar antes de la búsqueda vectorial.
                           Ejemplo: {"metadata.category": "specific_topic"}
        """
        if not query_embedding:
            logging.info("Error: El embedding de la consulta no puede estar vacío.")
            return []

        pipeline = [
            {
                "$vectorSearch": {
                    "index": settings.MONGO_VECTOR_SEARCH_INDEX,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 15,
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text_chunk": 1,
                    "source": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        if custom_filter:
            # Añadir la etapa $match ANTES de $vectorSearch si es un pre-filtro general
            # O, si el índice vectorial soporta filtros en el propio $vectorSearch (más eficiente):
            pipeline[0]["$vectorSearch"]["filter"] = custom_filter

        try:
            results = list(self.collection.aggregate(pipeline))
            return results
        except Exception as e:
            logging.info(f"Error durante la búsqueda vectorial en MongoDB: {e}")
            return []

    def get_all_knowledge_entries(
        self, limit: int = 0, projection: Optional[Dict[str, int]] = None
    ) -> list[Dict[str, Any]]:
        """
        Recupera documentos de la base de conocimiento.
        Permite limitar el número de resultados y especificar una proyección.

        Args:
            limit: Número máximo de documentos a retornar (0 para todos).
            projection: Diccionario para especificar qué campos incluir/excluir.
                        Ejemplo: {"text_chunk": 1, "source": 1, "_id": 0}
        """
        query_filter = {}

        # Definir una proyección por defecto si no se proporciona una
        if projection is None:
            projection = {"text_chunk": 1, "source": 1, "metadata": 1, "_id": 0}

        cursor = self.collection.find(query_filter, projection)

        if limit > 0:
            cursor = cursor.limit(limit)

        # Convertir ObjectId a str para que sea serializable si es necesario al retornar _id
        # pero como lo estamos excluyendo por defecto en la proyección, no sería estrictamente necesario aquí
        # a menos que la proyección personalizada lo incluya.
        return list(cursor)

    def close_connection(self):
        """Cierra la conexión a MongoDB."""
        if self.client:
            self.client.close()
            logging.info("Conexión del Repositorio de Conocimiento a MongoDB cerrada.")
