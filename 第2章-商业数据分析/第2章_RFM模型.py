import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第2章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第2章 数据分析方法/1、分析的基础范式/data-无答案/1-2RFM模型.xlsx'), sheet_name='原始数据')
df['销售日期'] = pd.to_datetime(df['销售日期'])

now = df['销售日期'].max()

rfm = df.groupby('用户编号').agg(
    R=('销售日期', lambda x: (now - x.max()).days),
    F=('流水号', 'count'),
    M=('销售金额', 'sum')
).reset_index()

r_med = rfm['R'].median()
f_med = rfm['F'].median()
m_med = rfm['M'].median()

rfm['R高'] = (rfm['R'] <= r_med).astype(int)
rfm['F高'] = (rfm['F'] > f_med).astype(int)
rfm['M高'] = (rfm['M'] > m_med).astype(int)

def classify(row):
    r, f, m = row['R高'], row['F高'], row['M高']
    if r == 1 and f == 1 and m == 1:
        return '重要价值用户'
    if r == 1 and f == 0 and m == 1:
        return '重要发展用户'
    if r == 0 and f == 1 and m == 1:
        return '重要保持用户'
    if r == 0 and f == 0 and m == 1:
        return '重要挽留用户'
    if r == 1 and f == 1 and m == 0:
        return '一般价值用户'
    if r == 1 and f == 0 and m == 0:
        return '一般发展用户'
    if r == 0 and f == 1 and m == 0:
        return '一般保持用户'
    return '一般挽留用户'

rfm['用户类别'] = rfm.apply(classify, axis=1)

cat = rfm['用户类别'].value_counts()
fig, ax = plt.subplots(figsize=(8, 6))
cat.plot(kind='bar', ax=ax, color='#1f77b4')
ax.set_title('RFM 用户分类分布')
ax.set_xlabel('用户类别')
ax.set_ylabel('用户数')
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(out, '第2章_RFM模型.png'), dpi=150)
plt.show()

print(cat)
