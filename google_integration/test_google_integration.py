import unittest
import datetime
from unittest.mock import MagicMock, patch
import asyncio

# Import modules to test
from google_integration.calendar_sync import CalendarSync
from google_integration.budget_tracker import BudgetTracker

class TestGoogleIntegration(unittest.TestCase):

    def setUp(self):
        self.mock_auth = MagicMock()
        self.mock_service = MagicMock()
        self.mock_auth.get_service.return_value = self.mock_service

    def test_calendar_parsing(self):
        """Test the regex/NLP parsing for calendar events."""
        cal = CalendarSync(self.mock_auth)
        
        # We need to run the async method in a loop
        query = "Schedule Dentist appointment next Tuesday at 2pm"
        result = asyncio.run(cal.parse_natural_language_event(query))
        
        self.assertEqual(result['summary'], "Dentist appointment")
        self.assertTrue(isinstance(result['start_time'], datetime.datetime))
        
    def test_budget_overview(self):
        """Test budget calculation logic."""
        tracker = BudgetTracker(self.mock_auth, spreadsheet_id="123")
        
        # Mock the API response for getting values
        mock_values = self.mock_service.spreadsheets().values().get().execute.return_value
        mock_values.get.return_value = [['$50.00'], ['$10.00']] # Mock expenses
        
        result = asyncio.run(tracker.get_budget_overview())
        
        self.assertEqual(result['total_expenses'], 60.00)

if __name__ == '__main__':
    unittest.main()
