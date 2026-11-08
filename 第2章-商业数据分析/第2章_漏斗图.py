import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

raw = pd.read_excel(os.path.join(base, '第2章 数据分析方法/1、分析的基础范式/data-无答案/2-1漏斗图.xlsx'), sheet_name='练习', header=None)

funnel1 = pd.DataFrame({
    '行为': raw.iloc[2:6, 1].tolist(),
    '用户数': pd.to_numeric(raw.iloc[2:6, 2]).tolist(),
})
funnel2 = pd.DataFrame({
    '行为': raw.iloc[10:14, 1].tolist(),
    '用户数': pd.to_numeric(raw.iloc[10:14, 2]).tolist(),
})


def plot_funnel(df, ax, title):
    max_v = df['用户数'].max()
    for i, (name, v) in enumerate(zip(df['行为'], df['用户数'])):
        width = v / max_v
        ax.barh(i, width, left=(1 - width) / 2, height=0.6, color='#1f77b4', alpha=0.85)
        ax.text(0.5, i, f'{name} {int(v)}人 ({v / max_v:.0%})', ha='center', va='center', color='white', fontsize=11)
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    for s in ['top', 'right', 'bottom', 'left']:
        ax.spines[s].set_visible(False)
    ax.set_title(title)


fig, axes = plt.subplots(1, 2, figsize=(14, 6))
plot_funnel(funnel1, axes[0], '用户行为漏斗')
plot_funnel(funnel2, axes[1], '用户运营行为漏斗（AARRR）')
plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_漏斗图.png'), dpi=150)
plt.show()

print('用户行为漏斗：')
print(funnel1)
print('\nAARRR 漏斗：')
print(funnel2)
