import pytest

import cursora_features
from cursora_features import extract_features


def test_public_api_is_exported() -> None:
    assert cursora_features.__all__ == ["FeatureVector", "extract_features"]


def test_extract_features_is_a_placeholder() -> None:
    with pytest.raises(NotImplementedError):
        extract_features({})
