# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@116a70b433c6fd5947a6656619aa8a1d3dba58a2",
#     "matplotlib==3.10.0",
#     "numpy==2.2.6",
#     "pandas==2.2.3",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///

"""Load the UKF Hypopharynx data and visualize how often modalities conflict.

We want to check this, because in a call, Dr. Rühle mentioned that, in order to report
e.g. CT-based lymphatic involvement, they sometimes also looked at other modalities.
This somewhat defies the idea of reporting the diagnostic modalities independently.
But, realistically, this is what happens in clinical practice, and probably also in
other data.

To get a sense of how often this happens, we will load the UKF Hypopharynx data and
visualize how often modalities conflict.
"""

import argparse
from pathlib import Path

import lydata  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes

pd.set_option("future.no_silent_downcasting", True)


def create_argparser() -> argparse.ArgumentParser:
    """Create an argument parser for the script."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument(
        "--input-file",
        type=Path,
        default="2025-ukf-hypopharynx/data.csv",
        help="the data to load.",
    )
    parser.add_argument(
        "--figure-dir",
        type=Path,
        default=Path("./2025-ukf-hypopharynx/figures"),
        help="directory to save the figures to.",
    )
    return parser


def load_dataset(args: argparse.Namespace) -> pd.DataFrame:
    """Fetch the dataset for the given arguments."""
    dataset = pd.read_csv(args.input_file, header=[0, 1, 2])
    return dataset.ly.enhance()


def create_axes_grid(num_modalities: int) -> np.ndarray:
    """Create a grid of axes for the given number of `num_modalities`."""
    fig, axes = plt.subplots(
        nrows=num_modalities - 1,
        ncols=num_modalities - 1,
        figsize=(12, 12),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )
    fig.suptitle("Conflicts between modalities", fontweight="bold", fontsize="x-large")
    return axes


def prepare_modality_data(table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Drop "core" column, fill NaNs with 0, also return mask where `table` is NaN."""
    table = table.drop(columns="core", errors="ignore")

    for side in ["ipsi", "contra"]:
        table = table.drop(
            columns=[
                (side, "Ia"),
                (side, "Ib"),
                (side, "IIa"),
                (side, "IIb"),
                (side, "Va"),
                (side, "Vb"),
                (side, "VIII"),
                (side, "IX"),
                (side, "X"),
            ],
            errors="ignore",
        )

    mask = table.isna()
    table = table.fillna(value=0).astype(dtype=int)
    return table, mask


def get_lnl_labels(table: pd.DataFrame) -> list[str]:
    """Return a list of labels for the columns of `table`."""
    contra_lnls = [f"c{lnl}" for lnl in table["ipsi"].columns]
    ipsi_lnls = [f"i{lnl}" for lnl in table["ipsi"].columns]
    return contra_lnls + ipsi_lnls


def configure_axis_grid(axes: Axes, table: pd.DataFrame) -> None:
    """Configure the grid of `axes` for the given `table`."""
    axes.set_xticks(
        ticks=np.arange(len(table.columns)),
        labels=get_lnl_labels(table),
    )
    axes.set_xticks(
        ticks=np.arange(len(table.columns) + 1) - 0.5,
        minor=True,
    )
    axes.set_yticks(
        ticks=np.arange(len(table) + 1) - 0.5,
        minor=True,
    )
    axes.grid(which="minor", color="gray", linestyle="-", linewidth=1)
    axes.axvline(
        x=len(table.columns) / 2 - 0.5,
        color="black",
        linewidth=2,
    )

    for spine in axes.spines.values():
        spine.set_linewidth(2)


def plot_total_conflicts(
    total_conflicts: np.ndarray,
    table: pd.DataFrame,
    figure_dir: Path,
) -> None:
    """Plot the total conflicts between all modalities."""
    plt.clf()
    plt.title(
        "Total conflicts between all modalities",
        fontweight="bold",
        fontsize="x-large",
    )
    plt.imshow(total_conflicts, cmap="Reds", interpolation="none", aspect="auto")
    plt.xlabel("Lymph node levels", size="large")
    plt.ylabel("Patient No.", size="large")
    ax = plt.gca()
    configure_axis_grid(axes=ax, table=table)
    plt.colorbar(label="Total conflicts")
    plt.savefig(figure_dir / "total_conflicts.png", dpi=400)


def main():
    """Load data and visualize how often modalities conflict."""
    args = create_argparser().parse_args()

    dataset = load_dataset(args)

    modalities = ["CT", "MRI", "PET", "sonography"]
    axes = create_axes_grid(num_modalities=len(modalities))
    total_conflicts = None

    for i, mod_a in enumerate(modalities):
        mod_a_data, mask_a = prepare_modality_data(dataset[mod_a])

        for j, mod_b in enumerate(modalities):
            if i <= j:
                if j < len(modalities) - 1 and (i - 1) >= 0:
                    axes[i - 1, j].axis("off")
                continue

            mod_a_data, mod_b_data = mod_a_data.align(dataset[mod_b], join="inner")
            mod_b_data, mask_b = prepare_modality_data(mod_b_data)

            conflicts = mod_a_data - mod_b_data
            conflicts = conflicts.mask(cond=mask_a | mask_b, other=0)
            axes[i - 1, j].imshow(
                conflicts.values,
                cmap="RdYlGn",
                aspect="auto",
                interpolation="none",
                vmin=-1,
                vmax=1,
            )
            configure_axis_grid(axes=axes[i - 1, j], table=mod_a_data)

            if i == len(modalities) - 1:
                axes[i - 1, j].set_xlabel(mod_b, fontweight="bold", fontsize="large")
            if j == 0:
                axes[i - 1, j].set_ylabel(mod_a, fontweight="bold", fontsize="large")

            if total_conflicts is None:
                total_conflicts = np.abs(conflicts.values)
            else:
                total_conflicts += np.abs(conflicts.values)

    args.figure_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.figure_dir / "conflicts.png", dpi=400)
    plot_total_conflicts(
        total_conflicts=total_conflicts,
        table=mod_a_data,
        figure_dir=args.figure_dir,
    )


if __name__ == "__main__":
    main()
