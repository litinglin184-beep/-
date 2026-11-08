import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第2章 数据分析方法/1、分析的基础范式/data-无答案/1-1波士顿矩阵.xlsx'), sheet_name='销售表')
df['销售日期'] = pd.to_datetime(df['销售日期'])
df['月份'] = df['销售日期'].dt.month
df['订单金额'] = df['单价'] * df['销量']

sales = df.pivot_table(index='品牌', columns='月份', values='订单金额', aggfunc='sum', fill_value=0)
sales = sales.reindex(columns=[7, 8], fill_value=0)
sales['销售额占比'] = sales.sum(axis=1) / sales.values.sum()
sales['销售额环比'] = (sales[8] - sales[7]) / sales[7]
sales['销售额环比'] = sales['销售额环比'].replace([float('inf'), -float('inf')], 0)

total_growth = (sales[8].sum() - sales[7].sum()) / sales[7].sum()
avg_share = sales['销售额占比'].mean()

sales['象限'] = '问题产品'
sales.loc[(sales['销售额占比'] >= avg_share) & (sales['销售额环比'] >= total_growth), '象限'] = '明星产品'
sales.loc[(sales['销售额占比'] >= avg_share) & (sales['销售额环比'] < total_growth), '象限'] = '金牛产品'
sales.loc[(sales['销售额占比'] < avg_share) & (sales['销售额环比'] < total_growth), '象限'] = '瘦狗产品'

colors = {'明星产品': '#d62728', '金牛产品': '#2ca02c', '问题产品': '#ff7f0e', '瘦狗产品': '#7f7f7f'}

fig, ax = plt.subplots(figsize=(10, 8))
for q, g in sales.groupby('象限'):
    ax.scatter(g['销售额占比'], g['销售额环比'], s=200, color=colors[q], label=q, alpha=0.8)
    for name, row in g.iterrows():
        ax.annotate(name, (row['销售额占比'], row['销售额环比']),
                    textcoords='offset points', xytext=(8, 8), fontsize=9)

ax.axhline(total_growth, color='gray', linestyle='--', linewidth=1)
ax.axvline(avg_share, color='gray', linestyle='--', linewidth=1)
ax.set_xlabel('市场占有率（销售额占比）')
ax.set_ylabel('销售增长率（销售额环比）')
ax.set_title('波士顿矩阵')
ax.legend(loc='best')
plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_波士顿矩阵.png'), dpi=150)
plt.show()

print(sales[['销售额占比', '销售额环比', '象限']].round(4).sort_values('销售额占比', ascending=False))
