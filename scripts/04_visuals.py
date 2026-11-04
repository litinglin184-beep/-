# -*- coding: utf-8 -*-
"""
04_visuals.py —— 足球博彩项目全部图表（22 张）

  fig01–fig15  对照《Excel 数据可视化》模板复现的 15 种图表
  fig16–fig22  与 7 类商业模型一一对应的业务图

用法
  python 04_visuals.py           # 全部重绘
  python 04_visuals.py 5 11 19   # 只重绘指定编号
"""
import json
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from scipy import stats as sps

from config import (C_ACC, C_ALT, C_GREY, C_LIGHT, C_MAIN, C_WARN, CLEAN, PALETTE,
                    STATS, TAB, finish, save, setup_style)

setup_style()
WANT = {int(x) for x in sys.argv[1:] if x.isdigit()}
R = lambda n: pd.read_csv(CLEAN / n, encoding="utf-8-sig")
T = lambda n: pd.read_csv(TAB / n, encoding="utf-8-sig")
want = lambda i: (not WANT) or (i in WANT)

S = json.loads(STATS.read_text(encoding="utf-8"))
M = R("matches_clean.csv")
M["日期"] = pd.to_datetime(M["日期"])
SEA = T("t03_赛季趋势.csv")
LEA = T("t04_联赛对比.csv")
SRC = "数据来源：Football-Data.co.uk 五大联赛＋荷甲/葡超 2010/11–2024/25 共 105 个赛季文件"


# ============================ fig01 柱线组合 ============================
def fig01():
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    x = np.arange(len(SEA))
    ax.bar(x, SEA["场次"], color=C_MAIN, width=0.62, label="场次（场）")
    ax.set_ylabel("场次（场）")
    ax.set_xticks(x)
    ax.set_xticklabels(SEA["赛季"], rotation=45, ha="right", fontsize=8)
    ax.set_xlim(-0.7, len(x) - 0.3)
    ax2 = ax.twinx()
    ax2.plot(x, SEA["场均进球"], color=C_ACC, marker="o", ms=5, lw=2.2, label="场均进球（球）")
    ax2.set_ylabel("场均进球（球）", color=C_ACC)
    ax2.tick_params(axis="y", colors=C_ACC)
    ax2.spines["top"].set_visible(False)
    for i in (0, len(SEA) - 1):
        v = SEA["场均进球"].iloc[i]
        ax2.annotate(f"{v:.2f}", (i, v), xytext=(0, 9), textcoords="offset points",
                     ha="center", fontsize=8.5, color=C_ACC, fontweight="bold")
    ax.set_ylim(0, SEA["场次"].max() * 1.18)
    ax2.set_ylim(SEA["场均进球"].min() * 0.94, SEA["场均进球"].max() * 1.06)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left", fontsize=8.5, ncol=2)
    finish(ax, "图01  赛季场次与场均进球：产量稳定、进球温和上行",
           f"15 个赛季共 {SEA.场次.sum():,} 场｜场均进球 {SEA.场均进球.min():.2f}–{SEA.场均进球.max():.2f} 球",
           SRC, grid_axis="y")
    save(fig, "fig01_赛季场次与场均进球.png")


# ============================ fig02 折线 + 移动平均 ============================
def fig02():
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    x = np.arange(len(SEA))
    ax.plot(x, SEA["抽水率"], color=C_MAIN, marker="o", ms=5.5, lw=2.2, label="抽水率")
    ax.plot(x, SEA["抽水率MA3"], color=C_ACC, lw=2.6, ls="--", label="3 季移动平均")
    ax.fill_between(x, SEA["抽水率"], SEA["抽水率"].min() - 0.2, color=C_LIGHT, alpha=0.55)
    i0, i1 = 0, len(SEA) - 1
    ax.annotate(f"{SEA.抽水率.iloc[i0]:.2f}%", (i0, SEA.抽水率.iloc[i0]), xytext=(6, 12),
                textcoords="offset points", fontsize=9, color=C_MAIN, fontweight="bold")
    ax.annotate(f"{SEA.抽水率.iloc[i1]:.2f}%", (i1, SEA.抽水率.iloc[i1]), xytext=(-6, 12),
                textcoords="offset points", fontsize=9, color=C_WARN, fontweight="bold", ha="right")
    ax.axhline(SEA["抽水率"].mean(), color=C_GREY, lw=1, ls=":")
    ax.text(0.2, SEA["抽水率"].mean() + 0.06, f"15 季均值 {SEA.抽水率.mean():.2f}%",
            fontsize=8.5, color=C_GREY)
    ax.set_xticks(x)
    ax.set_xticklabels(SEA["赛季"], rotation=45, ha="right", fontsize=8)
    ax.set_xlim(-0.7, len(x) - 0.3)
    ax.set_ylabel("抽水率（%）")
    ax.set_ylim(SEA["抽水率"].min() - 0.35, SEA["抽水率"].max() + 0.55)
    finish(ax, "图02  抽水率 15 年下降 2.07 个百分点：市场在变「薄」",
           "抽水率 = 1/主胜赔 + 1/平局赔 + 1/客胜赔 − 1，即博彩公司的理论毛利率",
           SRC, legend=True)
    save(fig, "fig02_抽水率趋势与移动平均.png")


# ============================ fig03 正负柱 ============================
def fig03():
    d = SEA.dropna(subset=["抽水率环比"]).copy()
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    x = np.arange(len(d))
    col = [C_ALT if v > 0 else C_WARN for v in d["抽水率环比"]]
    ax.bar(x, d["抽水率环比"], color=col, width=0.62)
    ax.axhline(0, color="#404040", lw=1)
    for i, v in enumerate(d["抽水率环比"]):
        ax.annotate(f"{v:+.2f}", (i, v), xytext=(0, 5 if v > 0 else -12),
                    textcoords="offset points", ha="center", fontsize=7.8,
                    color=C_ALT if v > 0 else C_WARN)
    ax.set_xticks(x)
    ax.set_xticklabels(d["赛季"], rotation=45, ha="right", fontsize=8)
    ax.set_xlim(-0.7, len(x) - 0.3)
    ax.set_ylabel("环比变化（百分点）")
    up, dn = int((d["抽水率环比"] > 0).sum()), int((d["抽水率环比"] < 0).sum())
    finish(ax, "图03  抽水率环比：14 次变动中 10 次为下降",
           f"上升 {up} 次、下降 {dn} 次；两次最大降幅出现在 2019/20 与 2024/25",
           SRC)
    save(fig, "fig03_抽水率环比变化.png")


# ============================ fig04 累计面积图 ============================
def fig04():
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    x = np.arange(len(SEA))
    cum = SEA["场次"].cumsum() / 1e4
    ax.fill_between(x, cum, color=C_LIGHT, alpha=0.85)
    ax.plot(x, cum, color=C_MAIN, lw=2.2)
    ax.set_ylabel("累计场次（万场）")
    ax2 = ax.twinx()
    ax2.plot(x, SEA["抽水率"], color=C_WARN, lw=2.0, marker="s", ms=4)
    ax2.set_ylabel("同期抽水率（%）", color=C_WARN)
    ax2.tick_params(axis="y", colors=C_WARN)
    ax2.spines["top"].set_visible(False)
    ax.set_xticks(x)
    ax.set_xticklabels(SEA["赛季"], rotation=45, ha="right", fontsize=8)
    ax.set_xlim(-0.7, len(x) - 0.3)
    ax.annotate(f"累计 {cum.iloc[-1]:.2f} 万场", (len(SEA) - 1, cum.iloc[-1]),
                xytext=(-8, -22), textcoords="offset points", ha="right",
                fontsize=9, color=C_MAIN, fontweight="bold")
    finish(ax, "图04  样本累积与抽水率同步下行",
           "样本量线性增长、抽水率持续走低——这不是抽样噪声，而是行业结构性变化",
           SRC)
    save(fig, "fig04_累计场次与抽水率.png")


# ============================ fig05 环形图 ============================
def fig05():
    tr = S["trend"]
    vals = [tr["主胜率全样本"], tr["平局率全样本"], tr["客胜率全样本"]]
    labs = ["主胜", "平局", "客胜"]
    cols = [C_MAIN, "#BFBFBF", C_ACC]
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    w, _ = ax.pie(vals, colors=cols, startangle=90, counterclock=False,
                  wedgeprops=dict(width=0.34, edgecolor="white", linewidth=2))
    ax.text(0, 0.12, f"{vals[0]:.1f}%", ha="center", va="center",
            fontsize=20, fontweight="bold", color=C_MAIN)
    ax.text(0, -0.16, "主胜占比", ha="center", va="center", fontsize=10, color=C_GREY)
    ax.legend(w, [f"{l}  {v:.2f}%" for l, v in zip(labs, vals)],
              loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False, fontsize=9)
    finish(ax, "图05  赛果结构：主场仍是六成球队的「隐形加成」",
           "样本 35,981 场；平局率 24.94%，低于足球分析中常见的 26% 经验值",
           SRC, grid_axis="none")
    save(fig, "fig05_赛果结构环形图.png")


# ============================ fig06 横向条形 ============================
def fig06():
    d = LEA.sort_values("场均进球")
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    y = np.arange(len(d))
    bars = ax.barh(y, d["场均进球"], color=[C_ACC if v == d["场均进球"].max() else C_MAIN
                                          for v in d["场均进球"]], height=0.6)
    for b, v in zip(bars, d["场均进球"]):
        ax.text(v + 0.03, b.get_y() + b.get_height() / 2, f"{v:.3f}",
                va="center", fontsize=9, color="#333333")
    ax.set_yticks(y)
    ax.set_yticklabels(d["联赛"], fontsize=9.5)
    ax.set_xlabel("场均进球（球）")
    ax.set_xlim(0, d["场均进球"].max() * 1.14)
    finish(ax, "图06  联赛进球效率：荷甲最高、法甲最低，差距 0.55 球",
           "荷甲 3.11 球 vs 法甲 2.56 球——大球策略必须按联赛分别设定阈值",
           SRC, grid_axis="x")
    save(fig, "fig06_联赛场均进球对比.png")


# ============================ fig07 漏斗 ============================
def fig07():
    n_all = len(M)
    steps = {
        "原始记录": 35997,
        "清洗后有效场次": n_all,
        "含完整 1X2 平均赔率": int(M["平均主胜赔"].notna().sum()),
        "含大小球 2.5 赔率": int(M["大25赔"].notna().sum()),
        "含射门等技术统计": int(M["主射门"].notna().sum()),
        "含全部上述字段（建模可用）": int((M["平均主胜赔"].notna() & M["大25赔"].notna()
                                & M["主射门"].notna()).sum()),
    }
    labs, vals = list(steps), list(steps.values())
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    ymax = vals[0]
    for i, (l, v) in enumerate(zip(labs, vals)):
        w = v / ymax
        ax.add_patch(Rectangle((0.5 - w / 2, len(labs) - i - 0.68), w, 0.52,
                               color=PALETTE[i % len(PALETTE)], alpha=0.9, lw=0))
        ax.text(0.5, len(labs) - i - 0.42, f"{l}", ha="center", va="center",
                fontsize=9.5, color="white", fontweight="bold")
        ax.text(0.5 + w / 2 + 0.02, len(labs) - i - 0.42, f"{v:,}（{v / ymax * 100:.1f}%）",
                ha="left", va="center", fontsize=9, color="#333333")
    ax.set_xlim(0, 1.22)
    ax.set_ylim(0, len(labs) + 0.1)
    ax.axis("off")
    finish(ax, "图07  数据可用性漏斗：建模可用样本仍达 99.3%",
           "从 35,997 条原始记录到 35,xxx 条全字段可用样本，损耗主要来自早期赛季缺失技术统计",
           SRC, grid_axis="none")
    save(fig, "fig07_数据可用性漏斗.png")


# ============================ fig08 热力图 ============================
def fig08():
    p = M.pivot_table(index="联赛", columns="赛季", values="抽水率", aggfunc="mean")
    order = ["英超", "德甲", "西甲", "意甲", "法甲", "荷甲", "葡超"]
    p = p.reindex([o for o in order if o in p.index])
    fig, ax = plt.subplots(figsize=(11.2, 4.4))
    im = ax.imshow(p.values, cmap="RdYlGn_r", aspect="auto", vmin=3.4, vmax=8.2)
    ax.set_xticks(range(p.shape[1]))
    ax.set_xticklabels(p.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(p.shape[0]))
    ax.set_yticklabels(p.index, fontsize=9.5)
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            v = p.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=6.8,
                        color="white" if v > 6.4 or v < 4.0 else "#333333")
    cb = fig.colorbar(im, ax=ax, pad=0.012, fraction=0.024)
    cb.set_label("抽水率（%）", fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    finish(ax, "图08  赛季 × 联赛抽水率热力图：颜色整体由红转绿",
           "同一联赛内部逐年走低，且葡超/荷甲始终是抽水最重的两个市场",
           SRC, grid_axis="none")
    save(fig, "fig08_赛季联赛抽水率热力图.png")


# ============================ fig09 箱线图 ============================
def fig09():
    order = ["英超", "德甲", "西甲", "意甲", "法甲", "荷甲", "葡超"]
    data = [M.loc[M["联赛"] == l, "抽水率"].dropna().sample(
        min(4000, int((M["联赛"] == l).sum())), random_state=42).values
        for l in order if (M["联赛"] == l).any()]
    labs = [l for l in order if (M["联赛"] == l).any()]
    fig, ax = plt.subplots(figsize=(9.6, 4.9))
    bp = ax.boxplot(data, tick_labels=labs, patch_artist=True, widths=0.55,
                    medianprops=dict(color=C_WARN, lw=1.8),
                    flierprops=dict(marker="o", ms=2.4, mfc=C_GREY, mec="none", alpha=0.4),
                    whiskerprops=dict(color="#808080"), capprops=dict(color="#808080"))
    for i, b in enumerate(bp["boxes"]):
        b.set_facecolor(PALETTE[i % len(PALETTE)])
        b.set_alpha(0.55)
        b.set_edgecolor(PALETTE[i % len(PALETTE)])
    for i, d in enumerate(data, start=1):
        ax.text(i, np.median(d) + 0.16, f"{np.median(d):.2f}", ha="center",
                fontsize=8.5, color=C_WARN, fontweight="bold")
    ax.set_ylabel("单场抽水率（%）")
    finish(ax, "图09  逐场抽水率分布：离散度远小于联赛间差异",
           "箱体高度普遍在 0.8 个百分点以内，说明「联赛级」而非「单场级」才是定价差异的主因",
           SRC)
    save(fig, "fig09_联赛抽水率箱线图.png")


# ============================ fig10 雷达图 ============================
def fig10():
    d = LEA.set_index("联赛")
    feats = ["场均进球", "主胜率", "大球率", "抽水率", "平局率"]
    lab = ["场均进球", "主胜率", "大球率", "抽水率", "平局率"]
    Z = d[feats].copy()
    for c in feats:                                   # 极差标准化到 20–100
        lo, hi = Z[c].min(), Z[c].max()
        Z[c] = 20 + (Z[c] - lo) / (hi - lo + 1e-9) * 80
    ang = np.linspace(0, 2 * np.pi, len(feats), endpoint=False).tolist()
    ang += ang[:1]
    fig = plt.figure(figsize=(7.4, 6.2))
    ax = fig.add_subplot(111, polar=True)
    show = ["荷甲", "英超", "葡超", "法甲"]
    for i, lg in enumerate(show):
        if lg not in Z.index:
            continue
        v = Z.loc[lg, feats].tolist()
        v += v[:1]
        ax.plot(ang, v, lw=2.0, color=PALETTE[i], label=lg, marker="o", ms=3.6)
        ax.fill(ang, v, color=PALETTE[i], alpha=0.10)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(lab, fontsize=10)
    ax.set_ylim(0, 110)
    ax.set_yticks([20, 45, 70, 95])
    ax.set_yticklabels(["20", "45", "70", "95"], fontsize=7.5, color=C_GREY)
    ax.grid(color="#E3E3E3", lw=0.7)
    ax.legend(loc="upper right", bbox_to_anchor=(1.22, 1.10), frameon=False, fontsize=9)
    finish(ax, "图10  联赛特征雷达：不存在「全面占优」的联赛",
           "荷甲强于进球、英超强于低抽水、葡超四维居后——联赛选择是权衡而非择优",
           SRC, grid_axis="none")
    save(fig, "fig10_联赛特征雷达图.png")


# ============================ fig11 气泡图 ============================
def fig11():
    d = LEA.copy()
    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    sc = ax.scatter(d["抽水率"], d["场均进球"], s=d["场次"] / 8, c=d["主胜率"],
                    cmap="viridis", alpha=0.82, edgecolor="white", lw=1.4)
    for _, r in d.iterrows():
        ax.annotate(r["联赛"], (r["抽水率"], r["场均进球"]), xytext=(0, -14),
                    textcoords="offset points", ha="center", fontsize=9, color="#333333")
    cb = fig.colorbar(sc, ax=ax, pad=0.012, fraction=0.03)
    cb.set_label("主胜率（%）", fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    ax.set_xlabel("抽水率（%）")
    ax.set_ylabel("场均进球（球）")
    ax.set_xlim(d["抽水率"].min() - 0.4, d["抽水率"].max() + 0.5)
    ax.set_ylim(d["场均进球"].min() - 0.08, d["场均进球"].max() + 0.12)
    finish(ax, "图11  抽水率 × 场均进球 × 场次：三者的权衡关系",
           "气泡大小=场次，颜色=主胜率；葡超/荷甲落在「高抽水」一侧，英超落在「低抽水＋高主胜」角落",
           SRC, grid_axis="both")
    save(fig, "fig11_联赛气泡图.png")


# ============================ fig12 校准散点 ============================
def fig12():
    d = T("t06_概率校准.csv").dropna(subset=["隐含", "实际"]).copy()
    if d["实际"].max() <= 1.0:                 # 源表为 0–1 小数，统一换算为百分数
        d["实际"] = d["实际"] * 100
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    cols = {"主胜": C_MAIN, "平局": C_ACC, "客胜": C_ALT}
    for t, g in d.groupby("类型"):
        ax.scatter(g["隐含"], g["实际"], s=np.sqrt(g["n"]) * 1.6, alpha=0.7,
                   color=cols.get(t, C_GREY), label=t, edgecolor="white", lw=0.8)
    ax.plot([0, 100], [0, 100], color=C_WARN, lw=1.6, ls="--", label="完美校准线")
    ax.set_xlabel("市场隐含概率（%）")
    ax.set_ylabel("实际命中率（%）")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    cl = S["calib"]
    ax.text(4, 92, f"Brier = {cl['Brier']:.4f}\nLogLoss = {cl['LogLoss']:.4f}\n"
                   f"冷门概率高估 {abs(cl['高估冷门']):.2f} 个百分点",
            fontsize=9.5, va="top", color="#333333",
            bbox=dict(fc="#F7FAFE", ec="#D6E2F0", lw=0.8, pad=6))
    finish(ax, "图12  概率校准：市场对冷门的定价系统性偏高",
           "气泡=该概率区间的场次数；对角线以上为低估、以下为高估",
           SRC, grid_axis="both", legend=True)
    save(fig, "fig12_概率校准散点.png")


# ============================ fig13 直方图 ============================
def fig13():
    d = M["总进球"].dropna()
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    bins = np.arange(-0.5, 12.5, 1)
    ax.hist(d, bins=bins, color=C_LIGHT, edgecolor="white", density=True, label="实际分布")
    lam = d.mean()
    xs = np.arange(0, 12)
    ax.plot(xs, sps.poisson.pmf(xs, lam), color=C_ACC, marker="o", ms=5, lw=2,
            label=f"泊松拟合 λ={lam:.2f}")
    ax.set_xlabel("单场总进球（球）")
    ax.set_ylabel("概率密度")
    ax.set_xticks(xs)
    finish(ax, "图13  单场总进球分布：泊松拟合良好，但 0-0 与 1-1 被低估",
           f"实际均值 {lam:.2f} 球；0 球与 2 球的观测频率高于泊松预测，是大小球定价的常见误差来源",
           SRC, legend=True)
    save(fig, "fig13_总进球分布直方图.png")


# ============================ fig14 100% 堆叠 ============================
def fig14():
    d = M.pivot_table(index="赛季", columns="赛果", values="主胜", aggfunc="size").fillna(0)
    d = d.div(d.sum(axis=1), axis=0) * 100
    for c in ("H", "D", "A"):
        if c not in d.columns:
            d[c] = 0
    d = d[["H", "D", "A"]]
    # 按联赛看更直观：改为联赛 × 赛果
    e = M.pivot_table(index="联赛", columns="赛果", values="主胜", aggfunc="size").fillna(0)
    e = e.div(e.sum(axis=1), axis=0) * 100
    e = e.reindex(["英超", "德甲", "西甲", "意甲", "法甲", "荷甲", "葡超"])
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    bottom = np.zeros(len(e))
    for c, lab, col in [("H", "主胜", C_MAIN), ("D", "平局", "#BFBFBF"), ("A", "客胜", C_ACC)]:
        v = e[c].values
        ax.bar(e.index, v, bottom=bottom, color=col, label=lab, width=0.62)
        for i, (b, x) in enumerate(zip(bottom, v)):
            if x > 4:
                ax.text(i, b + x / 2, f"{x:.1f}%", ha="center", va="center",
                        fontsize=8.5, color="white", fontweight="bold")
        bottom += v
    ax.set_ylabel("占比（%）")
    ax.set_ylim(0, 100)
    finish(ax, "图14  赛果结构按联赛：主胜率 42.6%–46.5%，平局率恒定在 24%–26%",
           "七联赛的平局率极差仅 2.1 个百分点——这是「平局难预测」的统计证据",
           SRC, legend=True)
    save(fig, "fig14_联赛赛果结构堆叠.png")


# ============================ fig15 双轴图 ============================
def fig15():
    fig, ax = plt.subplots(figsize=(9.6, 4.9))
    x = np.arange(len(SEA))
    ax.plot(x, SEA["场均进球"], color=C_MAIN, lw=2.2, marker="o", ms=4.5,
            label="场均进球（球）")
    ax.fill_between(x, 2.55, SEA["场均进球"], color=C_LIGHT, alpha=0.6)
    ax.set_ylabel("场均进球（球）", color=C_MAIN)
    ax.set_ylim(2.55, 2.98)
    ax2 = ax.twinx()
    ax2.plot(x, SEA["抽水率"], color=C_WARN, lw=2.2, marker="D", ms=4.5, label="抽水率（%）")
    ax2.set_ylabel("抽水率（%）", color=C_WARN)
    ax2.tick_params(axis="y", colors=C_WARN)
    ax2.spines["top"].set_visible(False)
    r = np.corrcoef(SEA["场均进球"], SEA["抽水率"])[0, 1]
    ax.set_xticks(x)
    ax.set_xticklabels(SEA["赛季"], rotation=45, ha="right", fontsize=8)
    ax.set_xlim(-0.7, len(x) - 0.3)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, loc="lower left", fontsize=8.5, ncol=2)
    finish(ax, "图15  进球数与抽水率的年度错位",
           f"两者相关系数 r = {r:+.2f}：抽水率由竞争格局决定，与进球数无稳定同步关系",
           SRC)
    save(fig, "fig15_场均进球与抽水率双轴.png")


# ============================ fig16 帕累托 ============================
def fig16():
    d = T("t05_比分帕累托.csv").head(15)
    fig, ax = plt.subplots(figsize=(9.8, 4.9))
    x = np.arange(len(d))
    ax.bar(x, d["占比"], color=[C_WARN if g == "A" else (C_ACC if g == "B" else C_MAIN)
                              for g in d["等级"]], width=0.62)
    ax.set_ylabel("占比（%）")
    ax.set_xticks(x)
    ax.set_xticklabels(d["比分"], fontsize=9)
    ax2 = ax.twinx()
    ax2.plot(x, d["累计"], color="#404040", marker="o", ms=4, lw=1.8)
    ax2.set_ylabel("累计占比（%）")
    ax2.set_ylim(0, 105)
    ax2.axhline(80, color=C_GREY, ls=":", lw=1)
    ax2.text(len(d) - 0.6, 81, "80% 线", fontsize=8, color=C_GREY, ha="right")
    for i in (0, 4, 9):
        ax2.annotate(f"TOP{i + 1} {d['累计'].iloc[i]:.1f}%", (i, d["累计"].iloc[i]),
                     xytext=(4, -14), textcoords="offset points", fontsize=8.5, color="#404040")
    finish(ax, "图16  比分帕累托：前 13 种比分覆盖 82% 的比赛",
           f"共 {S['pareto']['比分种类']} 种比分；1-1 单独占 {S['pareto']['TOP1占比']:.2f}%，"
           f"TOP5 合计 {S['pareto']['TOP5占比']:.1f}%",
           SRC)
    save(fig, "fig16_比分帕累托图.png")


# ============================ fig17 分群散点 ============================
def fig17():
    c = T("t07_比赛分群.csv")
    s = M.dropna(subset=["平均主胜赔", "平均客胜赔"]).sample(9000, random_state=42)
    # 用 03_analysis 产出的质心做最近质心分配（标准化空间），保证与建模口径一致
    mu = c[["主胜赔", "客胜赔"]].mean().values
    sd = c[["主胜赔", "客胜赔"]].std(ddof=0).replace(0, 1).values
    X = (s[["平均主胜赔", "平均客胜赔"]].values - mu) / sd
    C = (c[["主胜赔", "客胜赔"]].values - mu) / sd
    dist = ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
    lab = dist.argmin(axis=1)
    fig, ax = plt.subplots(figsize=(8.4, 6.0))
    for i, r in c.iterrows():
        m = lab == i
        ax.scatter(s["平均主胜赔"].values[m], s["平均客胜赔"].values[m], s=9, alpha=0.45,
                   color=PALETTE[i], label=f"{r['群名']}（{r['占比']:.2f}%）")
        ax.scatter([r["主胜赔"]], [r["客胜赔"]], s=280, marker="*", color=PALETTE[i],
                   edgecolor="white", lw=1.2, zorder=5)
    ax.set_xlim(1.0, 8.0)
    ax.set_ylim(1.0, 12.0)
    ax.set_xlabel("平均主胜赔")
    ax.set_ylabel("平均客胜赔")
    finish(ax, f"图17  比赛分群（K={S['cluster']['K']}，轮廓系数 {S['cluster']['轮廓系数']:.3f}）",
           "星号为质心；两群按「强弱悬殊程度」自然分开，是赔率档位策略的基础",
           SRC, grid_axis="both", legend=True)
    save(fig, "fig17_比赛分群散点.png")


# ============================ fig18 ROI 矩阵热力 ============================
def fig18():
    d = T("t08_ROI矩阵.csv").set_index("赛季")
    d = d[["冷门局", "偏冷", "偏热", "大热"]]
    fig, ax = plt.subplots(figsize=(7.6, 6.4))
    vmax = np.nanmax(np.abs(d.values))
    im = ax.imshow(d.values, cmap="RdYlGn", aspect="auto", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(d.shape[1]))
    ax.set_xticklabels(d.columns, fontsize=9.5)
    ax.set_yticks(range(d.shape[0]))
    ax.set_yticklabels(d.index, fontsize=8.5)
    for i in range(d.shape[0]):
        for j in range(d.shape[1]):
            v = d.values[i, j]
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(v) > vmax * 0.62 else "#333333")
    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.035)
    cb.set_label("单位注码 ROI（%）", fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    pos = int((d.values > 0).sum())
    finish(ax, f"图18  赛季 × 赔率档位 ROI 矩阵：{d.size} 个格子里仅 {pos} 个为正",
           "绿色为正收益；没有任何一个档位在 15 个赛季里持续为正，长期期望必为负",
           SRC, grid_axis="none")
    save(fig, "fig18_赛季档位ROI矩阵.png")


# ============================ fig19 波士顿矩阵 ============================
def fig19():
    d = T("t09_联赛波士顿矩阵.csv")
    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    mx, my = S["bcg"]["份额中位"], S["bcg"]["增速中位"]
    ax.axvline(mx, color=C_GREY, lw=1, ls="--")
    ax.axhline(my, color=C_GREY, lw=1, ls="--")
    qc = {"明星": C_ALT, "金牛": C_MAIN, "问题": C_ACC, "瘦狗": C_WARN}
    for _, r in d.iterrows():
        ax.scatter(r["份额"], r["增速"], s=r["场次"] / 2.2, color=qc.get(r["象限"], C_GREY),
                   alpha=0.75, edgecolor="white", lw=1.4, zorder=4)
        ax.annotate(r["联赛"], (r["份额"], r["增速"]), xytext=(0, -20),
                    textcoords="offset points", ha="center", fontsize=9.5, color="#222222")
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    for tx, ty, t, c in [(0.055, 0.93, "明星（高份额·高增速）", C_ALT),
                         (0.72, 0.93, "问题（低份额·高增速）", C_ACC),
                         (0.055, 0.06, "金牛（高份额·低增速）", C_MAIN),
                         (0.72, 0.06, "瘦狗（低份额·低增速）", C_WARN)]:
        ax.text(tx, ty, t, transform=ax.transAxes, fontsize=8.8, color=c, fontweight="bold")
    ax.set_xlabel("场次份额（%）")
    ax.set_ylabel("进球数增速（近 3 季 vs 前 3 季，%）")
    ax.set_xlim(x1, x2)
    ax.set_ylim(min(y1, -12), max(y2, 16))
    finish(ax, "图19  联赛波士顿矩阵：份额与「比赛观赏性增速」的错配",
           f"分界线取双中位数（份额 {mx:.1f}%、增速 {my:.1f}%）",
           SRC, grid_axis="both")
    save(fig, "fig19_联赛波士顿矩阵.png")


# ============================ fig20 关联规则 ============================
def fig20():
    d = T("t10_关联规则.csv").sort_values("提升度", ascending=False).head(12)[::-1]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    y = np.arange(len(d))
    sc = ax.scatter(d["提升度"], y, s=d["共现次数"] / 60, c=d["置信度_前→后(%)"],
                    cmap="Blues", vmin=30, vmax=100, edgecolor="#404040", lw=0.8, zorder=4)
    for i, v in enumerate(d["提升度"]):
        ax.text(v + 0.06, i, f"{v:.2f}", va="center", fontsize=8.5, color="#333333")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{a} → {b}" for a, b in zip(d["前项"], d["后项"])], fontsize=9)
    ax.axvline(1.0, color=C_WARN, ls="--", lw=1.2)
    ax.text(1.02, len(d) - 0.6, "提升度 = 1", fontsize=8, color=C_WARN)
    cb = fig.colorbar(sc, ax=ax, pad=0.012, fraction=0.03)
    cb.set_label("置信度（%）", fontsize=8.5)
    cb.ax.tick_params(labelsize=8)
    ax.set_xlabel("提升度（Lift）")
    ax.set_xlim(0.9, d["提升度"].max() * 1.14)
    finish(ax, "图20  事件关联规则 TOP12：强规则全部围绕「进球」",
           f"49 条规则中 {S['rules']['提升度大于1']} 条提升度>1；最强规则 {S['rules']['最强']}"
           f"（提升度 {S['rules']['最强提升度']:.2f}）",
           SRC, grid_axis="x")
    save(fig, "fig20_关联规则图.png")


# ============================ fig21 预测 ============================
def fig21():
    hist = pd.DataFrame(S["forecast"]["历史"])
    fut = pd.DataFrame(S["forecast"]["抽水率预测"])
    hist["月份"] = pd.to_datetime(hist["月份"])
    fut["月份"] = pd.to_datetime(fut["月份"])
    fig, ax = plt.subplots(figsize=(9.8, 4.9))
    ax.plot(hist["月份"], hist["抽水率"], color=C_MAIN, lw=1.9, marker="o", ms=3.2,
            label="历史抽水率（月度）")
    ax.plot([hist["月份"].iloc[-1]] + fut["月份"].tolist(),
            [hist["抽水率"].iloc[-1]] + fut["点预测"].tolist(),
            color=C_ACC, lw=2.4, ls="--", marker="s", ms=4.5, label="ARIMA 点预测")
    ax.fill_between(pd.concat([pd.Series([hist["月份"].iloc[-1]]), fut["月份"]]),
                    [hist["抽水率"].iloc[-1]] + fut["下限95"].tolist(),
                    [hist["抽水率"].iloc[-1]] + fut["上限95"].tolist(),
                    color="#9DC3E6", alpha=0.35,
                    label="95% 置信区间")
    ax.axvline(hist["月份"].iloc[-1], color=C_GREY, ls=":", lw=1)
    fc = S["forecast"]["ARIMA"]
    ax.text(0.015, 0.06, f"MAPE {fc['MAPE']:.2f}%（朴素基准 {fc['朴素MAPE']:.2f}%）\n"
                         f"RMSE {fc['RMSE']:.4f} 个百分点",
            transform=ax.transAxes, fontsize=9, color="#333333",
            bbox=dict(fc="#F7FAFE", ec="#D6E2F0", lw=0.8, pad=6))
    ax.set_ylabel("抽水率（%）")
    finish(ax, "图21  抽水率 6 个月外推：维持在 5.3%–5.4% 的平台期",
           "预测值和平稳期均值几乎重合，说明抽水率已进入低波动的成熟阶段",
           SRC, legend=True)
    save(fig, "fig21_抽水率ARIMA预测.png")


# ============================ fig22 策略 ROI 对比 ============================
def fig22():
    b = S["bet"]
    names = ["盲目主胜", "押最高赔率", "押大热门"]
    roi = [b[n]["ROI"] for n in names]
    hit = [b[n]["命中率"] for n in names]
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    x = np.arange(len(names))
    bars = ax.bar(x, roi, color=[C_WARN, "#A6A6A6", C_ACC], width=0.5)
    for i, (v, h) in enumerate(zip(roi, hit)):
        ax.text(i, v - 4.2, f"{v:.2f}%", ha="center", fontsize=10.5,
                color="white", fontweight="bold")
        ax.text(i, 2.5, f"命中率 {h:.1f}%", ha="center", fontsize=9, color="#404040")
    ax.axhline(0, color="#404040", lw=1.2)
    ax.axhline(b["理论返还率"] - 100, color=C_MAIN, ls="--", lw=1.4)
    ax.text(len(names) - 0.45, b["理论返还率"] - 100 + 1.6,
            f"理论期望 {b['理论返还率'] - 100:.2f}%（= 返还率 {b['理论返还率']:.2f}% − 100）",
            fontsize=8.5, color=C_MAIN, ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel("单位注码 ROI（%）")
    ax.set_ylim(min(roi) - 10, 8)
    finish(ax, "图22  三种朴素策略的 ROI：全部亏损，且与命中率无关",
           f"共 {b['盲目主胜']['注数']:,} 注、每注 1 单位；命中率 54.15% 的「押大热门」反而亏得更多",
           SRC)
    save(fig, "fig22_策略ROI对比.png")


fns = [fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10,
       fig11, fig12, fig13, fig14, fig15, fig16, fig17, fig18, fig19, fig20,
       fig21, fig22]

if __name__ == "__main__":
    for i, fn in enumerate(fns, start=1):
        if want(i):
            try:
                fn()
            except Exception as e:
                print(f"  [FAIL] fig{i:02d} {fn.__name__}: {type(e).__name__}: {e}")
    print("done")
