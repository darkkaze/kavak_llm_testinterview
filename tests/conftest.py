import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.connection import Base, get_db
from main import app
from fastapi.testclient import TestClient
import settings

from sqlalchemy.pool import StaticPool

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return engine

@pytest.fixture(scope="session")
def test_session_local(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session(test_engine, test_session_local):
    """
    Creates a fresh database for each test function.
    """
    # Import models to ensure they are registered with Base
    from db.models import Car, ChatHistory
    from db.rag import KnowledgeDoc
    
    # Create tables
    print(f"DEBUG: Creating tables for {Base.metadata.tables.keys()}")
    Base.metadata.create_all(bind=test_engine)
    
    session = test_session_local()
    yield session
    
    # Teardown
    session.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with overridden DB dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def populated_db(db_session):
    """
    Loads RAG documents and Car Catalog into the test database.
    """
    from db.models import Car
    from db.rag import KnowledgeDoc
    import json
    
    # 1. Insert Sample Cars
    cars = [
        Car(id=1, make="Volkswagen", model="Jetta", year=2018, price=220000, version="Trendline", km=50000),
        Car(id=2, make="Chevrolet", model="Aveo", year=2019, price=180000, version="LS", km=30000),
        Car(id=3, make="Nissan", model="Versa", year=2020, price=210000, version="Drive", km=20000),
    ]
    db_session.add_all(cars)
    
    # 2. Insert Sample RAG Docs
    fake_embedding = [1.0, 0.0, 0.0] 
    
    doc = KnowledgeDoc(
        category="locations",
        content="Kavak Puebla esta en Explanada.",
        embedding=json.dumps(fake_embedding)
    )
    db_session.add(doc)
    
    db_session.commit()
    return db_session

@pytest.fixture(autouse=True)
def patch_db_connection(monkeypatch, test_session_local):
    """
    Patches SessionLocal in all modules that import it.
    """
    # Patch the source
    monkeypatch.setattr("db.connection.SessionLocal", test_session_local)
    
    # Patch consumers (because they did 'from db.connection import SessionLocal')
    monkeypatch.setattr("agents.tools.catalog.SessionLocal", test_session_local, raising=False)
    monkeypatch.setattr("db.rag.SessionLocal", test_session_local, raising=False)
    monkeypatch.setattr("main.SessionLocal", test_session_local, raising=False)

@pytest.fixture
def mock_embeddings(monkeypatch):
    """Mocks OpenAIEmbeddings to avoid API calls."""
    from unittest.mock import MagicMock
    mock_class = MagicMock()
    
    def side_effect(text):
        if "puebla" in text.lower():
            return [1.0, 0.0, 0.0] 
        else:
            return [0.0, 1.0, 0.0]
            
    mock_instance = mock_class.return_value
    mock_instance.embed_query.side_effect = side_effect
    
    # Patch the source class in langchain_openai
    monkeypatch.setattr("langchain_openai.OpenAIEmbeddings", mock_class)
    # Patch the imported name in db.rag (in case it was already imported)
    monkeypatch.setattr("db.rag.OpenAIEmbeddings", mock_class, raising=False)
    return mock_instance

@pytest.fixture
def mock_llm(monkeypatch):
    """Mocks ChatOpenAI to avoid API calls."""
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessage
    
    mock_class = MagicMock()
    mock_instance = mock_class.return_value
    
    def side_effect(messages):
        # Inspect the last message to decide response
        last_msg = messages[-1].content.lower()
        first_msg = messages[0].content.lower()
        
        # Router Logic (detect_intention)
        if "clasificar la intención" in first_msg:
            if "donde" in last_msg or "garantia" in last_msg or "vender" in last_msg:
                return AIMessage(content="faq")
            elif "busco" in last_msg or "comprar" in last_msg:
                return AIMessage(content="buy")
            elif "financiamiento" in last_msg or "pagos" in last_msg:
                return AIMessage(content="financing_calc")
            else:
                return AIMessage(content="general")
        
        # Extraction Logic (reason_about_car)
        if "extract car search criteria" in first_msg:
            return AIMessage(content='```json\n{"make": "Volkswagen", "model": "Jetta", "max_price": 250000}\n```')
            
        # FAQ Logic (handle_faq)
        # SYSTEM_PROMPT_FAQ_ES contains "Eres un asistente útil de Kavak"
        if "asistente útil de kavak" in first_msg:
            return AIMessage(content="Respuesta simulada de FAQ.")
            
        # Seller Logic (respond_with_options)
        # SYSTEM_PROMPT_SELLER_ES contains "Eres un Agente de Ventas de Kavak"
        if "agente de ventas de kavak" in first_msg:
            return AIMessage(content="Aquí tienes opciones de Jetta...")
            
        # General Logic (handle_general)
        # SYSTEM_PROMPT_GENERAL_ES contains "Eres un asistente amable de Kavak"
        if "asistente amable de kavak" in first_msg:
            return AIMessage(content="Hola, soy el bot de Kavak.")
            
        # Fallback
        return AIMessage(content="Hola, soy el bot de Kavak (Fallback).")

    mock_instance.invoke.side_effect = side_effect
    
    # Patch langchain_openai.ChatOpenAI globally (for new instances)
    monkeypatch.setattr("langchain_openai.ChatOpenAI", mock_class)
    
    # Patch the global 'llm' instance in agents.nodes (since it's already instantiated)
    monkeypatch.setattr("agents.nodes.llm", mock_instance)
    
    return mock_instance
