"""声明式画像硬过滤。

在交给评分模型之前，先用确定性规则剔除明显不匹配的记录：
排除词优先，其次技术栈、关键词匹配。规则全部可读、可审计，
不依赖外部模型。
"""

from .models import matches_text


def evaluate(record, profile):
    """判断单条记录是否保留。

    Args:
        record: 标准化后的记录 dict。
        profile: 画像 dict，可选键：
            - stack_any: 技术栈任一命中即通过（OR）；空列表不限制。
            - exclude_terms: 命中任一即剔除。
            - keywords_any: 标题/描述任一命中即通过；空列表不限制。

    Returns:
        (keep: bool, reason: str)。
    """
    exclude_terms = profile.get("exclude_terms", [])
    for term in exclude_terms:
        if matches_text(record, term):
            return False, f"命中排除词：{term}"

    stack_any = profile.get("stack_any", [])
    if stack_any:
        stacks = {s.lower() for s in record.get("stack", [])}
        if not any(any(needle in s for s in stacks) for needle in stack_any):
            # 栈字段为空时，再退回标题/描述文本兜底匹配。
            if not any(matches_text(record, needle) for needle in stack_any):
                return False, "技术栈不匹配"

    keywords_any = profile.get("keywords_any", [])
    if keywords_any:
        if not any(matches_text(record, needle) for needle in keywords_any):
            return False, "关键词不匹配"

    return True, "通过硬过滤"


def apply_filter(records, profile):
    """批量过滤。

    Returns:
        dict：kept（保留记录）、dropped（剔除记录）、
        reasons（url -> 剔除原因）。
    """
    kept, dropped, reasons = [], [], {}
    for record in records:
        keep, reason = evaluate(record, profile)
        if keep:
            kept.append(record)
        else:
            dropped.append(record)
            reasons[record.get("url", record.get("title", ""))] = reason
    return {"kept": kept, "dropped": dropped, "reasons": reasons}
