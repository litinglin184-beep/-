import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第3章'
os.makedirs(out, exist_ok=True)

path = os.path.join(base, '第3章 商业数据分析框架/案例2：财务费用分析/案例2：财务费用分析-原始数据.xlsx')

total = pd.read_excel(path, sheet_name='总费用数据')
period = pd.read_excel(path, sheet_name='财务三大期间费用数据')
manage = pd.read_excel(path, sheet_name='管理费用数据')

total['年月'] = total['年份'].astype(str) + '-' + total['月份'].astype(str).str.zfill(2)
period['年月'] = period['年份'].astype(str) + '-' + period['月份'].astype(str).str.zfill(2)
manage['年月'] = manage['年份'].astype(str) + '-' + manage['份'].astype(str).str.zfill(2)

period = period.dropna(subset=['期间费用项'])
period['期间费用项'] = period['期间费用项'].str.strip()
manage = manage.dropna(subset=['管理费用项'])
manage['管理费用项'] = manage['管理费用项'].str.strip()

total['环比增长率'] = total['金额'].pct_change()

period_pivot = period.pivot_table(index='年月', columns='期间费用项', values='金额', aggfunc='sum', fill_value=0)

manage_pivot = manage.pivot_table(index='年月', columns='管理费用项', values='金额', aggfunc='sum', fill_value=0)

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

axes[0, 0].plot(total['年月'], total['金额'], marker='o', color='#1f77b4', linewidth=2)
axes[0, 0].set_title('总费用趋势')
axes[0, 0].set_ylabel('金额')

period_pivot[['管理费用', '销售费用', '财务费用']].plot(kind='bar', ax=axes[0, 1], stacked=True)
axes[0, 1].set_title('三大期间费用构成')
axes[0, 1].set_ylabel('金额')
axes[0, 1].tick_params(axis='x', rotation=0)

period_share = period_pivot[['管理费用', '销售费用', '财务费用']].div(period_pivot[['管理费用', '销售费用', '财务费用']].sum(axis=1), axis=0)
period_share.plot(kind='bar', ax=axes[1, 0], stacked=True)
axes[1, 0].set_title('三大期间费用占比')
axes[1, 0].set_ylabel('占比')
axes[1, 0].tick_params(axis='x', rotation=0)

manage_pivot.plot(kind='bar', ax=axes[1, 1])
axes[1, 1].set_title('管理费用明细')
axes[1, 1].set_ylabel('金额')
axes[1, 1].tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig(os.path.join(out, '第3章_财务费用分析.png'), dpi=150)
plt.show()

print('总费用：')
print(total[['年月', '金额', '环比增长率']].round(4))
print('\n期间费用占比：')
print(period_pivot.round(4))
