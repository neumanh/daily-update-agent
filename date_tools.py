import datetime
import requests

from email_tools import send_error_update


def is_tomorrow_working_day() -> tuple[bool, str]:
    """
    Check if tomorrow is a working day in Israel.
    Accounts for Shabbat (Friday sunset to Saturday night) and Jewish holidays.

    Returns:
        tuple: (is_working_day: bool, reason: str)
    """
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return is_working_day(tomorrow)


def is_working_day(date: datetime.date) -> tuple[bool, str]:
    """
    Check if a given date is a working day in Israel.

    Args:
        date: The date to check.

    Returns:
        tuple: (is_working_day: bool, reason: str)
    """
    # Check Shabbat (Saturday = weekday 5)
    if date.weekday() == 5:  # Saturday
        return False, "Shabbat"

    # Check Jewish holidays using the Hebcal API
    holiday = get_jewish_holiday(date)
    if holiday:
        return False, f"Jewish holiday: {holiday}"

    return True, "Regular working day"


def get_jewish_holiday(date: datetime.date) -> str | None:
    """
    Query the Hebcal API for Jewish holidays on a given date.
    Returns the holiday name if found, otherwise None.
    """
    url = "https://www.hebcal.com/hebcal"
    params = {
        "v": "1",
        "cfg": "json",
        "maj": "on",       # Major holidays
        "min": "off",      # Minor holidays
        "mod": "off",      # Modern holidays
        "nx": "off",       # Rosh Chodesh (optional)
        "year": date.year,
        "month": date.month,
        "ss": "off",       # Special Shabbatot
        "mf": "off",       # Minor fasts
        "c": "off",        # Candle lighting times (not needed)
        "geo": "il",       # Israel
        "M": "on",         # Include Hebrew month names
        "s": "off",        # Include Shabbat times (not needed)
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        date_str = date.strftime("%Y-%m-%d")
        for item in data.get("items", []):
            if item.get("date", "").startswith(date_str):
                # Only return items that are actual holidays (not Torah portions etc.)
                category = item.get("category", "")
                if category in ("holiday", "modern-holiday"):
                    return item.get("title", "Unknown holiday")
    except requests.RequestException as e:
        # Don't fail the whole process if the API call fails, just log a warning
        err_str = f"Warning: Could not fetch holiday data: {e}"
        print(err_str)
        send_error_update(err_str)

    return None


if __name__ == "__main__":
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    is_working, reason = is_tomorrow_working_day()
    print(f"Tomorrow ({tomorrow.strftime('%A, %Y-%m-%d')}): "
          f"{'Working day' if is_working else 'Not a working day'} - {reason}")

    # Test a specific date
    test_date = datetime.date(2026, 4, 14)

    print("\n--- Test dates ---")
    is_working, reason = is_working_day(test_date)
    print(f"{test_date.strftime('%A, %Y-%m-%d')}: "
          f"{'Working' if is_working else 'Not working'} - {reason}")
