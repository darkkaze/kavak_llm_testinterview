from agents.graph import app
import pytest

def test_agent_general_greeting(populated_db, mock_embeddings, mock_llm):
    inputs = {"input_user": "Hola, buenas tardes", "messages": []}
    result = app.invoke(inputs)
    assert result["intent"] == "general"
    assert "Hola" in result["messages"][-1].content

def test_agent_faq_location(populated_db, mock_embeddings, mock_llm):
    inputs = {"input_user": "Donde estan ubicados en Puebla?", "messages": []}
    result = app.invoke(inputs)
    assert result["intent"] == "faq"
    # Mock returns "Respuesta simulada de FAQ."
    assert "Respuesta simulada" in result["messages"][-1].content

def test_agent_buy_car(populated_db, mock_embeddings, mock_llm):
    inputs = {"input_user": "Busco un Jetta de menos de 250 mil pesos", "messages": []}
    result = app.invoke(inputs)
    assert result["intent"] == "buy"
    # Mock extraction returns Jetta, so Seller tool should run (using populated_db)
    # populated_db has a Jetta at 220k.
    # Mock LLM seller response says "Aquí tienes opciones de Jetta..."
    assert "Jetta" in result["messages"][-1].content

def test_agent_faq_warranty(populated_db, mock_embeddings, mock_llm):
    inputs = {"input_user": "Tienen garantia?", "messages": []}
    result = app.invoke(inputs)
    assert result["intent"] == "faq"
