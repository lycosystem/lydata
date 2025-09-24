# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@93aac555929eefb5e95b81e01fbf9f451bf893b3",
#     "numpy==2.2.6",
#     "loguru==0.7.3",
#     "pandas==2.3.1",
#     "typer==0.16.0",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///
"""Validation for LyData."""

import sys
from pathlib import Path

import pandas as pd
from loguru import logger
from lydata.validator import is_valid

sys.tracebacklimit = 0
logger.enable("lydata")
logger.remove()
logger.add(sys.stdout, level="INFO", backtrace=False)


def main(input_file: Path) -> None:
    """Show validation errors for every patient in the table."""
    df = pd.read_csv(input_file, header=[0, 1, 2])
    logger.info(f"Read {len(df)} rows from {input_file=}.")

    if is_valid(df, fail_on_error=False):
        logger.success("Dataframe is valid.")
    else:
        logger.error("Dataframe is not valid.")


if __name__ == "__main__":
    import typer

    typer.run(main)
