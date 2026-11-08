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

raw = pd.read_excel(os.path.join(base, '第2章 数据分析方法/2、由基础分析范式引申出的分析方法/data-无答案/5关系分析.xlsx'), header=None)

cat_df = pd.DataFrame({
    '营销活动': raw.iloc[3:8, 1].tolist(),
    '下单用户': pd.to_numeric(raw.iloc[3:8, 2]).tolist(),
    '未下单用户': pd.to_numeric(raw.iloc[3:8, 3]).tolist(),
})

cont = pd.DataFrame({
    '产出收益': pd.to_numeric(raw.iloc[1:, 24], errors='coerce'),
    '投入成本': pd.to_numeric(raw.iloc[1:, 25], errors='coerce'),
}).dropna()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

x = np.arange(len(cat_df))
w = 0.4
axes[0].bar(x - w / 2, cat_df['下单用户'], w, label='下单用户', color='#2ca02c')
axes[0].bar(x + w / 2, cat_df['未下单用户'], w, label='未下单用户', color='#d62728')
axes[0].set_xticks(x)
axes[0].set_xticklabels(cat_df['营销活动'])
axes[0].set_ylabel('人数')
axes[0].set_title('不同营销活动客户下单情况对比')
axes[0].legend()

x_c = cont['投入成本'].values
y_c = cont['产出收益'].values
axes[1].scatter(x_c, y_c, color='#1f77b4', alpha=0.7)
coef = np.polyfit(x_c, y_c, 1)
trend = np.poly1d(coef)
xs = np.linspace(x_c.min(), x_c.max(), 100)
axes[1].plot(xs, trend(xs), color='#d62728', linewidth=2)
axes[1].set_xlabel('投入成本')
axes[1].set_ylabel('产出收益')
axes[1].set_title('投入成本与收益关系')

plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_关系分析.png'), dpi=150)
plt.show()

print('营销活动下单情况：')
print(cat_df)
print(f'\n投入成本与收益相关系数：{np.corrcoef(x_c, y_c)[0, 1]:.4f}')
