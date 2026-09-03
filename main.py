import json
import os
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI
from query_router import get_filtered_tool_schemas
from tools import AVAILABLE_TOOLS, tools_schema

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("DEEPSEEK_API_KEY not found in .env file.")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
MODEL_NAME = "deepseek-chat"

# --- ANSI PALETTE & BANNER CONFIGURATION ---
CYAN = "\033[96m"
RED = "\033[91m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

BANNER = rf"""{RED}{BOLD}
  ██████╗  █████╗ ███╗   ██╗██████╗ ██╗ ██████╗ ██████╗ 
  ██╔══██╗██╔══██╗████╗  ██║██╔══██╗██║██╔═══██╗██╔══██╗
  ██████╔╝███████║██╔██╗ ██║██║  ██║██║██║   ██║██████╔╝
  ██╔═══╝ ██╔══██║██║╚██╗██║██║  ██║██║██║   ██║██╔══██╗
  ██║     ██║  ██║██║ ╚████║██████╔╝██║╚██████╔╝██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═╝{RESET}
{GREY}  ENGINE: KERES CORE // TACTICAL OSINT & TELEMETRY HUB
  STATUS: ACTIVE // MODEL: DEEPSEEK-CHAT // SEC: LEVEL 4{RESET}
"""


def show_banner():
    print(BANNER)
    print(f"{GREY}" + "═" * 64 + f"{RESET}")
    print(f"{BOLD} Type your query below (or 'exit' / 'q' to disconnect).{RESET}\n")


SYSTEM_PROMPT = """You are PANDIOR-KERES, an autonomous tactical intelligence and OSINT engine. Your objective is high-precision factual synthesis using deterministic tools.

Operational Rules:
1. Tool Selection Hierarchy:
   - Always call dedicated API tools FIRST (e.g., AeroAPI for flights, DNS recon for network domains) before attempting web searches.
   - Use web search ('search_web') ONLY as a fallback or for contextual details (fares, news, local road conditions).
   
2. Search Constraint & Anti-Loop Policy:
   - Never execute more than 2 web searches for the same entity or topic.
   - If an API or search returns an empty result, an error, or a cancellation, DO NOT guess hex codes, registrations, or repeat similar search variations. State the limitation and proceed.
   
3. Synthesis Standards:
   - Distinguish strictly between verified telemetry (API outputs) and estimated or third-party claims (web snippets).
   - Format outputs cleanly using Markdown tables and bullet points for metrics (flight delay minutes, coordinates, fares, IPs).
   - Never invent flights, dates, or transponder codes. If a flight is inactive or cancelled, state it directly.
"""


def ask_agent(user_query: str, max_turns: int = 6) -> str:
    """Executes the agent loop with a circuit-breaker to prevent infinite search cycles."""
    messages: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    active_tools = get_filtered_tool_schemas(user_query, tools_schema)
    print(f"\n[Agent] Active Tools: {[t['function']['name'] for t in active_tools]}")

    turns = 0
    while turns < max_turns:
        turns += 1
        kwargs: dict[str, Any] = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.2,
        }

        if active_tools:
            kwargs["tools"] = active_tools  # type: ignore[assignment]
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            return msg.content or "No response generated."

        messages.append(msg)

        for tc in tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            if fn_name in AVAILABLE_TOOLS:
                try:
                    tool_output = AVAILABLE_TOOLS[fn_name](**fn_args)
                except Exception as err:
                    tool_output = json.dumps({"error": f"Error running {fn_name}: {err}"})
            else:
                tool_output = json.dumps({"error": f"Tool {fn_name} not found."})

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": fn_name,
                "content": tool_output,
            })

    # Hard circuit breaker
    print(f"  ⚠️ [Agent] Max iteration limit ({max_turns}) reached. Forcing synthesis...")
    messages.append({
        "role": "user",
        "content": (
            "You have reached your maximum retrieval steps. Stop using tools immediately. "
            "Synthesize a direct, transparent answer right now based only on the data retrieved so far."
        ),
    })

    final_res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.2,
    )
    return final_res.choices[0].message.content or "No response generated."


def main():
    show_banner()

    while True:
        try:
            prompt = input(f"{BOLD}PANDIOR-KERES{RESET} > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "q", "quit"]:
                print(f"{RED}\n[!] Terminating session. Pandior-Keres offline.{RESET}")
                break

            response = ask_agent(prompt)
            print(f"\n{GREY}" + "─" * 64 + f"{RESET}")
            print(f"{CYAN}{BOLD}INTEL SYNTHESIS:{RESET}")
            print(f"{GREY}" + "─" * 64 + f"{RESET}")
            print(response)
            print(f"{GREY}" + "─" * 64 + f"{RESET}")

        except (KeyboardInterrupt, EOFError):
            print(f"{RED}\n[!] Session interrupted. Pandior-Keres offline.{RESET}")
            break


if __name__ == "__main__":
    main()