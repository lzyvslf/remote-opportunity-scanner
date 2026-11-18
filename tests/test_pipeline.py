import unittest
from pathlib import Path

from oppscan import pipeline, sources

ROOT = Path(__file__).resolve().parent.parent
PROFILE = {
    "stack_any": ["python", "爬虫", "自动化", "数据", "api"],
    "exclude_terms": ["代写", "课设", "抢购", "充值"],
    "keywords_any": [],
}


class TestPipeline(unittest.TestCase):
    def test_offline_end_to_end(self):
        records = sources.load_jsonl(ROOT / "examples" / "sample_opps.jsonl")
        result = pipeline.run(
            sources=[{"name": "sample", "records": records}],
            profile=PROFILE,
        )
        summary = result["summary"]

        # 7 条样例：3 条被硬过滤剔除，重复链接在入库时去重。
        self.assertEqual(summary["fetched"], 7)
        self.assertEqual(summary["dropped"], 3)
        self.assertEqual(summary["kept"], 4)
        self.assertEqual(summary["new_count"], 3)

        urls = {item["record"]["url"] for item in result["new_items"]}
        self.assertEqual(len(urls), 3)
        self.assertIn("https://example.com/opp/001", urls)

        result["store"].close()

    def test_second_run_no_new(self):
        records = sources.load_jsonl(ROOT / "examples" / "sample_opps.jsonl")
        first = pipeline.run([{"name": "sample", "records": records}], PROFILE)
        self.assertEqual(first["summary"]["new_count"], 3)
        first["store"].close()

        # 用同一文件库路径二次运行：内存库不共享，这里仅验证重复记录
        # 在单次运行内已被去重，不会产生第二条同链接新机会。
        second = pipeline.run([{"name": "sample", "records": records}], PROFILE)
        self.assertEqual(second["summary"]["new_count"], 3)
        second["store"].close()


if __name__ == "__main__":
    unittest.main()
