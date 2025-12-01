import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import settings
from db.connection import SessionLocal, engine, Base
from db.models import ChatHistory
from agents.graph import app as agent_app
from agents.utils import format_user_prompt
from utils import save_chat_message, get_chat_history

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kavak Chatbot")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message")
    session_id = data.get("session_id", "default_session")
    
    if not user_message:
        return {"error": "No message provided"}
    
    # 1. Save User Message
    save_chat_message(session_id, "user", user_message)
    
    # 2. Get History
    history = get_chat_history(session_id)
    
    # 3. Format Prompt
    # Exclude the current message from history to avoid duplication
    prompt = format_user_prompt(history[:-1], user_message)
    
    # 4. Invoke Agent
    inputs = {"input_user": prompt, "messages": []}
    result = agent_app.invoke(inputs)
    
    agent_response_content = result["messages"][-1].content
    
    # 5. Save Agent Response
    save_chat_message(session_id, "assistant", agent_response_content)
    
    return {"response": agent_response_content, "intent": result.get("intent")}

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request):
    # Twilio sends data as Form Data, not JSON
    form_data = await request.form()
    user_message = form_data.get("Body")
    sender_id = form_data.get("From") # e.g., "whatsapp:+52155..."
    
    if not user_message or not sender_id:
        return {"status": "ignored", "reason": "no_message_or_sender"}
    
    print(f"DEBUG: [Twilio] Received from {sender_id}: {user_message}")

    # 1. Save User Message
    # We use the phone number as session_id
    save_chat_message(sender_id, "user", user_message)
    
    # 2. Get History
    history = get_chat_history(sender_id)
    
    # 3. Format Prompt
    prompt = format_user_prompt(history[:-1], user_message)
    
    # 4. Invoke Agent
    inputs = {"input_user": prompt, "messages": []}
    result = agent_app.invoke(inputs)
    agent_response_content = result["messages"][-1].content
    
    # 5. Save Agent Response
    save_chat_message(sender_id, "assistant", agent_response_content)
    
    # 6. Send Response via Twilio
    if settings.TWILIO_SID and settings.TWILIO_TOKEN and settings.TWILIO_PHONE:
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
            
            message = client.messages.create(
                from_=settings.TWILIO_PHONE,
                body=agent_response_content,
                to=sender_id
            )
            print(f"DEBUG: [Twilio] Sent response SID: {message.sid}")
        except Exception as e:
            print(f"ERROR: [Twilio] Failed to send message: {e}")
    else:
        print("WARNING: [Twilio] Credentials not configured, skipping response send.")

    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
