# -*- coding: utf-8 -*-
"""
run_all.py —— 一键复现第 8 项（体育博彩）的全部成果
------------------------------------------------------------
    python run_all.py                 # 全流程
    python run_all.py 3 4 5           # 只跑第 3、4、5 步
    python run_all.py --no-download   # 跳过下载（复用 data/raw 已有文件）

步骤
    1  01_download.py   下载 7 联赛 × 15 赛季 = 105 个 CSV（11.63 MB）
    2  02_clean.py      三代列结构归一化 + C1–C6 + 派生指标
    3  03_analysis.py   7 类模型（写 outputs/stats.json）
    4  04_visuals.py    22 张静态图
    5  05_dashboard.py  Pyecharts 交互大屏
    6  06_report.py     生成 Word 论文
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
PY = sys.executable

STEPS = [
    ("01_download.py", "下载原始数据（Football-Data.co.uk 公开 CSV）"),
    ("02_clean.py", "列结构归一化与清洗"),
    ("03_analysis.py", "7 类商业模型"),
    ("04_visuals.py", "22 张静态图"),
    ("05_dashboard.py", "交互式大屏"),
    ("06_report.py", "生成 Word 论文"),
]


def main():
    args = list(sys.argv[1:])
    skip_dl = "--no-download" in args
    pick = {int(a) for a in args if a.isdigit()}

    for i, (name, desc) in enumerate(STEPS, start=1):
        if pick and i not in pick:
            continue
        if i == 1 and skip_dl:
            print(f"[{i}/6] 跳过下载（--no-download）")
            continue
        print(f"\n[{i}/6] {desc}  →  {name}", flush=True)
        t0 = time.time()
        r = subprocess.run([PY, str(SCRIPTS / name)], cwd=str(SCRIPTS))
        if r.returncode != 0:
            print(f"  失败：{name} 退出码 {r.returncode}")
            sys.exit(r.returncode)
        print(f"  完成，用时 {time.time() - t0:.1f}s", flush=True)

    print("\n全部完成。成果在 docs/ 、outputs/ 、dashboard/ 三个目录。")


if __name__ == "__main__":
    main()
