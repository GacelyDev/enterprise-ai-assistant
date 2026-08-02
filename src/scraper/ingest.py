import json
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.database.vector_db import VectorDBClient

def ingest_data_to_vectordb(json_path: str, chunk_size: int = 1024, chunk_overlap: int = 128, host: str = "localhost", port: int = 8000):
    # 1. Instantiate the singleton client (will connect to localhost:8000 by default)
    db_client = VectorDBClient(host=host, port=port)
    
    # 2. Load the JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logging.error(f"Error: File not found: {json_path}")
        return

    # 3. Configure the text splitter
    # 1024 characters with a 128 overlap is a common industry standard
    # to avoid cutting ideas in half.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    texts_to_insert = []
    metadatas_to_insert = []

    # 4. Process and split the text from each scraped page
    logging.info("Starting data chunking...")
    for item in data:
        url = item.get("url", "desconocida")
        content = item.get("content", "")
        
        if content:
            chunks = text_splitter.split_text(content)
            for chunk in chunks:
                texts_to_insert.append(chunk)
                # Save the source URL as metadata (useful for LLM source attribution)
                metadatas_to_insert.append({"source": url})

    # 5. Enviar a ChromaDB
    logging.info(f"Generated {len(texts_to_insert)} chunks. Starting vectorization...")
    db_client.add_texts(texts_to_insert, metadatas_to_insert)

    