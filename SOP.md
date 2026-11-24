# P1 项目 SOP｜电商用户行为分析与高潜用户画像

> 适用：数据分析师岗位作品集项目 / 面试讲述 / 团队复现
> 数据：50,601,736 行行为日志（2.19 GB）+ 105,321 行用户属性
> 周期：单人 3~5 天（含报告）；工具：SQL + Python(Pandas) + Excel/Tableau

---

## 一、流程总览（11 步）

| 阶段 | 步骤 | 输入 | 工具 | 输出 | 验收标准 | 耗时 |
|---|---|---|---|---|---|---|
| 立项 | 1. 定义业务问题 | 需求方/业务背景 | — | 问题陈述 + 成功指标 | 能一句话说清"解决什么业务问题" | 0.5h |
| 准备 | 2. 取数与数据字典 | 行为日志、用户表 | SQL | 数据字典 + 数据量评估 | 字段含义、时间范围、行数齐全 | 1h |
| 准备 | 3. 数据质量检查 | 原始 CSV | Python | 质量报告 | 缺失率/重复/异常有记录 | 0.5h |
| 清洗 | 4. 数据清洗加工 | 原始数据 | Python | 清洗后数据/中间表 | 类型正确、时间可解析、去重 | 1h |
| 定义 | 5. 指标体系与口径 | 业务问题 | 文档 | 指标定义文档 | 口径可复现、无歧义 | 0.5h |
| 加工 | 6. 聚合与建模 | 清洗数据 | SQL/Python | 用户级/品类级中间表 | 与原始数据对得上 | 2h |
| 分析 | 7. 描述与分层分析 | 中间表 | Python | 分层结果、漏斗 | 分层占比合计 100% | 2h |
| 分析 | 8. 画像对比与下钻 | 中间表 + 用户表 | Python | 画像对比表 | 组间差异可解释 | 1.5h |
| 呈现 | 9. 可视化与报告 | 分析结果 | Excel/Tableau | 图表 + 报告 | 结论有数据支撑 | 2h |
| 收尾 | 10. 复盘与归档 | 全部 | — | README + 代码 + 归档 | 他人可一键复现 | 0.5h |
| 收尾 | 11. GitHub 托管 | 代码/文档 | Git + GitHub | 远程仓库 + 版本历史 | 面试官可访问、可 clone 跑通 | 0.5h |

---

## 二、分步 SOP（可执行）

### Step 1｜定义业务问题
- 动作：把"做个用户分析"翻译成可量化问题。
- 本项目问题：
  1. 谁是高潜用户？规模多少？
  2. 高潜用户 vs 普通用户差异在哪？
  3. 资源有限时优先触达谁？
- 成功指标：识别出可运营的高潜人群 + 给出 3 条以上可执行策略。
- ✅ 检查点：问题必须能落到"人群 + 动作 + 预期效果"。

### Step 2｜取数与数据字典
- 动作：确认表结构、时间范围、数据量。
- 实际：3 个行为文件 50,601,736 行；用户表 105,321 行；时间 2016-01-31~04-15。
- ✅ 检查点：字段含义（尤其 `type` 1~6）必须与业务确认，不能猜。

### Step 3｜数据质量检查
- 动作：`df.head()`、`dtypes`、`isna().sum()`、`describe()`、时间 min/max、type 分布。
- 实际发现：`model_id` 仅点击行为有值（缺失约 43%~53%）；age/sex 有 -1/0 未知值；用户表 141 行缺失行为计数。
- ✅ 检查点：每个缺失字段都要说明"为什么缺、要不要补"。

### Step 4｜数据清洗加工
- 动作：类型转换（user_id float→int，type int8，cate int16）、时间→datetime、去重、过滤空值。
- 分块读取（数据 >2GB，内存装不下）：
```python
for chunk in pd.read_csv(path, usecols=['user_id','sku_id','time','type','cate'],
                         dtype={...}, chunksize=1_000_000):
    ...
```
- ✅ 检查点：清洗前后行数差可解释。

### Step 5｜指标体系与口径
- 动作：写死口径，避免"同名不同义"。
- 本项目口径：
  - 行为漏斗：用户级"是否发生"（非次数）。
  - 高潜用户：**有下单** 且 **首次交互→最后下单 > 1 天**。
  - 课程口径（品类 4）：该品类内下单且首次交互→最后下单 > 1 天。
- ✅ 检查点：口径写进文档，代码注释一致。

### Step 6｜聚合与建模
- 动作：一次扫描产出中间表（用户表/用户-品类表/日表/品类表）。
- 关键：**先聚合再分析**，后续只读小表，避免重复扫 2GB。
- ✅ 检查点：中间表行数 = 去重用户数（105,180）等可核对值。

### Step 7｜描述与分层分析
- 动作：用户分层（决策型高潜/快速决策/高意向未购/普通浏览）、漏斗、周内规律。
- 实际：买家率 28.03%；高潜 26,385（占买家 89.5%）。
- ✅ 检查点：分层互斥且合计 100%。

### Step 8｜画像对比与下钻
- 动作：高潜 vs 购买 vs 全体，按年龄/性别/等级对比；品类转化率下钻。
- 实际：高潜中等级 5 占 50.14%；cate 8 转化 9.67%、cate 7 转化 24.04%。
- ✅ 检查点：每个差异给出业务解释，不做"数字堆砌"。

### Step 9｜可视化与报告
- 动作：漏斗图、品类转化柱状图、画像对比、周内曲线；报告按"结论先行"写。
- 工具：Excel 透视表/图表，或 Tableau。
- ✅ 检查点：每张图对应一个结论，标题即结论。

### Step 10｜复盘与归档
- 动作：README（问题/数据/方法/结论/复现步骤）、代码目录、报告归档。
- ✅ 检查点：新人拿到项目能 30 分钟内跑通。

---

## 三、三个工具的使用情况

> 项目"三件套"：**SQL 取数 → Python 分析 → Excel/Tableau 呈现**。
> 本次实际运行以 Python 为主（全流程可跑通），SQL 与 Excel/Tableau 是等价复现与呈现方案。

### 3.1 SQL（MySQL）—— 取数与聚合

| 项目 | 说明 |
|---|---|
| 使用环节 | Step 2 取数、Step 6 聚合、日常取数 |
| 承担工作 | 从原始日志做 `GROUP BY` 聚合、窗口/时间差计算 |
| 工作量占比 | 约 **20%**（在真实生产环境通常是主入口） |

关键 SQL（与 Python 口径一致）：

```sql
-- 用户行为汇总
CREATE TABLE user_behavior AS
SELECT user_id,
       SUM(type = 1) AS cnt_1, SUM(type = 2) AS cnt_2,
       SUM(type = 4) AS cnt_4, SUM(type = 5) AS cnt_5, SUM(type = 6) AS cnt_6,
       MIN(time) AS first_time, MAX(time) AS last_time
FROM data_action
GROUP BY user_id;

-- 每用户最后下单时间
CREATE TABLE user_last_order AS
SELECT user_id, MAX(time) AS last_order
FROM data_action WHERE type = 4
GROUP BY user_id;

-- 决策型高潜：首交互→最后下单 > 1 天
SELECT b.user_id,
       TIMESTAMPDIFF(DAY, b.first_time, o.last_order) AS gap_days
FROM user_behavior b
JOIN user_last_order o USING (user_id)
WHERE b.cnt_4 > 0
  AND TIMESTAMPDIFF(DAY, b.first_time, o.last_order) > 1;
```

- 价值：数据量再大也能在库里完成聚合，只把"小结果"拉进 Python。
- 面试常问：`TIMESTAMPDIFF`、窗口函数、大表 JOIN 优化。

### 3.2 Python（Pandas / NumPy）—— 清洗、聚合、分析

| 项目 | 说明 |
|---|---|
| 使用环节 | Step 3~8 全流程 |
| 承担工作 | 分块读取、类型转换、聚合、分层、画像、指标计算 |
| 工作量占比 | 约 **70%**（本次实际 100% 由它完成） |

关键代码（分块 + 增量聚合，2GB 不进内存）：

```python
def combine(acc, new, agg):
    if acc is None:
        return new
    return pd.concat([acc, new]).groupby(level=list(range(new.index.nlevels))).agg(agg)

for chunk in pd.read_csv(path, usecols=USE, dtype=DT, chunksize=1_000_000):
    chunk = chunk[chunk['type'].notna()]
    chunk['user_id'] = chunk['user_id'].astype('int64')
    chunk['type'] = chunk['type'].astype('int8')
    u = pd.DataFrame({'user_id': chunk['user_id'], 'time': chunk['time']})
    for k in (1, 2, 3, 4, 5, 6):
        u[f'cnt_{k}'] = (chunk['type'] == k).astype('int8')
    g = u.groupby('user_id').agg({...})
    user_acc = combine(user_acc, g, {...})
```

- 价值：可复用、可版本化、能处理单机装不下的数据。
- 面试常问：为什么用 chunk？如何保证内存可控？聚合口径怎么对齐？

### 3.3 Excel / Tableau —— 呈现与初探

| 项目 | 说明 |
|---|---|
| 使用环节 | Step 9 可视化、Step 3 快速初探 |
| 承担工作 | 透视表核对、漏斗/柱状/折线图、看板、汇报 |
| 工作量占比 | 约 **10%** |

典型操作：
- Excel：`数据透视表` 做"品类 × 下单量"；`插入图表` 做漏斗与周内曲线；`条件格式` 标异常。
- Tableau：把 `segments.csv` 连入 → 拖维度出图 → 做"分层 × 画像 × 品类"三联看板。
- 价值：**非技术同事/面试官看的是图，不是代码**。

### 3.4 三工具分工总结

| 环节 | SQL | Python | Excel/Tableau |
|---|---|---|---|
| 取数 | ★★★ | ★ | ★ |
| 清洗 | ★ | ★★★ | ★★（小数据） |
| 聚合 | ★★★（大表） | ★★★（单机） | ★ |
| 分析/建模 | ★ | ★★★ | ★ |
| 可视化/汇报 | — | ★ | ★★★ |
| 复现性 | ★★ | ★★★ | ★ |

> 一句话：**SQL 负责"把数据变小"，Python 负责"把数据想清楚"，Excel/Tableau 负责"把结论讲明白"。**

---

## 四、GitHub 使用（代码托管 + 版本管理 + 作品集）

| 项目 | 说明 |
|---|---|
| 使用环节 | Step 10/11：归档与托管 |
| 承担工作 | 版本控制、远程备份、作品集展示、协作与复现 |
| 核心动作 | `git init` → `.gitignore` → `add/commit` → `remote add` → `push` |

### 4.1 本项目到底用 GitHub 做什么

1. **版本管理**：口径改一次就 commit 一次，面试被问"为什么这么定义"可回看历史。
2. **作品集展示**：README + 代码 + 结果表，是简历上"项目经历"的可点击证据。
3. **可复现**：`requirements.txt` + 三步命令，任何人能跑通。
4. **加分玩法**：GitHub Pages 放报告、Issues 管理分析任务、Actions 定时跑数。

### 4.2 标准操作（在项目根目录执行）

```bash
git init
git add .
git commit -m "feat: 初始化电商用户画像项目（数据画像/聚合/高潜识别）"

# 在 GitHub 新建空仓库后：
git branch -M main
git remote add origin https://github.com/<你的用户名>/p1-ecommerce-user-profile.git
git push -u origin main
```

### 4.3 关键注意事项

- **原始数据绝不能提交**：`.gitignore` 已排除 `data/raw/`（2.19 GB），只提交代码、结果、文档。
- **敏感信息**：不要把数据库密码、账号 token 写进代码（用环境变量）。
- **提交粒度**：一个分析点一个 commit，信息用 `feat/fix/docs/chore` 前缀。
- **面试话术**："代码在 GitHub，README 里有复现步骤和结果，您可以点开看。"

> 本机当前**未安装 git**，仓库文件（`.gitignore`、`requirements.txt`、README）已准备好；装好 Git 后按 4.2 执行即可。

---

## 五、质量检查清单（交付前必过）

- [ ] 数据量、时间范围与数据字典一致
- [ ] 每个缺失字段有处理说明
- [ ] 中间表行数可与原始数据核对
- [ ] 分层互斥、合计 100%
- [ ] 每个结论有一张图/一组数支撑
- [ ] 口径文档与代码注释一致
- [ ] README 能让他人复现
- [ ] 报告"结论先行"，不超过 5 页
- [ ] `.gitignore` 已排除原始数据，仓库可公开

---

## 六、交付物与归档

```
project_p1/
├─ README.md              # 项目说明 + 结果摘要
├─ SOP.md                 # 本文件
├─ requirements.txt       # 依赖
├─ .gitignore             # 排除原始数据
├─ code/                  # 01画像 02聚合 03分析
├─ data/raw/              # 原始数据（不入库，只留说明）
├─ output/                # 中间表 + 结果 CSV
└─ report/分析报告.md       # 业务报告
```
