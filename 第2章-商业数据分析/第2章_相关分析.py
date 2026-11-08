import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第2章 数据分析方法/1、分析的基础范式/data-无答案/3-1相关分析.xlsx'), sheet_name='原始数据')

x = df['x'].values
y = df['y'].values

r = np.corrcoef(x, y)[0, 1]

coef = np.polyfit(x, y, 1)
trend = np.poly1d(coef)

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(x, y, color='#1f77b4', alpha=0.7)
xs = np.linspace(x.min(), x.max(), 100)
ax.plot(xs, trend(xs), color='#d62728', linewidth=2)
ax.set_xlabel('投入成本')
ax.set_ylabel('产出收益')
ax.set_title(f'投入成本与收益相关分析（相关系数 r = {r:.4f}）')
ax.text(0.05, 0.9, f'r = {r:.4f}', transform=ax.transAxes, fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_相关分析.png'), dpi=150)
plt.show()

print(f'相关系数 r = {r:.4f}')
print(f'线性回归：y = {coef[0]:.4f} * x + {coef[1]:.4f}')
