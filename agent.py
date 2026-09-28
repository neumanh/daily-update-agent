import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool

from date_tools import is_tomorrow_working_day
from finance_tools import get_ta125_change
from weather_tools import get_weather_interval, when_will_it_rain_tomorrow
from gpt_tools import get_empowering_message, get_dvar_torah
import email_tools as eu

# Load environment variables
load_dotenv()


TOPICS_FILE = Path("family_topics.json")


def load_family_topics():
    if not TOPICS_FILE.exists():
        return {
            "Hallel": [],
            "Israel": [],
            "Michael": [],
            "Yehonatan": [],
        }

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_family_topics(topics):
    temp_file = TOPICS_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

    temp_file.replace(TOPICS_FILE)


@function_tool
def record_family_topic(child: str, topic: str):
    """
    Record a topic that was sent to a child so it won't be reused
    in future daily updates.
    """
    topics = load_family_topics()

    if child not in topics:
        topics[child] = []

    topics[child].append(topic)

    # Keep only the 20 most recent topics per child
    topics[child] = topics[child][-20:]

    save_family_topics(topics)

    return f"Recorded topic for {child}: {topic}"


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
        record_family_topic,
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
        "5. Include interesting, educational, or surprising content.\n"
        "6. Optionally include a Dvar Torah or empowering message if it adds value."
    )

    await Runner.run(agent, prompt)


async def run_family_agent(*agent: Agent):
    """
    Send personalized uplifting messages to each child.
    """
    recent_topics = load_family_topics()

    prompt = (
        "Write a short, interesting message to each child.\n"
        "Each message must be sent via the appropriate email tool.\n\n"
        "CONTENT RULES:\n"
        "- Choose a specific, unusual fact or idea related to the child's interests.\n"
        "- Avoid the most obvious or well-known facts about the topic.\n"
        "- Never reuse a recent topic listed below.\n"
        "- Treat closely related facts as the same topic.\n"
        "- The children are teenagers: keep the tone intelligent, mature, interesting, and natural — not childish or cutesy.\n"
        "- Include something genuinely surprising, thought-provoking, or little-known.\n"
        "- Add a warm personal touch from The Cool Family Agent. Be witty when appropriate, but don't force jokes.\n\n"
        
        "INTERESTS — use these as a pool, not as fixed topics:\n"
        "  * Hallel: cats, the MikMak game, farm animal facts\n"
        "  * Israel: gun history, animals, botany\n"
        "  * Michael: architecture, archaeology, ancient civilizations, history, Israeli law\n"
        "  * Yehonatan: countries and flags, world geography, historical events, Jewish settlements in Judea and Samaria\n\n"
       
        "VARIETY:\n"
        "- Choose different interest categories when possible.\n"
        "- Do not always choose the first or most obvious interest listed.\n"
        "- Prefer less commonly known angles and unexpected connections.\n\n"
        f"RECENT TOPICS — do NOT reuse these:\n"
        f"{json.dumps(recent_topics, ensure_ascii=False, indent=2)}\n\n"
        "IMPORTANT WORKFLOW:\n"
        "- For each child, first choose a topic that is not in their recent topics.\n"
        "- Call record_family_topic with the child's name and the chosen topic.\n"
        "- Then send the email using the appropriate email tool.\n"
        "- Do not return text directly.\n"
        "- Use tools when needed.\n"
        "- Hebrew only."
    )

    await Runner.run(*agent, prompt)


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
    # Check if tomorrow is a working day before running the agent
    is_working, _ = is_tomorrow_working_day()
    if is_working:
        asyncio.run(main())
    print("Done.")
