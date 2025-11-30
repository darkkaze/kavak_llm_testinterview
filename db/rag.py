import json
import numpy as np
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import Column, Integer, String, Text
from db.connection import Base, SessionLocal, engine
import settings

# 1. Define the Knowledge Base Table
class KnowledgeDoc(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True) # e.g., "locations", "financing"
    content = Column(Text)
    embedding = Column(Text) # JSON string of the vector

# Create tables
Base.metadata.create_all(bind=engine)

# 2. RAG Logic
class SemanticRouter:
    def __init__(self):
        self.embeddings_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        self.docs = self._load_docs()

    def _load_docs(self):
        """Loads all docs and their embeddings into memory."""
        db = SessionLocal()
        docs = db.query(KnowledgeDoc).all()
        db.close()
        
        loaded_docs = []
        for doc in docs:
            loaded_docs.append({
                "category": doc.category,
                "content": doc.content,
                "embedding": np.array(json.loads(doc.embedding))
            })
        return loaded_docs

    def get_content_by_category(self, category: str) -> str:
        """Retrieves the content of a specific category document."""
        for doc in self.docs:
            if doc["category"] == category:
                return doc["content"]
        return None
