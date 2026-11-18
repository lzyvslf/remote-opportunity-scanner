"""每日清单输出（Markdown / CSV）。

只生成供人工评估的清单文本，不生成投递话术，也不触发任何联系动作。
"""

import csv
import io

DECISION_ORDER = ["apply", "review", "skip"]
DECISION_LABELS = {"apply": "优先联系", "review": "待评估", "skip": "暂缓"}


def _group(items):
    groups = {key: [] for key in DECISION_ORDER}
    for item in items:
        groups.setdefault(item.get("decision", "skip"), []).append(item)
    return groups


def to_markdown(items, title="每日机会清单"):
    """生成 Markdown 清单，按决策分组。"""
    lines = [f"# {title}", ""]
    groups = _group(items)

    for decision in DECISION_ORDER:
        bucket = groups[decision]
        if not bucket:
            continue
        lines.append(f"## {DECISION_LABELS[decision]}（{len(bucket)}）")
        lines.append("")
        for item in bucket:
            reason = item.get("reason") or ""
            lines.append(f"- **{item['title']}**")
            lines.append(f"  - 来源：{item.get('source', '')}｜评分：{item.get('score', 0)}")
            if reason:
                lines.append(f"  - 理由：{reason}")
            lines.append(f"  - 链接：{item.get('url', '')}")
        lines.append("")

    if not items:
        lines.append("今日无新机会。")
    return "\n".join(lines).strip() + "\n"


def to_csv(items):
    """生成 CSV 文本，便于导入表格跟进。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["decision", "score", "source", "title", "url", "reason"])
    for item in items:
        writer.writerow(
            [
                item.get("decision", ""),
                item.get("score", ""),
                item.get("source", ""),
                item.get("title", ""),
                item.get("url", ""),
                item.get("reason", ""),
            ]
        )
    return buffer.getvalue()
