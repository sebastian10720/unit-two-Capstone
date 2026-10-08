Enterprise Q&A System

## Overview

This project answers two types of questions:

- **Qualitative questions:** answered using uploaded business documents.
- **Quantitative questions:** answered using SQL queries against a SQLite database.

A Manager Agent decides which specialist to use.

## Project Structure

- `main.py`: command-line entry point.
- `agents/manager.py`: routes questions to the appropriate agent.
- `agents/qualitative.py`: searches documents and generates grounded answers.
- `agents/quantitative.py`: converts questions into SQL and queries SQLite.
- `validation/validator.py`: checks SQL and agent responses.
- `tokenomics/logger.py`: records token usage and estimated cost.
- `data/documents/`: source documents.
- `data/chroma/`: searchable document index.
- `data/database.sqlite`: SQLite transaction database.
- `tokenomics_log.jsonl`: token and cost records.

## How to Run

Activate the virtual environment, then run a question:

```bash
python main.py "What is the total amount by region?"