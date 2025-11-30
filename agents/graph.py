from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import (
    detect_intention,
    handle_faq,
    reason_about_car,
    respond_with_options,
    handle_general,
    handle_financing,
    resolve_car_context
)

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("detect_intention", detect_intention)
workflow.add_node("handle_faq", handle_faq)
workflow.add_node("reason_about_car", reason_about_car)
workflow.add_node("respond_with_options", respond_with_options)
workflow.add_node("resolve_car_context", resolve_car_context) # New node
workflow.add_node("handle_financing", handle_financing)
workflow.add_node("handle_general", handle_general)

# 3. Define Router Logic
def router(state: AgentState):
    intent = state["intent"]
    if intent == "faq":
        return "handle_faq"
    elif intent == "buy":
        return "reason_about_car"
    elif intent == "financing_calc":
        return "resolve_car_context" # Route to resolver first
    else:
        return "handle_general"

# 4. Add Edges
workflow.set_entry_point("detect_intention")

workflow.add_conditional_edges(
    "detect_intention",
    router,
    {
        "handle_faq": "handle_faq",
        "reason_about_car": "reason_about_car",
        "resolve_car_context": "resolve_car_context",
        "handle_general": "handle_general"
    }
)

workflow.add_edge("reason_about_car", "respond_with_options")
workflow.add_edge("resolve_car_context", "handle_financing") # Chain resolver to handler
workflow.add_edge("handle_faq", END)
workflow.add_edge("respond_with_options", END)
workflow.add_edge("handle_financing", END)
workflow.add_edge("handle_general", END)

# 5. Compile
app = workflow.compile()
