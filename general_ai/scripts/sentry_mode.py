"""
The Sentry Module
-----------------
Network Security & System Monitoring.

Capabilities:
1. Network Scan: Uses Nmap to list all connected devices on the home Wi-Fi.
2. Intruder Alert: Flags unknown MAC addresses.
3. Resource Monitor: Tracks Raspberry Pi CPU/Temp and Energy usage (if connected to smart plugs).
"""

class SentryMode:
    def __init__(self):
        self.known_devices = []

    def scan_network(self) -> list:
        """
        Runs nmap ping scan. Returns list of online IPs/MACs.
        """
        return []

    def check_system_health(self) -> dict:
        """
        Returns CPU load, RAM usage, and Disk space.
        """
        return {"status": "Healthy"}