import os
import asyncio
from typing import Optional
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from shared_utils import (
    setup_logging, 
    get_api_key, 
    load_faiss_index, 
    query_knowledge_base,
    get_embedding_model,
    DEFAULT_EMBEDDING_PROVIDER,
    PROJECT_ROOT
)

logger = setup_logging("GeneralAI")

class GeneralAI:
    """
    The General Purpose AI Agent.
    
    Capabilities:
    1. General Knowledge RAG (Boy Scouts, General Info) using 'general_index'
    2. Productivity Assistance (via Google Integration - handled by manager)
    3. Broad conversation
    
    No restrictions on modern content.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        
        # Load System Context (GEMINI.md)
        self.system_context = ""
        try:
            gemini_md_path = PROJECT_ROOT / "GEMINI.md"
            if gemini_md_path.exists():
                self.system_context = gemini_md_path.read_text(encoding="utf-8")
                logger.info("Loaded System Context from GEMINI.md")
            else:
                logger.warning("GEMINI.md not found! System context will be empty.")
        except Exception as e:
            logger.error(f"Failed to load GEMINI.md: {e}")

        # Load About Me Context (About Me.txt)
        self.about_me_context = ""
        try:
            about_me_path = PROJECT_ROOT / "Self summary" / "About Me.txt"
            if about_me_path.exists():
                self.about_me_context = about_me_path.read_text(encoding="utf-8")
                logger.info("Loaded User Context from About Me.txt")
            else:
                logger.warning("About Me.txt not found! Personal context will be empty.")
        except Exception as e:
            logger.error(f"Failed to load About Me.txt: {e}")

        # Initialize Knowledge Base
        logger.info("Loading General AI Knowledge Base...")
        # Initialize embedding model here to pass to FAISS loader
        self.embedding_model = get_embedding_model(provider=os.getenv("GENERAL_EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER))
        self.vector_store = load_faiss_index(self.embedding_model, "general_index")
        if not self.vector_store:
            logger.warning("General FAISS index not found! RAG features will be disabled. Please run generate_general_embeddings.py.")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.7, # Higher temperature for creativity/natural flow
        )

    async def respond_to_query(self, query: str) -> str:
        """
        Main entry point for General AI queries (Async).
        """
        try:
            return await self._handle_rag_query(query)
        except Exception as e:
            logger.error(f"General AI Error: {e}", exc_info=True)
            return "I'm sorry, I encountered an error processing your request."

    def respond_to_query_sync(self, query: str) -> str:
        """
        Synchronous wrapper for General AI queries.
        Useful for Streamlit or environments where asyncio loops are complex.
        """
        try:
            # We must recreate the chain synchronously here or rely on invoke()
            context_text = ""
            if self.vector_store:
                docs = query_knowledge_base(query, self.vector_store, k=4)
                for i, doc in enumerate(docs):
                    source = doc.metadata.get('source', 'Unknown')
                    context_text += f"[Source: {source}]\n{doc.page_content}\n\n"
            
            current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
            
            prompt_template = PromptTemplate.from_template(
                """
                {system_context}

                --- USER PERSONAL CONTEXT ---
                {about_me_context}
                -----------------------------
                
                Current Date & Time: {current_date}
                
                Use the following context (if relevant) to answer the user's question.
                If the context contains specific instructions (like Merit Badge requirements), cite them clearly.
                
                Context:
                {context}

                User Question:
                {question}

                Answer:
                """
            )

            chain = prompt_template | self.llm | StrOutputParser()
            # Use standard invoke() instead of ainvoke()
            response = chain.invoke({
                "system_context": self.system_context,
                "about_me_context": self.about_me_context,
                "context": context_text, 
                "question": query, 
                "current_date": current_date
            })
            return response
            
        except Exception as e:
            logger.error(f"General AI Sync Error: {e}", exc_info=True)
            return f"I'm sorry, I encountered an error: {e}"

    async def _handle_rag_query(self, query: str) -> str:
        """Performs RAG retrieval on General Index."""
        context_text = ""
        
        if self.vector_store:
            docs = query_knowledge_base(query, self.vector_store, k=4)
            
            # No strict filtering needed here, but good to check type for logging
            for i, doc in enumerate(docs):
                source = doc.metadata.get('source', 'Unknown')
                context_text += f"[Source: {source}]\n{doc.page_content}\n\n"
        
        current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        
        prompt_template = PromptTemplate.from_template(
            """
            {system_context}

            --- USER PERSONAL CONTEXT ---
            {about_me_context}
            -----------------------------
            
            Current Date & Time: {current_date}
            
            Use the following context (if relevant) to answer the user's question.
            If the context contains specific instructions (like Merit Badge requirements), cite them clearly.
            
            Context:
            {context}

            User Question:
            {question}

            Answer:
            """
        )

        chain = prompt_template | self.llm | StrOutputParser()
        response = await chain.ainvoke({
            "system_context": self.system_context,
            "about_me_context": self.about_me_context,
            "context": context_text, 
            "question": query, 
            "current_date": current_date
        })
        return response

if __name__ == "__main__":
    asyncio.run(GeneralAI().respond_to_query("What are the requirements for the Cooking Merit Badge?"))
