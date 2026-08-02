import json
from pathlib import Path
from typing import List, Dict, Any

def load_sessions(sessions_dir: str = "/app/data/sessions") -> List[Dict[str, Any]]:
    """Reads all JSON files from the sessions directory."""
    directory = Path(sessions_dir)
    sessions_data = []

    if not directory.exists():
        return sessions_data

    for file_path in directory.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                # Extract session ID from the filename (e.g., session_user_01.json -> user_01)
                session_id = file_path.stem.replace("session_", "")
                sessions_data.append({
                    "session_id": session_id,
                    "history": history
                })
            except json.JSONDecodeError:
                continue
                
    return sessions_data

def get_quantitative_metrics(history: List[Dict]) -> Dict[str, Any]:
    """Calculates detailed quantitative metrics from the chat history."""
    human_msgs = [m for m in history if m.get("type") == "human"]
    ai_msgs = [m for m in history if m.get("type") == "ai"]

    # LangChain stores the message content inside msg["data"]["content"] or msg["content"]
    def extract_text(msg):
        return msg.get("data", {}).get("content", msg.get("content", ""))

    human_words = sum(len(extract_text(m).split()) for m in human_msgs)
    ai_words = sum(len(extract_text(m).split()) for m in ai_msgs)
    total_words = human_words + ai_words

    return {
        "turnos_usuario": len(human_msgs),
        "turnos_ai": len(ai_msgs),
        "total_mensajes": len(history),
        "palabras_usuario_total": human_words,
        "palabras_ai_total": ai_words,
        "palabras_totales": total_words,
        "promedio_palabras_por_mensaje_usuario": round(human_words / len(human_msgs), 1) if human_msgs else 0,
        "promedio_palabras_por_mensaje_ai": round(ai_words / len(ai_msgs), 1) if ai_msgs else 0
    }