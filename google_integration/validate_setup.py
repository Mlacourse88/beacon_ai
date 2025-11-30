import asyncio
import sys
import os
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google_integration.auth import GoogleAuthManager
from google_integration.calendar_sync import CalendarSync
from google_integration.drive_manager import DriveManager
from shared_utils import setup_logging

logger = setup_logging("ValidateGoogle")

async def validate_connections():
    print("\n=== VALIDATING GOOGLE CONNECTIONS ===\n")
    
    # 1. Test Authentication
    print("[1/3] Authenticating Service Account...")
    try:
        auth = GoogleAuthManager()
        print("✅ Auth Successful!")
        print(f"   Service Account Email: {auth.creds.service_account_email}")
    except Exception as e:
        print(f"❌ Auth Failed: {e}")
        return

    # 2. Test Calendar Access
    print("\n[2/3] Testing Calendar Access...")
    try:
        cal = CalendarSync(auth)
        events = await cal.get_upcoming_events(days=1)
        print(f"✅ Calendar Access Successful! (Found {len(events)} upcoming events)")
        if not events:
            print("   (Note: No events found, but API call succeeded. Did you share your calendar?)")
    except Exception as e:
        print(f"❌ Calendar Access Failed: {e}")

    # 3. Test Drive Access
    print("\n[3/3] Testing Drive Access...")
    try:
        drive = DriveManager(auth)
        # Attempt to list files in root to verify access
        # We just check if we can run a query
        service = auth.get_service('drive', 'v3')
        results = service.files().list(pageSize=1).execute()
        print("✅ Drive Access Successful!")
        
        # Optional: Check for BEACON_AI folder
        folder_id = await drive._get_or_create_folder("BEACON_AI_TEST_CONNECTION")
        print(f"   Successfully verified/created test folder ID: {folder_id}")
        
    except Exception as e:
        print(f"❌ Drive Access Failed: {e}")

if __name__ == "__main__":
    asyncio.run(validate_connections())
