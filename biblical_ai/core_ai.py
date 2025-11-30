import os
import asyncio
import logging
import re
from typing import Dict, Optional, Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from shared_utils import (
    setup_logging, 
    get_api_key, 
    load_faiss_index, 
    query_knowledge_base,
    FAISS_INDEX_PATH,
    get_embedding_model,
    DEFAULT_EMBEDDING_PROVIDER
)
from .feast_date_calculator import FeastDateCalculator

# Configure logger
logger = setup_logging("BiblicalAI")

class BiblicalAI:
    """
    The Core Biblical AI Agent.
    
    Capabilities:
    1. Feast Date Calculation (using FeastDateCalculator)
    2. Historical Theological RAG (using FAISS + Gemini)
    3. Intent Routing (Feast vs. Theology vs. General)
    
    Constraints:
    - Only historical sources (Bible, Apocrypha, Fathers < 1000 AD).
    - No modern commentary.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        
        # Initialize Logic Components
        self.feast_calculator = FeastDateCalculator()
        
        # Initialize Knowledge Base
        logger.info("Loading Biblical AI Knowledge Base...")
        # Initialize embedding model here to pass to FAISS loader
        self.embedding_model = get_embedding_model(provider=os.getenv("BIBLICAL_EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER))
        self.vector_store = load_faiss_index(self.embedding_model, "biblical_index")
        if not self.vector_store:
            logger.warning("Biblical FAISS index not found! RAG features will be disabled. Please run generate_biblical_embeddings.py.")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.3, # Low temperature for factual/historical accuracy
            convert_system_message_to_human=True
        )

    def _detect_intent(self, query: str) -> str:
        """
        Simple rule-based intent detection. 
        Returns: 'FEAST', 'RAG', or 'RESTRICTION'
        """
        query_lower = query.lower()
        
        # Feast Keywords
        feast_terms = [
            "passover", "pesach", "sukkot", "tabernacles", "unleavened bread", 
            "weeks", "pentecost", "shavuot", "trumpets", "rosh hashanah", 
            "atonement", "yom kippur", "feast", "last great day"
        ]
        time_terms = ["when", "date", "calendar", "timing", "year", "202"]
        
        if any(term in query_lower for term in feast_terms) and any(term in query_lower for term in time_terms):
            return 'FEAST'
            
        # Modern/Restriction Keywords (Simple filter)
        modern_terms = ["billy graham", "c.s. lewis", "modern", "today", "current events", "politics"]
        if any(term in query_lower for term in modern_terms):
            return 'RESTRICTION'
            
        # Default to RAG for theological/biblical questions
        return 'RAG'

    def _extract_year(self, query: str) -> int:
        """Extracts a year from the query, defaulting to current year + 1 if 'next year' is found."""
        current_year = datetime.now().year
        
        if "next year" in query.lower():
            return current_year + 1
        if "this year" in query.lower():
            return current_year
            
        match = re.search(r'\b(20\d{2})\b', query)
        if match:
            return int(match.group(1))
            
        return current_year

    async def respond_to_query(self, query: str) -> str:
        """
        Main entry point for user queries.
        """
        try:
            intent = self._detect_intent(query)
            logger.info(f"Query: '{query}' | Detected Intent: {intent}")

            if intent == 'FEAST':
                return self._handle_feast_query(query)
            elif intent == 'RESTRICTION':
                return (
                    "I apologize, but I am restricted to historical biblical sources (Bible, Apocrypha, "
                    "and Church Fathers up to 1000 AD). I cannot discuss modern theology or contemporary figures."
                )
            else:
                return await self._handle_rag_query(query)

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return "I encountered an error while processing your request. Please check the logs."

    def respond_to_query_sync(self, query: str) -> str:
        """
        Synchronous wrapper for user queries.
        """
        try:
            intent = self._detect_intent(query)
            logger.info(f"Sync Query: '{query}' | Detected Intent: {intent}")

            if intent == 'FEAST':
                return self._handle_feast_query(query)
            elif intent == 'RESTRICTION':
                return (
                    "I apologize, but I am restricted to historical biblical sources (Bible, Apocrypha, "
                    "and Church Fathers up to 1000 AD). I cannot discuss modern theology or contemporary figures."
                )
            else:
                # Handle RAG synchronously
                return self._handle_rag_query_sync(query)

        except Exception as e:
            logger.error(f"Error processing query (Sync): {e}", exc_info=True)
            return f"I encountered an error: {e}"

    def _handle_feast_query(self, query: str) -> str:
        """Calculates and formats feast dates."""
        year = self._extract_year(query)
        try:
            feasts = self.feast_calculator.calculate_feasts(year)
            
            # Filter if specific feast requested
            query_lower = query.lower()
            selected_feasts = []
            
            # specific mapping to key names
            key_map = {
                "passover": "Passover", "pesach": "Passover",
                "unleavened": "Unleavened Bread",
                "firstfruits": "Firstfruits",
                "pentecost": "Pentecost", "shavuot": "Pentecost", "weeks": "Pentecost",
                "trumpets": "Trumpets", "teruah": "Trumpets",
                "atonement": "Atonement", "kippur": "Atonement",
                "tabernacles": "Tabernacles", "sukkot": "Tabernacles",
                "last great": "Last Great Day"
            }
            
            matched_keys = set()
            for term, key in key_map.items():
                if term in query_lower:
                    matched_keys.add(key)
            
            # If no specific feast found, show all (or if 'feast' is generic)
            if not matched_keys:
                matched_keys = feasts.keys()
                
            response_lines = [f"**Biblical Feasts for {year}**\n"]
            
            for key in matched_keys:
                if key in feasts:
                    f = feasts[key]
                    response_lines.append(f"### {f['title']}")
                    response_lines.append(f"- **Gregorian Date:** {f['gregorian_date_text']}")
                    response_lines.append(f"- **Hebrew Date:** {f['hebrew_date']}")
                    response_lines.append(f"- **Moon Phase:** {f['moon_phase']}")
                    response_lines.append(f"- **Day of Week:** {f['day_of_week']}")
                    response_lines.append(f"- **Sunset:** {f['sunset_time']}")
                    response_lines.append("")
            
            return "\n".join(response_lines)

        except Exception as e:
            logger.error(f"Feast calculation failed: {e}")
            return f"Unable to calculate feast dates for {year}."

    def _handle_rag_query_sync(self, query: str) -> str:
        """Performs RAG retrieval and generates a response synchronously."""
        if not self.vector_store:
            return "My knowledge base is currently unavailable. Please run the embeddings generator first."

        # 1. Retrieve Context
        docs = query_knowledge_base(query, self.vector_store, k=4)
        if not docs:
            return "I searched my historical records but couldn't find specific information matching your query."

        # Filter for biblical content type safety
        valid_docs = []
        for doc in docs:
            if doc.metadata.get('type') == 'biblical':
                valid_docs.append(doc)
            else:
                logger.warning(f"Filtered out non-biblical document: {doc.metadata.get('source')} (Type: {doc.metadata.get('type')})")
        
        if not valid_docs:
             return "I found some information, but it was filtered out because it did not meet the strict biblical source criteria."

        # 2. Format Context
        context_text = ""
        for i, doc in enumerate(valid_docs):
            source = doc.metadata.get('source', 'Unknown Source')
            context_text += f"[Source {i+1}: {source}]\n{doc.page_content}\n\n"

        # 3. Generate Response via LLM
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        prompt_template = PromptTemplate.from_template(
            """
            You are BiblicalAI, a specialized assistant restricted to historical biblical texts (Bible, Apocrypha, Early Church Fathers < 1000 AD).
            
            Current Date: {current_date}
            
            Answer the user's question based ONLY on the following provided historical context.
            - Cite the specific sources provided (e.g., "According to [Source 1]...").
            - Maintain a respectful, scholarly tone.
            - If the context doesn't answer the question, admit it politely.
            - Do not offer modern theological opinions.

            Context:
            {context}

            User Question:
            {question}

            Answer:
            """
        )

        chain = prompt_template | self.llm | StrOutputParser()
        response = chain.invoke({"context": context_text, "question": query, "current_date": current_date})
        return response

    async def _handle_rag_query(self, query: str) -> str:
        """Performs RAG retrieval and generates a response."""
        if not self.vector_store:
            return "My knowledge base is currently unavailable. Please run the embeddings generator first."

        # 1. Retrieve Context
        docs = query_knowledge_base(query, self.vector_store, k=4)
        if not docs:
            return "I searched my historical records but couldn't find specific information matching your query."

        # Filter for biblical content type safety
        valid_docs = []
        for doc in docs:
            if doc.metadata.get('type') == 'biblical':
                valid_docs.append(doc)
            else:
                logger.warning(f"Filtered out non-biblical document: {doc.metadata.get('source')} (Type: {doc.metadata.get('type')})")
        
        if not valid_docs:
             return "I found some information, but it was filtered out because it did not meet the strict biblical source criteria."

        # 2. Format Context
        context_text = ""
        for i, doc in enumerate(valid_docs):
            source = doc.metadata.get('source', 'Unknown Source')
            context_text += f"[Source {i+1}: {source}]\n{doc.page_content}\n\n"

        # 3. Generate Response via LLM
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        prompt_template = PromptTemplate.from_template(
            """
            You are BiblicalAI, a specialized assistant restricted to historical biblical texts (Bible, Apocrypha, Early Church Fathers < 1000 AD).
            
            Current Date: {current_date}
            
            Answer the user's question based ONLY on the following provided historical context.
            - Cite the specific sources provided (e.g., "According to [Source 1]...").
            - Maintain a respectful, scholarly tone.
            - If the context doesn't answer the question, admit it politely.
            - Do not offer modern theological opinions.

            Context:
            {context}

            User Question:
            {question}

            Answer:
            """
        )

        chain = prompt_template | self.llm | StrOutputParser()
        
        response = await chain.ainvoke({"context": context_text, "question": query, "current_date": current_date})
        return response

if __name__ == "__main__":
    # Simple sync test for init
    try:
        ai = BiblicalAI()
        print("BiblicalAI initialized successfully.")
    except Exception as e:
        print(f"Initialization failed: {e}")
