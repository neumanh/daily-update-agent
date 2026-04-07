import os
from typing import List, Optional

import requests
from openai import OpenAI
from dotenv import load_dotenv

from email_tools import send_email


# Load environment variables
load_dotenv()


# --- Constants ---
MODEL_NAME = "gpt-5-mini"
SEFARIA_URL = "https://www.sefaria.org/api/calendars"
ALIYAH_NAMES = {
    "1": "Rishon",   "2": "Sheni",   "3": "Shlishi",
    "4": "Revi'i",   "5": "Chamishi", "6": "Shishi",
    "7": "Shvi'i",   "M": "Maftir",
}

# Initialize OpenAI client once (reuse across calls)
_OPENAI_CLIENT: Optional[OpenAI] = None


def _get_openai_client() -> OpenAI:
    """
    Lazily initialize and return OpenAI client.

    Returns:
        OpenAI: Configured OpenAI client

    Raises:
        ValueError: If API key is missing
    """
    global _OPENAI_CLIENT

    if _OPENAI_CLIENT is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")

        _OPENAI_CLIENT = OpenAI(api_key=api_key)

    return _OPENAI_CLIENT


def get_chatgpt_response(prompt: str) -> str:
    """
    Generate a Hebrew-only response from the language model.

    Args:
        prompt (str): Input prompt

    Returns:
        str: Model response (plain text)

    Raises:
        RuntimeError: If API call fails or response is empty
    """
    client = _get_openai_client()

    # Enforce output constraints
    full_prompt = (
        f"{prompt}\n\n"
        "Output format: plain text answer only. "
        "Reply in Hebrew only (no English words)."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": full_prompt}],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Empty response from model")

        return content

    except Exception as e:
        raise RuntimeError(f"OpenAI request failed: {e}") from e


def get_empowering_message() -> str:
    """
    Generate a short empowering message.

    Returns:
        str: Hebrew uplifting message
    """
    prompt = (
        "Write a short empowering message dedicated to Hadas. "
        "Make it uplifting, inspiring, and strengthen her confidence."
    )

    return get_chatgpt_response(prompt)


def send_a_joke(email_address: str, key_words: Optional[List[str]] = None) -> None:
    """
    Generate and send a funny message via email.

    Args:
        email_address (str): Recipient email
        key_words (Optional[List[str]]): Topics to include in the joke
    """
    prompt = "Write a funny joke."

    if key_words:
        key_words_str = ", ".join(key_words)
        prompt += f"\n\nRelate the joke to these topics: {key_words_str}."

    joke = get_chatgpt_response(prompt)

    send_email(
        address=email_address,
        subject="בדיחה סופר סודית",
        body=joke
    )


def get_dvar_torah() -> str:
    """
    Generate a short Dvar Torah based on the weekly Parasha.

    Returns:
        str: Hebrew Dvar Torah

    Raises:
        RuntimeError: If Parasha cannot be retrieved
    """
    parasha = get_parasha_sefaria()
    if not parasha:
        raise RuntimeError("Could not retrieve weekly Parasha")

    prompt = f"Write a very short Dvar Torah about this week's Parasha: {parasha}."

    return get_chatgpt_response(prompt)


def get_parasha_sefaria() -> Optional[str]:
    """
    Fetch the weekly Parasha from Sefaria API.

    Returns:
        Optional[str]: Ready-to-use string like:
            - "Shmini (שמיני), part Rishon"  (weekday reading)
            - "Shmini (שמיני)"               (Shabbat - full parasha)
            - None if not found or request fails.
    """
    try:
        response = requests.get(SEFARIA_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for item in data.get("calendar_items", []):
            if item.get("title", {}).get("en") == "Parashat Hashavua":
                pr_value = item.get("displayValue", {})
                parasha = f"{pr_value.get('en')} ({pr_value.get('he')})"

                order = str(item.get("order", ""))
                parasha_part = ALIYAH_NAMES.get(order)

                if parasha_part:
                    return f"{parasha}, part {parasha_part}"
                return parasha

    except requests.RequestException:
        return None

    return None


if __name__ == "__main__":
    print(get_parasha_sefaria())