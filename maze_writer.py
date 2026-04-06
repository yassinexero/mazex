"""Output file writer for A-Maze-ing project.

Writes the generated maze to a file using the required format:
    - One hexadecimal digit per cell, one row per line
    - An empty line after the grid
    - Entry coordinates (x,y)
    - Exit coordinates (x,y)
    - Shortest path as a string of N/E/S/W letters
    - All lines end with \\n
"""

import sys
from typing import TextIO
from mazegen import MazeGenerator


def write_maze(generator: MazeGenerator, filepath: str) -> None:
    """Write the generated maze to the output file.

    Args:
        generator: A MazeGenerator instance after generate() has been called.
        filepath: Path to the output file to write.

    Raises:
        SystemExit: If the file cannot be written.
    """
    try:
        with open(filepath, "w") as f:
            _write_grid(f, generator)
            _write_metadata(f, generator)
    except OSError as e:
        print(f"Error: Could not write output file '{filepath}': {e}")
        sys.exit(1)


def _write_grid(f: TextIO, generator: MazeGenerator) -> None:
    """Write the hex grid rows to the file.

    Each row is written as a string of uppercase hex digits (one per cell),
    followed by a newline. After all rows, an empty line is written.

    Args:
        f: An open writable file object.
        generator: The maze generator with a populated grid.
    """
    for row in generator.grid:
        line = "".join(format(cell, "X") for cell in row)
        f.write(line + "\n")
    f.write("\n")


def _write_metadata(f: TextIO, generator: MazeGenerator) -> None:
    """Write entry coords, exit coords, and solution path to the file.

    Args:
        f: An open writable file object.
        generator: The maze generator with entry, exit_, and solution set.
    """
    ex, ey = generator.entry
    xx, xy = generator.exit_

    f.write(f"{ex},{ey}\n")
    f.write(f"{xx},{xy}\n")
    f.write(generator.solution + "\n")
