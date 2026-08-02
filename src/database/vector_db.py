import logging
import os
import uuid
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings

class VectorDBClient:
    """
    Singleton pattern for the network (HTTP) connection to the ChromaDB container
    and single-load Embeddings model.
    """
    _instance = None

    def __new__(cls, host="vector_db", port=8000):
        if cls._instance is None:
            logging.info(f"Connecting to ChromaDB at {host}:{port} and loading Embeddings model...")
            cls._instance = super(VectorDBClient, cls).__new__(cls)
            
            # 1. Load the open-source Embeddings model
            cls._instance.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
            
            # 2. HTTP connection to the ChromaDB container
            cls._instance.client = chromadb.HttpClient(
                host=host, 
                port=port,
                settings=Settings(allow_reset=True)
            )
            
            # 3. Create or connect to the collection
            cls._instance.collection = cls._instance.client.get_or_create_collection(
                name="banco_knowledge",
                metadata={"hnsw:space": "cosine"} # Use cosine similarity
            )
            
        return cls._instance

    def add_texts(self, texts: list[str], metadatas: list[dict]):
        """Vectorizes and stores texts while generating unique IDs."""
        if not texts:
            logging.info("No texts to index.")
            return

        embeddings_list = self.embeddings.embed_documents(texts)
        ids = [str(uuid.uuid4()) for _ in texts]
        
        self.collection.add(
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas,
            ids=ids
        )
        logging.info(f"Indexed {len(texts)} chunks into ChromaDB.")

    def search(self, query: str, n_results: int = 3):
        """Searches for the most relevant chunks."""
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results