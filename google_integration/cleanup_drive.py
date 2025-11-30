import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from google_integration.auth import GoogleAuthManager
from rich import print as rprint

def cleanup_drive():
    rprint("[bold yellow]Starting Service Account Drive Cleanup...[/bold yellow]")

    try:
        auth_manager = GoogleAuthManager()
        drive_service = auth_manager.get_service("drive", "v3")
        
        # 1. Empty Trash
        rprint("[yellow]Emptying Trash...[/yellow]")
        try:
            drive_service.files().emptyTrash().execute()
            rprint("[green]✔ Trash emptied.[/green]")
        except Exception as e:
            rprint(f"[red]✘ Failed to empty trash: {e}[/red]")

        # 2. List Files Owned by Service Account
        rprint("\n[yellow]Scanning files owned by Service Account...[/yellow]")
        # 'me' in owners checks for files owned by the service account
        query = "'me' in owners and trashed=false"
        results = drive_service.files().list(
            q=query, 
            fields="files(id, name, quotaBytesUsed, createdTime)"
        ).execute()
        files = results.get("files", [])

        rprint(f"[cyan]Found {len(files)} files owned by this account.[/cyan]")
        
        total_size = 0
        for f in files:
            size = int(f.get('quotaBytesUsed', 0))
            total_size += size
            size_mb = size / (1024 * 1024)
            
            msg_color = "white"
            if size_mb > 10: msg_color = "red"
            
            rprint(f" - [{msg_color}]{f['name']}[/{msg_color}] (ID: {f['id']}) - {size_mb:.2f} MB")

            # Auto-delete known junk/test files
            if f['name'] in ['permission_test_dummy.txt', 'BEACON_AI_CONNECTION_TEST', 'TEST_SHEET', 'Beacon Personal Budget']:
                 rprint(f"   [bold red]Deleting junk/duplicate file: {f['name']}...[/bold red]")
                 drive_service.files().delete(fileId=f['id']).execute()
                 rprint("     ✔ Deleted.")

        rprint(f"\n[bold]Total Quota Used: {total_size/(1024*1024):.2f} MB[/bold]")
        rprint("[dim]Note: Google quotas sometimes take a few minutes to update after deletion.[/dim]")

    except Exception as e:
        rprint(f"[bold red]Critical Error:[/bold red] {e}")

if __name__ == "__main__":
    cleanup_drive()
