"""Configuration file parser for A-Maze-ing project."""

import sys
from dataclasses import dataclass

from mazegen.generator import MIN_MAZE_WIDTH, MIN_MAZE_HEIGHT, pattern_cells


MANDATORY_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}


@dataclass
class MazeConfig:
    """Holds all maze generation parameters parsed from the config file.

    Attributes:
        width:       Number of columns in the maze.
        height:      Number of rows in the maze.
        entry:       (x, y) coordinates of the maze entry cell.
        exit:        (x, y) coordinates of the maze exit cell.
        output_file: Path to the output file.
        perfect:     Whether the maze must be perfect (one unique path).
        seed:        Optional random seed for reproducibility.
    """

    width:       int
    height:      int
    entry:       tuple[int, int]
    exit:        tuple[int, int]
    output_file: str
    perfect:     bool
    seed:        int | None = None


def _parse_coords(value: str, key: str) -> tuple[int, int]:
    """Parse a 'x,y' string into a tuple of ints.

    Args:
        value: The raw string value from the config (e.g. '0,0').
        key:   The config key name, used for error messages.

    Returns:
        A tuple (x, y) of integers.

    Raises:
        SystemExit: If the format is invalid or values are not integers.
    """
    parts = value.split(",")
    if len(parts) != 2:
        print(f"Error: '{key}' must be in format x,y (got '{value}')")
        sys.exit(1)
    try:
        return (int(parts[0].strip()), int(parts[1].strip()))
    except ValueError:
        print(f"Error: '{key}' coordinates must be integers (got '{value}')")
        sys.exit(1)


def _parse_pairs(lines: list[str]) -> dict[str, str]:
    """Extract KEY=VALUE pairs from config lines, skipping comments.

    Args:
        lines: Raw lines from the config file.

    Returns:
        A dict mapping keys to their raw string values.

    Raises:
        SystemExit: If a non-comment, non-blank line has invalid format.
    """
    pairs: dict[str, str] = {}
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            print(f"Error: Line {i} is not a valid KEY=VALUE pair: '{stripped}'")
            sys.exit(1)
        key, _, value = stripped.partition("=")
        pairs[key.strip().upper()] = value.strip()
    return pairs


def _validate_pairs(pairs: dict[str, str]) -> None:
    """Check that all mandatory keys are present.

    Args:
        pairs: Parsed key-value pairs from the config.

    Raises:
        SystemExit: If any mandatory key is missing.
    """
    allowed = MANDATORY_KEYS | {"SEED"}

    unknown = pairs.keys() - allowed
    if unknown:
        print(f"Error: Unknown config keys: {', '.join(sorted(unknown))}")
        sys.exit(1)
    missing = MANDATORY_KEYS - pairs.keys()
    if missing:
        print(f"Error: Missing mandatory config keys: {', '.join(sorted(missing))}")
        sys.exit(1)


def _build_config(pairs: dict[str, str]) -> MazeConfig:
    """Convert raw string pairs into a typed MazeConfig.

    Validates all values and exits with a clear error on any problem.

    Args:
        pairs: Validated key-value pairs from the config file.

    Returns:
        A fully populated MazeConfig instance.

    Raises:
        SystemExit: If any value has an invalid type or fails validation.
    """
    try:
        width  = int(pairs["WIDTH"])
        height = int(pairs["HEIGHT"])
    except ValueError:
        print("Error: WIDTH and HEIGHT must be integers.")
        sys.exit(1)

    if width < 2 or height < 2:
        print("Error: WIDTH and HEIGHT must be at least 2.")
        sys.exit(1)

    if width < MIN_MAZE_WIDTH or height < MIN_MAZE_HEIGHT:
        print(
            f"Error: Maze too small to embed the '42' pattern. "
            f"Minimum size is {MIN_MAZE_WIDTH}x{MIN_MAZE_HEIGHT} "
            f"(got {width}x{height})."
        )
        sys.exit(1)

    entry = _parse_coords(pairs["ENTRY"], "ENTRY")
    exit_ = _parse_coords(pairs["EXIT"],  "EXIT")

    for name, coord in [("ENTRY", entry), ("EXIT", exit_)]:
        x, y = coord
        if not (0 <= x < width and 0 <= y < height):
            print(
                f"Error: {name} ({x},{y}) is outside maze bounds "
                f"(0..{width - 1}, 0..{height - 1})."
            )
            sys.exit(1)

    if entry == exit_:
        print("Error: ENTRY and EXIT must be different cells.")
        sys.exit(1)

    pat = pattern_cells(width, height)
    for name, coord in [("ENTRY", entry), ("EXIT", exit_)]:
        if coord in pat:
            print(
                f"Error: {name} {coord} overlaps with the '42' pattern. "
                f"Choose a different cell."
            )
            sys.exit(1)

    perfect_raw = pairs["PERFECT"].strip().lower()
    if perfect_raw not in ("true", "false"):
        print(f"Error: PERFECT must be True or False (got '{pairs['PERFECT']}').")
        sys.exit(1)
    perfect = perfect_raw == "true"

    seed: int | None = None
    if "SEED" in pairs:
        try:
            seed = int(pairs["SEED"])
            seed = str(seed)
        except ValueError:
            print(f"Error: SEED must be an integer (got '{pairs['SEED']}').")
            sys.exit(1)

    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=pairs["OUTPUT_FILE"],
        perfect=perfect,
        seed=seed,
    )


def parse_config(filepath: str) -> MazeConfig:
    """Parse a maze configuration file and return a MazeConfig.

    Args:
        filepath: Path to the configuration file.

    Returns:
        A MazeConfig dataclass with all settings.

    Raises:
        SystemExit: On any file, format, or validation error.
    """
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Config file '{filepath}' not found.")
        sys.exit(1)
    except OSError as e:
        print(f"Error: Could not read config file '{filepath}': {e}")
        sys.exit(1)

    pairs = _parse_pairs(lines)
    _validate_pairs(pairs)
    return _build_config(pairs)
