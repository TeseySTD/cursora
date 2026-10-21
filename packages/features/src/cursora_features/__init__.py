"""Shared feature extraction for Cursora.

Pure Python: no web framework, database or ML-library dependencies.
"""

from cursora_features.extract import FeatureVector, extract_features

__all__ = ["FeatureVector", "extract_features"]
