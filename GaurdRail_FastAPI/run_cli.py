from guardrails.cli import cli
import sys

if __name__ == "__main__":
    # Simulate command line arguments
    # Note: cli() might consume sys.argv, so we set it up.
    # If using Typer/Click, usually the first arg is the script name.
    sys.argv = ["guardrails", "hub", "install", "hub://guardrails/detect_pii"]
    try:
        cli()
    except SystemExit as e:
        print(f"CLI exited with code {e.code}")
    except Exception as e:
        print(f"CLI failed with error: {e}")
