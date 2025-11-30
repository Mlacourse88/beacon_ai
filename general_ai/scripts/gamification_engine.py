"""
Gamification Engine (LifeRPG)
-----------------------------
Backend logic for the Family Achievement System.
Manages XP, Levels, and persistence for the family squad.
"""

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Define Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "general_ai" / "data"
STATS_FILE = DATA_DIR / "family_stats.json"

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GamificationEngine")

class GamificationEngine:
    DEFAULT_USERS = {
        "Micheal": {
            "role": "Commander", 
            "xp": 0, 
            "level": 1, 
            "streak": 0, 
            "badges": [],
            "history": []
        },
        "Hunter": {
            "role": "Guardian", 
            "xp": 0, 
            "level": 1, 
            "streak": 0, 
            "badges": [],
            "history": [],
            "focus": "Allergy Safety"
        },
        "Fiona": {
            "role": "Scholar", 
            "xp": 0, 
            "level": 1, 
            "streak": 0, 
            "badges": [],
            "history": [],
            "focus": "Grades/Reading"
        }
    }

    def __init__(self):
        self._ensure_data_dir()
        self.family_data = self._load_data()

    def _ensure_data_dir(self):
        """Creates the data directory if it doesn't exist."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create data directory: {e}")

    def _load_data(self) -> Dict:
        """Loads family stats from JSON or initializes defaults."""
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r") as f:
                    data = json.load(f)
                    # Validation: Ensure all default users exist
                    valid = True
                    for user in self.DEFAULT_USERS:
                        if user not in data:
                            valid = False
                            break
                    if valid:
                        return data
                    else:
                        logger.warning("Data file missing users. Merging defaults.")
                        for user, stats in self.DEFAULT_USERS.items():
                            if user not in data:
                                data[user] = stats
                        return data

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from {STATS_FILE}: {e}. Resetting DB.")
                self.reset_database()
                return self.DEFAULT_USERS.copy()
            except Exception as e:
                logger.error(f"Unexpected error loading data: {e}. Resetting DB.")
                self.reset_database()
                return self.DEFAULT_USERS.copy()
        
        return self.DEFAULT_USERS.copy()

    def reset_database(self):
        """Backs up corrupt DB and resets to defaults."""
        if STATS_FILE.exists():
            backup_path = STATS_FILE.with_suffix(f".bak.{int(time.time())}")
            try:
                shutil.copy(STATS_FILE, backup_path)
                logger.info(f"Backed up corrupt DB to {backup_path}")
            except Exception as e:
                logger.error(f"Failed to backup DB: {e}")
        
        self.family_data = self.DEFAULT_USERS.copy()
        self._save_data()
        logger.info("Database reset to defaults.")

    def _save_data(self):
        """Persists data to JSON."""
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(self.family_data, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save data to {STATS_FILE}: {e}")

    def calculate_level_threshold(self, level: int) -> int:
        """
        Returns XP needed to reach next level.
        Formula: Current Level * 1000
        """
        return max(1000, level * 1000)

    def award_xp(self, user: str, amount: int, task: str) -> str:
        """
        Adds XP, checks for level up, and saves data.
        Returns a success message describing the event.
        """
        if user not in self.family_data:
            return f"Error: User '{user}' not found."

        profile = self.family_data[user]
        
        profile["xp"] += amount
        profile["history"].append({"task": task, "xp": amount, "timestamp": time.time()})
        
        logger.info(f"Awarding {amount} XP to {user} for '{task}'. Total XP: {profile['xp']}")

        threshold = self.calculate_level_threshold(profile["level"])
        
        message = f"🌟 {user} gained {amount} XP for '{task}'!"
        
        # Check for level up (potentially multiple)
        while profile["xp"] >= threshold:
            profile["level"] += 1
            threshold = self.calculate_level_threshold(profile["level"]) # Recalculate for next loop
            message += f"\n🎉 LEVEL UP! {user} is now Level {profile['level']}!"
            logger.info(f"{user} leveled up to {profile['level']}!")
        
        self._save_data()
        return message

    def get_user_stats(self, user: str) -> Dict:
        """Returns the full profile for a user, or empty dict if not found."""
        return self.family_data.get(user, {})

if __name__ == "__main__":
    # Test Logic
    engine = GamificationEngine()
    print(engine.award_xp("Hunter", 150, "Cleaning Room"))