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

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
