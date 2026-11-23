"""Signal -> feature vector extraction."""

from collections.abc import Mapping
from typing import Any

type FeatureVector = dict[str, float]


def extract_features(signals: Mapping[str, Any]) -> FeatureVector:
    """Turn raw behavioural signals collected by the widget into a feature vector.

    This is the single source of truth for feature extraction. Both the API
    (online inference in the Risk Engine) and the ML stream (offline training)
    MUST call this function, so that training and serving never drift apart
    (train/serve skew).

    The payload is a stored signal batch, as validated by ``SignalBatchIn`` in the API's
    sessions module (``t`` plus a list of ``move``, ``click`` and ``env`` signals).

    TODO(team): the feature set, and whether features span one batch or a whole session.
    """
    raise NotImplementedError
