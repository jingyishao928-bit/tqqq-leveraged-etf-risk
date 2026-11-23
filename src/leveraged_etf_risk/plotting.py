"""Shared plotting configuration."""

FIGURE_DPI = 300
FIGURE_FORMAT = "png"


def set_plot_style() -> None:
    """Apply the project plotting style after matplotlib is installed."""
    import matplotlib.pyplot as plt

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": FIGURE_DPI,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
        }
    )

