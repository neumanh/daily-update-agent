# Emailer Agent

A personal update agent that composes weather, finance, and inspirational messages, then sends them by email.

## What this project does

- Uses OpenAI to generate Hebrew-only messages.
- Fetches weather forecasts with Open-Meteo.
- Reads financial data via Yahoo Finance.
- Sends email updates through Gmail SMTP.
- Supports multiple recipient email tools.

## Requirements

- Python 3.10+
- `requirements.txt` includes all required dependencies.

## Setup

1. Create and activate a Python environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with the required variables.

## Environment variables

Required values:

- `OPENAI_API_KEY`
- `SMTP_PASSWORD`
- `MY_EMAIL`
- `HALLELS_EMAIL`
- `MICHAELS_EMAIL`
- `ISRAELS_EMAIL`
- `DEFAULT_LOCATION`

Example `.env`:

```env
OPENAI_API_KEY=your-openai-key
SMTP_PASSWORD=your-gmail-app-password
MY_EMAIL=your.email@example.com
HALLELS_EMAIL=hallel@example.com
MICHAELS_EMAIL=michael@example.com
ISRAELS_EMAIL=israel@example.com
DEFAULT_LOCATION=Ramat Gan, Israel
```

## Run

From the project root:

```bash
python -u agent.py
```

Or use the bundled batch file on Windows:

```powershell
./run_agent.bat
```

## Notes

- The project loads environment variables using `python-dotenv`.
- `weather_tools.py` uses `DEFAULT_LOCATION` to resolve location coordinates.
- Gmail SMTP typically requires an app password and TLS.
