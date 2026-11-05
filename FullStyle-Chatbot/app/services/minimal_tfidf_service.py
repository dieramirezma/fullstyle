import logging
import os
import pickle
from typing import List, Optional

logger = logging.getLogger(__name__)


class MinimalTFIDFService:
    """
    Servicio TF-IDF ultra-ligero que solo carga el vectorizador entrenado desde Colab
    para transformar consultas, sin cargar el corpus completo en memoria.
    """

    def __init__(self, model_path: str = "models/tfidf_vectorizer_only.pkl"):
        """
        Args:
            model_path: Ruta al archivo con solo el vectorizador TF-IDF (no el corpus)
        """
        self.model_path = model_path
        self.vectorizer = None
        self.embedding_dimensions = None
        self._load_vectorizer()

    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Genera embedding TF-IDF para una consulta usando el vectorizador pre-entrenado desde Colab.
        Usa exactamente la misma lógica que funcionó en Colab.

        Args:
            query: Texto de la consulta

        Returns:
            Lista con el embedding o None si hay error
        """
        if not self.vectorizer:
            logger.error("Vectorizador TF-IDF no está cargado")
            return None

        if not query or not query.strip():
            logger.warning("Query vacía proporcionada")
            return None

        try:
            # transform() devuelve una matriz sparse, toarray() la convierte a numpy array
            # [0] extrae el primer elemento (el embedding), tolist() lo convierte a lista Python
            query_embedding = self.vectorizer.transform([query]).toarray()[0].tolist()

            # Validar dimensiones
            if len(query_embedding) != self.embedding_dimensions:
                logger.error(
                    f"Dimensión incorrecta: esperada {self.embedding_dimensions}, obtenida {len(query_embedding)}"
                )
                return None

            logger.debug(
                f"Embedding generado: dimensión {len(query_embedding)}, valores no-cero: {sum(1 for x in query_embedding if x != 0)}"
            )
            return query_embedding

        except Exception as e:
            logger.error(
                f"Error generando embedding para consulta '{query[:10]}...': {e}"
            )
            return None

    def _load_vectorizer(self):
        """Carga solo el vectorizador TF-IDF desde disco y valida su configuración."""
        if not os.path.exists(self.model_path):
            logger.warning(f"No se encontró vectorizador en {self.model_path}")
            return

        try:
            with open(self.model_path, "rb") as f:
                self.vectorizer = pickle.load(f)

            # Validar que el vectorizador esté entrenado
            if (
                not hasattr(self.vectorizer, "vocabulary_")
                or self.vectorizer.vocabulary_ is None
            ):
                logger.error("El vectorizador no está entrenado (no tiene vocabulario)")
                self.vectorizer = None
                return

            test_embedding = self.vectorizer.transform(["test"]).toarray()[0]
            self.embedding_dimensions = len(test_embedding)

        except Exception as e:
            logger.error(f"Error cargando vectorizador TF-IDF: {e}")
            self.vectorizer = None

    def is_ready(self) -> bool:
        """Verifica si el vectorizador está listo para usar."""
        return self.vectorizer is not None and self.embedding_dimensions is not None

    def get_embedding_dimensions(self) -> Optional[int]:
        """Retorna las dimensiones del embedding."""
        return self.embedding_dimensions


minimal_tfidf_service = MinimalTFIDFService()
