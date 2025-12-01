from typing import List, Dict
from datetime import datetime, timedelta
from db.connection import SessionLocal
from db.models import ChatHistory

def save_chat_message(session_id: str, role: str, content: str):
    """Saves a message to the database."""
    db = SessionLocal()
    try:
        db.add(ChatHistory(
            session_id=session_id,
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        ))
        db.commit()
    finally:
        db.close()

def get_chat_history(session_id: str, limit: int = 10, hours: int = 24) -> List[Dict]:
    """Retrieves recent chat history from the last N hours."""
    db = SessionLocal()
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history_objs = db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id,
            ChatHistory.timestamp >= cutoff_time.isoformat()
        ).order_by(ChatHistory.id.desc()).limit(limit).all()
        # Reverse to chronological order
        return [{"role": h.role, "content": h.content} for h in reversed(history_objs)]
    finally:
        db.close()

def delete_chat_history(session_id: str):
    """Deletes all chat history for a session."""
    db = SessionLocal()
    try:
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
    finally:
        db.close()
