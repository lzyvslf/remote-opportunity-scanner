import unittest

from oppscan import models, store


def record(url, title="示例"):
    return models.normalize({"title": title, "url": url, "description": ""})


class TestStore(unittest.TestCase):
    def setUp(self):
        self.db = store.Store(":memory:")

    def tearDown(self):
        self.db.close()

    def test_first_upsert_is_new(self):
        is_new = self.db.upsert(record("https://example.com/a"), score=7, decision="apply", reason="匹配")
        self.assertTrue(is_new)

    def test_repeat_upsert_not_new(self):
        self.db.upsert(record("https://example.com/a"), score=7, decision="apply", reason="一")
        is_new = self.db.upsert(record("https://example.com/a"), score=8, decision="review", reason="二")
        self.assertFalse(is_new)
        rows = self.db.recent()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["score"], 8)

    def test_mark_status(self):
        self.db.upsert(record("https://example.com/b"), score=5, decision="review", reason="")
        self.db.mark_status("https://example.com/b", "applied")
        rows = self.db.recent()
        self.assertEqual(rows[0]["status"], "applied")

    def test_recent_filter_by_decision(self):
        self.db.upsert(record("https://example.com/c1"), score=8, decision="apply", reason="")
        self.db.upsert(record("https://example.com/c2"), score=2, decision="skip", reason="")
        apply_rows = self.db.recent(decision="apply")
        self.assertEqual(len(apply_rows), 1)
        self.assertEqual(apply_rows[0]["url"], "https://example.com/c1")


if __name__ == "__main__":
    unittest.main()
