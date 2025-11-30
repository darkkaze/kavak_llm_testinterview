# LangGraph Architecture - Kavak Chatbot

This document describes the state machine implemented in `agents/graph.py`.

## Visual Representation

                            [ START ]
                                |
                                v
                     +----------------------+
                     |   detect_intention   |
                     | (Router Classifier)  |
                     +----------------------+
                                |
          +---------------------+---------------------+---------------------+
          |                     |                     |                     |
          v                     v                     v                     v
   [ intent="faq" ]      [ intent="buy" ]    [ intent="financing" ]  [ intent="general" ]
          |                     |                     |                     |
          v                     v                     v                     v
 +------------------+  +------------------+  +-------------------+  +------------------+
 |    handle_faq    |  | reason_about_car |  |resolve_car_context|  |  handle_general  |
 | (RAG Retrieval)  |  | (Extract & Find) |  | (History Analysis)|  | (Chitchat/Help)  |
 +------------------+  +------------------+  +-------------------+  +------------------+
          |                     |                     |                     |
          |                     v                     v                     |
          |            +------------------+  +------------------+       |
          |            |respond_with_options|| handle_financing |       |
          |            | (Format Results) |  | (Calc Payments)  |       |
          |            +------------------+  +------------------+       |
          |                     |                     |                     |
          +---------------------+---------------------+---------------------+
                                |
                                v
                             [ END ]

## Node Descriptions

1.  **detect_intention (Entry Point)**
    *   **Input**: User message.
    *   **Action**: Uses LLM to classify intent into `faq`, `buy`, or `general`.
    *   **Output**: Updates `state["intent"]`.

2.  **handle_faq**
    *   **Input**: User query.
    *   **Logic**:
        1.  **Sub-Routing**: Classifies the query into `locations`, `financing`, `buying_selling`, or `warranty`.
        2.  **Retrieval**: Fetches the *specific* document for that category (e.g., only `locations`).
        3.  **Generation**: Uses the retrieved context to answer. If the context doesn't have the answer (e.g., "Tampico" not in `locations`), it says "I don't know".
    *   **Output**: Answer based *only* on the relevant category.

3.  **reason_about_car**
    *   **Trigger**: `intent == "buy"`
    *   **Action**:
        1.  Extracts criteria (Make, Model, Price) from text to JSON.
        2.  Executes `CatalogTool.search_cars()` (Fuzzy Search + SQL).
        3.  Updates `state["found_cars"]`.
    *   **Output**: List of car dictionaries.

4.  **respond_with_options**
    *   **Trigger**: Always follows `reason_about_car`.
    *   **Action**: Formats the list of found cars into a natural language response.
    *   **Output**: Final AIMessage.

5.  **resolve_car_context**
    *   **Trigger**: `intent == "financing_calc"`.
    *   **Action**: Analyzes conversation history to identify the last mentioned car (Make, Model, Price).
    *   **Output**: Updates `state["car_context"]`.

6.  **handle_financing**
    *   **Trigger**: Follows `resolve_car_context`.
    *   **Action**: Uses `state["car_context"]` (or user input fallback) to calculate down payment and monthly installments.
    *   **Output**: Financing plan details.

7.  **handle_general**
    *   **Trigger**: `intent == "general"` (or fallback).
    *   **Action**: Returns a polite greeting or help message.
    *   **Output**: Final AIMessage.

## State Schema (`AgentState`)

The state is passed between all nodes:

```python
class AgentState(TypedDict):
    messages: Sequence[BaseMessage]  # Chat history
    input_user: str                  # Current user input
    intent: str                      # "faq", "buy", "general"
    car_preferences: Dict            # {make, model, max_price}
    found_cars: List[Dict]           # Search results
```

## Detailed Node Flows

### 1. `handle_faq` (RAG Flow)

```ascii
[ Input: "Donde estan en Puebla?" ]
            |
            v
    +----------------+
    | SemanticRouter |
    | (Embeddings)   |
    +----------------+
            |
            v
   [ Similarity Check ]
   ( vs. Locations, Financing, Warranty )
            |
            +------------------------+
            | Match > Threshold?     |
            +-----------+------------+
            | Yes       | No
            v           v
    [ Retrieve Doc ]  [ Return "Don't Know" ]
    (Locations Doc)     (Fallback)
            |
            v
    +----------------+
    |      LLM       | <--- System Prompt (FAQ)
    | (Generate Ans) | <--- Context (Locations Doc)
    +----------------+
            |
            v
[ Output: "En Puebla estamos en..." ]
```

### 2. `reason_about_car` (Seller Flow)

```ascii
[ Input: "Busco un Jetta de 200k" ]
            |
            v
    +----------------+
    |      LLM       | <--- Extraction Prompt
    | (Extract JSON) |
    +----------------+
            |
            v
   { make: "Jetta", price: 200000 }
            |
            v
    +----------------+
    |  CatalogTool   |
    +----------------+
            |
            +---> [ Fuzzy Match ] ("Jetta" -> "Volkswagen" + "Jetta")
            |
            +---> [ SQL Query ] (SELECT * FROM cars WHERE...)
            |
            v
    [ List of Cars ]
    ( [Car(id=1, ...), Car(id=2, ...)] )
            |
            v
    [ Update State ]
    ( state["found_cars"] = [...] )
```

## Architecture Decision: Stateless Graph, Stateful History

We have adopted a **"Stateless Graph, Stateful History"** approach.

### Why?
Instead of relying on LangGraph's internal checkpointers to persist the state machine (which can be rigid and hard to migrate), we treat the Graph as a **pure function** that runs from start to finish for each request.

### How it works?
1.  **Persistence**: We store the raw conversation history (User/AI messages) in a SQLite table `chat_history`.
2.  **Injection**: On each request, we retrieve the history and inject it into the prompt.
3.  **Prompt Structure**:
    The LLM does not just receive a list of messages. It receives a structured prompt:
    ```text
    [SYSTEM PROMPT]
    (Role definitions, RAG context, Tools)

    [USER PROMPT]
    Here is the conversation history:
    - User: ...
    - AI: ...
    
    The user's LAST message is: "..."
    
    Important Notes: ...
    ```
4.  **Benefits**:
    - **Robustness**: Code changes apply immediately to old conversations.
    - **Control**: We have fine-grained control over what context the LLM sees in each turn.
    - **Flexibility**: The Router evaluates intent based on the *entire* history every time, allowing for natural context switching.
