import sys
from pathlib import Path
import json

# Add project root to path so we can import our modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from google_integration.auth import GoogleAuthManager
from googleapiclient.errors import HttpError
from rich import print as rprint

def debug_permissions():
    rprint("[bold yellow]Starting Google Drive Permission Debugger...[/bold yellow]")

    # 1. Authenticate
    try:
        auth_manager = GoogleAuthManager()
        drive_service = auth_manager.get_service("drive", "v3")
        rprint("[green]✔ Authenticated with Drive API.[/green]")
        
        # Get Service Account Email from creds
        service_account_email = auth_manager.creds.service_account_email
        rprint(f"   [dim]Service Account: {service_account_email}[/dim]")

    except Exception as e:
        rprint(f"[bold red]✘ Authentication Failed:[/bold red] {e}")
        return

    # 2. Search for BEACON_AI Folder
    folder_name = "BEACON_AI"
    try:
        # Query for folder
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])

        if not folders:
            rprint(f"[bold red]✘ Folder '{folder_name}' NOT FOUND.[/bold red]")
            rprint("   Please create this folder in your Drive and share it with the service account.")
            return

        folder_id = folders[0]['id']
        rprint(f"[green]✔ Found Folder '{folder_name}': {folder_id}[/green]")

    except Exception as e:
        rprint(f"[bold red]✘ Search Failed:[/bold red] {e}")
        return

    # 3. Check Permissions
    try:
        rprint(f"[yellow]Checking permissions for folder {folder_id}...[/yellow]")
        permissions_result = drive_service.permissions().list(
            fileId=folder_id, fields="permissions(type, emailAddress, role)"
        ).execute()
        permissions = permissions_result.get("permissions", [])

        found_myself = False
        for perm in permissions:
            email = perm.get('emailAddress', 'N/A')
            role = perm.get('role', 'N/A')
            
            if email == service_account_email:
                found_myself = True
                color = "green" if role in ['owner', 'writer', 'organizer', 'fileOrganizer'] else "red"
                rprint(f"   - [bold {color}]ME ({email}): {role}[/bold {color}]")
            else:
                rprint(f"   - {email}: {role}")

        if not found_myself:
            rprint(f"[bold red]✘ Service Account ({service_account_email}) is NOT in the permission list![/bold red]")
            rprint("   Action: Share the 'BEACON_AI' folder with this email as 'Editor'.")
        
    except Exception as e:
        rprint(f"[bold red]✘ Permission Check Failed:[/bold red] {e}")

    # 4. Test Write (Create Dummy File)
    try:
        rprint(f"[yellow]Attempting to write a test file into '{folder_name}'...[/yellow]")
        file_metadata = {
            'name': 'permission_test_dummy.txt',
            'parents': [folder_id]
        }
        # Using media_body is optional for empty files, creating strictly metadata based file first to test permission
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        rprint(f"[green]✔ WRITE SUCCESS! Created file ID: {file.get('id')}[/green]")
        
        # Cleanup
        drive_service.files().delete(fileId=file.get('id')).execute()
        rprint("[green]✔ Cleanup: Deleted test file.[/green]")

    except HttpError as e:
        if e.resp.status == 403:
            rprint("[bold red]✘ WRITE FAILED (403 Forbidden).[/bold red]")
            rprint("   The Service Account has 'Viewer' access but needs 'Editor' access.")
        else:
            rprint(f"[bold red]✘ Write Error:[/bold red] {e}")
    except Exception as e:
        rprint(f"[bold red]✘ Unexpected Write Error:[/bold red] {e}")

if __name__ == "__main__":
    debug_permissions()
