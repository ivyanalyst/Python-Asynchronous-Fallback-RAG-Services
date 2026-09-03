import logging
from dataclasses import dataclass
from enum import Enum

class ResponseSource(Enum):
    FULL_PIPELINE = "full_pipeline"
    BACKUP_SEARCH = "backup_search"
    STATIC_FALLBACK = "static_fallback"

@dataclass
class RAGResponse:
    text: str
    source: ResponseSource

class RAGService:
    def __init__(self, vector_db, llm_client, local_cache):
        self.vector_db = vector_db
        self.llm_client = llm_client
        self.local_cache = local_cache

    async def answer(self, query: str) -> RAGResponse:
        context = ""
        source_used = ResponseSource.FULL_PIPELINE
        
        # STEP 1: Context Retrieval with Fallback 
        try:
            # Attempt primary vector database retrieval
            documents = await self.vector_db.retrieve_relevant_docs(query)
            context = "\n".join(documents)
        except Exception as e:
            logging.error(f"Vector DB failed. Falling back to local keyword index: {e}")
            context = self.local_cache.keyword_search(query)
            source_used = ResponseSource.BACKUP_SEARCH
            
        # STEP 2: Generation with Fallback 
        try:
            ai_response = await self.llm_client.generate_answer(query=query, context=context)
            return RAGResponse(text=ai_response, source=source_used)
        except Exception as e:
            logging.error(f"LLM generation failed. Returning generic helpful fallback: {e}")
            fallback_text = (
                f"I'm having trouble connecting to my primary knowledge base right now. "
                f"Regarding your question '{query}', please check your connection and try again shortly."
            )
            return RAGResponse(text=fallback_text, source=ResponseSource.STATIC_FALLBACK)
        
async def main():
    vector_db = Pinecone(...)
    llm_client = OpenAI(...)
    local_cache = BM25(...)
    
    
    rag_service = RAGService(
        vector_db=vector_db,
        llm_client=llm_client,
        local_cache=local_cache
    )
    
    query = "What is the capital of France?"
    response = await rag_service.answer(query)
    
    print(f"Answer : {response.text}")
    print(f"Source : {response.source.value}")
    
if __name__= "__main__":
    import asyncio
    asyncio.run(main())
