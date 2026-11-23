"""Compatibility entry point for the analysis stored with Part 1 outputs.

The full source is outputs/part1/analyze_part1.py. Keep the original command
working without maintaining a second copy of the calculation code.
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    script = Path(__file__).resolve().parents[1] / "outputs/part1/analyze_part1.py"
    runpy.run_path(str(script), run_name="__main__")
