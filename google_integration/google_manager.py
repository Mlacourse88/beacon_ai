import asyncio
import json
from pathlib import Path
from typing import Dict, Optional

from shared_utils import setup_logging, get_project_root

from .auth import GoogleAuthManager
from .calendar_sync import CalendarSync
from .budget_tracker import BudgetTracker
from .docs_generator import DocsGenerator
from .drive_manager import DriveManager

logger = setup_logging("GoogleManager")

CONFIG_FILE = "google_config.json"

class GoogleManager:
    """
    Unified facade for all Google Workspace integrations.
    """

    def __init__(self, credentials_file: str = "geminicli_oauth_credentials.json"):
        self.auth = GoogleAuthManager(credentials_file)
        
        # Initialize subsystems
        self.calendar = CalendarSync(self.auth)
        self.docs = DocsGenerator(self.auth)
        self.drive = DriveManager(self.auth)
        
        # Load config for Sheets ID
        self.config_path = get_project_root() / CONFIG_FILE
        self.config = self._load_config()
        
        sheet_id = self.config.get('budget_spreadsheet_id')
        self.budget = BudgetTracker(self.auth, drive_manager=self.drive, spreadsheet_id=sheet_id)

    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    async def initialize_system(self):
        """Performs first-time setup."""
        logger.info("Initializing Google System...")
        
        # 1. Setup Drive Folders
        await self.drive.initialize_folder_structure()
        
        # 2. Setup Budget Sheet if missing
        if not self.budget.spreadsheet_id:
            sheet_id = await self.budget.create_budget_spreadsheet()
            if sheet_id:
                self.config['budget_spreadsheet_id'] = sheet_id
                self._save_config()
                
                # Move sheet to Budget folder
                budget_folder_id = self.drive.folder_ids.get('Budget_Sheets')
                if budget_folder_id:
                    # Note: Moving files requires 'files.update' with addParents/removeParents
                    pass # Placeholder for move logic
            else:
                logger.warning("Budget functionality disabled due to creation failure (likely storage quota).")
                
        logger.info("System Initialization Complete.")

    async def generate_daily_briefing_workflow(self) -> str:
        """
        Orchestrates the daily briefing generation.
        1. Get Calendar events.
        2. Get Budget overview (optional).
        3. Create Doc.
        4. Return link.
        """
        events = await self.calendar.get_upcoming_events(days=3)
        # Simulated news data
        news = {"world": "Global markets stable.", "local": "Green Springs council meeting tonight."}
        
        doc_id = await self.docs.generate_daily_briefing(
            date_str=asyncio.get_event_loop().time(), # Just a placeholder
            news_data=news,
            events=events
        )
        return f"https://docs.google.com/document/d/{doc_id}"

    async def process_voice_command(self, transcript: str) -> str:
        """
        Entry point for parsed voice commands.
        """
        # In a real scenario, NLP analysis determines the route.
        # Here we demonstrate direct mapping.
        if "schedule" in transcript.lower():
            parsed = await self.calendar.parse_natural_language_event(transcript)
            if parsed:
                await self.calendar.create_event(**parsed)
                return f"Scheduled: {parsed['summary']}"
        
        return "Command not recognized."
