import importlib


def test_subpackages_import() -> None:
    for name in ("cursora_ml.bot_generator", "cursora_ml.training"):
        importlib.import_module(name)
