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

df = pd.read_excel(os.path.join(base, '第2章 数据分析方法/1、分析的基础范式/data-无答案/1-4同期群分析.xlsx'), sheet_name='用户登录明细')
df['注册日期'] = pd.to_datetime(df['注册日期']).dt.date
df['登录时点'] = pd.to_datetime(df['登录时点']).dt.date
df['天数差'] = (pd.to_datetime(df['登录时点']) - pd.to_datetime(df['注册日期'])).dt.days

df = df.drop_duplicates(subset=['用户编号', '注册日期', '天数差'])

cohort_size = df.groupby('注册日期')['用户编号'].nunique()

cohort = df.pivot_table(index='注册日期', columns='天数差', values='用户编号', aggfunc='nunique')
cohort = cohort.reindex(columns=range(0, 31), fill_value=0)

retention = cohort.div(cohort_size, axis=0)

cols_to_show = [0, 1, 3, 7, 14, 30]
ret_show = retention[cols_to_show]

fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(ret_show.values, cmap='YlGnBu', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(cols_to_show)))
ax.set_xticklabels([f'第{i}天' for i in cols_to_show])
ax.set_yticks(range(ret_show.shape[0]))
ax.set_yticklabels([str(x) for x in ret_show.index])
for i in range(ret_show.shape[0]):
    for j in range(ret_show.shape[1]):
        v = ret_show.iloc[i, j]
        ax.text(j, i, f'{v:.0%}', ha='center', va='center', fontsize=9)
ax.set_xlabel('注册后留存天数')
ax.set_ylabel('注册日期')
ax.set_title('同期群留存分析（按注册日）')
plt.colorbar(im)
plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_同期群分析.png'), dpi=150)
plt.show()

print(ret_show.round(2))
