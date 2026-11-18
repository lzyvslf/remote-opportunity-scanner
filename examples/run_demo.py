"""离线演示：读取合成样例，跑完整流水线并打印每日清单。

运行方式（在仓库根目录）：
    python examples/run_demo.py
"""

import sys
from pathlib import Path

# 允许从仓库根目录直接运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oppscan import digest, pipeline, sources

PROFILE = {
    "stack_any": ["python", "爬虫", "自动化", "数据", "api"],
    "exclude_terms": ["代写", "课设", "抢购", "充值"],
    "keywords_any": [],
}


def main():
    records = sources.load_jsonl(ROOT / "examples" / "sample_opps.jsonl")
    result = pipeline.run(
        sources=[{"name": "sample", "records": records}],
        profile=PROFILE,
    )
    store = result["store"]

    print("== 流水线统计 ==")
    for key, value in result["summary"].items():
        print(f"  {key}: {value}")
    print()

    items = store.recent()
    print("== Markdown 清单 ==")
    print(digest.to_markdown(items))

    print("== CSV 预览（前 3 行） ==")
    csv_text = digest.to_csv(items).splitlines()
    for line in csv_text[:3]:
        print("  " + line)

    store.close()
    print("\n演示完成。清单仅供人工评估，联系动作需手动完成。")


if __name__ == "__main__":
    main()
