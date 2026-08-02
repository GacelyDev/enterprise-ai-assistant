import os
import logging
import importlib
from pathlib import Path
from src.database.vector_db import VectorDBClient
from langchain_ollama import ChatOllama
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_prompts(version: str):
    """
    Factory method to dynamically load prompt templates based on version.
    Falls back to 'v1' if the specified version module is not found.
    """
    module_name = f"src.prompts.rag_prompts_{version}"
    try:
        prompt_module = importlib.import_module(module_name)
        logging.info(f"Successfully loaded prompts version: {version}")
        return prompt_module.CONTEXTUALIZE_Q_SYSTEM_PROMPT, prompt_module.QA_SYSTEM_PROMPT
    except ModuleNotFoundError:
        logging.warning(f"Prompt module '{module_name}' not found. Falling back to 'v1'.")
        fallback_module = importlib.import_module("src.prompts.rag_prompts_v1")
        return fallback_module.CONTEXTUALIZE_Q_SYSTEM_PROMPT, fallback_module.QA_SYSTEM_PROMPT

class LimitedChatMessageHistory(FileChatMessageHistory):
    """
    File history extension that limits the context sent to the LLM
    to the last N messages, meeting the technical test requirement.
    """
    def __init__(self, file_path: str, max_messages: int):
        super().__init__(file_path=file_path)
        self.max_messages = max_messages

    @property
    def messages(self):
        # Retrieve messages from disk and return only the last 'max_messages'
        all_messages = super().messages
        return all_messages[-self.max_messages:] if self.max_messages > 0 else all_messages

def get_session_history(session_id: str) -> FileChatMessageHistory:
    """
    Factory pattern: creates or retrieves the persistent history while limiting the messages.
    """
    max_history_messages = int(os.getenv("MAX_HISTORY_MESSAGES", 6)) # 6 messages = 3 conversational turns
    sessions_dir = Path("/app/data/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = sessions_dir / f"session_{session_id}.json"
    return LimitedChatMessageHistory(str(file_path), max_history_messages)

def create_conversational_rag_chain():
    max_history_messages = int(os.getenv("MAX_HISTORY_MESSAGES", 6)) 
    prompt_version = os.getenv("PROMPT_VERSION", "v1")
    
    # Dynamically load the configured prompts
    contextualize_prompt, qa_prompt = load_prompts(prompt_version)
    
    # Connect to ChromaDB and Model
    host = os.getenv("CHROMA_HOST", "vector_db")
    db_client = VectorDBClient(host=host)
    retriever = db_client.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama_server:11434")
    llm = ChatOllama(model="phi3", base_url=ollama_url, temperature=0.2)
    
    # Use the dynamically loaded prompt to contextualize the question
    contextualize_q_prompt_template = ChatPromptTemplate.from_messages([
        ("system", contextualize_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt_template
    )
    
    # Use the dynamically loaded main RAG prompt
    qa_prompt_template = ChatPromptTemplate.from_messages([
        ("system", qa_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt_template)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # Wrap with history management
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    
    return conversational_rag_chain, max_history_messages, prompt_version