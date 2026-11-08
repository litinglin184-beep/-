import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第3章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第3章 商业数据分析框架/案例1：收入趋势分析/案例1：收入趋势分析原始数据.xlsx'), sheet_name='原始数据')

df['年月'] = df['订单年份'].astype(str) + '-' + df['订单月份'].astype(str).str.zfill(2)
df['年月'] = pd.to_datetime(df['年月'])

monthly = df.groupby('年月')['销售额'].sum().reset_index().sort_values('年月')
monthly['环比增长率'] = monthly['销售额'].pct_change()
monthly['同比增长率'] = monthly['销售额'].pct_change(12)

province = df.groupby('销售省份')['销售额'].sum().sort_values(ascending=False)

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

axes[0, 0].plot(monthly['年月'], monthly['销售额'], marker='o', color='#1f77b4', linewidth=2)
axes[0, 0].set_title('月度销售额趋势')
axes[0, 0].set_xlabel('月份')
axes[0, 0].set_ylabel('销售额')
axes[0, 0].tick_params(axis='x', rotation=45)

axes[0, 1].bar(monthly['年月'].astype(str), monthly['环比增长率'] * 100, color='#ff7f0e')
axes[0, 1].set_title('月度销售额环比增长率')
axes[0, 1].set_ylabel('增长率(%)')
axes[0, 1].tick_params(axis='x', rotation=45)

top10 = province.head(10)
axes[1, 0].barh(top10.index[::-1], top10.values[::-1], color='#2ca02c')
axes[1, 0].set_title('销售额 TOP10 省份')
axes[1, 0].set_xlabel('销售额')

top10_pct = top10 / province.sum() * 100
axes[1, 1].pie(top10_pct, labels=top10_pct.index, autopct='%1.1f%%', startangle=90)
axes[1, 1].set_title('TOP10 省份销售额占比')

plt.tight_layout()
plt.savefig(os.path.join(out, '第3章_收入趋势分析.png'), dpi=150)
plt.show()

print('月度销售额汇总：')
print(monthly[['年月', '销售额', '环比增长率']].round(4))
print('\n省份销售额 TOP10：')
print(top10.head(10))
