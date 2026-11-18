"""SQLite 去重与状态存储。

以链接哈希为主键去重：同一来源链接再次出现时只刷新最近可见时间，
不会重复计入新机会。状态字段预留 new / review / applied / skipped，
方便后续人工跟进；本工具不产生任何自动联系动作。
"""

import hashlib
import json
import sqlite3
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    url_hash   TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    source     TEXT,
    title      TEXT,
    score      INTEGER,
    decision   TEXT,
    reason     TEXT,
    status     TEXT DEFAULT 'new',
    first_seen TEXT,
    last_seen  TEXT,
    payload    TEXT
)
"""


def hash_url(url):
    """生成链接哈希，作为去重主键。"""
    return hashlib.sha1((url or "").strip().encode("utf-8")).hexdigest()


class Store:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def upsert(self, record, score, decision, reason):
        """写入或刷新一条记录。

        Returns:
            bool，True 表示本次为首次入库，False 表示已存在。
        """
        url = record.get("url", "")
        url_hash = hash_url(url)
        now = datetime.now().isoformat(timespec="seconds")
        payload = json.dumps(record, ensure_ascii=False)

        existing = self.conn.execute(
            "SELECT url_hash FROM opportunities WHERE url_hash = ?", (url_hash,)
        ).fetchone()

        if existing:
            self.conn.execute(
                """
                UPDATE opportunities
                SET last_seen = ?, score = ?, decision = ?, reason = ?
                WHERE url_hash = ?
                """,
                (now, score, decision, reason, url_hash),
            )
            is_new = False
        else:
            self.conn.execute(
                """
                INSERT INTO opportunities
                    (url_hash, url, source, title, score, decision, reason,
                     status, first_seen, last_seen, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?)
                """,
                (
                    url_hash,
                    url,
                    record.get("source", ""),
                    record.get("title", ""),
                    score,
                    decision,
                    reason,
                    now,
                    now,
                    payload,
                ),
            )
            is_new = True

        self.conn.commit()
        return is_new

    def mark_status(self, url, status):
        """人工跟进后更新状态，如 applied / skipped。"""
        self.conn.execute(
            "UPDATE opportunities SET status = ? WHERE url_hash = ?",
            (status, hash_url(url)),
        )
        self.conn.commit()

    def recent(self, decision=None, limit=50):
        """读取最近记录，可按决策结果过滤。"""
        sql = "SELECT url_hash, url, source, title, score, decision, reason, status, payload FROM opportunities"
        params: list = []
        if decision:
            sql += " WHERE decision = ?"
            params.append(decision)
        sql += " ORDER BY last_seen DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        result = []
        for row in rows:
            (url_hash, url, source, title, score, decision_, reason, status, payload) = row
            record = json.loads(payload) if payload else {}
            result.append(
                {
                    "url_hash": url_hash,
                    "url": url,
                    "source": source,
                    "title": title,
                    "score": score,
                    "decision": decision_,
                    "reason": reason,
                    "status": status,
                    "record": record,
                }
            )
        return result

    def close(self):
        self.conn.close()
