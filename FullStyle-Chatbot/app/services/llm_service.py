import logging
from typing import Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.domain.prompts.templates import AGENT_PROMPT_BASE
from app.domain.tools import all_tools
from app.repositories.knowledge_repository import MongoKnowledgeRepository
from app.services.minimal_tfidf_service import minimal_tfidf_service

# Get a logger specific to this module
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        logger.info("LLMService __init__ - Configurando servicio LLM...")
        # Initialize the Gemini LLM for Langchain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.5,
            timeout=5,
            max_retries=0,
        )
        self.AGENT_PROMPT = AGENT_PROMPT_BASE
        self.tools = all_tools
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.AGENT_PROMPT)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )

        self.tfidf_service = minimal_tfidf_service
        if self.tfidf_service.is_ready():
            logger.info("Vectorizador TF-IDF de Colab cargado exitosamente.")
        else:
            logger.warning(
                "Vectorizador TF-IDF no encontrado. Coloca el archivo 'tfidf_vectorizer_only.pkl' en la carpeta 'models/'."
            )

        try:
            self.knowledge_repo = MongoKnowledgeRepository(
                mongo_uri=settings.MONGO_URI,
                database_name=settings.MONGO_DATABASE_NAME,
                collection_name=settings.MONGO_KB_COLLECTION_NAME,
            )
            logger.info("Repositorio de conocimiento conectado exitosamente.")
        except Exception as e:
            logger.error(f"FALLO CRÍTICO al conectar con MongoKnowledgeRepository: {e}")
            self.knowledge_repo = None

    async def _get_knowledge_context(self, user_input: str, top_k: int = 3) -> str:
        """Generates embedding for user input and retrieves relevant knowledge."""
        retrieved_knowledge_context = ""

        if not self.tfidf_service.is_ready() or not self.knowledge_repo:
            logger.warning(
                "Advertencia RAG: Vectorizador TF-IDF no disponible o repositorio de conocimiento no inicializado. Saltando recuperación."
            )
            return retrieved_knowledge_context

        try:
            query_embedding = self.tfidf_service.get_query_embedding(user_input)
            if query_embedding is None:
                logger.warning("No se pudo generar embedding para la consulta")
                return retrieved_knowledge_context

            similar_docs = self.knowledge_repo.find_similar_entries(
                query_embedding, top_k=top_k
            )

            if similar_docs:
                retrieved_knowledge_context = "\n\nInformación relevante de nuestra base de conocimiento para tu consulta:\n"
                for i, doc in enumerate(similar_docs):
                    text_chunk = doc.get("text_chunk", "Chunk no disponible")
                    score = doc.get("score", 0)
                    retrieved_knowledge_context += (
                        f"- {text_chunk} (similitud: {score:.3f})\n"
                    )
                logger.info(
                    f"RAG: Contexto recuperado con {len(similar_docs)} documentos."
                )
            else:
                logger.info(
                    "RAG: No se encontró información relevante en la base de conocimiento para este input."
                )
        except Exception as e:
            logger.error(f"Error durante la recuperación de conocimiento (RAG): {e}")

        return retrieved_knowledge_context

    async def generate_text_with_agent(
        self, user_input: str, session_id: Optional[str] = "default_session", history=None
    ) -> str:
        """
        Processes user input using the Langchain agent, enriched with RAG.
        Includes basic chat history management.
        """
        logging.info("[LLMService] Procesando entrada para sesión")

        current_chat_history = history or []

        # 1. Retrieve context from Knowledge Base (RAG step)
        knowledge_context = await self._get_knowledge_context(user_input)
        try:
            response = await self.agent_executor.ainvoke(
                {
                    "input": user_input,
                    "chat_history": current_chat_history,
                    "retrieved_knowledge_context": knowledge_context,
                }
            )
            agent_reply = response.get("output", "Lo siento, no pude procesar eso.")

            return agent_reply
        except Exception as e:
            logger.error(
                f"[LLMService] Error invocando al agente para sesión {session_id}: {e}"
            )
            return f"Lo siento, encontré un error procesando tu solicitud: {str(e)}"


llm_service = LLMService()
