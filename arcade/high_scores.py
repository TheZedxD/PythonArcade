import os
import sqlite3
from typing import List, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), 'high_scores.db')


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS scores (game TEXT, name TEXT, score INTEGER)'
    )
    return conn


def save_score(game: str, name: str, score: int) -> None:
    """Save a high score entry."""
    conn = _get_conn()
    with conn:
        conn.execute(
            'INSERT INTO scores (game, name, score) VALUES (?, ?, ?)',
            (game, name, score),
        )
    conn.close()


def get_high_scores(game: str, limit: int = 5) -> List[Tuple[str, int]]:
    """Return top *limit* scores for *game*."""
    conn = _get_conn()
    cur = conn.execute(
        'SELECT name, score FROM scores WHERE game = ? ORDER BY score DESC LIMIT ?',
        (game, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [(name, int(score)) for name, score in rows]
