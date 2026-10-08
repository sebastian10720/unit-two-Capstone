import re
import sqlite3
from pathlib import Path


def validate_sql(sql: str, db_path: str = "data/database.sqlite") -> dict:
    query = sql.strip()

    if not query:
        return {"status": "FAILED", "message": "SQL query is empty."}

    if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
        return {"status": "FAILED", "message": "Only read-only queries are allowed."}

    blocked = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|REPLACE|VACUUM)\b"
    if re.search(blocked, query, re.IGNORECASE):
        return {"status": "FAILED", "message": "Potentially destructive SQL was blocked."}

    if query.count(";") > 1:
        return {"status": "FAILED", "message": "Multiple SQL statements are not allowed."}

    database = Path(db_path)

    if not database.exists():
        return {
            "status": "MISSING_DATABASE",
            "message": f"Database not found: {db_path}",
        }

    try:
        with sqlite3.connect(database) as connection:
            connection.execute(f"EXPLAIN QUERY PLAN {query.rstrip(';')}")
        return {"status": "PASSED", "message": "SQL validation passed."}
    except sqlite3.Error as error:
        return {"status": "FAILED", "message": str(error)}

    
def validate_qualitative(answer: str, chunks: list[dict]) -> dict:
    sources_cited = []

    for index, chunk in enumerate(chunks, start=1):
        if f"Source {index}" in answer:
            sources_cited.append(chunk.get("source", "unknown"))

    refused = "cannot find" in answer.lower()
    grounded = len(sources_cited) > 0

    return {
        "is_grounded": grounded,
        "refused_to_answer": refused,
        "sources_cited": sources_cited,
        "flag": not grounded and not refused,
        "warning": (
            "Response may not be grounded in source documents"
            if not grounded and not refused
            else None
        ),
    }


def validate_quantitative(
    answer: str,
    sql: str,
    validation_status: str,
) -> dict:
    del answer
    del sql

    passed = validation_status == "PASSED"

    return {
        "sql_validated": passed,
        "sql_blocked": validation_status == "FAILED",
        "execution_error": validation_status == "ERROR",
        "flag": not passed,
        "warning": (
            f"SQL validation status: {validation_status}"
            if not passed
            else None
        ),
    }