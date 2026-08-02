import logging
import os
import uuid
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class VectorDBClient:
    """
    Singleton pattern for the network (HTTP) connection to the ChromaDB container,
    Embeddings model, and LangChain integration wrapper with Cosine Similarity.
    """
    _instance = None

    def __new__(cls, host="vector_db", port=8000):
        if cls._instance is None:
            logging.info(f"Connecting to ChromaDB at {host}:{port} and loading Embeddings model...")
            cls._instance = super(VectorDBClient, cls).__new__(cls)
            
            # 1. Load the open-source Embeddings model
            model_name = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
            cls._instance.embeddings = HuggingFaceEmbeddings(
                model_name=model_name
            )
            
            # 2. HTTP connection to the ChromaDB container
            cls._instance.client = chromadb.HttpClient(
                host=host, 
                port=port,
                settings=Settings(allow_reset=True)
            )
            
            # 3. Initialize LangChain's Chroma wrapper 
            # with explicit cosine similarity configuration
            cls._instance.vector_store = Chroma(
                client=cls._instance.client,
                collection_name="banco_knowledge",
                embedding_function=cls._instance.embeddings,
                collection_metadata={"hnsw:space": "cosine"}
            )
            
        return cls._instance

    def add_texts(self, texts: list[str], metadatas: list[dict]):
        """Vectorizes and stores texts while generating unique IDs using LangChain."""
        if not texts:
            logging.info("No texts to index.")
            return

        ids = [str(uuid.uuid4()) for _ in texts]
        
        # LangChain's wrapper handles vectorization and insertion automatically
        self.vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        logging.info(f"Indexed {len(texts)} chunks into ChromaDB.")

    def search(self, query: str, n_results: int = 3):
        """Searches for the most relevant chunks using LangChain similarity search."""
        return self.vector_store.similarity_search(query, k=n_results)

    def as_retriever(self, **kwargs):
        """
        Exposes LangChain's retriever directly so it can be plugged 
        into chains (like create_retrieval_chain) seamlessly.
        """
        return self.vector_store.as_retriever(**kwargs)