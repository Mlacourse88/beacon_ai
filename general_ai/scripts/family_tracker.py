"""
Family & Fleet Tracker Module
-----------------------------
1. GPS DASHBOARD:
   - Integrates with Life360 API or Apple Find My (via iCloud).
   - Privacy: Data stays local.

2. VEHICLE LOG:
   - Tracks '2016 Dodge Grand Caravan'.
   - Maintenance Logic:
     If (Current_Odometer - Last_Oil_Change) > 3000:
         Trigger Alert: "Schedule Oil Change"
"""

class FamilyTracker:
    def __init__(self):
        self.vehicle_stats = {
            "name": "Dodge Grand Caravan",
            "current_odometer": 120600,
            "last_oil_change": 118000,
            "maintenance_interval": 3000
        }

    def get_gps_locations(self) -> dict:
        """
        Fetches coordinates from Life360/iCloud.
        """
        # Placeholder for actual API call
        return {
            "Micheal": {"lat": 0.0, "lon": 0.0, "status": "Home"},
            "Hunter": {"lat": 0.0, "lon": 0.0, "status": "School"},
            "Fiona": {"lat": 0.0, "lon": 0.0, "status": "School"}
        }

    def log_trip(self, distance: float, purpose: str):
        """
        Updates odometer. Checks maintenance triggers.
        """
        self.vehicle_stats["current_odometer"] += distance
        self._check_maintenance()

    def _check_maintenance(self):
        """
        Logic: If current - last > 3000, add to To-Do list.
        """
        miles_since_service = self.vehicle_stats["current_odometer"] - self.vehicle_stats["last_oil_change"]
        if miles_since_service >= self.vehicle_stats["maintenance_interval"]:
            print("ALERT: Oil Change Required!")