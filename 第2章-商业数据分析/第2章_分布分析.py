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

raw = pd.read_excel(os.path.join(base, '第2章 数据分析方法/2、由基础分析范式引申出的分析方法/data-无答案/4分布分析.xlsx'), header=None)

data = pd.DataFrame({
    '用户id': raw.iloc[2:340, 10].tolist(),
    '客单价': pd.to_numeric(raw.iloc[2:340, 11], errors='coerce').tolist(),
})
data = data.dropna(subset=['客单价'])

values = data['客单价'].values
q1 = np.percentile(values, 25)
q3 = np.percentile(values, 75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

print(f'样本量：{len(values)}')
print(f'均值：{values.mean():.2f}')
print(f'中位数：{np.median(values):.2f}')
print(f'最小值：{values.min():.2f} 最大值：{values.max():.2f}')
print(f'Q1：{q1:.2f}  Q3：{q3:.2f}  IQR：{iqr:.2f}')
print(f'异常值区间：[{lower:.2f}, {upper:.2f}]')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].hist(values, bins=20, color='#1f77b4', edgecolor='white', alpha=0.8)
axes[0].axvline(values.mean(), color='red', linestyle='--', label='均值')
axes[0].axvline(np.median(values), color='green', linestyle='--', label='中位数')
axes[0].set_title('客单价分布直方图')
axes[0].set_xlabel('客单价')
axes[0].set_ylabel('频数')
axes[0].legend()

bp = axes[1].boxplot(values, vert=True, patch_artist=True, tick_labels=['客单价'])
bp['boxes'][0].set_facecolor('#4c72b0')
axes[1].set_title('客单价箱线图')
axes[1].set_ylabel('客单价')

outliers = values[(values < lower) | (values > upper)]
print(f'识别到异常值数量：{len(outliers)}')

plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_分布分析.png'), dpi=150)
plt.show()
