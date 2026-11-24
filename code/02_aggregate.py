# -*- coding: utf-8 -*-
"""P1 第2步（v2，优化版）：一次扫描 5000 万行，产出紧凑中间表
优化：不再对全部 (user,cate) 求 first_int，只保留 cate=4（课程口径需要的品类），
      其余中间表规模都只有 O(10万) 行，因此每块聚合极快。
"""
import os, time
import numpy as np
import pandas as pd

RAW = r'D:\dooker\project_p1\data\raw'
OUT = r'D:\dooker\project_p1\output'
os.makedirs(OUT, exist_ok=True)

FILES = ['Data_Action_201602.csv', 'Data_Action_201603.csv', 'Data_Action_201604.csv']
CHUNK = 1_000_000
USE = ['user_id', 'sku_id', 'time', 'type', 'cate']
DT = {'user_id': 'float64', 'sku_id': 'float64', 'time': 'string',
      'type': 'float64', 'cate': 'float64'}


def combine(acc, new, agg):
    if acc is None:
        return new
    return pd.concat([acc, new]).groupby(level=list(range(new.index.nlevels))).agg(agg)


user_acc = None
uc_order_acc = None
uc4_first_acc = None
daily_acc = None
cate_acc = None

t0 = time.time()
for fn in FILES:
    path = os.path.join(RAW, fn)
    n = 0
    for chunk in pd.read_csv(path, usecols=USE, dtype=DT, chunksize=CHUNK):
        n += 1
        chunk = chunk[chunk['type'].notna() & chunk['user_id'].notna() & chunk['cate'].notna()]
        chunk['user_id'] = chunk['user_id'].astype('int64')
        chunk['type'] = chunk['type'].astype('int8')
        chunk['cate'] = chunk['cate'].astype('int16')

        # ---- 用户行为计数 + 首末时间
        u = pd.DataFrame({'user_id': chunk['user_id'].to_numpy(), 'time': chunk['time'].to_numpy()})
        for k in (1, 2, 3, 4, 5, 6):
            u[f'cnt_{k}'] = (chunk['type'].to_numpy() == k).astype('int8')
        g = u.groupby('user_id').agg(
            cnt_1=('cnt_1', 'sum'), cnt_2=('cnt_2', 'sum'), cnt_3=('cnt_3', 'sum'),
            cnt_4=('cnt_4', 'sum'), cnt_5=('cnt_5', 'sum'), cnt_6=('cnt_6', 'sum'),
            first_time=('time', 'min'), last_time=('time', 'max'))
        user_acc = combine(user_acc, g, {'cnt_1': 'sum', 'cnt_2': 'sum', 'cnt_3': 'sum',
                                         'cnt_4': 'sum', 'cnt_5': 'sum', 'cnt_6': 'sum',
                                         'first_time': 'min', 'last_time': 'max'})

        # ---- (用户,品类) 下单（量很小，只几万行）
        o = chunk.loc[chunk['type'] == 4, ['user_id', 'cate', 'time']]
        if len(o):
            go = o.groupby(['user_id', 'cate']).agg(order_cnt=('time', 'size'),
                                                    last_order=('time', 'max'))
            uc_order_acc = combine(uc_order_acc, go, {'order_cnt': 'sum', 'last_order': 'max'})

        # ---- 仅 cate=4 的首次交互时间（课程口径）
        c4 = chunk.loc[chunk['cate'] == 4, ['user_id', 'cate', 'time']]
        if len(c4):
            g4 = c4.groupby(['user_id', 'cate']).agg(first_int=('time', 'min'))
            uc4_first_acc = combine(uc4_first_acc, g4, {'first_int': 'min'})

        # ---- 日维度
        d = pd.DataFrame({'date': chunk['time'].str.slice(0, 10).to_numpy(),
                          'type': chunk['type'].to_numpy()})
        dg = d.groupby(['date', 'type']).size().unstack(fill_value=0)
        daily_acc = combine(daily_acc, dg, {c: 'sum' for c in dg.columns})

        # ---- 品类维度
        cg = pd.DataFrame({'cate': chunk['cate'].to_numpy(),
                           'type': chunk['type'].to_numpy()}) \
            .groupby(['cate', 'type']).size().unstack(fill_value=0)
        cate_acc = combine(cate_acc, cg, {c: 'sum' for c in cg.columns})

    print(f'{fn} done chunks={n} elapsed={time.time()-t0:.0f}s', flush=True)

# ---------------- 落盘 ----------------
user_acc.index.name = 'user_id'
user_acc.to_csv(os.path.join(OUT, 'user_behavior.csv'), encoding='utf-8-sig')

uc_order_acc.index.names = ['user_id', 'cate']
uc_order_acc.to_csv(os.path.join(OUT, 'user_cate_order.csv'), encoding='utf-8-sig')

uc4_first_acc.index.names = ['user_id', 'cate']
uc4_first_acc.to_csv(os.path.join(OUT, 'user_cate4_first.csv'), encoding='utf-8-sig')

daily_acc.to_csv(os.path.join(OUT, 'daily_stats.csv'), encoding='utf-8-sig')
cate_acc.to_csv(os.path.join(OUT, 'cate_stats.csv'), encoding='utf-8-sig')

print('rows user_behavior =', len(user_acc), flush=True)
print('rows user_cate_order =', len(uc_order_acc), flush=True)
print('rows user_cate4_first =', len(uc4_first_acc), flush=True)
print('rows daily =', len(daily_acc), 'rows cate =', len(cate_acc), flush=True)
print(f'ALL DONE in {time.time()-t0:.0f}s', flush=True)
