import ephem
import pytz
from datetime import datetime, timedelta, date
import math
from typing import Dict, Any, Optional

class FeastDateCalculator:
    """
    Calculates biblical feast dates based on astronomical observations relative to Jerusalem.
    
    Logic:
    - Uses an astronomical calendar model.
    - Nisan 1 is determined based on the New Moon relative to the Vernal Equinox.
    - Rule used: The month of Nisan is the first lunar month such that the 14th day (Passover) 
      falls on or after the Vernal Equinox. This ensures Passover is in the Spring.
    - Days begin at sunset.
    - Times are calculated for Jerusalem.
    """

    def __init__(self):
        self.jerusalem = ephem.Observer()
        self.jerusalem.lat = '31.7683'
        self.jerusalem.lon = '35.2137'
        self.jerusalem.elevation = 754  # meters
        self.tz = pytz.timezone('Asia/Jerusalem')

    def _get_vernal_equinox(self, year: int) -> ephem.Date:
        """Finds the vernal equinox for the given year."""
        # ephem uses '0' for 1899/1900, so we pass year as string or use constructor
        return ephem.next_spring_equinox(str(year))

    def _find_nisan_one(self, year: int) -> datetime:
        """
        Determines the Gregorian date of Nisan 1 for the given Gregorian year.
        Logic: Find the New Moon that places Passover (Day 14) on or after the Equinox.
        """
        equinox = self._get_vernal_equinox(year)
        
        # Start searching for new moons a bit before the equinox (approx 1 month)
        search_date = ephem.Date(equinox - 30)
        
        while True:
            next_nm = ephem.next_new_moon(search_date)
            # Check if this new moon is the start of Nisan
            # Criterion: Nisan 14 (New Moon + 13 days) >= Equinox
            # Note: Biblical days start at sunset, but for approx matching, we compare float dates
            if (next_nm + 13) >= equinox:
                # Convert ephem date to python datetime
                return next_nm.datetime()
            search_date = next_nm + 1  # Advance search

    def _get_sunset_time(self, target_date: datetime) -> str:
        """Calculates sunset time in Jerusalem for a given date."""
        self.jerusalem.date = target_date
        sunset = self.jerusalem.next_setting(ephem.Sun())
        # Convert to localized datetime
        dt_utc = sunset.datetime().replace(tzinfo=pytz.utc)
        dt_jerusalem = dt_utc.astimezone(self.tz)
        return dt_jerusalem.strftime("%I:%M %p")

    def _get_moon_phase_desc(self, target_date: datetime) -> str:
        """Returns a description of the moon phase."""
        moon = ephem.Moon()
        moon.compute(target_date)
        phase = moon.phase # 0 to 100
        
        # Determine standard description
        # This is approximate based on illumination percentage
        if phase < 2: return "New Moon"
        if phase < 45: return "Waxing Crescent"
        if phase < 55: return "First Quarter"
        if phase < 95: return "Waxing Gibbous"
        if phase > 98: return "Full Moon"
        if phase > 55: return "Waning Gibbous"
        if phase > 45: return "Last Quarter"
        return "Waning Crescent"

    def calculate_feasts(self, year: int) -> Dict[str, Any]:
        """
        Calculates all major biblical feasts for the given Gregorian year.
        Returns a dictionary of feast details.
        """
        # 1. Determine Nisan 1
        nisan_one_dt = self._find_nisan_one(year)
        
        # Helper to create the feast object
        def make_feast_entry(name_eng, name_heb, month_name, day_num, offset_days, duration=1):
            # Calculate date
            start_date_dt = nisan_one_dt + timedelta(days=offset_days)
            
            # Check day of week
            dow = start_date_dt.strftime("%A")
            
            # Sunset logic: The biblical day begins at sunset of the PREVIOUS Gregorian day
            # But typically we list the feast date as the day it is observed during the day.
            # However, precise output requested: "April 2 (begins at sunset April 1)"
            
            prev_day = start_date_dt - timedelta(days=1)
            sunset_time = self._get_sunset_time(prev_day)
            
            greg_str = start_date_dt.strftime("%B %d, %Y")
            prev_greg_str = prev_day.strftime("%B %d")
            
            # Moon Phase
            moon_desc = self._get_moon_phase_desc(start_date_dt)
            
            return {
                "title": f"{name_eng} ({name_heb})",
                "gregorian_date_text": f"{greg_str} (begins at sunset {prev_greg_str})",
                "hebrew_date": f"{day_num} {month_name}",
                "moon_phase": moon_desc,
                "day_of_week": dow,
                "sunset_time": f"~{sunset_time} (Jerusalem time)"
            }

        feasts = {}
        
        # Spring Feasts (Nisan)
        # Passover: Nisan 14
        feasts['Passover'] = make_feast_entry("Passover", "Pesach", "Nisan", 14, 13)
        
        # Unleavened Bread: Nisan 15 (7 days)
        feasts['Unleavened Bread'] = make_feast_entry("Feast of Unleavened Bread", "Chag HaMatzot", "Nisan", 15, 14, duration=7)
        
        # Firstfruits: Day after Sabbath during Unleavened Bread
        # Logic: Find the Saturday within the Unleavened Bread week (Nisan 15-21)
        # Then add 1 day.
        # Note: There are different interpretations (Pharisee vs Sadducee). 
        # Sadducee/Karaite: Sunday after the weekly Sabbath during the feast.
        # Pharisee/Rabbinic: Nisan 16 (Day after the "High Sabbath" of Nisan 15).
        # Given "Biblical/Historical" context often looks at the Sunday resurrection typology, 
        # we will calculate the "Sunday after the Sabbath" (Waving of the Sheaf).
        ub_start = nisan_one_dt + timedelta(days=14) # Nisan 15
        # Find next Sunday
        days_ahead = 6 - ub_start.weekday() # 0=Mon, 6=Sun. If Mon(0), need 6 days to Sun.
        if days_ahead <= 0: days_ahead += 7 # Should not happen if strictly >
        # Actually, if UB starts on Sunday, the Sabbath is the previous day? No, "during" the feast.
        # Simplest Sunday calculation: First Sunday *after* the Sabbath that falls within or immediately after?
        # Let's stick to the Sunday following the weekly Sabbath that occurs during the week of Unleavened Bread.
        # If Nisan 15 is Saturday, Firstfruits is Sunday Nisan 16.
        # If Nisan 15 is Sunday, Sabbath is next Saturday (Nisan 21), Firstfruits is Sunday Nisan 22.
        # Let's find the Sunday after Nisan 14.
        passover_dt = nisan_one_dt + timedelta(days=13) # Nisan 14
        days_to_sunday = 6 - passover_dt.weekday()
        if days_to_sunday == 0: days_to_sunday = 7 
        firstfruits_dt = passover_dt + timedelta(days=days_to_sunday)
        
        offset_ff = (firstfruits_dt - nisan_one_dt).days
        feasts['Firstfruits'] = make_feast_entry("Firstfruits", "Bikkurim", "Nisan", f"{offset_ff + 1} (approx)", offset_ff)

        # Pentecost (Shavuot): 50 days from Firstfruits (inclusive count, so +49 days)
        offset_pent = offset_ff + 49
        feasts['Pentecost'] = make_feast_entry("Pentecost", "Shavuot", "Sivan", "Unknown", offset_pent)

        # Fall Feasts (Tishrei)
        # Tishrei 1 is usually the 7th New Moon. (Nisan + 6 lunations)
        # 1 Lunation approx 29.53 days. 6 * 29.53 = 177.18 days.
        # Let's verify with ephem
        tishrei_one_search = nisan_one_dt + timedelta(days=170)
        tishrei_one_nm = ephem.next_new_moon(ephem.Date(tishrei_one_search))
        tishrei_one_dt = tishrei_one_nm.datetime()
        
        # Calculate offset from Nisan 1 to Tishrei 1 for consistent internal math
        tishrei_offset = (tishrei_one_dt - nisan_one_dt).days

        # Trumpets: Tishrei 1
        feasts['Trumpets'] = make_feast_entry("Feast of Trumpets", "Yom Teruah", "Tishrei", 1, tishrei_offset)

        # Atonement: Tishrei 10
        feasts['Atonement'] = make_feast_entry("Day of Atonement", "Yom Kippur", "Tishrei", 10, tishrei_offset + 9)

        # Tabernacles: Tishrei 15 (7 days)
        feasts['Tabernacles'] = make_feast_entry("Feast of Tabernacles", "Sukkot", "Tishrei", 15, tishrei_offset + 14, duration=7)

        # Last Great Day: Tishrei 22
        feasts['Last Great Day'] = make_feast_entry("The Last Great Day", "Shemini Atzeret", "Tishrei", 22, tishrei_offset + 21)

        return feasts

if __name__ == "__main__":
    # Quick Test
    calc = FeastDateCalculator()
    res = calc.calculate_feasts(2026)
    print("Passover 2026:", res['Passover'])
