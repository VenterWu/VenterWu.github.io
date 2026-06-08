"""Command-line entry point for the local blog publisher."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m tools.blog_publisher",
        description="Launch the Tkinter GUI for importing content and publishing the Astro blog.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="Path to the Astro repository root. If omitted, the tool searches upward from the current directory.",
    )
    parser.add_argument("--version", action="version", version=f"blog-publisher {__version__}")
    args = parser.parse_args()

    from .app import run_app

    run_app(args.repo)


if __name__ == "__main__":
    main()