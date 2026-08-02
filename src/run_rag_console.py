import os
import logging
from src.rag.engine import create_conversational_rag_chain

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # --- Console Interface (Spanish) ---
    print("\n==================================================")
    print("--- Asistente RAG Conversacional con Memoria ---")
    print("==================================================\n")
    
    try:
        conversational_rag_chain, max_history_messages, prompt_version = create_conversational_rag_chain()
    except Exception as e:
        logging.error(f"Error initializing the RAG pipeline: {e}")
        return
    
    session_id = input("🔑 Ingresa un ID para tu sesión de chat (ej: usuario_01): ").strip()
    if not session_id:
        session_id = "default_session"
        
    print(f"\n✅ Sesión activa: [{session_id}]")
    print(f"🧠 Memoria: Recordando últimos {max_history_messages} mensajes.")
    print(f"📝 Prompts: Usando versión '{prompt_version}'")
    print("Escribe tu pregunta (o escribe 'exit'/'salir' para terminar).\n")
    
    while True:
        try:
            user_input = input(f"\n👤 [{session_id}] Pregunta: ")
            if user_input.lower() in ["exit", "quit", "salir"]:
                print("Saliendo del asistente...")
                break
            
            if not user_input.strip():
                continue
                
            print("🤖 Procesando con memoria conversacional...")
            
            # Invoke the chain passing the config with the session_id
            response = conversational_rag_chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            
            print("\n💡 Respuesta:")
            print(response["answer"])
            
            print("\n📚 Fuentes consultadas:")
            docs = response.get("context", [])
            if docs:
                # Avoid duplicate sources for a cleaner output
                sources = list(set([doc.metadata.get('source', 'Desconocida') for doc in docs]))
                for source in sources:
                    print(f"  - {source}")
            else:
                print("  - Ninguna fuente relevante encontrada.")
                
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
        except Exception as e:
            # Logs are kept in English for standard monitoring
            logging.error(f"Error processing the query: {e}")

if __name__ == "__main__":
    main()