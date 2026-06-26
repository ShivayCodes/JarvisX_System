import sys
from jarvis_x.core.config import Config


class JarvisCLI:
    def __init__(self, engine):
        self.engine = engine

    def run(self):
        print(f"\n  JARVIS-X v7.0  |  {Config.OWNER}")
        print("  Type 'help' for commands | 'quit' to exit\n")
        while self.engine.running:
            try:
                text = input(f"[{Config.OWNER}]> ").strip()
                if not text:
                    continue
                
                def on_thought(thought_text):
                    print(f"  [Thinking] {thought_text}")
                
                response = self.engine.process_with_history(text, on_thought_cb=on_thought)
                print(f"  JARVIS: {response}")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            except Exception as e:
                print(f"  Error: {e}")
        self.engine.shutdown()
        print("Jarvis offline.")
