import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

from finance_tools import get_ta125_change
from weather_tools import get_weather_interval, when_will_it_rain_tomorrow
from gpt_tools import get_empowering_message, get_dvar_torah
import email_tools as eu


# Load environment variables
load_dotenv()


# --- Tool registration ---
def build_tools():
    """
    Wrap all available functions as agent tools.

    Returns:
        list: List of function_tool-wrapped callables
    """
    return [
        function_tool(get_ta125_change),
        function_tool(get_weather_interval),
        function_tool(when_will_it_rain_tomorrow),
        function_tool(get_empowering_message),
        function_tool(get_dvar_torah),

        # Email tools
        function_tool(eu.send_update_email_to_myself),
        function_tool(eu.send_update_email_to_hallel),
        function_tool(eu.send_update_email_to_michael),
        function_tool(eu.send_update_email_to_israel),
        function_tool(eu.send_update_email_to_yehonatan),
    ]


# --- Agent definition ---
def build_agent() -> Agent:
    """
    Create and configure the main agent.

    Returns:
        Agent: Configured agent instance
    """
    return Agent(
        name="Update Agent",
        instructions=(
            "You generate thoughtful daily updates.\n"
            "You MUST send all outputs via email tools and NEVER return text directly.\n"
            "You may include: weather updates, financial updates, jokes, empowering messages, or Dvar Torah.\n"
            "Only use tools for factual data. Do not invent facts.\n"
            "Always reply in Hebrew only."
        ),
        tools=build_tools(),
    )


# --- Agent tasks ---
async def run_hadas_agent(agent: Agent):
    """
    Generate and send a daily update to Hadas.
    """
    prompt = (
        "Create a warm, informative, and empowering update.\n"
        "Send it using send_update_email_to_myself.\n\n"
        "Rules:\n"
        "1. Do NOT return the update as text.\n"
        "2. If tomorrow's weather is rainy or significantly different, include weather info.\n"
        "3. If the stock market changed significantly, include financial info.\n"
        "4. Use tools for all real data.\n"
        "5. Optionally include a Dvar Torah or empowering message if it adds value."
    )

    await Runner.run(agent, prompt)


async def run_family_agent(agent: Agent):
    """
    Send personalized uplifting messages to each child.
    """
    prompt = (
        "Write a short, uplifting message to each child:\n"
        "- Michael\n"
        "- Yehonatan\n"
        "- Israel\n"
        "- Hallel\n\n"
        "Each message must be sent via the appropriate email tool.\n\n"
        "Guidelines:\n"
        "- Tailor content to their interests:\n"
        "  * Hallel: cats, MikMak, jokes\n"
        "  * Israel: animals and history of weapons\n"
        "  * Michael: high level architecture, history, archaeology\n"
        "  * Yehonatan: history, geography of Israel\n"
        "- Include something interesting or educational.\n"
        "- You may include a joke, Dvar Torah, or empowering message.\n"
        "- Do not return text directly.\n"
        "- Use tools when needed.\n"
        "- Hebrew only."
    )

    await Runner.run(agent, prompt)


# --- Main runner ---
async def main():
    """
    Run all agent workflows with isolated error handling.
    """
    agent = build_agent()

    tasks = [
        ("hadas_agent", run_hadas_agent),
        ("family_agent", run_family_agent),
    ]

    for name, task in tasks:
        try:
            await task(agent)
        except Exception as e:
            error_message = f"Error in {name}: {e}"
            print(error_message)
            eu.send_error_update(error_message)


if __name__ == "__main__":
    asyncio.run(main())
    print("Done.")