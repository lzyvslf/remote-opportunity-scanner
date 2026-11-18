"""流水线编排：采集 -> 标准化 -> 硬过滤 -> 评分决策 -> 去重入库 -> 清单。

流水线本身不直接发起网络请求：数据源记录由调用方通过 sources 模块
拉取后传入，便于离线测试与逐源隔离。整条链路只产出清单，不执行
任何自动私信、发信或投递动作。
"""

from . import filter as filter_mod
from . import score as score_mod
from .models import normalize
from .store import Store


def run(sources, profile, db_path=":memory:", thresholds=None):
    """跑完整流水线。

    Args:
        sources: list[dict]，每项形如 {"name": "remotive", "records": [...]}。
        profile: 画像 dict，传给 filter 与 score。
        db_path: SQLite 路径，默认内存库。
        thresholds: 可选决策阈值覆盖。

    Returns:
        dict：summary 统计、new_items 本次新入库记录、store 实例。
    """
    raw_records = []
    source_errors = []
    for source in sources:
        for record in source.get("records", []):
            raw_records.append(normalize(record, source=source.get("name", "")))

    filtered = filter_mod.apply_filter(raw_records, profile)

    scored_items = []
    for record in filtered["kept"]:
        result = score_mod.evaluate(record, profile, thresholds)
        scored_items.append({"record": record, **result})

    store = Store(db_path)
    new_items = []
    for item in scored_items:
        is_new = store.upsert(
            item["record"],
            score=item["score"],
            decision=item["decision"],
            reason="；".join(item["reasons"]),
        )
        if is_new:
            new_items.append(item)

    decisions = {}
    for item in scored_items:
        decisions[item["decision"]] = decisions.get(item["decision"], 0) + 1

    summary = {
        "fetched": len(raw_records),
        "kept": len(filtered["kept"]),
        "dropped": len(filtered["dropped"]),
        "new_count": len(new_items),
        "decisions": decisions,
        "source_errors": source_errors,
    }
    return {"summary": summary, "new_items": new_items, "store": store}
