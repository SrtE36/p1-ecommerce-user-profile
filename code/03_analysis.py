# -*- coding: utf-8 -*-
"""P1 第3步：高潜用户识别 + 画像对比 + 行为漏斗 + 周内规律"""
import os, json
import pandas as pd
import numpy as np

OUT = r'D:\dooker\project_p1\output'
RAW = r'D:\dooker\project_p1\data\raw'

ub = pd.read_csv(os.path.join(OUT, 'user_behavior.csv'), index_col='user_id')
uco = pd.read_csv(os.path.join(OUT, 'user_cate_order.csv'))
ucf = pd.read_csv(os.path.join(OUT, 'user_cate4_first.csv'))
daily = pd.read_csv(os.path.join(OUT, 'daily_stats.csv'), index_col='date')
cate = pd.read_csv(os.path.join(OUT, 'cate_stats.csv'), index_col='cate')
ut = pd.read_csv(os.path.join(RAW, 'User_table.csv'))

for df in (ub, uco, ucf, ut):
    if 'user_id' in df.columns:
        df['user_id'] = df['user_id'].astype('int64')

ut = ut.drop_duplicates('user_id')

# ---------- 1) 用户维度汇总 ----------
ub['total_events'] = ub[['cnt_1', 'cnt_2', 'cnt_3', 'cnt_4', 'cnt_5', 'cnt_6']].sum(axis=1)
ub['has_order'] = ub['cnt_4'] > 0
ub['has_addcart'] = ub['cnt_2'] > 0
ub['has_favor'] = ub['cnt_5'] > 0
ub['has_click'] = ub['cnt_6'] > 0
ub['has_browse'] = ub['cnt_1'] > 0

last_order = uco.groupby('user_id')['last_order'].max()
order_cnt_user = uco.groupby('user_id')['order_cnt'].sum()
ub['last_order_time'] = last_order
ub['order_cnt_allcate'] = order_cnt_user.reindex(ub.index).fillna(0).astype('int64')

ub['first_time'] = pd.to_datetime(ub['first_time'], errors='coerce')
ub['last_order_time'] = pd.to_datetime(ub['last_order_time'], errors='coerce')
ub['decision_gap_days'] = (ub['last_order_time'] - ub['first_time']).dt.total_seconds() / 86400

# 用户级「决策型高潜」：有购买 且 首次交互→最后下单 > 1 天
ub['is_high_pot_user'] = ub['has_order'] & (ub['decision_gap_days'] > 1)

# 课程口径（品类 4）的高潜：该品类下单 且 该品类首次交互→最后下单 > 1 天
c4 = uco[uco['cate'] == 4].set_index(['user_id', 'cate'])
f4 = ucf[ucf['cate'] == 4].set_index(['user_id', 'cate'])
c4 = c4.join(f4, how='left')
c4['last_order'] = pd.to_datetime(c4['last_order'], errors='coerce')
c4['first_int'] = pd.to_datetime(c4['first_int'], errors='coerce')
c4['gap_days'] = (c4['last_order'] - c4['first_int']).dt.total_seconds() / 86400
high_pot_c4 = c4[(c4['gap_days'] > 1)].reset_index()[['user_id']].drop_duplicates()
high_pot_c4['is_high_pot_cate4'] = 1

# 高意向未购：有加购或关注，但无下单
ub['is_intent_no_buy'] = (~ub['has_order']) & (ub['has_addcart'] | ub['has_favor'])

# ---------- 2) 合并静态属性 ----------
full = ub.reset_index().merge(ut, on='user_id', how='left')
full = full.merge(high_pot_c4, on='user_id', how='left')
full['is_high_pot_cate4'] = full['is_high_pot_cate4'].fillna(0).astype(int)

# ---------- 3) 分层 ----------
def seg(r):
    if r['is_high_pot_user']:
        return '决策型高潜'
    if r['has_order']:
        return '快速决策购买'
    if r['is_intent_no_buy']:
        return '高意向未购'
    if r['has_browse'] or r['has_click']:
        return '普通浏览'
    return '沉默'

full['segment'] = full.apply(seg, axis=1)

# ---------- 4) 漏斗（用户级） ----------
funnel = {
    '点击用户': int(full['has_click'].sum()),
    '浏览用户': int(full['has_browse'].sum()),
    '加购用户': int(full['has_addcart'].sum()),
    '关注用户': int(full['has_favor'].sum()),
    '下单用户': int(full['has_order'].sum()),
}
base = funnel['点击用户']
funnel_pct = {k: round(v / base * 100, 2) for k, v in funnel.items()}

# ---------- 5) 画像对比（高潜 vs 快速决策 vs 全体） ----------
buyers = full[full['has_order']]
hp = full[full['is_high_pot_user']]
fast = buyers[~buyers['is_high_pot_user']]

def dist(df, col, order=None):
    s = df[col].value_counts(normalize=True, dropna=False) * 100
    if order is not None:
        s = s.reindex(order).fillna(0)
    return s.round(2)

age_order = [-1, 1, 2, 3, 4, 5, 6]
profile = pd.DataFrame({
    '全体用户': dist(full, 'age', age_order),
    '购买用户': dist(buyers, 'age', age_order),
    '高潜用户': dist(hp, 'age', age_order),
})
profile.index.name = 'age'

sex_profile = pd.DataFrame({
    '全体用户': dist(full, 'sex', [0, 1, 2]),
    '购买用户': dist(buyers, 'sex', [0, 1, 2]),
    '高潜用户': dist(hp, 'sex', [0, 1, 2]),
})

lv_profile = pd.DataFrame({
    '全体用户': dist(full, 'user_lv_cd', [1, 2, 3, 4, 5]),
    '购买用户': dist(buyers, 'user_lv_cd', [1, 2, 3, 4, 5]),
    '高潜用户': dist(hp, 'user_lv_cd', [1, 2, 3, 4, 5]),
})

# ---------- 6) 周内下单规律 ----------
d = daily.copy()
d.index = pd.to_datetime(d.index, errors='coerce')
d = d[d.index.notna()]
d['weekday'] = d.index.dayofweek
order_col = '4' if '4' in d.columns else 4
weekday = d.groupby('weekday')[order_col].sum().rename('orders')

# ---------- 7) 输出 ----------
summary = {
    'n_users': int(len(full)),
    'n_buyers': int(full['has_order'].sum()),
    'n_high_pot_user': int(full['is_high_pot_user'].sum()),
    'n_high_pot_cate4': int(full['is_high_pot_cate4'].sum()),
    'n_intent_no_buy': int(full['is_intent_no_buy'].sum()),
    'buyer_rate_pct': round(full['has_order'].mean() * 100, 2),
    'high_pot_rate_in_buyers_pct': round(full.loc[buyers.index, 'is_high_pot_user'].mean() * 100, 2),
    'hp_avg_orders': round(float(hp['order_cnt_allcate'].mean()), 3) if len(hp) else 0,
    'fast_avg_orders': round(float(fast['order_cnt_allcate'].mean()), 3) if len(fast) else 0,
    'segment_counts': full['segment'].value_counts().to_dict(),
    'funnel_users': funnel,
    'funnel_pct_of_click': funnel_pct,
    'weekday_orders': {int(k): int(v) for k, v in weekday.items()},
}

os.makedirs(OUT, exist_ok=True)
full[['user_id', 'segment', 'is_high_pot_user', 'is_high_pot_cate4', 'order_cnt_allcate',
      'decision_gap_days', 'total_events', 'cnt_1', 'cnt_2', 'cnt_3', 'cnt_4', 'cnt_5', 'cnt_6']] \
    .to_csv(os.path.join(OUT, 'segments.csv'), index=False, encoding='utf-8-sig')
hp.to_csv(os.path.join(OUT, 'high_potential_users.csv'), index=False, encoding='utf-8-sig')
profile.to_csv(os.path.join(OUT, 'profile_age.csv'), encoding='utf-8-sig')
sex_profile.to_csv(os.path.join(OUT, 'profile_sex.csv'), encoding='utf-8-sig')
lv_profile.to_csv(os.path.join(OUT, 'profile_level.csv'), encoding='utf-8-sig')
weekday.to_csv(os.path.join(OUT, 'weekday_orders.csv'), encoding='utf-8-sig')

with open(os.path.join(OUT, '03_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
print('\nAGE PROFILE:\n', profile)
print('\nSEX PROFILE:\n', sex_profile)
print('\nLEVEL PROFILE:\n', lv_profile)
print('\nWEEKDAY ORDERS:\n', weekday)
