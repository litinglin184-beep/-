import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.sankey import Sankey
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第2章 数据分析方法/2、由基础分析范式引申出的分析方法/data-无答案/6桑吉图.xlsx'), sheet_name='Sheet1')

nodes = sorted(set(df['来源']) | set(df['目标']))
node_map = {n: i for i, n in enumerate(nodes)}
df['source_idx'] = df['来源'].map(node_map)
df['target_idx'] = df['目标'].map(node_map)

fig, ax = plt.subplots(figsize=(12, 8))
sankey = Sankey(ax=ax, unit=None, scale=0.0001, offset=0.2, format='%.0f')
for _, row in df.iterrows():
    sankey.add(flows=[-row['流量'], row['流量']],
               labels=[row['来源'], row['目标']],
               orientations=[0, 0],
               pathlengths=[0.5, 0.5],
               facecolor='#1f77b4',
               alpha=0.6)
diagrams = sankey.finish()
plt.title('网站用户流转桑基图')
plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_桑基图.png'), dpi=150)
plt.show()

print(df[['来源', '目标', '流量']])
