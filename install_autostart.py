#!/usr/bin/env python3
"""Helper to install/remove JARVIS-X auto-start on boot."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_v6 import AutoStart


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JARVIS-X Auto-Start Manager")
    parser.add_argument("--remove", action="store_true", help="Remove auto-start")
    args = parser.parse_args()

    if args.remove:
        AutoStart.remove()
    else:
        AutoStart.install()


if __name__ == "__main__":
    main()
