import sys
import pathlib

ARCADE_DIR = pathlib.Path(__file__).resolve().parents[3]
sys.path.append(str(ARCADE_DIR))

from games.wyrm.wyrm import WyrmGame  # type: ignore  # noqa: E402
import high_scores  # type: ignore  # noqa: E402
from main import load_games  # type: ignore  # noqa: E402


def test_segment_split() -> None:
    game = WyrmGame()
    game.handle_segment_hit(0, 5)
    assert len(game.wyrms) == 2
    assert (5, 0) in game.blocks


def test_high_score_insert(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(high_scores, "DB_PATH", str(tmp_path / "scores.db"))
    high_scores.save_score("wyrm", "AAA", 123)
    scores = high_scores.get_high_scores("wyrm")
    assert ("AAA", 123) in scores


def test_menu_registration() -> None:
    games = load_games()
    assert "wyrm" in games
