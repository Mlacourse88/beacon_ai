import asyncio
import sys
from generate_gemini_embeddings import query_cli, generate_index

def print_menu():
    print("\n=== Beacon AI RAG Test Console ===")
    print("1. Generate/Update Embeddings (Full Pipeline)")
    print("2. Query Knowledge Base")
    print("3. Exit")
    print("==================================")

async def main():
    while True:
        print_menu()
        choice = input("Select an option (1-3): ")
        
        if choice == "1":
            print("\nRunning generation pipeline...")
            await generate_index()
        elif choice == "2":
            query_cli()
        elif choice == "3":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
