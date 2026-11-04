# -*- coding: utf-8 -*-
"""
02_clean.py —— 足球赛事与赔率数据清洗、字段归一化

难点
  Football-Data.co.uk 的列结构在 15 个赛季里改过三次：
    2010/11–2012/13  用 Betbrain 聚合列（BbAvH / BbMxH），无标准 Max/Avg
    2013/14–2018/19  只有各公司原始赔率（B365/BW/IW/PS/WH/VC），无聚合列
    2019/20 起       新增 Max/Avg 聚合列与收盘赔率（C 后缀）
  若直接 concat 会出现大量空列。这里按「聚合列 → Betbrain 列 → 各公司均值」
  的优先级逐层回退，重建出统一的市场平均赔率与最高赔率。

清洗规则（写入 outputs/tables/t02_清洗日志.csv）
  C1  缺少赛果 FTR 的行（比赛未进行/数据缺失）
  C2  缺少市场平均主胜赔率的行（无法计算抽水率）
  C3  赔率非正数（录入错误）
  C4  抽水率异常（<0 或 >30%，超出正常盘口区间）
  C5  重复比赛（同日期同主客队）
  C6  日期解析失败

派生指标
  总进球、大 2.5 球、双方进球、赛果编码、抽水率（overround）、
  归一化隐含概率、冷门标记、主场优势、赛季序号
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from config import CLEAN, LEAGUE_CN, MAIN_LEAGUES, RAW, SEASON_MAX, SEASON_MIN, TAB

BOOKS = {"B365": "Bet365", "BW": "Bet&Win", "IW": "Interwetten",
         "PS": "Pinnacle", "WH": "William Hill", "VC": "VC Bet",
         "GB": "Gamebookers", "LB": "Ladbrokes", "SJ": "Stan James",
         "SB": "Sportingbet", "BS": "Blue Square"}

log = []


def pick(df, cands, how="first"):
    """按候选列顺序回退取列：第一个存在的列 / 或对存在的列求均值。"""
    cols = [c for c in cands if c in df.columns]
    if not cols:
        return pd.Series(np.nan, index=df.index)
    v = df[cols].apply(pd.to_numeric, errors="coerce")
    if how == "first":
        return v.bfill(axis=1).iloc[:, 0]
    if how == "mean":
        return v.mean(axis=1)
    if how == "max":
        return v.max(axis=1)
    raise ValueError(how)


def read_one(fp: Path) -> pd.DataFrame:
    d = pd.read_csv(fp, dtype=str, encoding="utf-8-sig", on_bad_lines="skip")
    d.columns = [c.strip() for c in d.columns]
    m = re.match(r"([A-Z]+\d)_(\d{4})\.csv", fp.name)
    div, season = m.group(1), m.group(2)
    y = 2000 + int(season[:2])

    book_cols = {}
    for k in BOOKS:
        for suf in ("H", "D", "A"):
            if f"{k}{suf}" in d.columns:
                book_cols[f"{k}{suf}"] = f"{k}{suf}"

    out = pd.DataFrame({
        "联赛代码": div,
        "联赛": LEAGUE_CN.get(div, div),
        "赛季": f"{y}/{str(y+1)[2:]}",
        "赛季起始年": y,
        "日期": pd.to_datetime(d.get("Date"), dayfirst=True, errors="coerce"),
        "主队": d.get("HomeTeam"),
        "客队": d.get("AwayTeam"),
        "主队进球": pd.to_numeric(d.get("FTHG"), errors="coerce"),
        "客队进球": pd.to_numeric(d.get("FTAG"), errors="coerce"),
        "赛果": d.get("FTR"),
        "半场主": pd.to_numeric(d.get("HTHG"), errors="coerce"),
        "半场客": pd.to_numeric(d.get("HTAG"), errors="coerce"),
        "主射门": pd.to_numeric(d.get("HS"), errors="coerce"),
        "客射门": pd.to_numeric(d.get("AS"), errors="coerce"),
        "主射正": pd.to_numeric(d.get("HST"), errors="coerce"),
        "客射正": pd.to_numeric(d.get("AST"), errors="coerce"),
        "主角球": pd.to_numeric(d.get("HC"), errors="coerce"),
        "客角球": pd.to_numeric(d.get("AC"), errors="coerce"),
        "主黄牌": pd.to_numeric(d.get("HY"), errors="coerce"),
        "客黄牌": pd.to_numeric(d.get("AY"), errors="coerce"),
        "主红牌": pd.to_numeric(d.get("HR"), errors="coerce"),
        "客红牌": pd.to_numeric(d.get("AR"), errors="coerce"),
    })

    # ---- 市场平均赔率：Avg → Betbrain BbAv → 各公司均值 ----
    out["平均主胜赔"] = pick(d, ["AvgH", "BbAvH"])
    out["平均平局赔"] = pick(d, ["AvgD", "BbAvD"])
    out["平均客胜赔"] = pick(d, ["AvgA", "BbAvA"])
    for suf, name in [("H", "主胜"), ("D", "平局"), ("A", "客胜")]:
        need = ["%s%s" % (k, suf) for k in BOOKS]
        avg = out[f"平均{name}赔"]
        out[f"平均{name}赔"] = avg.where(avg.notna(), pick(d, need, how="mean"))
    # ---- 最高赔率 ----
    out["最高主胜赔"] = pick(d, ["MaxH", "BbMxH"])
    out["最高平局赔"] = pick(d, ["MaxD", "BbMxD"])
    out["最高客胜赔"] = pick(d, ["MaxA", "BbMxA"])
    for suf, name in [("H", "主胜"), ("D", "平局"), ("A", "客胜")]:
        need = ["%s%s" % (k, suf) for k in BOOKS]
        out[f"最高{name}赔"] = out[f"最高{name}赔"].where(
            out[f"最高{name}赔"].notna(), pick(d, need, how="max"))

    # ---- 收盘赔率（仅 2019/20 起有）----
    out["收盘主胜赔"] = pick(d, ["AvgCH", "BbAvCH"])

    # ---- 大小球 ----
    out["大25赔"] = pick(d, ["Avg>2.5", "BbAv>2.5", "B365>2.5", "P>2.5", "PC>2.5"])
    out["小25赔"] = pick(d, ["Avg<2.5", "BbAv<2.5", "B365<2.5", "P<2.5", "PC<2.5"])

    # ---- 各公司赔率（用于公司间定价比较，保留原始列）----
    for k in BOOKS:
        for suf, name in [("H", "主"), ("D", "平"), ("A", "客")]:
            c = f"{k}{suf}"
            out[f"{BOOKS[k]}_{name}"] = pd.to_numeric(d[c], errors="coerce") if c in d.columns else np.nan
    return out


def main():
    files = sorted(RAW.glob("*.csv"))
    files = [f for f in files if not f.name.startswith("_")]
    assert files, "未找到原始数据，请先运行 01_download.py"
    print(f"读取 {len(files)} 个赛季文件")

    parts = []
    for f in files:
        d = read_one(f)
        if d.日期.notna().sum() == 0:
            print(f"  [skip] {f.name} 无有效日期")
            continue
        parts.append(d)
    raw = pd.concat(parts, ignore_index=True)
    n0 = len(raw)
    print(f"原始合计 {n0:,} 场")

    # C6 日期
    d = raw[raw.日期.notna()].copy()
    log.append({"规则": "C6 日期解析失败", "处理前": n0, "处理后": len(d),
                "影响行数": n0 - len(d), "说明": "Date 列格式异常"})
    # C1 赛果
    b = len(d); d = d[d.赛果.isin(["H", "D", "A"])]
    log.append({"规则": "C1 缺少赛果 FTR", "处理前": b, "处理后": len(d),
                "影响行数": b - len(d), "说明": "未进行或数据缺失的比赛"})
    # C3 赔率非正
    b = len(d)
    ok = (d.平均主胜赔 > 1) & (d.平均平局赔 > 1) & (d.平均客胜赔 > 1)
    d = d[ok]
    log.append({"规则": "C3 赔率非正/缺失", "处理前": b, "处理后": len(d),
                "影响行数": b - len(d), "说明": "三家赔率须齐全且 >1"})
    # C4 抽水率异常
    d["抽水率"] = (1 / d.平均主胜赔 + 1 / d.平均平局赔 + 1 / d.平均客胜赔 - 1) * 100
    b = len(d)
    d = d[(d.抽水率 > 0) & (d.抽水率 < 30)]
    log.append({"规则": "C4 抽水率越界（<0 或 >30%）", "处理前": b, "处理后": len(d),
                "影响行数": b - len(d), "说明": "正常盘口抽水率 1%–15%"})
    # C5 重复
    b = len(d)
    d = d.drop_duplicates(subset=["日期", "主队", "客队"])
    log.append({"规则": "C5 重复比赛", "处理前": b, "处理后": len(d),
                "影响行数": b - len(d), "说明": "同日期同主客队只保留一条"})
    # C2 联赛/赛季范围
    b = len(d)
    d = d[(d.赛季起始年 >= SEASON_MIN) & (d.赛季起始年 <= SEASON_MAX)]
    log.append({"规则": "C2 赛季范围外", "处理前": b, "处理后": len(d),
                "影响行数": b - len(d), "说明": f"保留 {SEASON_MIN}–{SEASON_MAX}"})

    # ---------------- 派生 ----------------
    d["总进球"] = d.主队进球 + d.客队进球
    d["大25"] = (d.总进球 > 2.5).astype(int)
    d["双方进球"] = ((d.主队进球 > 0) & (d.客队进球 > 0)).astype(int)
    d["主胜"] = (d.赛果 == "H").astype(int)
    d["平局"] = (d.赛果 == "D").astype(int)
    d["客胜"] = (d.赛果 == "A").astype(int)
    d["净胜球"] = d.主队进球 - d.客队进球

    # 归一化隐含概率（去掉抽水后的"公平概率"）
    inv = 1 / d.平均主胜赔 + 1 / d.平均平局赔 + 1 / d.平均客胜赔
    d["隐含主胜"] = (1 / d.平均主胜赔) / inv * 100
    d["隐含平局"] = (1 / d.平均平局赔) / inv * 100
    d["隐含客胜"] = (1 / d.平均客胜赔) / inv * 100

    # 冷门程度：按归一化隐含概率排序，最低者夺冠即为冷门
    d["最大隐含概率"] = d[["隐含主胜", "隐含平局", "隐含客胜"]].max(axis=1)
    d["最小隐含概率"] = d[["隐含主胜", "隐含平局", "隐含客胜"]].min(axis=1)

    # 主场优势：主胜概率 - 客胜概率
    d["主场优势"] = d.隐含主胜 - d.隐含客胜
    d["是否五大联赛"] = d.联赛代码.isin(MAIN_LEAGUES)
    d["月份"] = d.日期.dt.month
    d["年季序"] = d.赛季起始年 + (d.月份 >= 7).astype(int) * 0  # 保留原始赛季序

    # 排序落盘
    d = d.sort_values(["日期", "联赛代码"]).reset_index(drop=True)
    keep = ["联赛代码", "联赛", "赛季", "赛季起始年", "日期", "主队", "客队",
            "主队进球", "客队进球", "赛果", "半场主", "半场客",
            "主射门", "客射门", "主射正", "客射正", "主角球", "客角球",
            "主黄牌", "客黄牌", "主红牌", "客红牌", "总进球", "大25", "双方进球",
            "主胜", "平局", "客胜", "净胜球",
            "平均主胜赔", "平均平局赔", "平均客胜赔",
            "最高主胜赔", "最高平局赔", "最高客胜赔", "收盘主胜赔",
            "大25赔", "小25赔", "抽水率",
            "隐含主胜", "隐含平局", "隐含客胜", "最大隐含概率", "最小隐含概率",
            "主场优势", "是否五大联赛", "月份", "年季序"]
    keep += [c for c in d.columns if c.startswith(tuple(BOOKS.values())) and c not in keep]
    d = d[keep]
    d.to_csv(CLEAN / "matches_clean.csv", index=False, encoding="utf-8-sig")

    import sqlite3
    con = sqlite3.connect(CLEAN / "football.sqlite")
    d.to_sql("matches", con, if_exists="replace", index=False)
    agg = (d.groupby(["联赛代码", "联赛", "赛季"]).size().rename("场次").reset_index())
    agg.to_sql("league_season", con, if_exists="replace", index=False)
    agg.to_csv(CLEAN / "league_season.csv", index=False, encoding="utf-8-sig")
    con.close()

    pd.DataFrame(log).to_csv(TAB / "t02_清洗日志.csv", index=False, encoding="utf-8-sig")

    # 数据字典
    dic = [
        ("联赛代码", "str", "联赛代码", "E0 英超 / D1 德甲 / SP1 西甲 / I1 意甲 / F1 法甲 / N1 荷甲 / P1 葡超"),
        ("赛季", "str", "赛季", "如 2010/11"),
        ("日期", "date", "比赛日期", "当地时间"),
        ("主队", "str", "主队", "球队英文名（原数据口径，15 季内名称可能变更）"),
        ("客队", "str", "客队", "同上"),
        ("主队进球", "int", "主队全场进球", "全场比分"),
        ("客队进球", "int", "客队全场进球", "全场比分"),
        ("赛果", "str", "赛果", "H 主胜 / D 平局 / A 客胜"),
        ("平均主胜赔", "float", "市场平均主胜赔率", "优先 Avg/AvgH，其次 Betbrain 均值，最后各公司算术均值"),
        ("最高主胜赔", "float", "市场最高主胜赔率", "同期各公司最高值，代表最优可得价格"),
        ("收盘主胜赔", "float", "收盘时平均主胜赔率", "仅 2019/20 起有数据，用于检验信息含量"),
        ("抽水率", "float", "抽水率（%）", "overround = (1/H+1/D+1/A−1)×100"),
        ("隐含主胜", "float", "归一化隐含主胜概率（%）", "1/H ÷ Σ(1/O)，即去掉抽水后的公平概率"),
        ("大25", "int", "是否大 2.5 球", "总进球 ≥3 记为 1"),
        ("双方进球", "int", "是否双方进球", "主客队均进球"),
        ("主场优势", "float", "主场优势度", "隐含主胜 − 隐含客胜（百分点）"),
    ]
    pd.DataFrame(dic, columns=["字段", "类型", "中文名", "口径说明"]).to_csv(
        TAB / "t01_数据字典.csv", index=False, encoding="utf-8-sig")

    print(f"\n清洗后 {len(d):,} 场，{d.联赛.nunique()} 个联赛，"
          f"{d.赛季.nunique()} 个赛季，{d.日期.min().date()} ~ {d.日期.max().date()}")
    print(d.联赛.value_counts().to_string())


if __name__ == "__main__":
    main()
