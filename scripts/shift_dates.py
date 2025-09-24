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
"""Shift all dates in a table by a random amount.

All dates in a row will be shifted by the same random amount. Note that this is intended
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
    regex_date_format: str = r"^\d{4}-\d{2}-\d{2}$",
    date_format: str = "%Y-%m-%d",
    seed: int = 1648,
    num_headers: int = 3,
) -> None:
    """Shift all dates in every row of a table by a random amount."""
    table = pd.read_csv(input_path, header=list(range(num_headers)))
    logger.info(f"Loaded table from {input_path}.")

    rng = np.random.default_rng(seed)
    random_shift = pd.Series(
        pd.to_timedelta(rng.integers(low=-30, high=30, size=len(table)), unit="D"),
        index=table.index,
    )
    logger.info(f"Drew {len(random_shift)} random shifts using {seed=}.")

    for col_name, series in table.items():
        try:
            if series.str.match(regex_date_format).any():
                dates = pd.to_datetime(series, format=date_format, errors="coerce")
                shifted_dates = dates + random_shift
                table[col_name] = shifted_dates
                logger.info(f"Shifted dates in column '{col_name}'.")
        except AttributeError:
            # If the series is not a string type, skip it
            logger.debug(f"Skipped column '{col_name}'.")
            continue

    table.to_csv(output_path, index=False, date_format=date_format)
    logger.success(f"Table with shifted dates saved to {output_path}.")


if __name__ == "__main__":
    # main(
    #     input_path=Path("2025-usz-hypopharynx-larynx/parsed.csv"),
    #     output_path=Path("shifted.csv"),
    # )
    import typer

    typer.run(main)
