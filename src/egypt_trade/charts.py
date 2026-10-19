"""Static README figures (matplotlib). One chart per analysis question.

Colour roles stay fixed across every chart: exports = slot 1 (blue), imports = slot 2 (orange),
so a reader learns the encoding once.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
OTHER = "#b5b4ad"
EXPORT, IMPORT = SERIES[0], SERIES[1]

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_2,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "ytick.left": False,
        "font.size": 10,
        "lines.linewidth": 2,
        "legend.frameon": False,
        "text.parse_math": False,
        "axes.titlepad": 24,
    }
)

YEARS = list(range(2014, 2026))


def _finish(fig: plt.Figure, ax: plt.Axes, path: Path, subtitle: str, source: str) -> None:
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9.5, va="bottom")
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", length=0)
    fig.text(0.01, 0.01, f"Source: UN Comtrade. {source}", color=INK_2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _label_end(ax: plt.Axes, x, y, text: str, dy: float = 0) -> None:
    ax.annotate(
        text,
        (x, y),
        xytext=(6, dy),
        textcoords="offset points",
        va="center",
        color=INK,
        fontsize=9.5,
    )


def _bn(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}bn")


def _pct(ax: plt.Axes, step: float = 0.05) -> None:
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(step))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")


def trade_balance(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = df["year"]
    imp, exp = df["imports_usd"] / 1e9, df["exports_usd"] / 1e9
    ax.fill_between(x, exp, imp, color=IMPORT, alpha=0.08, linewidth=0)
    ax.plot(x, imp, color=IMPORT, marker="o", markersize=4)
    ax.plot(x, exp, color=EXPORT, marker="o", markersize=4)
    last = df.iloc[-1]
    _label_end(ax, last.year, imp.iloc[-1], f"Imports ${imp.iloc[-1]:.0f}bn")
    _label_end(ax, last.year, exp.iloc[-1], f"Exports ${exp.iloc[-1]:.0f}bn")
    mid = df[df.year == 2022].iloc[0]
    ax.annotate(
        f"Deficit ${-mid.balance_usd / 1e9:.0f}bn",
        (2022, (mid.imports_usd + mid.exports_usd) / 2e9),
        ha="center",
        color=INK_2,
        fontsize=9,
    )
    ax.set_ylim(0, 115)
    ax.set_xlim(2013.6, 2027.4)
    _bn(ax)
    ax.set_title("Egypt still imports twice what it exports")
    _finish(
        fig,
        ax,
        path,
        "Merchandise trade, USD bn, as reported by Egypt",
        "HS2012 to 2021, HS2022 from 2022.",
    )


def import_partners(df: pd.DataFrame, path: Path) -> None:
    imp = df[df.flow == "import"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    offsets = {"China": 0, "USA": 4, "Saudi Arabia": -4}
    for color, name in zip(SERIES[:3], ["China", "USA", "Saudi Arabia"], strict=True):
        s = imp[imp.partner_name == name].sort_values("year")
        ax.plot(s.year, s.share_of_total, color=color, marker="o", markersize=4)
        _label_end(
            ax,
            s.year.iloc[-1],
            s.share_of_total.iloc[-1],
            f"{name} {s.share_of_total.iloc[-1]:.0%}",
            offsets[name],
        )
    ax.set_ylim(0, 0.21)
    ax.set_xlim(2013.6, 2027.4)
    _pct(ax)
    ax.set_title("Three suppliers now ship 41% of Egypt's imports, up from 22%")
    _finish(fig, ax, path, "Share of Egypt's total imports by partner", "Egypt-reported, CIF.")


def gas_swing(df: pd.DataFrame, path: Path) -> None:
    gas = df[df.hs4 == "2711"].sort_values("year")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(gas.year, gas.exports_usd / 1e9, color=EXPORT, marker="o", markersize=4)
    ax.plot(gas.year, gas.imports_usd / 1e9, color=IMPORT, marker="o", markersize=4)
    _label_end(ax, 2025, gas.imports_usd.iloc[-1] / 1e9, "Imports $10.1bn")
    _label_end(ax, 2025, gas.exports_usd.iloc[-1] / 1e9, "Exports $0.4bn")
    peak = gas[gas.year == 2022].iloc[0]
    ax.annotate(
        "2022: $10.1bn of LNG exports\ninto the European gas crunch",
        (2022, peak.exports_usd / 1e9),
        xytext=(-150, -8),
        textcoords="offset points",
        color=INK_2,
        fontsize=9,
        arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 0.8},
    )
    ax.set_ylim(0, 11.5)
    ax.set_xlim(2013.6, 2027.4)
    _bn(ax)
    ax.set_title("Natural gas went from a $6.9bn surplus to a $9.7bn bill in three years")
    _finish(fig, ax, path, "Egypt's trade in petroleum gases (HS 2711), USD bn", "Egypt-reported.")


def wheat_sourcing(df: pd.DataFrame, path: Path) -> None:
    main = ["Russian Federation", "Ukraine", "Romania", "France"]
    d = df.assign(origin=df.origin.where(df.origin.isin(main), "Other"))
    pivot = d.pivot_table(index="year", columns="origin", values="share", aggfunc="sum").fillna(0)
    pivot = pivot[[*main, "Other"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = pd.Series(0.0, index=pivot.index)
    colors = [*SERIES[:4], OTHER]
    for color, col in zip(colors, pivot.columns, strict=True):
        ax.bar(
            pivot.index,
            pivot[col],
            bottom=bottom,
            color=color,
            width=0.72,
            edgecolor=SURFACE,
            linewidth=1.5,
            label=col.replace("Russian Federation", "Russia"),
        )
        bottom += pivot[col]
    for year in (2014, 2022, 2024, 2025):
        share = pivot.loc[year, "Russian Federation"]
        ax.text(
            year,
            share / 2,
            f"{share:.0%}",
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
        )
    ax.set_ylim(0, 1)
    _pct(ax, 0.2)
    ax.legend(ncols=5, loc="upper left", bbox_to_anchor=(0, -0.07), fontsize=9)
    ax.set_title("Russia's share of Egypt's wheat bill rose from 37% to 69%")
    _finish(
        fig,
        ax,
        path,
        "Origin of Egypt's wheat imports (HS 1001), share of value",
        "Egypt-reported.",
    )


def mirror_ratio(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.axhspan(1.0, 1.10, color=GRID, alpha=0.6, linewidth=0)
    ax.axhline(1.0, color=INK_2, linewidth=0.8)
    ax.text(
        2014, 1.105, "CIF/FOB band: imports should sit here", color=INK_2, fontsize=8.5, va="bottom"
    )
    for flow, color, label in (("import", IMPORT, "Imports"), ("export", EXPORT, "Exports")):
        s = df[df.egypt_flow == flow].sort_values("year")
        ax.plot(s.year, s.egypt_to_partner_ratio, color=color, marker="o", markersize=4)
        _label_end(
            ax,
            s.year.iloc[-1],
            s.egypt_to_partner_ratio.iloc[-1],
            f"{label} {s.egypt_to_partner_ratio.iloc[-1]:.2f}",
        )
    ax.set_ylim(0.7, 1.2)
    ax.set_xlim(2013.6, 2027.4)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}x")
    ax.set_title("Partners record more imports from Egypt than Egypt records as exports")
    _finish(
        fig,
        ax,
        path,
        "Egypt-reported value / partner-reported value, same partners and year",
        "Mirror statistics; 2024-25 cover fewer reporting partners.",
    )
