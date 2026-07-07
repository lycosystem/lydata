# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "loguru == 0.7.3",
#     "pandas == 2.3.1",
#     "typer == 0.16.0",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///
"""Shift ages in a table by a random amount.

The age of every row will be shifted by a different random amount. Note that this is intended
to be used for anonymization purposes, so do not add this shifting to a DVC pipeline,
otherwise it will be recoverable.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger


def main(
    input_path: Path,
    output_path: Path,
    age_column: str,
    seed: int = 1648,
    num_headers: int = 3,
) -> None:
    """Shift age in every row of a table by a random amount."""
    table = pd.read_csv(input_path, header=list(range(num_headers)))
    logger.info(f"Loaded table from {input_path}.")

    rng = np.random.default_rng(seed)
    random_shift = pd.Series(
        rng.integers(low=-2, high=2, size=len(table)),
        index=table.index,
    )
    logger.info(f"Drew {len(random_shift)} random shifts using {seed=}.")

    try:
        table[age_column] = table[age_column] + random_shift
    except AttributeError:
        logger.debog(f"No age column '{age_column}.")

    table.to_csv(output_path, index=False)
    logger.success(f"Table with shifted ages saved to {output_path}.")


if __name__ == "__main__":
    import typer

    typer.run(main)
