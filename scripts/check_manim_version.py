#!/usr/bin/env python
"""Print the version of Manim available in the current Python environment."""
from __future__ import annotations

import manim


def main() -> int:
    print(manim.__version__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
