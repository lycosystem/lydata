# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@02f7a8e8e7494802421186f72d48ce6201374b50",
#     "numpy==2.2.6",
#     "loguru==0.7.3",
#     "pandas==2.3.1",
#     "typer==0.16.0",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///
"""Cast dtypes in CSV files."""

from pathlib import Path

import pandas as pd
from loguru import logger
from lydata.validator import cast_dtypes


def main(input_file: Path, output_file: Path) -> None:
    """Cast dtypes in CSV files."""
    df = pd.read_csv(input_file, header=[0, 1, 2])
    logger.info(f"Read {len(df)} rows from {input_file=}.")

    logger.enable("lydata")
    df = cast_dtypes(df)

    df.to_csv(output_file, index=False)
    logger.success(f"Saved casted data to {output_file=}.")


if __name__ == "__main__":
    import typer

    typer.run(main)
