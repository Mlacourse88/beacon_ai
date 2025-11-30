import asyncio
import logging
import json
import re
from typing import Optional, Dict
from datetime import datetime

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from shared_utils import setup_logging, get_project_root
from biblical_ai.core_ai import BiblicalAI
from general_ai.core_ai import GeneralAI
from google_integration.google_manager import GoogleManager

# Configure logger
logger = setup_logging("BeaconMainAgent")

PROJECT_ROOT = get_project_root()

class BeaconAgent:
    """
    The Primary Orchestrator Agent.
    Routes queries to BiblicalAI, GeneralAI, or Google Tools.
    """

    def __init__(self):
        logger.info("Initializing BEACON System...")
        try:
            self.biblical_ai = BiblicalAI()
            self.general_ai = GeneralAI()
            self.google_manager = GoogleManager()
        except Exception as e:
            logger.critical(f"Failed to initialize sub-agents: {e}")
            raise e

    async def initialize(self):
        """Async initialization for components that need it."""
        await self.google_manager.initialize_system()
        
        # --- Proactive Budget Init ---
        # With hardcoded ID, just check balance logic
        if self.google_manager.budget.spreadsheet_id:
            balance = await self.google_manager.budget.get_balance()
            # If expenses are 0, maybe add default income rows if Income sheet is empty?
            # Simplified: Just log the balance status
            logger.info(f"Budget initialized. Balance: {balance.get('remaining')}")
            
            # Logic: If expenses are 0, check if we should auto-add income?
            # Actually, `get_balance` uses fixed income variable, so income is always > 0.
            # We can check if `total_expenses` is 0 to prompt user? 
            pass

    async def process_query(self, query: str, force_mode: str = None) -> str:
        """
        Smart Routing Logic using LLM to determine intent.
        
        Args:
            query: User's question or command.
            force_mode: Optional override ('BIBLICAL' or 'GENERAL') to bypass router.
        """
        logger.info(f"Processing Query: '{query}' (Force Mode: {force_mode})")
        
        # 0. Check Force Mode Override
        if force_mode == "Force Biblical":
            logger.info(f"Query: '{query}' | Routed to: BIBLICAL (Manual Override)")
            return await self.biblical_ai.respond_to_query(query)
        elif force_mode == "Force General":
            logger.info(f"Query: '{query}' | Routed to: GENERAL (Manual Override)")
            return await self.general_ai.respond_to_query(query)

        # 1. Router LLM Logic
        router_prompt = PromptTemplate.from_template(
            """
            Analyze the following user query and extract intent and data.
            Query: "{query}"
            Current Date: {date}
            
            Intents:
            - BIBLICAL: Theology, scripture, feast dates, religious questions.
            - ADD_EXPENSE: Spending money, buying things, tracking costs. Extract category, amount, date.
            - CHECK_BUDGET: Asking about affordability, balance, budget status, "can I buy".
            - GENERAL: Everything else (News, Chat, Weather, Merit Badges, Personal questions).
            
            Return JSON ONLY:
            {{
                "intent": "INTENT_NAME",
                "entities": {{
                    "category": "string (optional)",
                    "amount": "string/number (optional)",
                    "date": "string (YYYY-MM-DD optional)"
                }} 
            }}
            """
        )
        
        # Reuse GeneralAI's LLM for routing decision
        chain = router_prompt | self.general_ai.llm | JsonOutputParser()
        
        try:
            # Run the router
            result = await chain.ainvoke({"query": query, "date": datetime.now().strftime("%Y-%m-%d")})
            intent = result.get("intent")
            logger.info(f"Router Intent: {intent}")
            
            if intent == "BIBLICAL":
                logger.info(f"Query: '{query}' | Routed to: BIBLICAL")
                return await self.biblical_ai.respond_to_query(query)
            
            elif intent == "ADD_EXPENSE":
                logger.info(f"Query: '{query}' | Routed to: BUDGET_ADD")
                data = result.get("entities", {})
                amount_raw = data.get("amount")
                
                amount = 0.0
                if amount_raw:
                    if isinstance(amount_raw, (int, float)):
                        amount = float(amount_raw)
                    else:
                        clean_str = re.sub(r"[^\\d.]", "", str(amount_raw))
                        if clean_str:
                            amount = float(clean_str)
                
                if amount > 0:
                    success = await self.google_manager.budget.add_expense(
                        category=data.get("category", "Uncategorized"),
                        amount=amount,
                        date_str=data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        note=query
                    )
                    return f"💸 Expense Logged: ${amount:.2f} for {data.get('category')}." if success else "Failed to log expense."
                return "I couldn't determine the amount to log."

            elif intent == "CHECK_BUDGET":
                logger.info(f"Query: '{query}' | Routed to: BUDGET_QUERY")
                balance = await self.google_manager.budget.get_balance()
                
                advice_prompt = f"""
                User asks: '{query}'
                
                Current Budget Status:
                - Total Income: ${balance.get('total_income', 0)}
                - Total Expenses: ${balance.get('total_expenses', 0)}
                - Remaining: ${balance.get('remaining', 0)}
                
                Provide brief, helpful financial advice based on these numbers. 
                """
                response = await self.general_ai.llm.ainvoke(advice_prompt)
                return response.content

            else: # GENERAL or Fallback
                logger.info(f"Query: '{query}' | Routed to: GENERAL")
                return await self.general_ai.respond_to_query(query)

        except Exception as e:
            logger.error(f"Router Error: {e}")
            return await self.general_ai.respond_to_query(query)

    def respond_to_query_sync(self, query: str, force_mode: str = None) -> str:
        """
        Synchronous wrapper for Streamlit usage.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.process_query(query, force_mode))

async def main():
    agent = BeaconAgent()
    await agent.initialize()
    
    print("\n=== BEACON AI READY ===")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        response = await agent.process_query(user_input)
        print(f"Beacon: {response}\n")

if __name__ == "__main__":
    asyncio.run(main())