import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents.state import AgentState
from agents.prompts import SYSTEM_PROMPT_ROUTER, SYSTEM_PROMPT_FAQ, SYSTEM_PROMPT_SELLER, SYSTEM_PROMPT_GENERAL
from db.rag import SemanticRouter
from agents.tools.catalog import CatalogTool
from agents.tools.financing import calculate_financing
import settings

llm = ChatOpenAI(model=settings.MODEL_NAME, api_key=settings.OPENAI_API_KEY)
rag = SemanticRouter()
catalog = CatalogTool()

def detect_intention(state: AgentState):
    """Classifies user intent."""
    user_input = state["input_user"]
    print(f"DEBUG: [detect_intention] Input: '{user_input}'")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_ROUTER),
        HumanMessage(content=user_input)
    ]
    response = llm.invoke(messages)
    intent = response.content.strip().lower()
    
    # Fallback for safety
    if intent not in ["faq", "buy", "financing_calc", "general"]:
        intent = "general"
        
    print(f"DEBUG: [detect_intention] Classified as: '{intent}'")
    return {"intent": intent}

def handle_faq(state: AgentState):
    """Retrieves RAG context and answers based on specific topic."""
    print(f"DEBUG: [handle_faq] Processing query...")
    query = state["input_user"]
    
    # 1. Sub-Routing: Classify the FAQ topic
    # We ask the LLM to map the query to one of our known categories
    classification_prompt = """
    Classify the user's question into one of these categories:
    - locations: Address, cities, where are you located.
    - financing: Credit, down payment, monthly payments, requirements.
    - buying_selling: How to sell, how to buy, inspection process.
    - warranty: Guarantee, return policy, post-sales.
    - app_services: App usage, maintenance appointments, paperwork, Kavak Total.
    - general_info: What is Kavak, mission, company info.
    - other: If it doesn't fit any of the above.
    
    Return ONLY the category name.
    """
    messages = [
        SystemMessage(content=classification_prompt),
        HumanMessage(content=query)
    ]
    response = llm.invoke(messages)
    category = response.content.strip().lower()
    print(f"DEBUG: [handle_faq] Sub-classification: '{category}'")
    
    # 2. Retrieve Specific Context
    context = None
    if category in ["locations", "financing", "buying_selling", "warranty", "app_services", "general_info"]:
        context = rag.get_content_by_category(category)
        print(f"DEBUG: [handle_faq] Retrieved context for category: '{category}'")
    else:
        # Fallback if "other" or unclear
        print(f"DEBUG: [handle_faq] Category unclear.")
        context = None

    if not context:
        print(f"DEBUG: [handle_faq] No relevant context found.")
        return {"messages": [AIMessage(content="Lo siento, no tengo información específica sobre eso. ¿Te gustaría ver nuestro catálogo de autos?")]}
    
    print(f"DEBUG: [handle_faq] Context found. Generating response...")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_FAQ + f"\n\nCONTEXT ({category}):\n{context}"),
        HumanMessage(content=query)
    ]
    response = llm.invoke(messages)
    return {"messages": [response]}

def reason_about_car(state: AgentState):
    """Extracts car preferences and searches catalog."""
    print(f"DEBUG: [reason_about_car] Extracting criteria...")
    query = state["input_user"]
    
    # 1. Extract entities (Make, Model, Price) using LLM
    extraction_prompt = """
    Extract car search criteria from the user input.
    Return JSON: {"make": str|null, "model": str|null, "max_price": float|null}
    Example: "Busco un Jetta de menos de 200k" -> {"make": "Volkswagen", "model": "Jetta", "max_price": 200000}
    """
    messages = [
        SystemMessage(content=extraction_prompt),
        HumanMessage(content=query)
    ]
    response = llm.invoke(messages)
    try:
        criteria = json.loads(response.content.replace("```json", "").replace("```", ""))
    except:
        criteria = {}
    
    print(f"DEBUG: [reason_about_car] Criteria: {criteria}")
    
    # 2. Search Catalog
    results = catalog.search_cars(
        make=criteria.get("make"),
        model=criteria.get("model"),
        max_price=criteria.get("max_price"),
        limit=3
    )
    
    # 3. Format results for the next step (Response)
    found_cars = []
    for car in results:
        found_cars.append({
            "id": car.id,
            "make": car.make,
            "model": car.model,
            "year": car.year,
            "price": car.price
        })
        
    print(f"DEBUG: [reason_about_car] Found {len(found_cars)} cars.")
    return {"car_preferences": criteria, "found_cars": found_cars}

def respond_with_options(state: AgentState):
    """Generates response based on found cars."""
    print(f"DEBUG: [respond_with_options] Generating response...")
    cars = state.get("found_cars", [])
    
    if not cars:
        return {"messages": [AIMessage(content="No encontré autos exactos con esos criterios. ¿Te gustaría ver otras opciones o ajustar tu presupuesto?")]}
    
    car_list_str = "\n".join([f"- {c['make']} {c['model']} ({c['year']}): ${c['price']:,.2f}" for c in cars])
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_SELLER + f"\n\nAVAILABLE CARS:\n{car_list_str}"),
        HumanMessage(content=state["input_user"])
    ]
    response = llm.invoke(messages)
    return {"messages": [response]}

def resolve_car_context(state: AgentState):
    """
    Analyzes conversation history to find the car the user is referring to.
    This makes the agent stateless regarding car selection.
    """
    print(f"DEBUG: [resolve_car_context] Resolving car from history...")
    query = state["input_user"]
    
    # We pass the full conversation history (implicitly in input_user if formatted correctly, 
    # but here we rely on the fact that the LLM sees the history in the prompt context).
    # Actually, state["input_user"] is just the last message. 
    # The history is passed to the LLM via the messages list in the invoke call.
    # So we need to ask the LLM to look at the *conversation context*.
    
    resolution_prompt = """
    Analyze the conversation history to identify the car the user is interested in.
    Look for the LAST mentioned car by the AI or the User.
    
    Return JSON: {"make": str|null, "model": str|null, "price": float|null}
    
    If no car is found in context, return nulls.
    Example: AI said "Ford Figo $188,999", User says "financing for that one" -> {"make": "Ford", "model": "Figo", "price": 188999.0}
    """
    
    # NOTE: In a real LangGraph with memory, we would pass state["messages"].
    # Here, we assume the 'input_user' might contain the history if the frontend/main.py packs it.
    # Based on the logs, 'input_user' DOES contain "--- CONVERSATION HISTORY ---".
    
    messages = [
        SystemMessage(content=resolution_prompt),
        HumanMessage(content=query)
    ]
    response = llm.invoke(messages)
    
    try:
        car_context = json.loads(response.content.replace("```json", "").replace("```", ""))
    except:
        car_context = {}
        
    print(f"DEBUG: [resolve_car_context] Resolved: {car_context}")
    return {"car_context": car_context}

def handle_financing(state: AgentState):
    """Calculates financing for a car in context or from user input."""
    print(f"DEBUG: [handle_financing] Calculating financing...")
    
    # 1. Try to get car from resolved context
    car_context = state.get("car_context", {})
    target_price = car_context.get("price")
    car_name = f"{car_context.get('make', '')} {car_context.get('model', '')}".strip() or "tu auto"
    
    # 2. If no context, try to extract price from explicit user input (fallback)
    if not target_price:
        extraction_prompt = """
        Extract the car price from the user input if present.
        Return JSON: {"price": float|null}
        Example: "para un auto de 300k" -> {"price": 300000}
        """
        messages = [
            SystemMessage(content=extraction_prompt),
            HumanMessage(content=state["input_user"])
        ]
        response = llm.invoke(messages)
        try:
            data = json.loads(response.content.replace("```json", "").replace("```", ""))
            target_price = data.get("price")
        except:
            pass

    # 3. Calculate or Ask for Info
    if target_price:
        plan = calculate_financing(target_price)
        msg = (
            f"Para {car_name} (Precio: ${target_price:,.2f}):\n"
            f"- Enganche (20%): ${plan['down_payment']:,.2f}\n"
            f"- Mensualidad (48 meses): ${plan['monthly_payment']:,.2f}\n"
            f"- Pago Total Estimado: ${plan['total_paid']:,.2f}\n\n"
            "¿Te gustaría ajustar el enganche o el plazo?"
        )
        return {"messages": [AIMessage(content=msg)]}
    else:
        return {"messages": [AIMessage(content="Claro, puedo ayudarte con el financiamiento. ¿Cuál es el precio del auto que te interesa o qué modelo estás buscando?")]}

def handle_general(state: AgentState):
    """Handles general chitchat or off-topic queries dynamically."""
    print(f"DEBUG: [handle_general] Handling general query...")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_GENERAL),
        HumanMessage(content=state["input_user"])
    ]
    response = llm.invoke(messages)
    return {"messages": [response]}
