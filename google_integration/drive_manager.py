import io
from typing import List, Dict, Optional
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from shared_utils import setup_logging
from .auth import GoogleAuthManager

logger = setup_logging("DriveManager")

class DriveManager:
    """
    Manages Google Drive files and folders.
    Structure:
    /BEACON_AI/
       /Budget_Sheets/
       /Daily_Briefings/
       /Voice_Transcripts/
       /Reports/
       /Backups/
    """

    ROOT_FOLDER_NAME = "BEACON_AI"
    
    SUBFOLDERS = [
        "Budget_Sheets",
        "Daily_Briefings", 
        "Voice_Transcripts",
        "Reports",
        "Backups"
    ]

    def __init__(self, auth_manager: GoogleAuthManager):
        self.service = auth_manager.get_service('drive', 'v3')
        self.folder_ids = {} # Cache for folder IDs

    async def initialize_folder_structure(self):
        """Ensures the required folder structure exists."""
        root_id = await self._get_or_create_folder(self.ROOT_FOLDER_NAME)
        self.folder_ids['root'] = root_id
        
        for folder_name in self.SUBFOLDERS:
            f_id = await self._get_or_create_folder(folder_name, parent_id=root_id)
            self.folder_ids[folder_name] = f_id

    async def _get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Finds or creates a folder."""
        query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create if not exists
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            metadata['parents'] = [parent_id]
            
        folder = self.service.files().create(body=metadata, fields='id').execute()
        logger.info(f"Created folder: {name} ({folder.get('id')})")
        return folder.get('id')

    async def upload_file(self, file_path: str, folder_name: str = None) -> str:
        """Uploads a local file to a specific Drive folder."""
        from pathlib import Path
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"{file_path} does not exist")
            
        parent_id = self.folder_ids.get(folder_name, self.folder_ids.get('root'))
        
        metadata = {'name': path_obj.name}
        if parent_id:
            metadata['parents'] = [parent_id]
            
        media = MediaFileUpload(file_path, resumable=True)
        
        file = self.service.files().create(
            body=metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        
        logger.info(f"Uploaded {path_obj.name} to Drive (ID: {file.get('id')})")
        return file.get('id')
