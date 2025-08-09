import sys
import pathlib

ARCADE_DIR = pathlib.Path(__file__).resolve().parents[3]
sys.path.append(str(ARCADE_DIR))

from games.wyrm.wyrm import WyrmGame, MOVE_DELAY  # type: ignore  # noqa: E402
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


def test_two_player_scoring() -> None:
    game = WyrmGame()
    game.handle_segment_hit(0, 0, shooter=1)
    assert game.score1 == 100 and game.score2 == 0
    game = WyrmGame()
    game.handle_segment_hit(0, 0, shooter=2)
    assert game.score2 == 100 and game.score1 == 0


def test_speed_increase() -> None:
    game = WyrmGame()
    game.score1 = 500
    game._update_speed()
    assert game.move_delay < MOVE_DELAY


def test_player_collision() -> None:
    game = WyrmGame()
    game.player1 = list(game.wyrms[0][0])
    game.update(0)
    assert game.lives1 == 2


def test_game_over_highest_score(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(high_scores, "DB_PATH", str(tmp_path / "scores.db"))
    game = WyrmGame()
    game.score1 = 100
    game.score2 = 200
    game.game_over("AAA")
    scores = high_scores.get_high_scores("wyrm")
    assert ("AAA", 200) in scores


def test_menu_registration() -> None:
    games = load_games()
    assert "wyrm" in games
