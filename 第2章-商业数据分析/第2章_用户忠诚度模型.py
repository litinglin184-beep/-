import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第2章 数据分析方法/1、分析的基础范式/data-无答案/1-3用户忠诚度模型.xlsx'), sheet_name='销售流水表')
df['消费日期'] = pd.to_datetime(df['消费日期'])

agg = df.groupby('会员编号').agg(
    消费次数=('订单编号', 'count'),
    消费金额=('消费金额', 'sum'),
    最近消费=('消费日期', 'max')
).reset_index()

agg = agg.sort_values(['消费次数', '消费金额'], ascending=False).reset_index(drop=True)
agg['累计人数占比'] = (agg.index + 1) / len(agg)
agg['累计消费金额占比'] = agg['消费金额'].cumsum() / agg['消费金额'].sum()
agg['累计消费次数占比'] = agg['消费次数'].cumsum() / agg['消费次数'].sum()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].plot(agg['累计人数占比'], agg['累计消费金额占比'], color='#d62728', linewidth=2)
axes[0].plot([0, 1], [0, 1], color='gray', linestyle='--')
axes[0].set_xlabel('累计用户占比')
axes[0].set_ylabel('累计消费金额占比')
axes[0].set_title('用户忠诚度（金额维度）')

axes[1].plot(agg['累计人数占比'], agg['累计消费次数占比'], color='#2ca02c', linewidth=2)
axes[1].plot([0, 1], [0, 1], color='gray', linestyle='--')
axes[1].set_xlabel('累计用户占比')
axes[1].set_ylabel('累计消费次数占比')
axes[1].set_title('用户忠诚度（次数维度）')

plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_用户忠诚度模型.png'), dpi=150)
plt.show()

print(agg.head(20).round(4))
