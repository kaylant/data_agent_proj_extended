"""CLI entry point for the agent"""

import sys
import threading
import time
import uuid

from src.agent import build_graph, df
from src.data_loader import get_schema_summary


class Spinner:
    """Simple terminal spinner"""

    def __init__(self, message="Thinking"):
        self.message = message
        self.running = False
        self.thread = None

    def _spin(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while self.running:
            sys.stdout.write(f"\r{chars[i % len(chars)]} {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * (len(self.message) + 15) + "\r")
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()


def main():
    print("=" * 50)
    print("Data Analysis Agent")
    print("=" * 50)
    print(f"Dataset: {len(df):,} rows × {len(df.columns)} columns")
    print("\nCommands:")
    print("  /schema - Show dataset schema")
    print("  /clear  - Clear conversation history")
    print("  /quit   - Exit & have a nice day.")
    print("=" * 50)

    app = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            question = input("\nYou: ").strip()

            if not question:
                continue
            if question == "/quit":
                print("Bye!")
                break
            if question == "/schema":
                print(get_schema_summary(df))
                continue
            if question == "/clear":
                thread_id = str(uuid.uuid4())
                config = {"configurable": {"thread_id": thread_id}}
                print("Conversation history cleared.")
                continue

            spinner = Spinner("Thinking")
            spinner.start()

            start_time = time.time()
            result = app.invoke({"messages": [("user", question)]}, config=config)
            elapsed = time.time() - start_time

            spinner.stop()

            print(f"Agent: {result['messages'][-1].content}")
            print(f"\n[Response time: {elapsed:.2f}s]")

        except KeyboardInterrupt:
            print(r"\Bye!")
            break


if __name__ == "__main__":
    main()
