"""Terminal interface for ToolWise AI."""
from pathlib import Path

from dotenv import load_dotenv

from toolwise.agent import AgentError, ask_agent


def main() -> None:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    print("ToolWise AI — type 'exit' to quit")
    history: list[dict[str, str]] = []
    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if prompt.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not prompt:
            print("Please enter a message.")
            continue
        try:
            result = ask_agent(prompt, history=history)
            print(f"\nToolWise AI: {result['answer']}")
            for call in result["tool_calls"]:
                print(f"  [tool: {call['tool']}] {call['result']}")
            history.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": result["answer"]}])
            history = history[-10:]
        except AgentError as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
