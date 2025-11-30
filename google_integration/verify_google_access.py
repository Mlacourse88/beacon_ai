import sys
from pathlib import Path

# Add project root to path so we can import our modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from google_integration.auth import GoogleAuthManager
from googleapiclient.errors import HttpError
from rich import print as rprint

def verify_access():
    rprint("[bold yellow]Starting Google Cloud Connectivity Check...[/bold yellow]")

    # 1. Test Authentication
    try:
        auth_manager = GoogleAuthManager()
        rprint("[green]✔ Authentication initialized successfully.[/green]")
    except Exception as e:
        rprint(f"[bold red]✘ Authentication Failed:[/bold red] {e}")
        return

    # 2. Test Drive API (List Files)
    try:
        drive_service = auth_manager.get_service("drive", "v3")
        # Try to list up to 5 files
        results = drive_service.files().list(
            pageSize=5, fields="nextPageToken, files(id, name)"
        ).execute()
        files = results.get("files", [])
        
        rprint(f"[green]✔ Drive API Connected. Found {len(files)} files.[/green]")
        if files:
            rprint(f"   [dim]First file: {files[0]['name']} (ID: {files[0]['id']})[/dim]")
            
    except HttpError as e:
        if e.resp.status == 403:
            rprint("[bold red]✘ Drive API Permission Error (403).[/bold red]")
            rprint("  - Ensure 'Google Drive API' is ENABLED in Cloud Console.")
        else:
            rprint(f"[bold red]✘ Drive API Error:[/bold red] {e}")
    except Exception as e:
        rprint(f"[bold red]✘ Drive API Unexpected Error:[/bold red] {e}")

    # 3. Test Sheets API (Create Sheet)
    try:
        sheets_service = auth_manager.get_service("sheets", "v4")
        sheet_body = {
            "properties": {
                "title": "BEACON_AI_CONNECTION_TEST"
            }
        }
        request = sheets_service.spreadsheets().create(body=sheet_body)
        response = request.execute()
        
        spreadsheet_id = response.get('spreadsheetId')
        rprint(f"[green]✔ Sheets API Connected. Created test sheet.[/green]")
        rprint(f"   [dim]Sheet ID: {spreadsheet_id}[/dim]")
        
        # Cleanup: Delete the test sheet (requires Drive scope)
        try:
            drive_service.files().delete(fileId=spreadsheet_id).execute()
            rprint("[green]✔ Cleanup: Test sheet deleted successfully.[/green]")
        except Exception:
            rprint("[yellow]⚠ Warning: Could not delete test sheet automatically. You may delete 'BEACON_AI_CONNECTION_TEST' manually from Drive.[/yellow]")

    except HttpError as e:
        if e.resp.status == 403:
            rprint("[bold red]✘ Sheets API Permission Error (403).[/bold red]")
            rprint("  - Ensure 'Google Sheets API' is ENABLED in Cloud Console.")
        else:
            rprint(f"[bold red]✘ Sheets API Error:[/bold red] {e}")
    except Exception as e:
        rprint(f"[bold red]✘ Sheets API Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    verify_access()
