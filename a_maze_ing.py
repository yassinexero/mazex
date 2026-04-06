"""A-Maze-ing — main entry point.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys
from parser import parse_config
from mazegen.generator import MazeGenerator
from maze_writer import write_maze
from maze_display import MazeVisual


def main() -> None:
    """Parse config, generate maze, write output file, launch visual.

    Raises:
        SystemExit: On any argument, config, generation, or write error.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    # Step 1 — parse config
    config = parse_config(sys.argv[1])

    # Step 2 — generate maze
    generator = MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit_=config.exit,
        perfect=config.perfect,
        seed=config.seed,
    )
    generator.generate()

    # Step 3 — write output file
    write_maze(generator, config.output_file)
    print(f"Maze written to '{config.output_file}'.")

    # Step 4 — launch visual
    visual = MazeVisual(generator, config.output_file)
    visual.run()


if __name__ == "__main__":
    main()
