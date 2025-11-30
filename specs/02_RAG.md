# 02_RAG.md - Semantic Routing & RAG Strategy

## Philosophy: "Intent-based Context Injection"
Instead of traditional RAG (chunking documents and retrieving fragments), we will use **Semantic Routing**.
Since the knowledge base is small (locations, financing rules, warranty), we can classify the user's intent and inject the *entire* relevant context into the LLM. This ensures the model has the full picture and avoids missing context.

## Architecture
1.  **Embeddings**: OpenAI `text-embedding-3-small`.
2.  **Storage**: SQLite table `knowledge_base` storing the full text of each category and its embedding vector.
3.  **Retrieval**:
    - Calculate embedding of user query.
    - Perform Cosine Similarity with stored vectors (in-memory using `numpy`, as N < 10).
    - If similarity > threshold, retrieve the full document.

## Categories (Documents)
We will split `rag_info.md` into 4 master documents:

### 1. Locations (Sedes)
- **Keywords/Intent**: "donde estan", "tienes local en", "horarios", "ubicacion".
- **Content**: Addresses and hours for Puebla, Monterrey, CDMX, Guadalajara, Querétaro, Cuernavaca.

### 2. Financing (Financiamiento)
- **Keywords/Intent**: "credito", "meses", "requisitos", "enganche", "tasa".
- **Content**: Payment plans, requirements (INE, proof of income), down payment rules.

### 3. Buying/Selling Process (Compra/Venta)
- **Keywords/Intent**: "quiero vender", "como compran", "aceptan cambios", "es seguro".
- **Content**: Selling process, 3 offers (instant, 30 days, consignment), inspection.

### 4. Warranty & Post-sales (Garantía)
- **Keywords/Intent**: "garantia", "si no me gusta", "devolucion", "taller", "app".
- **Content**: 7 days/300km trial, 3-month warranty, Kavak App features.

## Why this approach?
- **Minimalist**: No Vector DB (Chroma/Pinecone) required. Just Python + SQLite.
- **Flexible**: Handles synonyms ("local" = "sede") and typos naturally via embeddings.
- **Robust**: The LLM gets the *whole* policy, not just a sentence, preventing hallucinations due to partial context.
