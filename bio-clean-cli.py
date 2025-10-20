#!/usr/bin/env python3
"""
Bio Clean Agent - Interactive CLI

Launch the interactive command-line interface for data cleaning.
Similar to Claude Code's conversational interface with LLM support.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env file if exists
def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"📄 Loading configuration from {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Only set if not already in environment and value is not placeholder
                    if key and value and not os.getenv(key):
                        if not value.startswith('your_') and value not in ['', 'None']:
                            os.environ[key] = value
                            if 'API_KEY' in key:
                                print(f"   ✓ Loaded {key}")

# Load .env before main
load_env_file()


def main():
    """Main entry point."""
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Bio Clean Agent - AI-Powered Interactive CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with DeepSeek (default)
  python bio-clean-cli.py

  # Use OpenAI instead
  python bio-clean-cli.py --llm openai

  # Disable LLM (rule-based mode)
  python bio-clean-cli.py --no-llm

  # With custom user ID
  python bio-clean-cli.py --user analyst01

Environment Variables:
  DEEPSEEK_API_KEY - DeepSeek API key (get at: https://platform.deepseek.com)
  OPENAI_API_KEY   - OpenAI API key
  LLM_MODEL        - Override default model
  LLM_BASE_URL     - Override API base URL

Natural language examples (with LLM):
  - "Load the clinical trial data from trial_data.csv"
  - "Can you show me what the data looks like?"
  - "Assess the quality and tell me what issues you find"
  - "Clean the data by removing duplicates and handling missing values"
  - "Save everything and export the audit trail"

Slash commands:
  /help      - Show all commands
  /llm       - Show LLM information
  /tools     - List available tools
  /stats     - Show session statistics
  /status    - Show current status
  /reset     - Clear conversation history
  /exit      - Quit the program
        """
    )

    parser.add_argument(
        "--user",
        default="user",
        help="User ID for session tracking (default: user)"
    )

    parser.add_argument(
        "--llm",
        default="deepseek",
        choices=["deepseek", "openai"],
        help="LLM provider (default: deepseek)"
    )

    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM, use rule-based mode"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Bio Clean Agent v0.5.0 - LLM-Powered Edition"
    )

    args = parser.parse_args()

    # Check for API keys
    enable_llm = not args.no_llm
    if enable_llm:
        if args.llm == "deepseek" and not os.getenv("DEEPSEEK_API_KEY"):
            print("⚠ Warning: DEEPSEEK_API_KEY not set", file=sys.stderr)
            print("Get your key at: https://platform.deepseek.com", file=sys.stderr)
            print("Falling back to rule-based mode\n", file=sys.stderr)
            enable_llm = False
        elif args.llm == "openai" and not os.getenv("OPENAI_API_KEY"):
            print("⚠ Warning: OPENAI_API_KEY not set", file=sys.stderr)
            print("Falling back to rule-based mode\n", file=sys.stderr)
            enable_llm = False

    # Create and start REPL
    try:
        if enable_llm:
            # Use LLM-powered REPL
            from bio_clean_agent.interactive.repl_llm import LLMPoweredREPL
            repl = LLMPoweredREPL(
                user_id=args.user,
                llm_provider=args.llm,
                enable_llm=True
            )
        else:
            # Use rule-based REPL
            from bio_clean_agent.interactive.repl import InteractiveREPL
            repl = InteractiveREPL(user_id=args.user)

        repl.start()

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
