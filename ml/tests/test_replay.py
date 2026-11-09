import pytest

# CapyCap comes from a git submodule in the optional `notebook` group: `pnpm test:ml` skips this
# file without it, `pnpm test:ml:replay` (run in CI) installs the group and fails if it is broken.
pytest.importorskip("capycap")

from cursora_ml.replay import GAME_TYPES, STRIDE, render_replay, simulate


def _ticks(count: int) -> list[dict[str, float | bool]]:
    return [{"x": 100.0 + i, "y": 100.0, "isDown": i > 0} for i in range(count)]


@pytest.mark.parametrize("game_type", GAME_TYPES)
def test_simulate_snapshots_every_stride(game_type: str) -> None:
    n_ticks = STRIDE + 1  # the last tick falls on the stride

    data = simulate(game_type, 1, _ticks(n_ticks))

    assert data["game"] == game_type
    assert data["n_ticks"] == n_ticks
    assert len(data["frames"]) == 2


@pytest.mark.parametrize("game_type", GAME_TYPES)
def test_simulate_always_snapshots_the_last_tick(game_type: str) -> None:
    ticks = _ticks(STRIDE + 2)

    frames = simulate(game_type, 1, ticks)["frames"]

    assert len(frames) == 3
    assert frames[-1]["i"][0] == ticks[-1]["x"]


def test_simulate_takes_the_needle_radius_from_the_engine() -> None:
    data = simulate("thread-the-needle", 1, _ticks(1))

    assert data["static"]["r"] == pytest.approx(21.06)


def test_simulate_rejects_an_unknown_game_type() -> None:
    with pytest.raises(ValueError, match="no-such-game"):
        simulate("no-such-game", 1, _ticks(1))


def test_render_replay_fills_the_player() -> None:
    data = simulate("sheep-herding", 1, _ticks(1))

    html = render_replay(data, title="session · 1", window=(0, 1))

    assert "__DATA__" not in html
    assert "session" in html


def test_render_replay_keeps_the_title_inside_the_data_script() -> None:
    data = simulate("sheep-herding", 1, _ticks(1))

    html = render_replay(data, title="</script><img src=x>", window=(0, 1))

    assert "</script><img" not in html
    assert "\\u003c/script>\\u003cimg" in html
