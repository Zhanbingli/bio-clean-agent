#!/usr/bin/env python3
"""
🚀 Bio Clean Agent Web Interface Launcher

This script starts the web interface for the Bio Clean Agent.
Just run: python start_web.py

Then open http://localhost:8080 in your browser!
"""

import sys
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required packages are installed."""
    required = ["fastapi", "uvicorn", "pandas", "numpy"]
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    return missing


def install_dependencies(packages):
    """Install missing packages."""
    print(f"📦 Installing missing packages: {', '.join(packages)}")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install"] + packages
    )
    print("✅ Dependencies installed!")


def main():
    """Main launcher."""
    print("=" * 70)
    print("🧬 Bio Clean Agent - Web Interface")
    print("=" * 70)
    print()

    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()

    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        response = input("Install them now? [Y/n]: ").strip().lower()

        if response in {"", "y", "yes"}:
            try:
                install_dependencies(missing)
            except Exception as e:
                print(f"❌ Failed to install dependencies: {e}")
                print("\nPlease install manually:")
                print(f"  pip install {' '.join(missing)}")
                sys.exit(1)
        else:
            print("Please install dependencies manually:")
            print(f"  pip install {' '.join(missing)}")
            sys.exit(1)
    else:
        print("✅ All dependencies installed")

    print()
    print("🚀 Starting web server...")
    print()
    print("=" * 70)
    print("  Open your browser and go to:")
    print("  👉 http://localhost:8080")
    print("=" * 70)
    print()
    print("Press Ctrl+C to stop the server")
    print()

    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Start server
    try:
        from bio_clean_agent.web.server import run_server
        run_server(host="127.0.0.1", port=8080, reload=False)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure port 8080 is not in use")
        print("2. Check that all dependencies are installed: pip install -e .[api]")
        print("3. Try running: python -m bio_clean_agent.web.server")
        sys.exit(1)


if __name__ == "__main__":
    main()
