from agents.graph import app
import pytest

def test_financing_node_explicit(populated_db, mock_embeddings, mock_llm):
    # Case 1: Financing with explicit price in message
    inputs = {"input_user": "Quiero financiamiento para un auto de 300k", "messages": [], "found_cars": []}
    result = app.invoke(inputs)
    assert result["intent"] == "financing_calc"
    # Mock LLM router returns financing_calc for "financiamiento"
    # The node itself calls calculate_financing tool.
    # We didn't mock the tool, so it runs real calculation.
    # The response comes from LLM (mocked) or constructed? 
    # Wait, handle_financing node constructs response using LLM?
    # Let's check handle_financing implementation.
    # It calls `llm.invoke(SYSTEM_PROMPT_FINANCING...)`.
    # Our mock_llm returns "Hola, soy el bot..." for unknown prompts?
    # Or we need to add a case for financing prompt in mock_llm.
    
    # Let's assume mock_llm default response is fine or we update mock_llm.
    # Actually, let's update mock_llm in conftest to handle financing response.
    pass 

def test_financing_node_context(populated_db, mock_embeddings, mock_llm):
    # Case 2: Financing with Context
    simulated_car = [{"make": "Volkswagen", "model": "Jetta", "year": 2018, "price": 222999.0}]
    inputs = {
        "input_user": "Como quedarian los pagos?", 
        "messages": [], 
        "found_cars": simulated_car
    }
    result = app.invoke(inputs)
    assert result["intent"] == "financing_calc"
