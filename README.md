# remote-opportunity-scanner · 公开需求聚合扫描器（示例）

一个轻量、纯 Python 标准库 + SQLite 的需求线索扫描器：把多个公开来源的项目/远程需求汇总成清单，按画像硬过滤、规则评分、阈值决策，本地去重入库，最后输出 Markdown / CSV 每日清单。不依赖任何 Web 框架或第三方包。

> 本仓库由自由职业者查找对口项目的实际流程抽象而成，重写为标准库示例；样例数据全部为合成数据，不含真实客户联系方式、私信记录或业务敏感信息。

## 一、模块一览

| 模块 | 作用 | 典型场景 |
|---|---|---|
| `oppscan.models` | 记录标准化与文本匹配，统一各来源字段 | 对接不同 API / JSONL 时先归一结构 |
| `oppscan.sources` | 公开 JSON API 与本地 JSONL 读取，逐源隔离错误 | 拉取公开需求板、读取离线样例 |
| `oppscan.filter` | 声明式画像硬过滤：排除词 → 技术栈 → 关键词 | 评分前先剔除明显不匹配的记录 |
| `oppscan.score` | 本地规则评分与 apply / review / skip 确定性决策 | 给出可复现、可审计的优先级判断 |
| `oppscan.store` | SQLite 链接哈希去重、状态记录与跟进标记 | 避免重复推送，记录 new / applied / skipped |
| `oppscan.digest` | 生成 Markdown 分组清单与 CSV 表格 | 人工评估与后续跟进 |
| `oppscan.pipeline` | 串联 采集 → 标准化 → 过滤 → 评分 → 去重 → 清单 | 每日定时跑一遍出清单 |

## 二、目录结构

```
remote-opportunity-scanner/
├── oppscan/
│   ├── models.py      # 标准化与文本匹配
│   ├── sources.py      # 公开数据源适配
│   ├── filter.py      # 画像硬过滤
│   ├── score.py       # 规则评分与决策
│   ├── store.py       # SQLite 去重与状态
│   ├── digest.py      # Markdown / CSV 清单
│   └── pipeline.py    # 流水线编排
├── examples/
│   ├── sample_opps.jsonl  # 合成样例
│   └── run_demo.py        # 离线演示
├── tests/                 # unittest 用例
├── README.md
└── LICENSE
```

## 三、本地运行

环境：Python 3.10+，无第三方依赖。

```powershell
# 离线演示：读取合成样例，打印统计与每日清单
python examples/run_demo.py

# 运行单元测试
python -m unittest discover -s tests -v
```

## 四、使用示例

### 1. 定义画像并跑流水线

```python
from oppscan import pipeline, sources

profile = {
    "stack_any": ["python", "自动化", "爬虫", "api"],
    "exclude_terms": ["代写", "课设", "抢购", "充值"],
    "keywords_any": [],
}

records = sources.load_jsonl("examples/sample_opps.jsonl")
result = pipeline.run(
    sources=[{"name": "sample", "records": records}],
    profile=profile,
)
print(result["summary"])
result["store"].close()
```

### 2. 接入公开 JSON API

```python
from oppscan import sources

records = sources.fetch_json(
    "https://example.com/api/jobs",
    list_key="data.jobs",
    field_map={"title": "name", "url": "link"},
)
```

### 3. 输出清单

```python
from oppscan import digest

items = store.recent()
print(digest.to_markdown(items))   # Markdown 分组清单
print(digest.to_csv(items))       # CSV 表格文本
```

### 4. 人工跟进后标记状态

```python
store.mark_status("https://example.com/opp/001", "applied")
```

## 五、合规与边界

- 只读取公开可访问的 API 与公开页面；**不登录任何社交/职业平台账号，不采集私人联系方式，不绕过平台风控**。
- 工具只产出供人工评估的清单；**不自动私信、不自动发信、不自动投递**，联系动作始终由本人手动完成。
- 样例数据全部为合成数据；真实使用时应尊重各数据源的服务条款与 robots 约定，数据归属对应来源与发布方。
- 仓库不含任何交易策略、荐股内容或收益承诺。

## 六、许可证

MIT，见 [LICENSE](LICENSE)。
