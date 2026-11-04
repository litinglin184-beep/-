# -*- coding: utf-8 -*-
"""全局配置：路径、口径常量、配色与绘图风格（足球博彩项目）"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "data/raw", ROOT / "data/clean"
FIG, TAB, DOCS, DASH = (ROOT / "outputs/figures", ROOT / "outputs/tables",
                        ROOT / "docs", ROOT / "dashboard")
for d in (RAW, CLEAN, FIG, TAB, DOCS, DASH):
    d.mkdir(parents=True, exist_ok=True)
STATS = ROOT / "outputs/stats.json"

RANDOM_SEED = 42
MAIN_LEAGUES = ["E0", "D1", "SP1", "I1", "F1"]          # 五大联赛（主分析）
EXTRA_LEAGUES = ["N1", "P1"]                            # 荷甲/葡超（对照）
LEAGUE_CN = {"E0": "英超", "D1": "德甲", "SP1": "西甲", "I1": "意甲",
             "F1": "法甲", "N1": "荷甲", "P1": "葡超"}
SEASON_MIN, SEASON_MAX = 2010, 2024                     # 2010/11 – 2024/25
BACKTEST_SEASONS = 3                                    # 预测回测留出的赛季数
BET_SIZE = 1.0                                          # 策略回测单位注码（1 单位本金）

C_MAIN = "#1F4E79"
C_ACC = "#ED7D31"
C_ALT = "#70AD47"
C_WARN = "#C00000"
C_GREY = "#7F7F7F"
C_LIGHT = "#DCE6F1"
PALETTE = ["#1F4E79", "#ED7D31", "#70AD47", "#C00000", "#7030A0",
           "#2E75B6", "#FFC000", "#A5A5A5", "#5B9BD5", "#264478"]


def setup_style():
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"],
        "axes.unicode_minus": False,
        "figure.dpi": 160, "savefig.dpi": 160,
        "savefig.bbox": "tight", "savefig.facecolor": "white",
        "axes.titlesize": 12, "axes.labelsize": 10,
        "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
        "axes.edgecolor": "#BFBFBF", "axes.linewidth": 0.8,
        "figure.facecolor": "white",
    })


def finish(ax, title, subtitle=None,
           source="数据来源：Football-Data.co.uk 五大联赛 2010/11–2024/25 赛季",
           grid_axis="y", legend=False):
    ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold",
                 color="#1F1F1F", pad=24 if subtitle else 8)
    if subtitle:
        ax.text(0, 1.012, subtitle, transform=ax.transAxes, fontsize=8.8,
                color=C_GREY, ha="left", va="bottom")
    for s in ("top", "right"):
        if s in ax.spines:
            ax.spines[s].set_visible(False)
    if grid_axis in ("y", "both"):
        ax.yaxis.grid(True, ls="--", lw=0.6, color="#E0E0E0", alpha=0.9)
        ax.set_axisbelow(True)
    if grid_axis in ("x", "both"):
        ax.xaxis.grid(True, ls="--", lw=0.6, color="#E0E0E0", alpha=0.9)
        ax.set_axisbelow(True)
    if legend:
        ax.legend(frameon=False, fontsize=8.5)
    ax.figure.text(0.995, -0.02, source, ha="right", va="top",
                   fontsize=7, color="#A6A6A6")


def save(fig, name):
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [fig] {name}")
