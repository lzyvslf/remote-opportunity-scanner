"""公开数据源适配。

只读取公开可访问的 JSON API 与本地离线样例；不登录任何账号，
不抓取社交平台页面，不采集私人联系方式。网络请求使用标准库
urllib，失败时抛出 SourceError，由流水线逐源隔离处理。
"""

import json
import urllib.request


class SourceError(RuntimeError):
    """数据源拉取或解析失败。"""


def _dig(data, dotted_key):
    """按点号路径取嵌套字段，如 "data.jobs"。"""
    if not dotted_key:
        return data
    current = data
    for part in dotted_key.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def fetch_json(api_url, list_key=None, field_map=None, timeout=10):
    """从公开 JSON API 拉取记录列表。

    Args:
        api_url: 公开可访问的 JSON 地址。
        list_key: 可选；列表所在的点号路径，如 "data.jobs"。
        field_map: 可选；标准字段 -> 源字段名的映射，未列出的字段
            按同名直接取。
        timeout: 网络超时秒数。

    Returns:
        list[dict]，原始记录（尚未标准化）。

    Raises:
        SourceError: 网络失败、非 JSON 或结构不符合预期。
    """
    try:
        with urllib.request.urlopen(api_url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - 统一包装为 SourceError
        raise SourceError(f"拉取失败 {api_url}: {exc}") from exc

    items = _dig(payload, list_key)
    if items is None:
        raise SourceError(f"未在 {list_key} 路径下找到列表: {api_url}")
    if not isinstance(items, list):
        raise SourceError(f"列表路径返回的不是数组: {api_url}")

    field_map = field_map or {}
    records = []
    for item in items:
        if not isinstance(item, dict):
            continue
        record = {}
        for std_field, src_field in field_map.items():
            record[std_field] = item.get(src_field)
        # 未在映射中的字段按同名补齐，便于保留原始信息。
        for key, value in item.items():
            record.setdefault(key, value)
        records.append(record)
    return records


def load_jsonl(path):
    """读取本地 JSONL 样例文件，每行一条记录。"""
    records = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
    except FileNotFoundError as exc:
        raise SourceError(f"样例文件不存在: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceError(f"JSONL 解析失败 {path}: {exc}") from exc
    return records
