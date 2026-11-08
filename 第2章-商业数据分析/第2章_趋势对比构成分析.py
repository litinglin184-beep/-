import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

trend_raw = pd.read_excel(os.path.join(base, '第2章 数据分析方法/2、由基础分析范式引申出的分析方法/data-无答案/1趋势分析.xlsx'), header=None)
trend = pd.DataFrame({
    'year': pd.to_numeric(trend_raw.iloc[2:13, 1]).astype(int).tolist(),
    '订单量': pd.to_numeric(trend_raw.iloc[2:13, 2]).tolist(),
})

compare_raw = pd.read_excel(os.path.join(base, '第2章 数据分析方法/2、由基础分析范式引申出的分析方法/data-无答案/2对比分析.xlsx'), header=None)
compare = pd.DataFrame({
    '产品类型': compare_raw.iloc[2:12, 1].tolist(),
    '订单量': pd.to_numeric(compare_raw.iloc[2:12, 2]).tolist(),
})

comp_raw = pd.read_excel(os.path.join(base, '第2章 数据分析方法/2、由基础分析范式引申出的分析方法/data-无答案/3构成分析.xlsx'), header=None)
comp = pd.DataFrame({
    '产品类型': comp_raw.iloc[4:8, 1].tolist(),
    '销售量': pd.to_numeric(comp_raw.iloc[4:8, 2]).tolist(),
})
comp['占比'] = comp['销售量'] / comp['销售量'].sum()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].plot(trend['year'], trend['订单量'], marker='o', color='#1f77b4', linewidth=2)
axes[0, 0].set_title('趋势分析：近10年订单量波动')
axes[0, 0].set_xlabel('年份')
axes[0, 0].set_ylabel('订单量')

axes[0, 1].bar(compare['产品类型'], compare['订单量'], color='#ff7f0e')
axes[0, 1].set_title('对比分析：不同产品订单量')
axes[0, 1].set_xlabel('产品类型')
axes[0, 1].set_ylabel('订单量')
axes[0, 1].tick_params(axis='x', rotation=45)

axes[1, 0].pie(comp['销售量'], labels=comp['产品类型'], autopct='%1.1f%%', startangle=90)
axes[1, 0].set_title('构成分析：各产品销售量占比')

comp_sorted = comp.sort_values('销售量', ascending=True)
axes[1, 1].barh(comp_sorted['产品类型'], comp_sorted['销售量'], color='#2ca02c')
axes[1, 1].set_title('构成分析：各产品销售量（量）')
axes[1, 1].set_xlabel('销售量')

plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_趋势对比构成分析.png'), dpi=150)
plt.show()

print('趋势分析：')
print(trend)
print('\n构成分析：')
print(comp)
