import os
import re
import time

from dotenv import load_dotenv
from openai import APIError, OpenAI

from agents.qualitative import run as run_qualitative
from agents.quantitative import run as run_quantitative
from tokenomics.logger import log as log_tokenomics
from validation.validator import validate_qualitative, validate_quantitative

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


def classify(question: str) -> tuple[str, int, int]:
    text = question.lower()

    quantitative_terms = (
        "total",
        "sum",
        "average",
        "mean",
        "count",
        "how many",
        "trend",
        "amount by",
        "revenue by",
        "sales by",
        "highest",
        "lowest",
        "compare",
        "calculate",
    )

    qualitative_terms = (
        "what does",
        "what is",
        "explain",
        "describe",
        "say about",
        "according to",
        "policy",
        "privacy",
        "bot",
        "document",
    )

    if any(term in text for term in quantitative_terms):
        return "quantitative", 0, 0

    if any(term in text for term in qualitative_terms):
        return "qualitative", 0, 0

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": f"""
Classify this question as exactly one word:
qualitative, quantitative, or both.

Question:
{question}

Return only one word.
""",
            }
        ],
        max_tokens=10,
    )

    output = (response.choices[0].message.content or "").lower()
    match = re.search(r"\b(qualitative|quantitative|both)\b", output)
    route = match.group(1) if match else "qualitative"

    return (
        route,
        response.usage.prompt_tokens if response.usage else 0,
        response.usage.completion_tokens if response.usage else 0,
    )


def run_qualitative_with_retry(question: str) -> dict:
    for attempt in range(3):
        try:
            return run_qualitative(question)
        except APIError as error:
            if attempt == 2:
                return {"status": "MODEL_UNAVAILABLE", "message": str(error)}
            time.sleep(2**attempt)

    return {"status": "MODEL_UNAVAILABLE", "message": "Model request failed."}


def run_quantitative_safely(question: str) -> dict:
    try:
        return run_quantitative(question)
    except APIError as error:
        return {"status": "MODEL_UNAVAILABLE", "message": str(error)}


def validate_qualitative_result(agent_result: dict) -> dict:
    validation = validate_qualitative(
        agent_result.get("answer", ""),
        agent_result.get("chunks", []),
    )
    return {**agent_result, "validation": validation}


def validate_quantitative_result(agent_result: dict) -> dict:
    validation = validate_quantitative(
        answer="",
        sql=agent_result.get("sql", ""),
        validation_status=agent_result.get("status", "ERROR"),
    )
    return {**agent_result, "validation": validation}


def log_manager_usage(question: str, route: str, result: dict) -> dict:
    if route == "both":
        agent_results = [
            result.get("qualitative", {}),
            result.get("quantitative", {}),
        ]
    else:
        agent_results = [result.get("answer", {})]

    input_tokens = int(result.get("manager_input_tokens", 0) or 0)
    output_tokens = int(result.get("manager_output_tokens", 0) or 0)

    for agent_result in agent_results:
        input_tokens += int(agent_result.get("input_tokens", 0) or 0)
        output_tokens += int(agent_result.get("output_tokens", 0) or 0)

    return log_tokenomics(
        query=question,
        agent=f"manager:{route}",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def run(question: str) -> dict:
    route, input_tokens, output_tokens = classify(question)

    result = {
        "route": route,
        "manager_input_tokens": input_tokens,
        "manager_output_tokens": output_tokens,
    }

    if route == "quantitative":
        agent_result = run_quantitative_safely(question)
        result["answer"] = validate_quantitative_result(agent_result)

    elif route == "both":
        qualitative_result = run_qualitative_with_retry(question)
        quantitative_result = run_quantitative_safely(question)

        result["qualitative"] = validate_qualitative_result(qualitative_result)
        result["quantitative"] = validate_quantitative_result(quantitative_result)

    else:
        agent_result = run_qualitative_with_retry(question)
        result["answer"] = validate_qualitative_result(agent_result)

    try:
        result["tokenomics"] = log_manager_usage(question, route, result)
    except OSError as error:
        result["tokenomics_error"] = str(error)

    return result