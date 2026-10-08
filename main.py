import json
import sys

from agents.manager import run


def display_result(result: dict) -> None:
    print(json.dumps(result, indent=2, default=str))


def ask_once(question: str) -> None:
    try:
        display_result(run(question))
    except Exception as error:
        print(f"Request failed: {error}")


def interactive_mode() -> None:
    print("Enterprise Q&A system")
    print("Type 'quit' or 'exit' to stop.")

    while True:
        try:
            question = input("\nAsk a question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        if question.lower() in {"quit", "exit"}:
            print("Goodbye.")
            return

        if question:
            ask_once(question)


def main() -> None:
    if len(sys.argv) > 1:
        ask_once(" ".join(sys.argv[1:]))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()