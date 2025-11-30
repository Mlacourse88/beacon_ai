import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from general_ai.core_ai import GeneralAI

async def test_general_ai():
    print("\n=== TESTING GENERAL AI FUNCTIONALITY ===\n")
    
    ai = GeneralAI()
    
    queries = [
        "What are the requirements for the Cooking Merit Badge?",
        "How do I organize a patrol camping trip?",
        "Tell me a joke."
    ]
    
    for q in queries:
        print(f"Query: {q}")
        response = await ai.respond_to_query(q)
        print(f"Response: {response[:200]}...") # Truncate for display
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_general_ai())

