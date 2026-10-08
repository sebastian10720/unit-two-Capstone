import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from validation.validator import validate_sql

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_DIR / "data" / "database.sqlite"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


def get_schema() -> str:
    with sqlite3.connect(DATABASE_PATH) as connection:
        tables = connection.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

    return "\n\n".join(
        f"Table: {name}\nDefinition: {definition}"
        for name, definition in tables
    )


def extract_sql(text: str) -> str:
    cleaned = re.sub(r"```sql|```", "", text.strip(), flags=re.IGNORECASE)
    match = re.search(r"\b(SELECT|WITH)\b", cleaned, flags=re.IGNORECASE)

    if not match:
        return cleaned.strip()

    sql = cleaned[match.start():].strip()
    return sql.split(";", 1)[0].strip()


def build_prompt(question: str, schema: str, retry: bool = False) -> str:
    correction = (
        "The previous SQL was incomplete. Return a complete query with every "
        "GROUP BY expression finished."
        if retry
        else ""
    )

    return f"""
Convert the user's question into exactly one complete SQLite SELECT query.

{correction}

Rules:
- Return only the SQL query.
- Never return explanations, Markdown, or code fences.
- The query must be complete and executable.
- Use only SELECT or WITH.
- Use only the tables and columns in the schema.
- For "total amount by region", use:
  SELECT region, SUM(amount_usd) AS total_amount
  FROM transactions
  GROUP BY region
- Do not end the query with incomplete keywords such as GROUP BY, WHERE, or ORDER BY.

Schema:
{schema}

User question:
{question}
"""


def request_sql(question: str, schema: str, retry: bool = False) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": build_prompt(question, schema, retry),
            }
        ],
        max_tokens=600,
    )

    return {
        "sql": extract_sql(response.choices[0].message.content or ""),
        "input_tokens": response.usage.prompt_tokens if response.usage else 0,
        "output_tokens": response.usage.completion_tokens if response.usage else 0,
    }


def run(question: str) -> dict:
    if not DATABASE_PATH.exists():
        return {
            "status": "MISSING_DATABASE",
            "message": f"Database not found: {DATABASE_PATH}",
        }

    schema = get_schema()
    total_input_tokens = 0
    total_output_tokens = 0
    validation = {"status": "FAILED", "message": "SQL generation failed."}
    sql = ""

    for retry in (False, True):
        generated = request_sql(question, schema, retry)
        sql = generated["sql"]
        total_input_tokens += generated["input_tokens"]
        total_output_tokens += generated["output_tokens"]
        validation = validate_sql(sql, str(DATABASE_PATH))

        if validation["status"] == "PASSED":
            break

    result = {
        "status": validation["status"],
        "sql": sql,
        "validation_message": validation["message"],
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }

    if validation["status"] != "PASSED":
        return result

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(sql).fetchall()

        result["rows"] = [dict(row) for row in rows]
        return result
    except sqlite3.Error as error:
        result["status"] = "FAILED"
        result["message"] = str(error)
        return result