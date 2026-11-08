import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

base = r'D:/学习作业/数据可视化/1《CDA 一级认证教材：商业数据分析》'
out = r'D:/学习作业/数据可视化/第3章'
os.makedirs(out, exist_ok=True)

df = pd.read_excel(os.path.join(base, '第3章 商业数据分析框架/案例3：电商平台的精准营销/案例3：电商平台的精准营销-原始数据.xlsx'), sheet_name='原始数据')

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

gender = df['性别'].value_counts()
axes[0, 0].pie(gender, labels=gender.index, autopct='%1.1f%%', startangle=90)
axes[0, 0].set_title('性别分布')

age_bins = [0, 20, 30, 40, 50, 60, 100]
age_labels = ['<20', '20-30', '30-40', '40-50', '50-60', '60+']
df['年龄段'] = pd.cut(df['年龄'], bins=age_bins, labels=age_labels, right=False)
age_cnt = df['年龄段'].value_counts().sort_index()
axes[0, 1].bar(age_cnt.index, age_cnt.values, color='#1f77b4')
axes[0, 1].set_title('年龄分布')
axes[0, 1].set_ylabel('人数')

cat = df['品类'].value_counts()
axes[0, 2].barh(cat.index[::-1], cat.values[::-1], color='#2ca02c')
axes[0, 2].set_title('品类销量')
axes[0, 2].set_xlabel('销量')

pay = df['支付方式'].value_counts()
axes[1, 0].pie(pay, labels=pay.index, autopct='%1.1f%%', startangle=90)
axes[1, 0].set_title('支付方式分布')

cross = pd.crosstab(df['性别'], df['品类'])
cross.plot(kind='bar', stacked=True, ax=axes[1, 1])
axes[1, 1].set_title('性别与品类交叉分析')
axes[1, 1].set_ylabel('销量')
axes[1, 1].tick_params(axis='x', rotation=0)

df['订单月份'] = df['订单月份'].astype(str)
month_cat = df.groupby('订单月份')['品类'].value_counts().unstack(fill_value=0)
month_cat.plot(kind='bar', stacked=True, ax=axes[1, 2])
axes[1, 2].set_title('各月份品类销量')
axes[1, 2].set_ylabel('销量')
axes[1, 2].tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig(os.path.join(out, '第3章_电商精准营销.png'), dpi=150)
plt.show()

print('品类销量：')
print(cat)
print('\n支付方式分布：')
print(pay)
print('\n性别 x 品类：')
print(cross)
