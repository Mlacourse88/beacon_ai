import datetime
from typing import List, Dict, Any, Optional
from googleapiclient.errors import HttpError
from shared_utils import setup_logging
from .auth import GoogleAuthManager

logger = setup_logging("BudgetTracker")

class BudgetTracker:
    """
    Manages a personal budget in Google Sheets.
    Handles Income, Debts, Credit Cards, Expenses, and Summaries.
    """
    
    # HARDCODED SPREADSHEET ID (Existing Sheet)
    SPREADSHEET_ID = "1DbeupYgSP5M0QwMvNIw8_dyKZlIB9CBd1dtXqP3s-iQ"

    def __init__(self, auth_manager: GoogleAuthManager, drive_manager=None, spreadsheet_id: Optional[str] = None):
        self.service = auth_manager.get_service('sheets', 'v4')
        self.drive_manager = drive_manager
        # Use passed ID if provided, otherwise fallback to hardcoded
        self.spreadsheet_id = spreadsheet_id or self.SPREADSHEET_ID
        self.fixed_income = 2148.00 

    async def create_budget_spreadsheet(self, title: str = "Beacon Personal Budget") -> Optional[str]:
        """
        Deprecated: We are using a hardcoded existing sheet. 
        Returns the existing ID.
        """
        logger.info(f"Using existing Hardcoded Spreadsheet: {self.SPREADSHEET_ID}")
        return self.SPREADSHEET_ID

    async def add_expense(self, category: str, amount: float, date_str: str, note: str = "") -> bool:
        """Adds an expense row to the 'Monthly Expenses' sheet."""
        if not self.spreadsheet_id: return False
        
        values = [[category, amount, date_str, note]]
        body = {'values': values}
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id, 
                range="Monthly Expenses!A:D", 
                valueInputOption="USER_ENTERED", 
                body=body
            ).execute()
            logger.info(f"Added expense: {category} - ${amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add expense: {e}")
            return False

    async def add_income(self, source: str, amount: float, date_str: str, note: str = "") -> bool:
        """Adds an income row to the 'Income' sheet."""
        if not self.spreadsheet_id: return False
        
        values = [[source, amount, date_str, note]]
        body = {'values': values}
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id, 
                range="Income!A:D", 
                valueInputOption="USER_ENTERED", 
                body=body
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add income: {e}")
            return False

    async def get_balance(self) -> Dict[str, Any]:
        """
        Calculates Net Balance based on Expenses vs Fixed Income ($2148).
        Returns dict with raw numbers and a formatted summary string.
        """
        if not self.spreadsheet_id: return {"formatted": "Budget Offline"}
        
        try:
            # Get Expenses
            exp_result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range="Monthly Expenses!B2:B"
            ).execute()
            exp_rows = exp_result.get('values', [])
            total_expenses = 0.0
            for row in exp_rows:
                if row:
                    try:
                        val_str = str(row[0]).replace('$', '').replace(',', '').strip()
                        if val_str:
                            total_expenses += float(val_str)
                    except ValueError: pass

            total_income = self.fixed_income
            remaining = total_income - total_expenses
            
            formatted_str = f"💰 Balance: ${remaining:.2f} (Income: ${total_income:.0f} | Spent: ${total_expenses:.2f})"
            
            return {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "remaining": remaining,
                "formatted": formatted_str
            }
        except Exception as e:
            logger.error(f"Error calculating balance: {e}")
            return {"formatted": "Error Calc Balance", "remaining": 0.0, "total_income": 0.0, "total_expenses": 0.0}

    async def get_budget_overview(self) -> str:
        """Returns the formatted balance string directly."""
        data = await self.get_balance()
        return data.get("formatted", "Budget Unavailable")
