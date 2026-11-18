"""规则评分与确定性决策。

评分全部由本地规则给出，可复现、可审计；最终 apply / review / skip
分类由固定阈值决定。预留 LLM 评分接口，但默认不调用任何外部模型，
无 API key 时规则评分即可独立工作。
"""

from datetime import date, datetime

from .models import matches_text

DEFAULT_THRESHOLDS = {"apply": 6, "review": 3}


def _freshness_bonus(posted_at):
    """按发布日期给新鲜度加分；日期缺失或无法解析时记 0。"""
    if not posted_at:
        return 0
    try:
        posted = datetime.fromisoformat(posted_at[:10]).date()
    except ValueError:
        return 0
    days = (date.today() - posted).days
    if days <= 7:
        return 2
    if days <= 30:
        return 1
    return 0


def score_record(record, profile):
    """对单条记录做规则评分。

    Returns:
        dict：score（0-10 分制）、decision、reasons（可读理由列表）。
    """
    reasons = []
    score = 0

    for needle in profile.get("stack_any", []):
        if matches_text(record, needle):
            score += 2
            reasons.append(f"匹配技术栈：{needle}")

    for needle in profile.get("keywords_any", []):
        if matches_text(record, needle):
            score += 1
            reasons.append(f"命中关键词：{needle}")

    fresh = _freshness_bonus(record.get("posted_at", ""))
    if fresh:
        score += fresh
        reasons.append("发布时间较新")

    if record.get("budget"):
        score += 1
        reasons.append("标注了预算/报酬")

    return {"score": min(score, 10), "reasons": reasons}


def llm_score(record, profile):
    """预留的 LLM 评分接口。

    默认返回 None：当前版本不调用外部模型。后续如需接入，可在此
    返回补充分数与理由，但最终决策仍由本地阈值做确定性判断。
    """
    return None


def decide(score, thresholds=None):
    """按阈值给出确定性决策。"""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    if score >= thresholds["apply"]:
        return "apply"
    if score >= thresholds["review"]:
        return "review"
    return "skip"


def evaluate(record, profile, thresholds=None):
    """评分并决策的组合入口。"""
    scored = score_record(record, profile)
    decision = decide(scored["score"], thresholds)
    return {
        "score": scored["score"],
        "decision": decision,
        "reasons": scored["reasons"],
    }
