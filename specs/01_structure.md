# 01_structure.md - Project Structure & Architecture

## Overview
This document outlines the directory structure and core architecture for the Kavak Chatbot. The system uses **LangGraph** for state management and orchestration, **SQLite** for RAG and data storage, and **OpenAI** for LLM and Embeddings.

## Directory Structure

```text
kavak_chatbot/
├── agents/                 # LangGraph Agent Logic
│   ├── __init__.py
│   ├── graph.py            # Main Graph Definition (Nodes + Edges)
│   ├── nodes.py            # Node implementations (detect_intention, handle_faq, etc.)
│   ├── state.py            # State definition (TypedDict)
│   ├── prompts.py          # System prompts and templates
│   └── tools/              # Specific tools
│       ├── __init__.py
│       ├── catalog.py      # Car search logic (Seller)
│       └── financing.py    # Financing calculator
├── db/                     # Data Layer
│   ├── __init__.py
│   ├── rag.py              # Semantic Router / RAG implementation
│   ├── loader.py           # Scripts to load Markdown/CSV into DB
│   └── connection.py       # Database connection handling
├── specs/                  # Documentation & Data
│   ├── problem.md
│   ├── rag_info.md         # Cleaned RAG source
│   ├── sample_caso_ai_engineer.csv
│   ├── 01_structure.md
│   ├── 02_RAG.md
│   └── 03_seller.md
├── main.py                 # Entry point (FastAPI/Webhook for Twilio)
├── settings.py             # Configuration (Env vars)
└── requirements.txt        # Dependencies
```

## Core Libraries
- **langgraph**: State machine and orchestration.
- **langchain-openai**: LLM interface.
- **sqlalchemy**: Database ORM (for Catalog).
- **sqlite3**: Lightweight database engine.
- **numpy**: Vector operations for RAG.
- **fastapi**: Web server for Twilio webhook.
- **thefuzz**: Fuzzy string matching (for car models/makes).

## Main Router Logic (LangGraph)
The graph will follow the flow defined by the user:

**Nodes:**
1.  `detect_intention`: Classifies user input into `faq`, `buy`, or `general`.
2.  `handle_faq`: Retrieves RAG context and generates answer.
3.  `reason_about_car`: Extracts car constraints (make, model, price) from conversation.
4.  `check_availability`: Queries the catalog.
5.  `respond_with_options`: Formats available cars as a response.
6.  `ask_for_info`: Asks for missing details (e.g., "What is your budget?").
7.  `suggest_similar`: If exact match fails, finds alternatives.

**Edges:**
- `detect_intention` -> `router` -> (`handle_faq`, `reason_about_car`)
- `reason_about_car` -> `router` -> (`check_availability` (if info present), `ask_for_info` (if info missing))
- `check_availability` -> `router` -> (`respond_with_options` (if found), `suggest_similar` (if empty))

## State Definition
Based on `examples/langgraph_example/agents/state.py`:

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    input_user: str
    intent: str
    car_preferences: dict  # {make, model, min_price, max_price, year}
    found_cars: list       # Results from catalog search
```
