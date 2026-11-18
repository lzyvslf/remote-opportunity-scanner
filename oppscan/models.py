"""标准化记录结构与字段清洗。

所有数据源适配后都归一为同一套字段，便于后续过滤、评分、去重与
清单输出。纯标准库实现，输入输出均为 dict / list[dict]。
"""

import re

# 标准字段顺序，便于清单与 CSV 输出对齐。
FIELDS = [
    "source",
    "title",
    "url",
    "description",
    "stack",
    "budget",
    "location",
    "posted_at",
]

_WS = re.compile(r"\s+")


def _clean_text(value):
    """压缩空白并去除首尾空格；非字符串按空串处理。"""
    if value is None:
        return ""
    return _WS.sub(" ", str(value)).strip()


def _clean_stack(value):
    """技术栈归一为小写、去重、保序的字符串列表。"""
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    else:
        items = list(value)
    seen = set()
    out = []
    for item in items:
        token = _clean_text(item).lower()
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def normalize(record, source=""):
    """把一条原始记录归一为标准结构。

    Args:
        record: dict，字段名可能来自不同数据源。
        source: 来源标识，如 "remotive"、"sample"。

    Returns:
        dict，包含 FIELDS 列出的标准字段与原始 raw 副本。
    """
    return {
        "source": _clean_text(record.get("source") or source),
        "title": _clean_text(record.get("title")),
        "url": _clean_text(record.get("url")),
        "description": _clean_text(record.get("description")),
        "stack": _clean_stack(record.get("stack")),
        "budget": _clean_text(record.get("budget")),
        "location": _clean_text(record.get("location")),
        "posted_at": _clean_text(record.get("posted_at")),
        "raw": dict(record),
    }


def matches_text(record, term):
    """在标题、描述、技术栈上做小写包含匹配。"""
    needle = term.lower()
    haystack = " ".join(
        [record.get("title", ""), record.get("description", ""), " ".join(record.get("stack", []))]
    ).lower()
    return needle in haystack
