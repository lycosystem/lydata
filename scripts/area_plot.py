# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lydata @ git+https://github.com/lycosystem/lydata-package@79c5d4996b37a833afca457629d8d854acc05a33",
#     "matplotlib==3.10.0",
#     "numpy==2.2.6",
#     "loguru==0.7.3",
#     "pandas==2.3.1",
#     "typer==0.16.0",
#     "tueplots==0.0.17",
# ]
# [tool.uv]
# exclude-newer = "2025-07-30T00:00:00Z"
# ///
"""Plot distribution over subsite and T-categories proportional to area."""

from pathlib import Path

import lydata  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from lydata import C
from matplotlib.patches import Rectangle
from shared import COLORS, MPLSTYLE
from tueplots import figsizes, fontsizes


def group_t_stage_by_subsite(data: pd.DataFrame) -> pd.DataFrame:
    """Return table with one col for subsites and four binary cols for T-stages."""
    data = data.ly.query(C("t_stage").isin([1, 2, 3, 4]))
    data[("_plot", "core", "subsite")] = pd.Series(dtype="string")
    is_hypopharynx = (
        C("subsite").contains("C13") | C("subsite").contains("C12")
    ).execute(data)
    is_glottic = (C("subsite") == "C32.0").execute(data)
    is_supraglottic = (C("subsite") == "C32.1").execute(data)
    is_other = ~(is_hypopharynx | is_glottic | is_supraglottic)

    subsite = pd.Series(dtype="string", index=data.index)
    subsite[is_hypopharynx] = "Hypopharynx"
    subsite[is_glottic] = "Glottic"
    subsite[is_supraglottic] = "Supraglottic"
    subsite[is_other] = "Other Larynx"
    subsite = subsite.astype("category")
    subsite = pd.DataFrame({"Subsite": subsite})

    t_dummy = pd.get_dummies(data.ly.t_stage.astype("Int64"), prefix="T", prefix_sep="")
    subsite_and_t = pd.concat([subsite, t_dummy], axis=1)
    subsite_vs_t_counts = subsite_and_t.groupby("Subsite", observed=True).sum()

    order = ["Other Larynx", "Supraglottic", "Glottic", "Hypopharynx"]
    return subsite_vs_t_counts.loc[[c for c in order if c in subsite_vs_t_counts.index]]


def create_plot_axis() -> tuple[plt.Figure, plt.Axes]:
    """Create and return a matplotlib axis with the desired size."""
    plt.style.use(MPLSTYLE)
    plt.rcParams.update(
        figsizes.icml2022_half(
            nrows=1,
            ncols=1,
            height_to_width_ratio=0.65,
        ),
    )
    plt.rcParams.update(fontsizes.icml2022())
    plt.rcParams.update({"axes.linewidth": 1.5})
    fig, ax = plt.subplots()

    size = plt.gcf().get_size_inches()
    logger.info(f"Created figure with {size=}.")
    return fig, ax


def annotate_one_percent(
    ax: plt.Axes,
    total: int,
    patch_xy: tuple[int, int] = (10, 40),
    text_xy: tuple[int, int] = (15, 70),
) -> None:
    """Show that one grid rectangle corresponds to 1%."""
    rect = Rectangle(xy=patch_xy, width=10, height=10, hatch="//////", alpha=0.0)
    ax.add_patch(rect)
    ax.annotate(
        text=f"1% ≈ {total / 100:.1f} p.",
        xy=(patch_xy[0] + 5, patch_xy[1] + 5),
        xytext=text_xy,
        va="top",
        ha="left",
        arrowprops={
            "arrowstyle": "->",
            "color": "black",
            "connectionstyle": "arc3,rad=-0.3",
            "patchB": rect,
        },
        fontsize="small",
    )
    logger.info(r"Annotated 1% area in the plot.")


def configure_grid_and_ticks(ax: plt.Axes) -> None:
    """Configure grid and ticks for the plot."""
    ax.set_xticks(np.linspace(0, 100, 11), minor=True)
    ax.set_xticks([], minor=False)
    ax.set_yticks(np.linspace(0, 100, 11), minor=True)
    ax.tick_params(which="both", length=0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(which="minor", color="white", linewidth=1.0)
    ax.grid(which="major", visible=False)


def main(
    data_path: Path,
    figure_path: Path,
    patch_xy: tuple[int, int] = (10, 40),
    text_xy: tuple[int, int] = (15, 70),
) -> None:
    """Plot distribution over subsite and T-categories proportional to area."""
    data = pd.read_csv(data_path, header=[0, 1, 2])
    logger.info(f"Loaded data from {data_path=}")

    subsite_vs_t_counts = group_t_stage_by_subsite(data)
    subsite_counts = subsite_vs_t_counts.sum(axis="columns")
    total = subsite_counts.sum()
    subsite_percent = 100 * subsite_counts / total
    subsite_vs_t_percent = (
        100 * subsite_vs_t_counts / subsite_counts.values[:, np.newaxis]
    )
    t_stage_percent = 100 * subsite_vs_t_counts.sum(axis="index") / total
    edge_positions = np.cumsum([0] + subsite_percent.tolist())[:-1]
    last_heights = np.zeros(len(subsite_vs_t_counts))

    fig, ax = create_plot_axis()
    colors = [COLORS[n] for n in ["green", "blue", "orange", "red"]]

    for t_stage in [1, 2, 3, 4]:
        t_col = f"T{t_stage}"
        t_in_subsite_percent = subsite_vs_t_percent[t_col]
        ax.barh(
            y=edge_positions,
            align="edge",
            width=t_in_subsite_percent,
            left=last_heights,
            height=subsite_percent,
            label=f"T{t_stage} ({t_stage_percent[t_col]:.0f}%)",
            linewidth=1.5,
            alpha=0.8,
            facecolor=colors[t_stage - 1],
            edgecolor="black",
        )
        last_heights += t_in_subsite_percent

    annotate_one_percent(ax, total=total, patch_xy=patch_xy, text_xy=text_xy)
    ax.legend(
        bbox_to_anchor=(0.0, -0.01, 1.0, -0.01),
        loc="upper left",
        ncol=4,
        borderaxespad=0.0,
        mode="expand",
        handlelength=1.5,
        handleheight=1.0,
        handletextpad=0.4,
    )
    ax.set_yticks(
        ticks=edge_positions + subsite_percent / 2,
        labels=[f"{s}\n{c} ({c / total:.0%})" for s, c in subsite_counts.items()],
        minor=False,
    )
    configure_grid_and_ticks(ax)

    fig.suptitle(
        "Distribution over T-Categories and Subsites",
        fontsize="medium",
    )

    plt.savefig(figure_path, bbox_inches="tight", dpi=300)
    logger.success(f"Saved plot to {figure_path}")


if __name__ == "__main__":
    import typer

    typer.run(main)
