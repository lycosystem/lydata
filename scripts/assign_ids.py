# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "loguru==0.7.3",
#     "pandas==2.3.1",
#     "typer==0.16.0",
#     "lydata @ git+https://github.com/lycosystem/lydata-package@116a70b433c6fd5947a6656619aa8a1d3dba58a2",
# ]
# ///
"""Assign unique IDs to patients in a dataset."""

import math
import re
from pathlib import Path

import pandas as pd
from loguru import logger


def ensure_valid(dataset_dir: Path, filename: str) -> tuple[str, str, str]:
    """Raise `ValueError`s if the directory is not a valid dataset."""
    dataset_match = re.match(r"([1-9][0-9]{3})-([a-z]+)-([a-z\-]+)", dataset_dir.name)

    if dataset_match is None:
        raise ValueError(f"{dataset_dir.name=} is not a valid dataset name")

    if not dataset_dir.is_dir():
        raise ValueError(f"{dataset_dir} is not a directory")

    if not (dataset_dir / filename).is_file():
        raise ValueError(f"{dataset_dir / filename} does not exist")

    logger.debug(f"Validated {dataset_dir.name=}.")
    return dataset_match.groups()


def generate_ids(
    year: str,
    institution: str,
    num: int,
    start: int = 1,
    suffix: str = "",
) -> list[str]:
    """Generate a list of unique patient IDs."""
    base = f"{year}-{institution.upper()}{suffix}"
    num_width = math.ceil(math.log10(num))

    return [f"{base}-{str(i).rjust(num_width, '0')}" for i in range(start, start + num)]


def main(
    dataset_dir: Path,
    input_csv: str = "data.csv",
    output_csv: str = "data.csv",
    start: int = 1,
    suffix: str = "",
) -> None:
    """Assign unique IDs to patients in a dataset."""
    year, institution, _ = ensure_valid(dataset_dir, input_csv)

    data = pd.read_csv(dataset_dir / input_csv, header=[0, 1, 2])
    logger.info(f"Loaded data from {dataset_dir / input_csv}.")

    if ("patient", "core", "id") in data.columns:
        data = data.astype({("patient", "core", "id"): "string"})

    ids = generate_ids(
        year=year,
        institution=institution,
        num=len(data),
        start=start,
        suffix=suffix,
    )
    data.loc[:, ("patient", "core", "id")] = pd.Series(ids, dtype="string")
    logger.info(f"Added IDs from {ids[0]} to {ids[-1]}.")

    cols = data.columns.tolist()
    cols.remove(("patient", "core", "id"))
    cols = [("patient", "core", "id")] + cols
    data = data[cols]
    logger.debug("Reordered columns to place patient ID first.")

    data.to_csv(dataset_dir / output_csv, index=False)
    logger.success(f"Stored updated data in {dataset_dir / output_csv}.")


if __name__ == "__main__":
    import typer

    typer.run(main)
