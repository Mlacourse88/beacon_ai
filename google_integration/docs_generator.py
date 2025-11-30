from typing import List, Dict, Optional
from shared_utils import setup_logging
from .auth import GoogleAuthManager

logger = setup_logging("DocsGenerator")

class DocsGenerator:
    """
    Generates and manages Google Docs (Reports, Briefings, Transcripts).
    """

    def __init__(self, auth_manager: GoogleAuthManager):
        self.service = auth_manager.get_service('docs', 'v1')
        self.drive_service = auth_manager.get_service('drive', 'v3')

    async def create_document(self, title: str, content: str) -> str:
        """Creates a new document with the given title and content."""
        try:
            # 1. Create blank doc
            doc = self.service.documents().create(body={'title': title}).execute()
            doc_id = doc.get('documentId')
            
            # 2. Insert content
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]
            
            self.service.documents().batchUpdate(
                documentId=doc_id, body={'requests': requests}
            ).execute()
            
            logger.info(f"Created document '{title}' (ID: {doc_id})")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise e

    async def generate_daily_briefing(self, date_str: str, news_data: Dict, events: List[Dict]) -> str:
        """
        Generates a formatted daily briefing document.
        """
        title = f"Daily Briefing - {date_str}"
        
        content = f"BEACON AI - DAILY BRIEFING\nDATE: {date_str}\n\n"
        
        content += "--- UPCOMING EVENTS ---\n"
        if events:
            for event in events:
                start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
                summary = event.get('summary', 'No Title')
                content += f"- {start}: {summary}\n"
        else:
            content += "No events scheduled.\n"
            
        content += "\n--- NEWS SUMMARY ---\n"
        # Placeholder for news integration
        content += "World: " + news_data.get('world', 'No updates') + "\n"
        content += "Local: " + news_data.get('local', 'No updates') + "\n"
        
        return await self.create_document(title, content)

    async def format_voice_transcription(self, raw_text: str) -> str:
        """
        Creates a cleaned up transcript document.
        """
        title = f"Transcript - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        header = "VOICE MEMO TRANSCRIPT\n---------------------\n\n"
        return await self.create_document(title, header + raw_text)
