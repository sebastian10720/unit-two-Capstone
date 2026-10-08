import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]
LOG_FILE = PROJECT_DIR / "tokenomics_log.jsonl"

INPUT_COST_PER_1K = float(os.getenv("GEMINI_INPUT_COST_PER_1K", "0"))
OUTPUT_COST_PER_1K = float(os.getenv("GEMINI_OUTPUT_COST_PER_1K", "0"))


def log(query: str, agent: str, input_tokens: int, output_tokens: int) -> dict:
    input_cost = input_tokens / 1000 * INPUT_COST_PER_1K
    output_cost = output_tokens / 1000 * OUTPUT_COST_PER_1K
    total_cost = input_cost + output_cost

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "agent": agent,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(total_cost, 6),
        "cost_per_1000_queries": round(total_cost * 1000, 2),
    }

    print(
        f"\n[TOKENOMICS] Agent: {agent} | "
        f"Input: {input_tokens} | Output: {output_tokens} | "
        f"Estimated cost: ${total_cost:.6f}"
    )

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")

    return entry