from typing import List, Dict

def format_user_prompt(history: List[Dict], current_input: str) -> str:
    """
    Formats the user prompt to include conversation history and the current input.
    
    Args:
        history: List of dicts [{"role": "user"|"assistant", "content": "..."}]
        current_input: The latest user message.
        
    Returns:
        Structured string for the LLM.
    """
    history_str = ""
    if history:
        history_str = "--- CONVERSATION HISTORY ---\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "AI"
            history_str += f"{role}: {msg['content']}\n"
        history_str += "----------------------------\n"
    
    prompt = f"""
{history_str}
USER'S LAST MESSAGE:
"{current_input}"

INSTRUCTIONS:
- Use the history above to understand context (e.g., if the user says "it", refer to the last discussed car).
- Respond to the USER'S LAST MESSAGE.
"""
    return prompt.strip()
