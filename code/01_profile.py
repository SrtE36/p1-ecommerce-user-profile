# -*- coding: utf-8 -*-
"""P1 电商用户画像 - 第1步：数据画像（chunked，低内存）"""
import os, json, time
import numpy as np
import pandas as pd
from collections import Counter

RAW = r'D:\dooker\project_p1\data\raw'
OUT = r'D:\dooker\project_p1\output'
os.makedirs(OUT, exist_ok=True)

FILES = ['Data_Action_201602.csv', 'Data_Action_201603.csv', 'Data_Action_201604.csv']

summary = {}
all_users = []

for fn in FILES:
    path = os.path.join(RAW, fn)
    t0 = time.time()
    rows = 0
    tmin = tmax = None
    type_cnt = Counter()
    cate_cnt = Counter()
    model_null = 0
    user_arrays = []

    it = pd.read_csv(
        path,
        usecols=['user_id', 'sku_id', 'time', 'model_id', 'type', 'cate', 'brand'],
        dtype={'user_id': 'float64', 'sku_id': 'float64', 'time': 'string',
               'type': 'float64', 'cate': 'float64', 'brand': 'float64'},
        chunksize=500_000,
    )
    for chunk in it:
        rows += len(chunk)
        s = chunk['time'].dropna()
        lo, hi = s.min(), s.max()
        if tmin is None or lo < tmin: tmin = lo
        if tmax is None or hi > tmax: tmax = hi
        vc = chunk['type'].dropna().astype(int).value_counts()
        type_cnt.update(vc.to_dict())
        vc2 = chunk['cate'].dropna().astype(int).value_counts().head(60)
        cate_cnt.update(vc2.to_dict())
        model_null += int(chunk['model_id'].isna().sum())
        u = np.unique(chunk['user_id'].dropna().astype('int64').to_numpy())
        user_arrays.append(u)

    uniq = np.unique(np.concatenate(user_arrays)) if user_arrays else np.array([], dtype='int64')
    all_users.append(uniq)
    summary[fn] = dict(rows=int(rows), t_min=str(tmin), t_max=str(tmax),
                       n_users=int(len(uniq)),
                       types={int(k): int(v) for k, v in type_cnt.items()},
                       model_null=int(model_null),
                       top_cate={int(k): int(v) for k, v in cate_cnt.most_common(15)},
                       secs=round(time.time() - t0, 1))
    print(fn, json.dumps(summary[fn], ensure_ascii=False), flush=True)

global_users = np.unique(np.concatenate(all_users)) if all_users else np.array([], dtype='int64')
print('GLOBAL unique users:', len(global_users), flush=True)

# User_table
u = pd.read_csv(os.path.join(RAW, 'User_table.csv'))
print('USER_TABLE rows', len(u), flush=True)
print('dtypes:', u.dtypes.to_dict(), flush=True)
print('age uniques:', sorted(u['age'].dropna().unique().tolist()), flush=True)
print('sex uniques:', sorted(u['sex'].dropna().unique().tolist()), flush=True)
print('lv uniques:', sorted(u['user_lv_cd'].dropna().unique().tolist()), flush=True)
print('null counts:', u.isna().sum().to_dict(), flush=True)

summary['global'] = dict(total_rows=int(sum(s['rows'] for s in summary.values() if isinstance(s, dict) and 'rows' in s)),
                         total_unique_users=int(len(global_users)))
summary['user_table'] = dict(rows=int(len(u)), cols=list(u.columns),
                             age_min=int(u['age'].min()), age_max=int(u['age'].max()),
                             lv_min=int(u['user_lv_cd'].min()), lv_max=int(u['user_lv_cd'].max()))

with open(os.path.join(OUT, '01_profile.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print('saved 01_profile.json', flush=True)
