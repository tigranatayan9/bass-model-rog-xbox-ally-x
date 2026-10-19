import matplotlib as mpl

BLUE = "#2a78d6"      # series 1
ORANGE = "#eb6834"    # series 2
BLUE_LIGHT = "#b7d3f6"
TEXT_1 = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"


def apply_style():
    mpl.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "xtick.color": TEXT_2,
        "ytick.color": TEXT_2,
        "text.color": TEXT_1,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })
