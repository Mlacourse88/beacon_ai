import sys
from pathlib import Path
from googleapiclient.errors import HttpError
from rich import print as rprint

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from google_integration.auth import GoogleAuthManager

def test_root_write():
    rprint("[bold yellow]Testing Write to Service Account Root...[/bold yellow]")
    try:
        auth_manager = GoogleAuthManager()
        drive_service = auth_manager.get_service("drive", "v3")

        # Try to create a file with NO parents (Root)
        file_metadata = {
            'name': 'ROOT_TEST_FILE.txt',
            'mimeType': 'text/plain'
        }
        
        rprint("Attempting to create 1-byte file in Root...")
        
        # Create metadata only (empty file)
        file = drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()

        rprint(f"[green]✔ SUCCESS! Created file ID: {file.get('id')}[/green]")
        
        # Cleanup
        drive_service.files().delete(fileId=file.get('id')).execute()
        rprint("[green]✔ Cleanup: Deleted test file.[/green]")
        rprint("\n[bold green]CONCLUSION:[/bold green] The Robot CAN write files. The issue is likely permissions/quota on the Shared Folder specifically.")

    except HttpError as e:
        rprint(f"[bold red]✘ FAILED:[/bold red] {e}")
        if "storageQuotaExceeded" in str(e):
             rprint("\n[bold red]CONCLUSION:[/bold red] The Robot has ZERO storage capability. It cannot create files.")
             rprint("WORKAROUND: You must create the Google Sheet manually in your Drive, Share it with the Robot, and give the Robot the ID.")

if __name__ == "__main__":
    test_root_write()
