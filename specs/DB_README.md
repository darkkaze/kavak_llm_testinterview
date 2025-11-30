# Database Documentation

The project uses **SQLite** as the database engine, managed via **SQLAlchemy ORM**.
The database file is located at `kavak_chatbot/kavak.db`.

## Tables

### 1. `cars` (Car Catalog)
Stores the inventory of available cars. Populated from `specs/sample_caso_ai_engineer.csv`.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Stock ID of the car. |
| `make` | String | Manufacturer (e.g., "Volkswagen"). Indexed. |
| `model` | String | Model name (e.g., "Jetta"). Indexed. |
| `year` | Integer | Manufacturing year. |
| `price` | Float | Price in MXN. |
| `version` | String | Trim level or version details. |
| `km` | Integer | Mileage. |
| `color` | String | Exterior color (nullable). |
| `transmission` | String | Transmission type (nullable). |

### 2. `knowledge_base` (RAG Documents)
Stores the documents used for Semantic Routing (RAG).

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier. |
| `category` | String | Topic category (e.g., "locations", "financing"). Unique. |
| `content` | Text | Full markdown content of the document. |
| `embedding` | Text | JSON string representation of the OpenAI embedding vector. |

### 3. `chat_history` (Conversation Logs)
Stores the raw conversation history for the "Stateless Graph, Stateful History" architecture.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique identifier. |
| `session_id` | String | Session ID (e.g., UUID). Indexed. |
| `role` | String | "user" or "assistant". |
| `content` | String | The message text. |
| `timestamp` | String | ISO 8601 timestamp. |

## Data Loading

- **Cars**: Loaded via `db/load_catalog.py`. Reads the CSV and inserts records into the `cars` table.
- **Knowledge Base**: Loaded via `db/loader.py`. Reads hardcoded content (from `rag_info.md`), generates embeddings using OpenAI, and inserts into `knowledge_base`.

## Access Patterns

- **Catalog Search**:
    - Uses `agents/tools/catalog.py`.
    - Performs **Fuzzy Matching** (using `thefuzz`) on `make` and `model` in Python memory (fetching candidates or filtering) because SQLite lacks native trigram support.
    - Filters by `price` using SQL `WHERE` clauses.

- **RAG Retrieval**:
    - Uses `db/rag.py`.
    - Loads all embeddings into memory on startup (efficient for small N).
    - Calculates **Cosine Similarity** between the user query embedding and stored document embeddings.
    - Returns the full document content if the score exceeds a threshold (currently 0.25).
