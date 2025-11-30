from agents.graph import app
import pytest

def test_general_greeting(populated_db, mock_embeddings, mock_llm):
    inputs = {"input_user": "Hola", "messages": []}
    result = app.invoke(inputs)
    assert result["intent"] == "general"
    # Mock LLM returns "Hola, soy el bot..." for general
    assert "Hola" in result["messages"][-1].content

def test_general_off_topic(populated_db, mock_embeddings, mock_llm):
    inputs = {"input_user": "Quien gano el partido de ayer?", "messages": []}
    result = app.invoke(inputs)
    assert result["intent"] == "general"
    # Mock LLM returns "Hola, soy el bot..." which is a fallback.
    # Ideally we'd mock a refusal message if the prompt asks for refusal.
    # But for now, checking intent is enough.
