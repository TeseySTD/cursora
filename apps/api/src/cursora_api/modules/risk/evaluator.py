"""RiskEvaluator: the core of the Risk Engine."""

from dataclasses import dataclass
from enum import StrEnum

from cursora_features import FeatureVector


class Decision(StrEnum):
    ALLOW = "allow"
    CHALLENGE = "challenge"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class RiskResult:
    score: float
    decision: Decision


class RiskEvaluator:
    """Pure risk evaluation: features (+ optional ML score) -> score -> decision.

    PURE: no I/O, no database, no network, no clock, no randomness. The same
    inputs always give the same result, so the evaluator is trivially unit-
    testable and replayable. Anything that needs I/O (loading site settings,
    calling an ML model) happens in the service layer *before* calling it.

    ``ml_score`` is optional: the engine must produce a decision without ML.
    """

    def evaluate(
        self,
        features: FeatureVector,
        *,
        sensitivity: int,
        ml_score: float | None = None,
    ) -> RiskResult:
        """TODO(team): rules, weights, score range and decision thresholds."""
        raise NotImplementedError
