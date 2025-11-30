from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State schema for Kavak Chatbot.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    input_user: str
    intent: str
    
    # Context for Car Search
    car_preferences: Dict[str, Any] # {make, model, min_price, max_price}
    found_cars: List[Dict[str, Any]] # Results from catalog (Ephemeral)
    
    # Context for Financing
    car_context: Dict[str, Any] # {make, model, price} resolved from history
    selected_car_id: int
