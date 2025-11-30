import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from biblical_ai.core_ai import BiblicalAI
from shared_utils import setup_logging

logger = setup_logging("TestSplitIndexes")

async def test_biblical_isolation():
    print("\n=== TESTING BIBLICAL AI INDEX ISOLATION ===\n")
    
    ai = BiblicalAI()
    
    # Test 1: Valid Biblical Query
    print("Test 1: Valid Biblical Query ('Book of Enoch watchers')")
    response1 = await ai.respond_to_query("What does the Book of Enoch say about the watchers?")
    print(f"Response length: {len(response1)}")
    if "Enoch" in response1 or "Watchers" in response1:
        print("✅ PASS: Retrieved biblical content.")
    else:
        print("❌ FAIL: Did not retrieve expected content.")
        
    print("-" * 50)

    # Test 2: Invalid General Query (Merit Badge)
    print("Test 2: Invalid General Query ('Cooking Merit Badge')")
    response2 = await ai.respond_to_query("What are the requirements for the Cooking Merit Badge?")
    print(f"Response: {response2}")
    
    # We expect it to NOT find info, or find it and filter it out.
    if "filtered out" in response2 or "couldn't find" in response2 or "restricted" in response2:
        print("✅ PASS: Correctly refused/filtered non-biblical content.")
    elif "requirements" in response2 and "Cooking" in response2:
        print("❌ FAIL: Leaked General Knowledge content!")
    else:
        print("⚠️ NOTE: Response was generic or unclear.")

    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_biblical_isolation())
