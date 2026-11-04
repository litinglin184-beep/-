# -*- coding: utf-8 -*-
"""
03_analysis.py —— 足球博彩项目核心分析（7 类商业模型）

业务问题：博彩平台如何给比赛定价？定价是否有系统性偏差？哪些市场能被击败？

  M1 趋势与结构   抽水率、主场胜率、场均进球的 15 季演化 + 移动平均
  M2 帕累托/ABC   正确比分的概率集中度（比分盘的定价难度）
  M3 K-Means 分群 按赔率结构对 3.6 万场比赛聚类，识别可定价的比赛类型
  M4 同期群矩阵   赛季 × 赔率档的投注回报率（ROI）矩阵
  M5 波士顿矩阵   联赛作为"产品组合"：场次份额 × 观赏性（场均进球）增速
  M6 关联规则     比赛事件的共现规则（Apriori 成对等价实现）
  M7 双预测       ① 逻辑回归 vs 市场隐含概率（校准 + Brier）
                  ② ARIMA 预测月度抽水率（95% CI + 滚动回测）
"""
import json
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, silhouette_score
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA

from config import CLEAN, LEAGUE_CN, MAIN_LEAGUES, RANDOM_SEED, STATS, TAB

warnings.filterwarnings("ignore")
OUT = {}


def r2(x, n=2):
    try:
        return float(np.round(x, n))
    except Exception:
        return None


def load():
    d = pd.read_csv(CLEAN / "matches_clean.csv", parse_dates=["日期"], encoding="utf-8-sig")
    return d


# ============================ M1 趋势 ============================
def trend(d):
    s = (d.groupby("赛季").agg(场次=("主胜", "size"), 主胜率=("主胜", "mean"),
                               平局率=("平局", "mean"), 客胜率=("客胜", "mean"),
                               场均进球=("总进球", "mean"), 大球率=("大25", "mean"),
                               抽水率=("抽水率", "mean"), 双进球率=("双方进球", "mean"),
                               主场优势=("主场优势", "mean")).reset_index())
    s["主胜率"] *= 100; s["平局率"] *= 100; s["客胜率"] *= 100
    s["大球率"] *= 100; s["双进球率"] *= 100
    s["抽水率环比"] = s.抽水率.pct_change() * 100
    s["抽水率MA3"] = s.抽水率.rolling(3).mean()
    s["主胜率MA3"] = s.主胜率.rolling(3).mean()

    first, last = s.iloc[0], s.iloc[-1]
    OUT["trend"] = {
        "赛季": s.round(3).to_dict("records"),
        "首季": first.赛季, "末季": last.赛季,
        "抽水率首": r2(first.抽水率), "抽水率末": r2(last.抽水率),
        "抽水率变化": r2(last.抽水率 - first.抽水率),
        "主胜率首": r2(first.主胜率), "主胜率末": r2(last.主胜率),
        "场均进球首": r2(first.场均进球), "场均进球末": r2(last.场均进球),
        "场均进球变化": r2(last.场均进球 - first.场均进球),
        "抽水率均值": r2(d.抽水率.mean()), "抽水率中位": r2(d.抽水率.median()),
        "主胜率全样本": r2(d.主胜.mean() * 100), "平局率全样本": r2(d.平局.mean() * 100),
        "客胜率全样本": r2(d.客胜.mean() * 100),
        "场均进球全样本": r2(d.总进球.mean()), "大球率全样本": r2(d.大25.mean() * 100),
    }
    s.to_csv(TAB / "t03_赛季趋势.csv", index=False, encoding="utf-8-sig")

    # 联赛对比
    lg = (d.groupby(["联赛代码", "联赛"]).agg(
        场次=("主胜", "size"), 主胜率=("主胜", "mean"), 平局率=("平局", "mean"),
        场均进球=("总进球", "mean"), 抽水率=("抽水率", "mean"),
        大球率=("大25", "mean")).reset_index())
    for c in ("主胜率", "平局率", "大球率"):
        lg[c] *= 100
    lg = lg.sort_values("抽水率")
    OUT["league"] = {
        "列表": lg.round(3).to_dict("records"),
        "抽水率最低": lg.iloc[0].联赛, "抽水率最低值": r2(lg.iloc[0].抽水率),
        "抽水率最高": lg.iloc[-1].联赛, "抽水率最高值": r2(lg.iloc[-1].抽水率),
        "进球最多联赛": lg.loc[lg.场均进球.idxmax()].联赛,
        "进球最多值": r2(lg.场均进球.max()),
    }
    lg.to_csv(TAB / "t04_联赛对比.csv", index=False, encoding="utf-8-sig")


# ============================ M2 帕累托 ============================
def pareto(d):
    sc = d.groupby(["主队进球", "客队进球"]).size().rename("场次").reset_index()
    sc["比分"] = sc.主队进球.astype(int).astype(str) + "-" + sc.客队进球.astype(int).astype(str)
    sc = sc.sort_values("场次", ascending=False).reset_index(drop=True)
    sc["占比"] = sc.场次 / sc.场次.sum() * 100
    sc["累计"] = sc.占比.cumsum()
    nA = int((sc.累计 <= 80).sum()) + 1
    nB = int((sc.累计 <= 95).sum()) + 1
    sc["等级"] = np.where(sc.index < nA, "A", np.where(sc.index < nB, "B", "C"))

    OUT["pareto"] = {
        "比分种类": int(len(sc)), "A类": nA, "A类占比": r2(nA / len(sc) * 100),
        "A类概率覆盖": r2(sc[sc.等级 == "A"].占比.sum()),
        "TOP1": sc.iloc[0].比分, "TOP1占比": r2(sc.iloc[0].占比),
        "TOP5占比": r2(sc.head(5).占比.sum()),
        "TOP10占比": r2(sc.head(10).占比.sum()),
        "TOP10": sc.head(10)[["比分", "场次", "占比", "累计"]].round(3).to_dict("records"),
        "C类占比": r2(sc[sc.等级 == "C"].占比.sum()),
    }
    sc.round(3).to_csv(TAB / "t05_比分帕累托.csv", index=False, encoding="utf-8-sig")


# ============================ 校准与偏差 ============================
def calibration(d):
    """把隐含概率按 5 个百分点分箱，比较预测频率与实际频率。"""
    rows = []
    for col, name in [("隐含主胜", "主胜"), ("隐含平局", "平局"), ("隐含客胜", "客胜")]:
        actual = d["主胜"] if name == "主胜" else (d["平局"] if name == "平局" else d["客胜"])
        bins = np.arange(0, 105, 5)
        g = pd.DataFrame({"p": d[col], "y": actual}).groupby(
            pd.cut(d[col], bins, right=False), observed=True).agg(
            隐含=("p", "mean"), 实际=("y", "mean"), n=("y", "size")).dropna()
        g["偏差"] = g.实际 * 100 - g.隐含
        g["类型"] = name
        rows.append(g.reset_index(drop=True))
    cal = pd.concat(rows, ignore_index=True)

    # 整体 Brier 与 LogLoss（市场隐含概率作为预测）
    P = d[["隐含主胜", "隐含平局", "隐含客胜"]].values / 100
    Y = d[["主胜", "平局", "客胜"]].values
    brier = float(np.mean(np.sum((P - Y) ** 2, axis=1)))
    ll = float(-np.mean(np.sum(Y * np.log(np.clip(P, 1e-15, 1)), axis=1)))

    # 分档偏差：按隐含概率五档
    d2 = d.copy()
    d2["档位"] = pd.qcut(d2.最大隐含概率, 5,
                         labels=["最低20%", "次低", "中", "次高", "最高20%"])
    fav = (d2.groupby("档位", observed=True)
           .agg(场次=("主胜", "size"), 隐含=("最大隐含概率", "mean"))
           .reset_index())
    hit = []
    for lab in fav.档位:
        sub = d2[d2.档位 == lab]
        ok = ((sub.隐含主胜 >= sub.隐含平局) & (sub.隐含主胜 >= sub.隐含客胜) & (sub.主胜 == 1)) | \
             ((sub.隐含平局 >= sub.隐含主胜) & (sub.隐含平局 >= sub.隐含客胜) & (sub.平局 == 1)) | \
             ((sub.隐含客胜 >= sub.隐含主胜) & (sub.隐含客胜 >= sub.隐含平局) & (sub.客胜 == 1))
        hit.append(ok.mean() * 100)
    fav["实际命中"] = hit
    fav["偏差"] = fav.实际命中 - fav.隐含

    # 冷门（favourite-longshot）：最低隐含概率项的实际频率
    ls = []
    for lo, hi in [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 45), (45, 60), (60, 101)]:
        sub = d[(d.最小隐含概率 >= lo) & (d.最小隐含概率 < hi)]
        if len(sub) < 50:
            continue
        ok = ((sub.隐含主胜 <= sub.隐含平局) & (sub.隐含主胜 <= sub.隐含客胜) & (sub.主胜 == 1)) | \
             ((sub.隐含平局 <= sub.隐含主胜) & (sub.隐含平局 <= sub.隐含客胜) & (sub.平局 == 1)) | \
             ((sub.隐含客胜 <= sub.隐含主胜) & (sub.隐含客胜 <= sub.隐含平局) & (sub.客胜 == 1))
        ls.append({"区间": f"{lo}-{hi}%", "场次": int(len(sub)),
                   "隐含": r2(sub.最小隐含概率.mean()), "实际": r2(ok.mean() * 100),
                   "偏差": r2(ok.mean() * 100 - sub.最小隐含概率.mean())})

    OUT["calib"] = {
        "校准": cal.round(3).to_dict("records"),
        "Brier": r2(brier, 4), "LogLoss": r2(ll, 4),
        "热门档": fav.round(3).to_dict("records"),
        "冷门偏差": ls,
        "高估冷门": r2(np.mean([x["偏差"] for x in ls if x["隐含"] < 15]) if ls else None),
    }
    cal.round(3).to_csv(TAB / "t06_概率校准.csv", index=False, encoding="utf-8-sig")


# ============================ M3 分群 ============================
def cluster(d):
    F = ["平均主胜赔", "平均平局赔", "平均客胜赔", "抽水率", "主场优势"]
    X = d[F].dropna()
    idx = X.index
    Z = StandardScaler().fit_transform(X)
    scan = []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_SEED).fit(Z)
        scan.append({"k": k, "inertia": float(km.inertia_),
                     "轮廓系数": float(silhouette_score(Z, km.labels_, sample_size=8000,
                                                        random_state=RANDOM_SEED))})
    best = max(scan, key=lambda x: x["轮廓系数"])["k"]
    km = KMeans(n_clusters=best, n_init=20, random_state=RANDOM_SEED).fit(Z)
    d.loc[idx, "簇"] = km.labels_

    prof = (d.dropna(subset=["簇"]).groupby("簇").agg(
        场次=("主胜", "size"), 主胜率=("主胜", "mean"), 平局率=("平局", "mean"),
        客胜率=("客胜", "mean"), 场均进球=("总进球", "mean"),
        抽水率=("抽水率", "mean"), 主胜赔=("平均主胜赔", "mean"),
        客胜赔=("平均客胜赔", "mean")).reset_index())
    for c in ("主胜率", "平局率", "客胜率"):
        prof[c] *= 100
    prof["占比"] = prof.场次 / prof.场次.sum() * 100

    # 命名：按主胜赔与平赔高低
    nm = {}
    q_h = prof.主胜赔.median()
    q_d = prof.平局率.median()
    for _, r in prof.iterrows():
        if r.主胜赔 <= q_h and r.平局率 <= q_d:
            nm[r.簇] = "强弱悬殊局"
        elif r.主胜赔 <= q_h:
            nm[r.簇] = "胶着强强局"
        elif r.场均进球 >= prof.场均进球.median():
            nm[r.簇] = "开放对攻局"
        else:
            nm[r.簇] = "低效闷战局"
    seen = {}
    for k, v in list(nm.items()):
        seen[v] = seen.get(v, 0) + 1
        if seen[v] > 1:
            nm[k] = f"{v}{seen[v]}"
    prof["群名"] = prof.簇.map(nm)
    d["群名"] = d.簇.map(nm)

    OUT["cluster"] = {"扫描": scan, "K": int(best),
                      "轮廓系数": r2([x["轮廓系数"] for x in scan if x["k"] == best][0], 3),
                      "画像": prof.round(2).to_dict("records")}
    prof.round(3).to_csv(TAB / "t07_比赛分群.csv", index=False, encoding="utf-8-sig")
    return d


# ============================ M4 同期群 / ROI ============================
def betting(d):
    """三种策略回测：盲目主胜、价值投注（最高赔率溢价）、冷门投注。"""
    d = d.copy()
    d["档位"] = pd.qcut(d.最大隐含概率, 4, labels=["冷门局", "偏冷", "偏热", "大热"])

    def roi(mask, ret):
        n = int(mask.sum())
        if n == 0:
            return {"注数": 0, "ROI": None}
        profit = ret[mask].sum() - n
        return {"注数": n, "命中率": r2((ret[mask] > 0).mean() * 100),
                "ROI": r2(profit / n * 100), "利润": r2(profit, 0)}

    # 策略 1：每场都押主胜
    r1 = np.where(d.主胜 == 1, d.平均主胜赔 - 1, -1.0)
    # 策略 2：押"最高赔率项"（市场分歧最大处）
    cols = ["最高主胜赔", "最高平局赔", "最高客胜赔"]
    pick = d[cols].idxmax(axis=1)
    odds = d[cols].max(axis=1)
    won = ((pick == "最高主胜赔") & (d.主胜 == 1)) | \
          ((pick == "最高平局赔") & (d.平局 == 1)) | \
          ((pick == "最高客胜赔") & (d.客胜 == 1))
    r2_ = np.where(won, odds - 1, -1.0)
    # 策略 3：押大热门（隐含概率最高项）
    fav_col = d[["隐含主胜", "隐含平局", "隐含客胜"]].idxmax(axis=1)
    fav_odds = np.where(fav_col == "隐含主胜", d.平均主胜赔,
                        np.where(fav_col == "隐含平局", d.平均平局赔, d.平均客胜赔))
    fav_won = ((fav_col == "隐含主胜") & (d.主胜 == 1)) | \
              ((fav_col == "隐含平局") & (d.平局 == 1)) | \
              ((fav_col == "隐含客胜") & (d.客胜 == 1))
    r3 = np.where(fav_won, fav_odds - 1, -1.0)

    # 同期群矩阵：赛季 × 档位 的"押大热门"ROI
    tmp = d.assign(收益=r3)
    mat = tmp.pivot_table(index="赛季", columns="档位", values="收益",
                          aggfunc="mean", observed=True) * 100

    OUT["bet"] = {
        "盲目主胜": roi(pd.Series(True, index=d.index), pd.Series(r1, index=d.index)),
        "押最高赔率": roi(pd.Series(True, index=d.index), pd.Series(r2_, index=d.index)),
        "押大热门": roi(pd.Series(True, index=d.index), pd.Series(r3, index=d.index)),
        "矩阵": {str(i): [r2(x) for x in row] for i, row in zip(mat.index, mat.values)},
        "档位": list(map(str, mat.columns)),
        "赛季": list(map(str, mat.index)),
        "理论返还率": r2(100 - d.抽水率.mean()),
    }
    mat.round(2).to_csv(TAB / "t08_ROI矩阵.csv", encoding="utf-8-sig")
    return d


# ============================ M5 波士顿矩阵 ============================
def bcg(d):
    g = (d.groupby(["联赛代码", "联赛"]).agg(
        场次=("主胜", "size"), 场均进球=("总进球", "mean"),
        抽水率=("抽水率", "mean"), 主胜率=("主胜", "mean")).reset_index())
    early = d[d.赛季起始年 <= 2014].groupby("联赛").总进球.mean()
    late = d[d.赛季起始年 >= 2020].groupby("联赛").总进球.mean()
    g["早期进球"] = g.联赛.map(early)
    g["近期进球"] = g.联赛.map(late)
    g["增速"] = (g.近期进球 / g.早期进球 - 1) * 100
    g["份额"] = g.场次 / g.场次.sum() * 100
    sm, gm = g.份额.median(), g.增速.median()
    g["象限"] = np.select([(g.份额 >= sm) & (g.增速 >= gm), (g.份额 >= sm) & (g.增速 < gm),
                           (g.份额 < sm) & (g.增速 >= gm)],
                          ["明星", "金牛", "问题"], default="瘦狗")
    OUT["bcg"] = {"联赛": g.round(3).to_dict("records"),
                  "份额中位": r2(sm), "增速中位": r2(gm),
                  "象限计数": g.象限.value_counts().to_dict()}
    g.round(3).to_csv(TAB / "t09_联赛波士顿矩阵.csv", index=False, encoding="utf-8-sig")


# ============================ M6 关联规则 ============================
def rules(d):
    """每场比赛的事件集合 → 成对规则（支持度/置信度/提升度）。"""
    ev = pd.DataFrame({
        "主胜": d.主胜 == 1, "平局": d.平局 == 1, "客胜": d.客胜 == 1,
        "大2.5球": d.大25 == 1, "小2.5球": d.大25 == 0,
        "双方进球": d.双方进球 == 1, "零封": d.双方进球 == 0,
        "上半场领先": d.半场主 > d.半场客,
        "红牌出现": (d.主红牌 + d.客红牌).fillna(0) > 0,
        "高角球": (d.主角球 + d.客角球) >= 11,
        "大比分": d.总进球 >= 4,
    })
    n = len(ev)
    sup = ev.mean()
    rows = []
    for a, b in combinations(ev.columns, 2):
        c = int((ev[a] & ev[b]).sum())
        if c < 200:
            continue
        s = c / n * 100
        conf_ab = c / ev[a].sum() * 100
        conf_ba = c / ev[b].sum() * 100
        lift = conf_ab / (sup[b] * 100)
        rows.append({"前项": a, "后项": b, "共现次数": c, "支持度(%)": s,
                     "置信度_前→后(%)": conf_ab, "置信度_后→前(%)": conf_ba,
                     "提升度": lift})
    rl = pd.DataFrame(rows).sort_values("提升度", ascending=False)
    OUT["rules"] = {
        "规则数": int(len(rl)), "提升度大于1": int((rl.提升度 > 1).sum()),
        "强规则": rl.head(12).round(3).to_dict("records"),
        "最强": rl.iloc[0].前项 + " → " + rl.iloc[0].后项,
        "最强提升度": r2(rl.iloc[0].提升度),
        "最强置信度": r2(rl.iloc[0]["置信度_前→后(%)"]),
        "最强支持度": r2(rl.iloc[0]["支持度(%)"]),
    }
    rl.round(3).to_csv(TAB / "t10_关联规则.csv", index=False, encoding="utf-8-sig")


# ============================ M7 预测 ============================
def forecast(d):
    # ① 市场隐含概率的样本外表现：按时间切分（前 80% 训练，后 20% 测试）
    d = d.sort_values("日期").reset_index(drop=True)
    cut = int(len(d) * 0.8)
    tr, te = d.iloc[:cut], d.iloc[cut:]
    F = ["隐含主胜", "隐含平局", "隐含客胜", "抽水率", "主场优势"]
    lr = LogisticRegression(max_iter=3000, random_state=RANDOM_SEED)
    lr.fit(tr[F], tr.赛果)
    pm = lr.predict_proba(te[F])
    cls = list(lr.classes_)
    Yte = np.zeros((len(te), 3))
    for i, c in enumerate(["A", "D", "H"]):
        Yte[:, i] = (te.赛果.values == c).astype(int)
    # 市场概率统一调整为 A、D、H 列序（与 Yte 对齐）
    Pm = te[["隐含客胜", "隐含平局", "隐含主胜"]].values / 100
    # 统一列顺序为 A、D、H
    order = [cls.index(x) for x in ["A", "D", "H"]]
    pm = pm[:, order]
    brier_model = float(np.mean(np.sum((pm - Yte) ** 2, axis=1)))
    brier_mkt = float(np.mean(np.sum((Pm - Yte) ** 2, axis=1)))
    acc_model = float((np.array(["A", "D", "H"])[pm.argmax(1)] == te.赛果).mean() * 100)
    acc_mkt = float((np.array(["A", "D", "H"])[Pm.argmax(1)] == te.赛果).mean() * 100)

    # ② ARIMA 预测月度抽水率
    m = (d.set_index("日期").抽水率.resample("ME").mean().dropna())
    y = m.values
    H = 6
    tr_y, te_y = y[:-H], y[-H:]
    a1 = ARIMA(tr_y, order=(1, 1, 1)).fit()
    pr = a1.forecast(H)
    mape = float(np.mean(np.abs((te_y - pr) / te_y)) * 100)
    rmse = float(np.sqrt(np.mean((te_y - pr) ** 2)))
    naive = np.full(H, tr_y[-1])
    mape_n = float(np.mean(np.abs((te_y - naive) / te_y)) * 100)

    full = ARIMA(y, order=(1, 1, 1)).fit()
    fc = full.get_forecast(H)
    mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)
    idx = pd.date_range(m.index[-1] + pd.offsets.MonthEnd(1), periods=H, freq="ME")

    OUT["forecast"] = {
        "样本外": {"训练": int(len(tr)), "测试": int(len(te)),
                   "模型准确率": r2(acc_model), "市场准确率": r2(acc_mkt),
                   "模型Brier": r2(brier_model, 4), "市场Brier": r2(brier_mkt, 4),
                   "模型优势": r2(brier_mkt - brier_model, 4)},
        "ARIMA": {"MAPE": r2(mape), "RMSE": r2(rmse, 4), "朴素MAPE": r2(mape_n),
                  "AIC": r2(full.aic, 0)},
        "抽水率预测": [{"月份": t.strftime("%Y-%m"), "点预测": r2(v),
                        "下限95": r2(lo), "上限95": r2(hi)}
                       for t, v, lo, hi in zip(idx, mean, ci[:, 0], ci[:, 1])],
        "历史": [{"月份": t.strftime("%Y-%m"), "抽水率": r2(v)}
                 for t, v in zip(m.index[-36:], y[-36:])],
    }


def main():
    d = load()
    print(f"载入 {len(d):,} 场")
    print("[1/7] 趋势");     trend(d)
    print("[2/7] 帕累托");   pareto(d)
    print("[3/7] 校准");     calibration(d)
    print("[4/7] 分群");     d = cluster(d)
    print("[5/7] 投注回测"); d = betting(d)
    print("[6/7] 波士顿");   bcg(d)
    print("[7/7] 关联规则"); rules(d)
    print("[+] 预测");       forecast(d)

    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=str)
    print(f"\n指标写入 {STATS}")
    print(json.dumps(OUT["trend"], ensure_ascii=False, indent=1)[:700])


if __name__ == "__main__":
    main()
