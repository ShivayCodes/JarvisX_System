"""Command-line interface for JARVIS-X."""
import sys


class JarvisCLI:
    """Command-line interface."""

    def __init__(self, engine):
        """
        Initialize the CLI.
        
        Args:
            engine: JarvisEngine instance.
        """
        self.engine = engine

    def run(self):
        """Run the CLI interface."""
        print("\n" + "="*60)
        print("  JARVIS-X v7.0 - Local AI Assistant")
        print("  Type 'exit', 'quit', or 'q' to exit")
        print("="*60 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\nGoodbye! Thanks for using JARVIS-X.\n")
                    break
                
                response = self.engine.process(user_input)
                print(f"JARVIS: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Exiting...")
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}\n")
