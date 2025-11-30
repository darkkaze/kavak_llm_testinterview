# 03_seller.md - Seller Logic & Catalog

## Overview
The "Seller" is the core component responsible for querying the car catalog (`sample_caso_ai_engineer.csv`) and calculating financing options.

## Database & Search Strategy
The user requested **SQLAlchemy with Trigram Search**.
*Constraint*: We are using **SQLite**, which does *not* support PostgreSQL's `pg_trgm` extension natively.
*Solution*: We will use a **Hybrid Approach**:
1.  **SQLAlchemy (SQLite)**: For structured filtering (Price range, Exact Make/Model).
2.  **TheFuzz (Python)**: For fuzzy matching/trigram-like behavior to handle typos (e.g., "Chvrolet" -> "Chevrolet") *before* constructing the SQL query.

### Catalog Schema (SQLite)
Table `cars`:
- `id` (stock_id)
- `make` (String)
- `model` (String)
- `year` (Integer)
- `price` (Float)
- `version` (String)
- ... (other columns from CSV)

## Supported Queries
The bot will handle these specific queries:

1.  **Price Range**: "que carros tienes en este precio"
    - Logic: `SELECT * FROM cars WHERE price BETWEEN (target - 10%) AND (target + 10%)`
2.  **Make**: "que carros tienes marca..."
    - Logic: Fuzzy match input -> Canonical Make -> `SELECT * FROM cars WHERE make = ?`
3.  **Model**: "estoy buscando un modelo..."
    - Logic: Fuzzy match input -> Canonical Model -> `SELECT * FROM cars WHERE model = ?`

*Note*: Queries for Year, KM, Transmission, etc., will be marked as `NotImplemented` and return a polite "I'm still learning" message.

## Financing Logic (Node: `handle_financing`)
The financing calculation is handled by a dedicated node `handle_financing`.

**Logic**:
1.  **Context Check**: The node checks `state["found_cars"]` to see if there's a recently discussed car.
2.  **Extraction**: If no car is in context, it tries to extract a price from the user's message (e.g., "para un auto de 300k").
3.  **Calculation**: Calls `calculate_financing` tool.
4.  **Response**: Returns the payment plan.

**Formula**:
- **Interest Rate**: 10% (Fixed)
- **Terms**: 3 to 6 years (36 to 72 months)
- **Down Payment (Enganche)**: User provided or Default (e.g., 20%)
- **Calculation**:
    1.  `Principal = Price - DownPayment`
    2.  `TotalInterest = Principal * 0.10 * (Years)`
    3.  `TotalAmount = Principal + TotalInterest`
    4.  `MonthlyPayment = TotalAmount / Months`

**Output**:
"Para el [Auto], con un enganche de $[X]:
- 3 años (36 meses): $[Y]/mes
- ...
- 6 años (72 meses): $[Z]/mes"

## Conversation History
The chat history is stateless in the backend but preserved in the context window.
- **LangGraph Checkpointer**: We will use `MemorySaver` (in-memory checkpointer) for the session state during the demo.
- **Context**: The `state` object passes the conversation history to the LLM so it "remembers" the car being discussed when asking for financing.
