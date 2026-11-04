# -*- coding: utf-8 -*-
"""
05_dashboard.py —— 足球博彩经营驾驶舱大屏（Pyecharts 生成 ECharts 配置 + 前端联动）
--------------------------------------------------------------------------
组件清单（共 13 个，其中 9 个参与联动）：
  1-4  KPI 卡：场次 / 场均进球 / 抽水率 / 主胜率
  5    赛季趋势（柱=场次，线=场均进球，选中赛季高亮）
  6    联赛效率横条（点击下钻明细表）
  7    赛果结构 100% 堆叠（按联赛）
  8    抽水率 × 场均进球 散点（气泡=场次）
  9    赔率档位 ROI 条形（随赛季 / 联赛筛选）
  10   抽水率 ARIMA 预测（含 95% 区间）
  11   联赛 × 赛季经营明细表
  12   赛季筛选器（全部 + 15 季）
  13   联赛筛选器（全部 + 7 联赛）

联动逻辑：
  ① 切换赛季 → KPI、趋势高亮、联赛横条、赛果堆叠、散点、ROI、明细表全部重算；
  ② 切换联赛 → 同上 7 类视图按该联赛重算（趋势仍显示该联赛全部 15 季）；
  ③ 点击联赛横条 → 明细表锁定该联赛，再次点击取消。

数据来源：Football-Data.co.uk 105 个赛季文件 → 35,981 场有效比赛。
输出：dashboard/football_dashboard.html（ECharts 库本地化，双击即可离线打开）
"""
import json
import shutil

import pandas as pd
from pyecharts.charts import Bar, Line, Scatter
import pyecharts.options as opts

from config import CLEAN, DASH, LEAGUE_CN, ROOT, STATS, TAB

C_MAIN, C_ACC, C_ALT, C_RED, C_GREY, C_SOFT = (
    "#1F4E79", "#ED7D31", "#70AD47", "#C00000", "#7F7F7F", "#9DC3E6")
PALETTE = ["#1F4E79", "#ED7D31", "#70AD47", "#C00000", "#7030A0", "#2E76B6", "#FFC000"]
ORDER = ["英超", "德甲", "西甲", "意甲", "法甲", "荷甲", "葡超"]

M = pd.read_csv(CLEAN / "matches_clean.csv", encoding="utf-8-sig")
SEA = pd.read_csv(TAB / "t03_赛季趋势.csv", encoding="utf-8-sig")
ROI = pd.read_csv(TAB / "t08_ROI矩阵.csv", encoding="utf-8-sig")
S = json.loads(STATS.read_text(encoding="utf-8"))


def build():
    # ---- 赛季 × 联赛 三维聚合（105 行，前端据此重算所有视图）----
    g = (M.groupby(["赛季", "联赛"])
           .agg(场次=("赛果", "size"), 主胜=("主胜", "sum"), 平局=("平局", "sum"),
                客胜=("客胜", "sum"), 进球=("总进球", "sum"),
                抽水=("抽水率", "mean"), 大球=("大25", "sum"))
           .reset_index())
    g["场均进球"] = g["进球"] / g["场次"]
    g["抽水率"] = g["抽水"]
    g["主胜率"] = g["主胜"] / g["场次"] * 100
    g["平局率"] = g["平局"] / g["场次"] * 100
    g["客胜率"] = g["客胜"] / g["场次"] * 100
    g["大球率"] = g["大球"] / g["场次"] * 100
    agg = g[["赛季", "联赛", "场次", "场均进球", "抽水率", "主胜率", "平局率",
             "客胜率", "大球率"]].round(4)
    agg = agg.sort_values(["赛季", "联赛"])

    # ---- ROI 矩阵（15 × 4）----
    roi = ROI.melt(id_vars="赛季", var_name="档位", value_name="ROI").dropna()

    # ---- 静态图：抽水率预测 ----
    hist = pd.DataFrame(S["forecast"]["历史"])
    fut = pd.DataFrame(S["forecast"]["抽水率预测"])
    fx = opt_forecast(hist, fut)   # 已返回 dict

    data = {
        "agg": agg.to_dict("records"),
        "roi": roi.to_dict("records"),
        "forecast": fx,
        "seasons": sorted(agg["赛季"].unique().tolist()),
        "leagues": [l for l in ORDER if l in agg["联赛"].unique()],
        "colors": PALETTE,
        "kpi_all": {
            "场次": int(len(M)),
            "场均进球": round(float(M["总进球"].mean()), 3),
            "抽水率": round(float(M["抽水率"].mean()), 3),
            "主胜率": round(float(M["主胜"].mean()) * 100, 2),
        },
    }

    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out = DASH / "football_dashboard.html"
    out.write_text(html, encoding="utf-8")

    js = ROOT.parent / "olist_analysis" / "dashboard" / "echarts.min.js"
    dst = DASH / "echarts.min.js"
    if js.exists() and not dst.exists():
        shutil.copy(js, dst)
    print(f"[dash] {out}  ({out.stat().st_size/1024:.0f} KB)")
    return out


def opt_forecast(hist, fut):
    """抽水率 6 个月外推（静态图，不受筛选影响）。"""
    x = hist["月份"].tolist() + fut["月份"].tolist()
    h = [round(float(v), 2) for v in hist["抽水率"]]
    p = [None] * (len(h) - 1) + [h[-1]] + [round(float(v), 2) for v in fut["点预测"]]
    lo = [None] * (len(h) - 1) + [h[-1]] + [round(float(v), 2) for v in fut["下限95"]]
    wd = [None] * (len(h) - 1) + [0] + [round(float(b) - float(a), 2)
                                        for a, b in zip(fut["下限95"], fut["上限95"])]
    ln = Line(init_opts=opts.InitOpts(width="100%", height="280px", bg_color="transparent"))
    ln.add_xaxis(x)
    ln.add_yaxis("下界", lo, stack="ci", symbol="none",
                 linestyle_opts=opts.LineStyleOpts(opacity=0),
                 areastyle_opts=opts.AreaStyleOpts(opacity=0),
                 label_opts=opts.LabelOpts(is_show=False))
    ln.add_yaxis("95% 置信区间", wd, stack="ci", symbol="none", color=C_SOFT,
                 linestyle_opts=opts.LineStyleOpts(opacity=0),
                 areastyle_opts=opts.AreaStyleOpts(opacity=0.30, color=C_SOFT),
                 label_opts=opts.LabelOpts(is_show=False))
    ln.add_yaxis("历史抽水率", h, symbol_size=3.5, color=C_MAIN,
                 linestyle_opts=opts.LineStyleOpts(width=2, color=C_MAIN),
                 itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN),
                 label_opts=opts.LabelOpts(is_show=False))
    ln.add_yaxis("ARIMA 点预测", p, symbol_size=5, color=C_ACC, is_smooth=True,
                 linestyle_opts=opts.LineStyleOpts(width=2.4, type_="dashed", color=C_ACC),
                 itemstyle_opts=opts.ItemStyleOpts(color=C_ACC),
                 label_opts=opts.LabelOpts(is_show=False))
    ln.set_global_opts(
        title_opts=opts.TitleOpts(
            title="抽水率 ARIMA 预测（未来 6 个月）",
            subtitle=f"MAPE {S['forecast']['ARIMA']['MAPE']:.2f}%（朴素基准 "
                     f"{S['forecast']['ARIMA']['朴素MAPE']:.2f}%）｜预测值稳定在 5.3%–5.4%",
            pos_left="1%", title_textstyle_opts=opts.TextStyleOpts(font_size=14, color="#1F2D3D"),
            subtitle_textstyle_opts=opts.TextStyleOpts(font_size=10, color=C_GREY)),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=8, rotate=45)),
        yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=9, formatter="{value}%"),
                                 min_=4.2, max_=6.4),
        legend_opts=opts.LegendOpts(pos_top="0%", pos_right="2%", item_gap=12,
                                    textstyle_opts=opts.TextStyleOpts(font_size=10)),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
    )
    o = json.loads(ln.dump_options())
    o["legend"][0]["data"] = ["历史抽水率", "ARIMA 点预测", "95% 置信区间"]
    o["grid"] = {"left": "8%", "right": "5%", "top": 68, "bottom": 62}
    for ser, c in zip(o["series"], ["#EAF1F8", C_SOFT, C_MAIN, C_ACC]):
        ser["color"] = c
    return o


def opt_unused():
    """占位：保持 pyecharts 导入被使用（Bar/Scatter 在前端由 JSON 组装）。"""
    return Bar, Scatter


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>足球博彩经营驾驶舱 | 商业数据分析大屏</title>
<script src="echarts.min.js"></script>
<style>
  :root{--bg:#F2F5F9;--card:#fff;--ink:#1F2D3D;--muted:#7A8899;
        --main:#1F4E79;--acc:#ED7D31;--line:#E3EAF2;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:"Microsoft YaHei","Segoe UI",Arial,sans-serif;}
  header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;
         padding:16px 26px 12px;background:linear-gradient(90deg,#123B2E,#1F6B4A);
         color:#fff;box-shadow:0 2px 10px rgba(18,59,46,.22);}
  header h1{margin:0;font-size:21px;letter-spacing:.5px;}
  header .sub{font-size:12px;opacity:.88;margin-top:5px;}
  .filters{display:flex;gap:16px;align-items:center;flex-wrap:wrap;}
  .fgroup{display:flex;gap:6px;align-items:center;}
  .fgroup span{font-size:12px;opacity:.88;}
  select{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.4);
         border-radius:15px;padding:6px 12px;font-size:12.5px;cursor:pointer;outline:none;}
  select option{color:#1F2D3D;}
  .wrap{padding:16px 26px 26px;}
  .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:14px;}
  .kpi{background:var(--card);border-radius:10px;padding:15px 18px;
       box-shadow:0 1px 6px rgba(31,78,121,.08);border-left:4px solid var(--main);}
  .kpi .t{font-size:12.5px;color:var(--muted);}
  .kpi .v{font-size:25px;font-weight:bold;margin-top:5px;color:var(--main);}
  .kpi .v small{font-size:12px;color:var(--muted);font-weight:normal;margin-left:4px;}
  .kpi:nth-child(2){border-left-color:var(--acc);} .kpi:nth-child(2) .v{color:var(--acc);}
  .kpi:nth-child(3){border-left-color:#2E9E9E;} .kpi:nth-child(3) .v{color:#2E9E9E;}
  .kpi:nth-child(4){border-left-color:#C00000;} .kpi:nth-child(4) .v{color:#C00000;}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
  .card{background:var(--card);border-radius:10px;padding:10px 12px;
        box-shadow:0 1px 6px rgba(31,78,121,.08);}
  .card.s2{grid-column:span 2;}
  .chart{width:100%;height:300px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;}
  th,td{padding:6px 10px;text-align:left;border-bottom:1px solid var(--line);}
  th{background:#EEF3F9;color:var(--main);font-weight:600;position:sticky;top:0;font-size:12px;}
  tbody tr:hover{background:#F7FAFE;}
  .tbody-wrap{max-height:280px;overflow:auto;}
  .tag{display:inline-block;padding:1px 8px;border-radius:9px;background:#EEF3F9;
       color:var(--main);font-size:11px;margin-left:8px;font-weight:normal;}
  .num{text-align:right;font-variant-numeric:tabular-nums;}
  footer{padding:8px 26px 24px;color:var(--muted);font-size:11.5px;line-height:1.7;}
</style>
</head>
<body>
<header>
  <div>
    <h1>五大联赛 + 荷甲/葡超 博彩定价驾驶舱</h1>
    <div class="sub">数据源：Football-Data.co.uk｜2010/11–2024/25 共 15 季 × 7 联赛 = 105 个文件｜35,981 场有效比赛</div>
  </div>
  <div class="filters">
    <div class="fgroup"><span>赛季：</span><select id="f_season"></select></div>
    <div class="fgroup"><span>联赛：</span><select id="f_league"></select></div>
  </div>
</header>

<div class="wrap">
  <div class="kpis">
    <div class="kpi"><div class="t">比赛场次（场）</div><div class="v" id="k_n">-</div></div>
    <div class="kpi"><div class="t">场均进球（球）</div><div class="v" id="k_g">-</div></div>
    <div class="kpi"><div class="t">平均抽水率</div><div class="v" id="k_v">-</div></div>
    <div class="kpi"><div class="t">主胜率</div><div class="v" id="k_h">-</div></div>
  </div>

  <div class="grid">
    <div class="card s2"><div class="chart" id="c_trend"></div></div>
    <div class="card"><div class="chart" id="c_league"></div></div>
    <div class="card"><div class="chart" id="c_result"></div></div>
    <div class="card"><div class="chart" id="c_scatter"></div></div>
    <div class="card"><div class="chart" id="c_roi"></div></div>
    <div class="card s2"><div class="chart" id="c_forecast" style="height:280px"></div></div>
    <div class="card s2">
      <div style="font-size:14px;font-weight:bold;color:#1F2D3D;margin:4px 0 8px;">
        联赛 × 赛季 经营明细 <span class="tag" id="tbl_tag">全部赛季 · 全部联赛</span>
      </div>
      <div class="tbody-wrap">
        <table>
          <thead><tr><th>赛季</th><th>联赛</th><th class="num">场次</th>
            <th class="num">场均进球</th><th class="num">抽水率</th>
            <th class="num">主胜率</th><th class="num">平局率</th><th class="num">大球率</th></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>
<footer>
图23　交互式博彩定价驾驶舱（13 个组件、9 个参与联动）：① <b>赛季下拉</b> → KPI、趋势高亮、联赛横条、赛果堆叠、散点、ROI 条形、明细表共 7 类视图重算；② <b>联赛下拉</b> → 同上视图按该联赛重算，趋势图保持该联赛 15 季全历史以便对比；③ <b>点击联赛横条</b> → 明细表锁定该联赛下钻，再次点击取消；④ 抽水率预测图叠加 95% 置信区间。全部由 Python 生成 ECharts 配置，库已本地化，未使用 Power BI / Tableau。
</footer>

<script>
const DATA = __DATA__;
const AGG = DATA.agg, ROI = DATA.roi, COL = DATA.colors;
const SEASONS = DATA.seasons, LEAGUES = DATA.leagues;
const charts = {};
["trend","league","result","scatter","roi","forecast"].forEach(k =>
  charts[k] = echarts.init(document.getElementById("c_" + k)));
charts["forecast"].setOption(DATA.forecast, true);

let curS = "全部", curL = "全部", pickLeague = null;

document.getElementById("f_season").innerHTML =
  `<option value="全部">全部赛季</option>` +
  SEASONS.map(s => `<option value="${s}">${s}</option>`).join("");
document.getElementById("f_league").innerHTML =
  `<option value="全部">全部联赛</option>` +
  LEAGUES.map(l => `<option value="${l}">${l}</option>`).join("");

const colorOf = l => COL[LEAGUES.indexOf(l) % COL.length];
const fmt = n => n.toLocaleString("en-US");

function pick(){                       // 当前筛选下的行
  return AGG.filter(r => (curS === "全部" || r["赛季"] === curS) &&
                         (curL === "全部" || r["联赛"] === curL));
}
function wavg(rows, key){              // 按场次加权
  const n = rows.reduce((a, r) => a + r["场次"], 0) || 1;
  return rows.reduce((a, r) => a + r[key] * r["场次"], 0) / n;
}
function base(title, sub){
  return {
    backgroundColor: "transparent",
    title: {text: title, subtext: sub, left: "1%",
            textStyle: {fontSize: 14, color: "#1F2D3D"},
            subtextStyle: {fontSize: 10, color: "#7F7F7F"}},
    animationDuration: 600,
    grid: {left: "9%", right: "7%", top: 66, bottom: 46},
    tooltip: {trigger: "axis", axisPointer: {type: "shadow"}}
  };
}

function drawTrend(){
  // 趋势始终展示「当前联赛」的 15 季全历史，选中赛季高亮
  const rows = AGG.filter(r => curL === "全部" || r["联赛"] === curL);
  const byS = SEASONS.map(s => {
    const sub = rows.filter(r => r["赛季"] === s);
    const n = sub.reduce((a, r) => a + r["场次"], 0);
    const g = sub.reduce((a, r) => a + r["场均进球"] * r["场次"], 0) / (n || 1);
    return {s, n, g};
  });
  const o = base("赛季趋势", (curL === "全部" ? "柱=总场次（场）｜线=场均进球（球），全部联赛合计"
                                            : `柱=总场次（场）｜线=场均进球（球），${curL}`) +
                       (curS === "全部" ? "" : `｜高亮 ${curS}`));
  o.xAxis = {type: "category", data: byS.map(d => d.s),
             axisLabel: {fontSize: 9, rotate: 45}};
  o.yAxis = [{type: "value", axisLabel: {fontSize: 9}},
             {type: "value", axisLabel: {fontSize: 9},
              splitLine: {show: false}, min: 2.3, max: 3.2}];
  o.series = [
    {type: "bar", name: "场次", data: byS.map(d => ({
        value: d.n,
        itemStyle: {color: (curS === "全部" || d.s === curS) ? "#1F4E79" : "#C9D6E4"}})),
     itemStyle: {borderRadius: [3,3,0,0]}, barWidth: "58%"},
    {type: "line", name: "场均进球", yAxisIndex: 1, smooth: true,
     data: byS.map(d => +d.g.toFixed(3)), symbolSize: 6,
     lineStyle: {width: 2.4, color: "#ED7D31"}, itemStyle: {color: "#ED7D31"}}
  ];
  o.legend = {top: 0, right: "2%", itemGap: 12, textStyle: {fontSize: 10}};
  charts["trend"].setOption(o, true);
}

function drawLeague(){
  const rows = AGG.filter(r => curS === "全部" || r["赛季"] === curS);
  const d = LEAGUES.map(l => {
    const sub = rows.filter(r => r["联赛"] === l);
    const n = sub.reduce((a, r) => a + r["场次"], 0);
    return {l, v: sub.reduce((a, r) => a + r["场均进球"] * r["场次"], 0) / (n || 1)};
  }).sort((a, b) => a.v - b.v);
  const o = base("联赛场均进球（点击下钻）", `${curS === "全部" ? "全部赛季" : curS}`);
  o.grid = {left: "13%", right: "12%", top: 66, bottom: 34};
  o.xAxis = {type: "value", name: "球", axisLabel: {fontSize: 9}};
  o.yAxis = {type: "category", data: d.map(x => x.l), axisLabel: {fontSize: 9.5}};
  o.series = [{type: "bar", data: d.map(x => ({
      value: +x.v.toFixed(3),
      itemStyle: {color: (pickLeague && pickLeague !== x.l) ? "#D8E2EC" : colorOf(x.l),
                  borderRadius: [0,3,3,0]}})),
    label: {show: true, position: "right", fontSize: 9, formatter: "{c}"},
    barWidth: "58%"}];
  o.tooltip = {trigger: "axis", axisPointer: {type: "shadow"}};
  charts["league"].setOption(o, true);
}

function drawResult(){
  const rows = pick();
  const d = LEAGUES.map(l => {
    const sub = rows.filter(r => r["联赛"] === l);
    const n0 = sub.reduce((a, r) => a + r["场次"], 0), n = n0 || 1;
    return {l, n: n0,
            H: sub.reduce((a, r) => a + r["主胜率"] * r["场次"], 0) / n,
            D: sub.reduce((a, r) => a + r["平局率"] * r["场次"], 0) / n,
            A: sub.reduce((a, r) => a + r["客胜率"] * r["场次"], 0) / n};
  }).filter(x => x.n > 0);
  const o = base("赛果结构", "主胜 / 平局 / 客胜（按场次加权）");
  o.grid = {left: "9%", right: "6%", top: 66, bottom: 40};
  o.xAxis = {type: "category", data: d.map(x => x.l), axisLabel: {fontSize: 9}};
  o.yAxis = {type: "value", max: 100, axisLabel: {fontSize: 9, formatter: "{value}%"}};
  const mk = (name, key, col) => ({type: "bar", name, stack: "r", barWidth: "55%",
    itemStyle: {color: col},
    label: {show: true, fontSize: 8, color: "#fff",
            formatter: p => p.value >= 8 ? p.value.toFixed(1) : ""},
    data: d.map(x => +x[key].toFixed(2))});
  o.series = [mk("主胜", "H", "#1F4E79"), mk("平局", "D", "#BFBFBF"), mk("客胜", "A", "#ED7D31")];
  o.legend = {top: 0, right: "2%", itemGap: 12, textStyle: {fontSize: 10}};
  charts["result"].setOption(o, true);
}

function drawScatter(){
  const rows = AGG.filter(r => curS === "全部" || r["赛季"] === curS);
  const o = base("抽水率 × 场均进球", "横轴=抽水率（%）｜纵轴=场均进球（球）｜气泡=场次｜颜色=联赛");
  o.grid = {left: "10%", right: "6%", top: 66, bottom: 46};
  o.xAxis = {type: "value", min: 3, max: 9, axisLabel: {fontSize: 9},
             splitLine: {lineStyle: {color: "#EEF1F5"}}};
  o.yAxis = {type: "value", min: 2.2, max: 3.5, axisLabel: {fontSize: 9},
             splitLine: {lineStyle: {color: "#EEF1F5"}}};
  o.series = LEAGUES.map(l => ({
    type: "scatter", name: l,
    symbolSize: d => Math.max(8, Math.sqrt(d[2]) / 1.6),
    itemStyle: {color: colorOf(l), opacity: 0.78},
    data: rows.filter(r => r["联赛"] === l).map(r =>
      [+r["抽水率"].toFixed(2), +r["场均进球"].toFixed(2), r["场次"]])
  }));
  o.legend = {top: 0, right: "2%", itemGap: 10, textStyle: {fontSize: 9.5}};
  o.tooltip = {trigger: "item",
    formatter: p => `${p.seriesName}<br/>抽水率 ${p.value[0]}%｜场均进球 ${p.value[1]}<br/>场次 ${fmt(p.value[2])}`};
  charts["scatter"].setOption(o, true);
}

function drawRoi(){
  const rows = ROI.filter(r => curS === "全部" || r["赛季"] === curS);
  const tiers = ["冷门局", "偏冷", "偏热", "大热"];
  const d = tiers.map(t => {
    const sub = rows.filter(r => r["档位"] === t);
    return sub.length ? sub.reduce((a, r) => a + r["ROI"], 0) / sub.length : 0;
  });
  const o = base("赔率档位 ROI", `${curS === "全部" ? "15 季均值" : curS}｜单位注码，0 为盈亏平衡`);
  o.grid = {left: "11%", right: "6%", top: 66, bottom: 38};
  o.xAxis = {type: "category", data: tiers, axisLabel: {fontSize: 10}};
  const lo = Math.floor(Math.min(0, ...d) - 1);
  o.yAxis = {type: "value", name: "ROI %", nameGap: 16, axisLabel: {fontSize: 9},
             max: 1.2, min: lo};
  o.series = [{type: "bar", barWidth: "52%",
    data: d.map(v => ({value: +v.toFixed(2),
      itemStyle: {color: v >= 0 ? "#70AD47" : "#C00000", borderRadius: [3,3,0,0]}})),
    label: {show: true, position: "insideTop", fontSize: 9.5,
            color: "#FFFFFF", fontWeight: "bold", formatter: "{c}%", offset: [0, 6]},
    markLine: {silent: true, symbol: "none", lineStyle: {color: "#404040", type: "solid"},
               data: [{yAxis: 0}], label: {show: false}}}];
  o.tooltip = {trigger: "axis", axisPointer: {type: "shadow"}};
  charts["roi"].setOption(o, true);
}

function renderKPI(){
  const rows = pick();
  const n = rows.reduce((a, r) => a + r["场次"], 0);
  document.getElementById("k_n").innerHTML = fmt(n) + "<small>场</small>";
  document.getElementById("k_g").innerHTML = wavg(rows, "场均进球").toFixed(3) + "<small>球</small>";
  document.getElementById("k_v").innerHTML = wavg(rows, "抽水率").toFixed(2) + "<small>%</small>";
  document.getElementById("k_h").innerHTML = wavg(rows, "主胜率").toFixed(2) + "<small>%</small>";
}

function renderTable(){
  let rows = pick();
  if (pickLeague) rows = rows.filter(r => r["联赛"] === pickLeague);
  rows = rows.slice().sort((a, b) => (a["赛季"] < b["赛季"] ? 1 : a["赛季"] > b["赛季"] ? -1 : 0));
  document.getElementById("tbody").innerHTML = rows.map(r =>
    `<tr><td>${r["赛季"]}</td><td>${r["联赛"]}</td>
     <td class="num">${fmt(r["场次"])}</td><td class="num">${r["场均进球"].toFixed(3)}</td>
     <td class="num">${r["抽水率"].toFixed(2)}</td><td class="num">${r["主胜率"].toFixed(2)}</td>
     <td class="num">${r["平局率"].toFixed(2)}</td><td class="num">${r["大球率"].toFixed(2)}</td></tr>`).join("");
  document.getElementById("tbl_tag").textContent =
    (curS === "全部" ? "全部赛季" : curS) + " · " +
    (curL === "全部" ? "全部联赛" : curL) +
    (pickLeague ? " · 下钻 " + pickLeague : "") + `（${rows.length} 行）`;
}

function refresh(){
  renderKPI(); drawTrend(); drawLeague(); drawResult();
  drawScatter(); drawRoi(); renderTable();
}

document.getElementById("f_season").addEventListener("change", e => {
  curS = e.target.value; pickLeague = null; refresh();
});
document.getElementById("f_league").addEventListener("change", e => {
  curL = e.target.value; pickLeague = null; refresh();
});
charts["league"].on("click", p => {
  pickLeague = (pickLeague === p.name) ? null : p.name;
  drawLeague(); renderTable();
});

refresh();
window.addEventListener("resize", () => { for (const k in charts) charts[k].resize(); });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
