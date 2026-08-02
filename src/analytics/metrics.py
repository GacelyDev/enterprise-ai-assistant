import os
import json
import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Disable unnecessary logs to keep the console clean
logging.getLogger("httpx").setLevel(logging.WARNING)

def evaluate_session_impact(history: list) -> dict:
    """Uses the LLM to evaluate quality, main topic, and resolution of the session."""
    # Reconstruct the full transcript in plain text
    transcript = ""
    for msg in history:
        role = "Usuario" if msg.get("type") == "human" else "Asistente"
        content = msg.get("data", {}).get("content", msg.get("content", ""))
        transcript += f"{role}: {content}\n"
        
    if not transcript.strip():
        return {"tema_principal": "Vacío", "resuelto": "No", "sentimiento": "Neutral"}

    # Configure LLM forcing a strict JSON response format
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama_server:11434")
    llm = ChatOllama(model="phi3", base_url=ollama_url, temperature=0.0, format="json")

    # Prompt instructing the model to return a strict schema
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un analista de datos evaluando transcripciones de un bot. 
        Analiza la conversación y devuelve ÚNICAMENTE un objeto JSON válido con estas claves:
        - "tema_principal": Un resumen muy corto (máximo 4 palabras) de lo que preguntó el usuario.
        - "resuelto": Escribe solo "Si", "No" o "Parcial" dependiendo de si el bot logró responder.
        - "sentimiento": Escribe solo "Positivo", "Neutral" o "Negativo" reflejando la actitud del usuario.
        """),
        ("human", "Transcripción de la sesión:\n{transcript}")
    ])

    chain = prompt | llm
    
    try:
        response = chain.invoke({"transcript": transcript})
        result = json.loads(response.content)
        return {
            "tema_principal": result.get("tema_principal", "Desconocido"),
            "resuelto": result.get("resuelto", "Desconocido"),
            "sentimiento": result.get("sentimiento", "Desconocido")
        }
    except Exception as e:
        logging.error(f"Error parsing LLM response for impact: {e}")
        return {"tema_principal": "Error", "resuelto": "Error", "sentimiento": "Error"}