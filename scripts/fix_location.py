# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@79c5d4996b37a833afca457629d8d854acc05a33",
#     "loguru==0.7.3",
#     "pandas==2.3.1",
#     "typer==0.16.0",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///
"""Fix the `location` column in the datasets.

Sometimes, the `location` columns - which contains the primary tumor location, e.g.
`"hypopharynx"` - is not set correctly. This script infers the `location` from the
`subsite` column, which contains the ICD-10 code of the disease, e.g. `"C13.0"`.
"""

from pathlib import Path

import lydata  # noqa: F401
import pandas as pd
from loguru import logger
from lydata import LyDataFrame
from shared import icd_to_location


def main(input_path: Path, output_path: Path) -> None:
    """Infer the `location` column from the `subsite` column."""
    data: LyDataFrame = pd.read_csv(input_path, header=[0, 1, 2])
    logger.info(f"Loaded {data.shape=} from {input_path=}")

    subsites = data.ly.subsite
    new_location = subsites.apply(icd_to_location)
    logger.info(f"Converted {subsites.nunique()=} to {new_location.nunique()=}")

    old_location = data.tumor.core.location
    num_different = (old_location != new_location).sum()
    if num_different > 0:
        logger.warning(f"{num_different} patients' location info was updated.")

    num_unknown = (new_location == "unknown").sum()
    if num_unknown > 0:
        logger.warning(f"{num_unknown} patients' location info unknown.")

    data["tumor", "core", "location"] = new_location.astype("category")
    data.to_csv(output_path, index=False)
    logger.success(f"Saved updated data to {output_path=}")


if __name__ == "__main__":
    import typer

    typer.run(main)
