import json
import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add project root to path so we can resolve paths correctly
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Define the path to the service account key file (relative to project root)
SERVICE_ACCOUNT_FILE = PROJECT_ROOT / 'service_account_key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def check_project_mismatch():
    """
    Loads service account credentials, prints project_id and client_email,
    and attempts to create a test Google Sheet.
    """
    try:
        # Load service account credentials
        with open(SERVICE_ACCOUNT_FILE, 'r') as f:
            service_account_info = json.load(f)

        # Print project_id and client_email
        project_id = service_account_info.get('project_id')
        client_email = service_account_info.get('client_email')

        print("-" * 30)
        if project_id:
            print(f"Project ID:   {project_id}")
        else:
            print("Error: 'project_id' not found in service account key.")

        if client_email:
            print(f"Client Email: {client_email}")
        else:
            print("Error: 'client_email' not found in service account key.")
        print("-" * 30)

        # Authenticate and build the Sheets service
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        # Attempt to create a test sheet
        spreadsheet_body = {
            'properties': {
                'title': 'TEST_SHEET'
            }
        }
        print("Attempting to create a test Google Sheet...")
        request = service.spreadsheets().create(body=spreadsheet_body)
        response = request.execute()

        sheet_id = response.get('spreadsheetId')
        print(f"SUCCESS: Created Sheet {sheet_id}")

    except FileNotFoundError:
        print(f"Error: Service account file not found at {SERVICE_ACCOUNT_FILE}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {SERVICE_ACCOUNT_FILE}")
    except HttpError as error:
        print(f"Error during Sheets API call: {error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    check_project_mismatch()
