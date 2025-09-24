# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@116a70b433c6fd5947a6656619aa8a1d3dba58a2",
#     "matplotlib==3.10.0",
#     "numpy==2.2.6",
#     "pandas==2.2.3",
#     "tueplots==0.0.17",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///

"""Create a bar plot of different filters applied to the dataset.

This should illustrate how the patient-individual data may be used.
"""

import argparse
from pathlib import Path

import lydata  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lydata import C
from shared import MPLSTYLE
from tueplots import figsizes, fontsizes

OUTPUT_NAME = Path(__file__).with_suffix(".png").name


def create_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the script."""
    parser = argparse.ArgumentParser(
        prog="bar_plot",
        description=__doc__,
    )
    parser.add_argument(
        "data",
        type=Path,
        help="Path to the data file.",
    )
    return parser


def main() -> None:
    """Run main function to execute the script."""
    parser = create_parser()
    args = parser.parse_args()

    plt.style.use(MPLSTYLE)
    plt.rcParams.update(
        figsizes.icml2022_half(
            nrows=1,
            ncols=1,
            height_to_width_ratio=0.75,
        ),
    )
    plt.rcParams.update(fontsizes.icml2022())
    fig, ax = plt.subplots()

    data = pd.read_csv(args.data, header=[0, 1, 2])
    data = data.ly.enhance()
    output_dir = args.data.parent / "figures"
    output_dir.mkdir(exist_ok=True)

    has_lnl_III = C("pathology", "ipsi", "III") == True  # noqa: N806

    scenarios = {
        "overall": None,
        "HPV pos": C("hpv") == True,
        "HPV neg": C("hpv") == False,
        "smoker": C("smoke") == True,
        "non-smoker": C("smoke") == False,
        "alcohol": C("alcohol") == True,
        "non-alcohol": C("alcohol") == False,
        "LNL II pos": C("pathology", "ipsi", "II") == True,
        "LNL II neg": C("pathology", "ipsi", "II") == False,
    }

    left = np.zeros(len(scenarios))
    positions = -np.array([0, 2, 3, 5, 6, 8, 9, 11, 12])
    for t_stage in [1, 2, 3, 4]:
        is_t_stage = C("t_stage") == t_stage
        right = left.copy()
        for j, condition in enumerate(scenarios.values()):
            portion = data.ly.portion(
                query=is_t_stage & has_lnl_III & condition,
                given=is_t_stage & condition,
            )
            right[j] += portion.percent

        ax.barh(
            positions,
            right - left,
            left=left,
            label=f"T{t_stage}",
        )
        left = right

    ax.set_yticks(positions)
    ax.set_yticklabels(scenarios.keys())
    ax.set_xlabel("Percentage of ipsilateral LNL III involvement")
    ax.legend(title="T-category")

    plt.savefig(output_dir / OUTPUT_NAME, dpi=300)


if __name__ == "__main__":
    main()
