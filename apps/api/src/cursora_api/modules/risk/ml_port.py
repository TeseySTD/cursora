"""Port for optional ML scoring. Implementations live outside the pure evaluator."""

from typing import Protocol

from cursora_features import FeatureVector


class MlScorer(Protocol):
    """Scores a feature vector with a trained model.

    TODO(team): score range/semantics and model loading strategy.
    """

    def score(self, features: FeatureVector) -> float: ...
