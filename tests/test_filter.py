import unittest

from oppscan import filter, models

PROFILE = {
    "stack_any": ["python", "自动化", "爬虫"],
    "exclude_terms": ["代写", "课设"],
    "keywords_any": [],
}


def record(**kwargs):
    base = {"title": "", "url": "", "description": "", "stack": []}
    base.update(kwargs)
    return models.normalize(base)


class TestFilter(unittest.TestCase):
    def test_stack_match_kept(self):
        rec = record(title="Python 流水线", stack=["python", "etl"])
        keep, reason = filter.evaluate(rec, PROFILE)
        self.assertTrue(keep)
        self.assertEqual(reason, "通过硬过滤")

    def test_exclude_term_dropped(self):
        rec = record(title="Python 课设代做", stack=["python"])
        keep, reason = filter.evaluate(rec, PROFILE)
        self.assertFalse(keep)
        self.assertIn("排除词", reason)

    def test_stack_mismatch_dropped(self):
        rec = record(title="React 改版", stack=["react", "css"])
        keep, reason = filter.evaluate(rec, PROFILE)
        self.assertFalse(keep)
        self.assertEqual(reason, "技术栈不匹配")

    def test_apply_filter_batches(self):
        records = [
            record(title="Python 自动化", stack=["python"]),
            record(title="前端页面", stack=["vue"]),
        ]
        result = filter.apply_filter(records, PROFILE)
        self.assertEqual(len(result["kept"]), 1)
        self.assertEqual(len(result["dropped"]), 1)
        self.assertIn(result["dropped"][0]["url"], result["reasons"])


if __name__ == "__main__":
    unittest.main()
