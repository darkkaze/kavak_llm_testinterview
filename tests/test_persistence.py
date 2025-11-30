import uuid

def test_persistence(client):
    session_id = str(uuid.uuid4())
    print(f"\n--- Testing Persistence (Session: {session_id}) ---\n")
    
    # 1. Turn 1: Introduce context
    msg1 = "Me llamo Carlos y busco un auto rojo"
    resp1 = client.post("/chat", json={"message": msg1, "session_id": session_id}).json()
    assert "response" in resp1
    
    # 2. Turn 2: Refer to context ("mi nombre", "color")
    msg2 = "Cual es mi nombre y que color de auto busco?"
    resp2 = client.post("/chat", json={"message": msg2, "session_id": session_id}).json()
    
    # 3. Verify DB (Implied if Agent answers correctly)
    response_text = resp2['response']
    assert "Carlos" in response_text
    assert "rojo" in response_text
