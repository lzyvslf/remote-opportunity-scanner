import unittest
from datetime import date, timedelta

from oppscan import models, score


def record(**kwargs):
    base = {"title": "", "url": "", "description": "", "stack": []}
    base.update(kwargs)
    return models.normalize(base)


class TestScore(unittest.TestCase):
    def setUp(self):
        self.profile = {"stack_any": ["python", "自动化"], "keywords_any": ["报表"]}

    def test_high_score_decides_apply(self):
        rec = record(
            title="Python 自动化报表",
            stack=["python", "自动化"],
            posted_at=(date.today() - timedelta(days=2)).isoformat(),
            budget="面议",
        )
        result = score.evaluate(rec, self.profile)
        self.assertGreaterEqual(result["score"], 6)
        self.assertEqual(result["decision"], "apply")
        self.assertTrue(result["reasons"])

    def test_low_score_decides_skip(self):
        rec = record(title="其他", description="无关内容")
        result = score.evaluate(rec, self.profile)
        self.assertEqual(result["decision"], "skip")
        self.assertEqual(result["score"], 0)

    def test_missing_date_is_neutral(self):
        rec = record(title="Python 脚本", stack=["python"])
        result = score.evaluate(rec, self.profile)
        self.assertNotIn("发布时间较新", result["reasons"])

    def test_llm_score_stub_returns_none(self):
        rec = record(title="x")
        self.assertIsNone(score.llm_score(rec, self.profile))


if __name__ == "__main__":
    unittest.main()
