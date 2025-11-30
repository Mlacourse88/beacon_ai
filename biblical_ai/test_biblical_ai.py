import asyncio
import sys
import os

# Add project root to path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from biblical_ai.core_ai import BiblicalAI

async def main():
    print("\n=== Biblical AI System Test ===\n")
    
    # Initialize AI
    try:
        print("Initializing BiblicalAI...")
        ai = BiblicalAI()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please ensure GOOGLE_API_KEY is set in your .env file.")
        return

    # Test Cases
    test_queries = [
        # 1. Feast Calculation (Next Year)
        "When is Passover 2026?",
        
        # 2. Feast Calculation (Specific)
        "What is the date for the Feast of Tabernacles in 2025?",
        
        # 3. Theological Query (RAG)
        "What does the Book of Enoch say about the watchers?",
        
        # 4. Restriction Check
        "What does Billy Graham say about salvation?"
    ]

    for query in test_queries:
        print(f"\n[Query]: {query}")
        print("-" * 50)
        response = await ai.respond_to_query(query)
        print(f"[Response]:\n{response}")
        print("=" * 50)

    print("\nInteractive Mode (Type 'exit' to quit)")
    while True:
        user_query = input("\nYour Question: ")
        if user_query.lower() in ['exit', 'quit']:
            break
        
        response = await ai.respond_to_query(user_query)
        print(f"\n>> {response}")

if __name__ == "__main__":
    asyncio.run(main())
