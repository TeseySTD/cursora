import json
from pathlib import Path

from cursora_ml.bot_generator.generate_bot_dataset import (
    BOT_TYPES,
    build_parser,
    generate_dataset,
    main,
)


def _sessions(*extra: str) -> list[dict]:
    args = build_parser().parse_args(["-n", "60", "--seed", "1", *extra])
    return generate_dataset(args)


def test_sessions_have_dataset_format() -> None:
    for s in _sessions():
        assert s["label"] == "bot"
        assert s["botType"] in BOT_TYPES
        assert s["physicsTickCount"] == len(s["tickInputs"]) >= 2
        for tick in s["tickInputs"]:
            assert set(tick) == {"x", "y", "isDown"}
            assert isinstance(tick["isDown"], bool)
            assert 0 <= tick["x"] <= 200
            assert 0 <= tick["y"] <= 200


def test_all_bot_types_are_generated() -> None:
    assert {s["botType"] for s in _sessions()} == set(BOT_TYPES)


def test_same_seed_gives_same_data() -> None:
    assert _sessions() == _sessions()


def test_bot_mix_limits_types() -> None:
    sessions = _sessions("--bot-mix", "linear_bot:1")
    assert {s["botType"] for s in sessions} == {"linear_bot"}


def test_main_writes_jsonl(tmp_path: Path) -> None:
    out = tmp_path / "bots.jsonl"
    main(["-n", "5", "--seed", "3", "-o", str(out)])
    lines = out.read_text().splitlines()
    assert len(lines) == 5
    assert json.loads(lines[0])["label"] == "bot"
