import os
from dotenv import load_dotenv
import openmeteo_requests
import pandas as pd
import requests_cache

from retry_requests import retry
from geopy.geocoders import Nominatim

load_dotenv()


def _get_default_location() -> str:
    """Retrieve the default location from environment variables."""
    location = os.getenv("DEFAULT_LOCATION")
    if not location:
        raise ValueError("DEFAULT_LOCATION is not set in environment")
    return location


def get_coordinates(location: str) -> tuple[float, float] | None:
    """
    Convert a human-readable location into geographic coordinates.

    Uses OpenStreetMap (via Nominatim) to geocode a location string.

    Args:
        location (str): A location string such as "Ramat Gan, Israel"
                        or "Paris, France".

    Returns:
        tuple[float, float] | None:
            (latitude, longitude) if found,
            None if the location could not be resolved.
    """
    # Initialize geocoder (user_agent is required by Nominatim)
    geolocator = Nominatim(user_agent="my_geocoder_app")

    # Attempt to geocode the location
    result = geolocator.geocode(location)

    # Handle case where location is not found
    if result is None:
        return None

    return result.latitude, result.longitude


def get_weather_data(
    location: str,
    forecast_days: int,
    past_days: int
) -> pd.DataFrame:
    """
    Retrieve hourly weather data for a given location.

    This function:
    1. Converts the location to coordinates
    2. Calls the Open-Meteo API
    3. Returns structured hourly weather data as a DataFrame

    Args:
        location (str): Location name (e.g., "Ramat Gan, Israel")
        forecast_days (int): Number of future days to include
        past_days (int): Number of past days to include

    Returns:
        pd.DataFrame:
            A DataFrame with columns:
            - date (datetime)
            - temperature_2m (°C)
            - rain (mm)
            - showers (mm)

    Raises:
        ValueError: If the location cannot be geocoded.
    """
    # Step 1: Convert location to coordinates
    coords = get_coordinates(location)
    if coords is None:
        raise ValueError(f"Location '{location}' not found.")
    latitude, longitude = coords

    # Step 2: Configure HTTP client with caching and retry logic
    # - cache reduces API calls
    # - retry improves robustness on network failures
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Step 3: Define API request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        # Order matters! We rely on this later when extracting variables
        "hourly": ["temperature_2m", "rain", "showers"],
        "timezone": "Africa/Cairo",  # close to Israel timezone
        "forecast_days": forecast_days,
        "past_days": past_days,
    }

    # Call API
    responses = openmeteo.weather_api(url, params=params)

    # We only requested one location → take first response
    response = responses[0]

    # Step 4: Extract hourly data
    hourly = response.Hourly()

    # IMPORTANT: indices must match the order in params["hourly"]
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()
    hourly_showers = hourly.Variables(2).ValuesAsNumpy()

    # Step 5: Build time index
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(
                hourly.Time() + response.UtcOffsetSeconds(),
                unit="s",
                utc=True
            ),
            end=pd.to_datetime(
                hourly.TimeEnd() + response.UtcOffsetSeconds(),
                unit="s",
                utc=True
            ),
            freq=pd.Timedelta(hours=1),
            inclusive="left"
        )
    }

    # Step 6: Attach weather variables
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["rain"] = hourly_rain
    hourly_data["showers"] = hourly_showers

    # Convert to DataFrame for easier processing
    return pd.DataFrame(data=hourly_data)


def get_weather_interval(
    location: str = None,
    past_days: int = 2,
    forecast_days: int = 1
) -> dict:
    """
    Aggregate weather data into daily summaries.

    Focuses on daytime hours (08:00–19:59) and returns:
    - Average temperature
    - Total precipitation (rain + showers)

    Args:
        location (str): Location name
        past_days (int): Number of past days
        forecast_days (int): Number of future days

    Returns:
        dict:
            {
                date: {
                    "temperature_2m": "XX°C",
                    "rain": float
                }
            }
    """
    if location is None:
        location = _get_default_location()

    # Get full hourly dataset
    hourly_dataframe = get_weather_data(
        location=location,
        past_days=past_days,
        forecast_days=forecast_days
    )

    # Filter to daytime hours (more relevant for most use cases)
    day_data = hourly_dataframe[
        hourly_dataframe["date"].dt.hour.between(8, 19)
    ]

    # Compute daily averages
    daily_averages = day_data.groupby(
        day_data["date"].dt.date
    ).mean(numeric_only=True)

    # Combine rain and showers into one metric
    daily_averages["rain"] = (
        daily_averages["rain"] + daily_averages["showers"]
    )

    # Improve readability
    daily_averages["rain"] = daily_averages["rain"].round(2)
    daily_averages["temperature_2m"] = (
        daily_averages["temperature_2m"].round()
    )

    # Remove redundant column
    daily_averages = daily_averages.drop(columns=["showers"])

    # Format temperature nicely (e.g., "25°C")
    daily_averages["temperature_2m"] = (
        daily_averages["temperature_2m"]
        .astype(int)
        .astype(str) + "°C"
    )

    return daily_averages.to_dict(orient="index")


def when_will_it_rain_tomorrow(location: str = None) -> dict | None:
    """
    Identify the hours when rain is expected tomorrow.

    Args:
        location (str): Location name

    Returns:
        dict | None:
            Dictionary of rainy hours (HH:MM → index),
            or None if no rain is expected.
    """
    if location is None:
        location = _get_default_location()

    hourly_dataframe = get_weather_data(
        location=location,
        past_days=0,
        forecast_days=1
    )

    # Filter hours with any precipitation
    rainy_hours = hourly_dataframe[
        (hourly_dataframe["rain"] > 0) |
        (hourly_dataframe["showers"] > 0)
    ]

    if rainy_hours.empty:
        return None

    # Return readable hour strings
    return rainy_hours["date"].dt.strftime("%H:%M").to_dict()


if __name__ == "__main__":
    # Simple manual test
    print(f"{get_weather_interval()=}")
