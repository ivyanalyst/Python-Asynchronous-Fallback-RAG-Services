# Python Asynchronous Fallback RAG Service

A lightweight, resilient **Retrieval-Augmented Generation (RAG)** service built with `asyncio`. It wraps a vector database and an LLM client in a two-layer fallback pattern so that retrieval or generation failures degrade gracefully instead of crashing or returning nothing.

## Why this exists

Production RAG pipelines have two failure-prone hops:

1. **Retrieval** — the vector database call can time out, error, or be unavailable.
2. **Generation** — the LLM call can fail (rate limits, network errors, provider outages).

This service wraps both hops in `try/except` blocks with dedicated fallback paths, and tags every response with the `ResponseSource` that actually produced it — so callers and logs always know whether an answer came from the full pipeline or a degraded path.

## How it works

```
Query
  │
  ▼
[1] Vector DB retrieval  ──fails──▶ local keyword search (BM25 / in-memory cache)
  │
  ▼
[2] LLM generation       ──fails──▶ static, user-friendly fallback message
  │
  ▼
RAGResponse(text, source)
```

| Step | Primary path | Fallback path | Resulting `ResponseSource` |
|------|--------------|----------------|------------------------------|
| Context retrieval | `vector_db.retrieve_relevant_docs(query)` | `local_cache.keyword_search(query)` | `FULL_PIPELINE` → `BACKUP_SEARCH` |
| Answer generation | `llm_client.generate_answer(query, context)` | Static apology/retry message | unchanged → `STATIC_FALLBACK` |

Every failure is logged via the standard `logging` module before falling back, so issues are visible without interrupting the user-facing response.

## Core components

- **`ResponseSource`** (`Enum`) — labels where a response came from: `full_pipeline`, `backup_search`, or `static_fallback`.
- **`RAGResponse`** (`dataclass`) — the return type of the service: `text` (the answer) and `source` (a `ResponseSource`).
- **`RAGService`** — the orchestrator. Takes a `vector_db`, `llm_client`, and `local_cache` client on construction and exposes a single async method, `answer(query: str) -> RAGResponse`.

## Requirements

- Python 3.8+
- A vector database client exposing `async retrieve_relevant_docs(query: str) -> list[str]` (e.g. Pinecone, Weaviate, Chroma)
- An LLM client exposing `async generate_answer(query: str, context: str) -> str` (e.g. OpenAI, Anthropic)
- A local cache/index exposing `keyword_search(query: str) -> str` (e.g. a BM25 index) as a fallback retriever

> **Note:** This repo defines the orchestration pattern only. The `Pinecone(...)`, `OpenAI(...)`, and `BM25(...)` clients referenced in `main()` are illustrative placeholders — plug in your own client implementations that satisfy the interfaces above.

## Installation

```bash
git clone https://github.com/ivyanalyst/Python-Asynchronous-Fallback-RAG-Services.git
cd Python-Asynchronous-Fallback-RAG-Services
```

Install whichever client libraries you use for your vector DB, LLM provider, and keyword index (not bundled — bring your own).

## Usage

```python
import asyncio
from Pythonfallback import RAGService

async def main():
    vector_db = MyVectorDBClient(...)
    llm_client = MyLLMClient(...)
    local_cache = MyKeywordIndex(...)

    rag_service = RAGService(
        vector_db=vector_db,
        llm_client=llm_client,
        local_cache=local_cache,
    )

    query = "What is the capital of France?"
    response = await rag_service.answer(query)

    print(f"Answer : {response.text}")
    print(f"Source : {response.source.value}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python Pythonfallback.py
```

## Example output

```
Answer : Paris is the capital of France.
Source : full_pipeline
```

If the vector DB is down but the LLM still succeeds using keyword-search context:

```
Answer : Paris is the capital of France.
Source : backup_search
```

If generation itself fails entirely:

```
Answer : I'm having trouble connecting to my primary knowledge base right now. Regarding your question 'What is the capital of France?', please check your connection and try again shortly.
Source : static_fallback
```

## Extending this pattern

- Add retry/backoff (e.g. `tenacity`) before falling back, to absorb transient errors.
- Swap the static fallback message for a cached previous answer or a "contact support" prompt.
- Add metrics/alerting on `ResponseSource` distribution to track how often fallbacks trigger in production.
- Add unit tests that mock `vector_db` and `llm_client` to simulate each failure path independently.

## License

No license specified yet. Add a `LICENSE` file to clarify how others may use this code.
