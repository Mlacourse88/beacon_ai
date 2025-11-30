import datetime
import re
from typing import List, Dict, Optional
from dateutil import parser
import pytz

from shared_utils import setup_logging
from .auth import GoogleAuthManager

logger = setup_logging("CalendarSync")

class CalendarSync:
    """
    Manages Google Calendar operations: sync, create, delete events.
    """

    def __init__(self, auth_manager: GoogleAuthManager, calendar_id: str = 'primary'):
        self.service = auth_manager.get_service('calendar', 'v3')
        self.calendar_id = calendar_id
        self.timezone = pytz.timezone('America/New_York')

    async def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Retrieves upcoming events for the next N days."""
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + 'Z'
        
        try:
            logger.info(f"Fetching events for next {days} days...")
            events_result = self.service.events().list(
                calendarId=self.calendar_id, 
                timeMin=now,
                timeMax=end_date,
                maxResults=50, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} upcoming events.")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []

    async def create_event(self, summary: str, start_time: datetime.datetime, end_time: datetime.datetime, description: str = "") -> Dict:
        """Creates a new calendar event."""
        try:
            # Ensure times are in correct format
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }

            created_event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise e

    async def delete_event(self, event_id: str) -> bool:
        """Deletes an event by ID."""
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            logger.info(f"Event {event_id} deleted.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            return False

    async def parse_natural_language_event(self, query: str) -> Dict:
        """
        Basic natural language parsing for events.
        Example: "Dentist appointment next Tuesday at 2pm"
        
        Note: In a full production system, the LLM would handle this extraction.
        This is a fallback regex/dateutil implementation.
        """
        try:
            # 1. Extract Time/Date
            # We use dateutil.parser fuzzy parsing. It's not perfect but works for "Next Tuesday 2pm"
            # We remove the "Schedule" or "Add" keywords to help parser
            clean_query = re.sub(r'^(schedule|add|create)\s+', '', query, flags=re.IGNORECASE)
            
            # Extract potential summary (everything before keywords like 'on', 'at', 'next')
            # This is a simplified heuristic
            summary_match = re.split(r'\s+(on|at|next|tomorrow|today|in)\s+', clean_query, 1, flags=re.IGNORECASE)
            summary = summary_match[0] if summary_match else clean_query
            
            # Parse date
            # Setting default to now helps resolve relative dates
            dt = parser.parse(clean_query, fuzzy=True, default=datetime.datetime.now())
            
            # Assume 1 hour duration if not specified
            start_time = dt
            end_time = dt + datetime.timedelta(hours=1)
            
            return {
                "summary": summary.strip(),
                "start_time": start_time,
                "end_time": end_time,
                "description": f"Auto-created from query: {query}"
            }
        except Exception as e:
            logger.error(f"NLP Parsing failed: {e}")
            return {}
