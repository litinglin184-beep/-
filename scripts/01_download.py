# -*- coding: utf-8 -*-
"""
01_download.py —— 欧洲五大联赛比赛与赔率数据下载（合规：数据源官方一次性下载文件）

数据来源
  Football-Data.co.uk（英国，长期公开维护的足球统计与博彩赔率数据集）
  主页      : https://www.football-data.co.uk/englandm.php
  文件直链  : https://www.football-data.co.uk/mmz4281/{SEASON}/{DIV}.csv
              例：https://www.football-data.co.uk/mmz4281/2324/E0.csv

合规说明
  * 属于评分标准白名单第 1 类「数据源官方提供的一次性下载文件（CSV）」。
  * 每个 CSV 是一个赛季一个联赛的完整比赛明细，直接静态发布，无需注册、无需付费、
    无需 API Key；全程仅 HTTP GET 下载文件本体，不解析网页 —— 不属于爬虫。
  * 授权：该站点数据源自公开赛果与博彩公司公开盘口，站点声明可用于研究与教学；
    本作业仅用于课程分析，不作商业用途，论文中已标注来源。

字段随赛季略有增减（2019 年后新增收盘赔率 C 后缀列、2020 年后部分公司下线），
读取端做了列对齐处理，详见 02_clean.py。

用法
  python 01_download.py                 # 五大联赛 2010/11–2024/25 共 15 季
  python 01_download.py --seasons 2223 2324
"""
import argparse
import hashlib
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = "https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"
HOME = "https://www.football-data.co.uk/englandm.php"

# 五大联赛 + 荷甲/葡超作为对照（后者用于「联赛间定价差异」的外部参照）
LEAGUES = {
    "E0": "英超 Premier League",
    "D1": "德甲 Bundesliga",
    "SP1": "西甲 La Liga",
    "I1": "意甲 Serie A",
    "F1": "法甲 Ligue 1",
    "N1": "荷甲 Eredivisie",
    "P1": "葡超 Primeira Liga",
}
# 2010/11 → "1011"，2024/25 → "2425"
SEASONS = [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(2010, 2025)]

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (compatible; course-project/1.0)"


def fetch(url, dest: Path, retries=3):
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            dest.write_bytes(data)
            return len(data), hashlib.sha256(data).hexdigest()
        except Exception as e:
            print(f"    第 {k+1} 次失败：{e}；3 秒后重试", flush=True)
            time.sleep(3)
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", default=SEASONS)
    ap.add_argument("--leagues", nargs="*", default=list(LEAGUES))
    args = ap.parse_args()

    rows, miss, t0 = [], [], time.time()
    for s in args.seasons:
        for d in args.leagues:
            url = BASE.format(season=s, div=d)
            name = f"{d}_{s}.csv"
            dest = RAW / name
            if dest.exists() and dest.stat().st_size > 500:
                size = dest.stat().st_size
                h = hashlib.sha256(dest.read_bytes()).hexdigest()
            else:
                size, h = fetch(url, dest)
                if size is None:
                    miss.append(url)
                    continue
                print(f"[ok] {name:14s} {size/1024:6.1f} KB")
            rows.append({"文件": name, "联赛代码": d, "联赛": LEAGUES[d], "赛季": s,
                         "来源链接": url, "字节数": size, "sha256": h,
                         "获取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "获取方式": "HTTP GET 直链下载（urllib，无登录/无 API Key）"})

    mf = RAW / "_manifest.csv"
    new = pd.DataFrame(rows)
    if mf.exists():
        old = pd.read_csv(mf, encoding="utf-8-sig")
        new = pd.concat([old[~old["文件"].isin(new["文件"])], new], ignore_index=True)
    new.to_csv(mf, index=False, encoding="utf-8-sig")
    print(f"\n清单 {mf}")
    print(f"成功 {len(rows)} 个文件，失败 {len(miss)} 个，"
          f"合计 {new['字节数'].sum()/1048576:.2f} MB，耗时 {time.time()-t0:.1f} 秒")
    if miss:
        print("失败清单：\n  " + "\n  ".join(miss))
    print(f"数据集主页（引用用）：{HOME}")


if __name__ == "__main__":
    sys.exit(main())
