"""
A placeholder for a machine learning based trading strategy.

This class illustrates where you would integrate a supervised model.  For
example, you could train a classifier to predict the direction of the next
price move or a regression model to forecast returns.  The strategy uses
historical features extracted from ``data`` and maintains an internal
pipeline consisting of a scaler and estimator.  Retraining and cross
validation logic should be implemented outside of this class.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler


class MLStrategy:
    """Machine learning based strategy skeleton."""

    def __init__(self, model: BaseEstimator, feature_window: int = 10) -> None:
        self.model = model
        self.feature_window = feature_window
        self.scaler = StandardScaler()

    def _extract_features(self, data: pd.DataFrame, index: int) -> np.ndarray:
        """Extract feature vector from the past ``feature_window`` bars."""
        start = max(0, index - self.feature_window)
        window = data.iloc[start:index]
        # Simple features: returns and rolling statistics
        returns = window["close"].pct_change().dropna().values
        features = []
        if len(returns) > 0:
            features.append(np.mean(returns))
            features.append(np.std(returns))
        else:
            features.extend([0.0, 0.0])
        return np.array(features).reshape(1, -1)

    def generate_signal(self, data: pd.DataFrame, index: int) -> str:
        """Generate a signal using the trained model."""
        if index < self.feature_window:
            return "hold"
        X = self._extract_features(data, index)
        # Scale features based on the training set
        X_scaled = self.scaler.transform(X) if hasattr(self.scaler, "mean_") else X
        try:
            pred = self.model.predict(X_scaled)[0]
        except Exception:
            return "hold"
        # Map prediction to trading signal; assumes classifier outputs -1, 0 or 1
        if pred > 0:
            return "buy"
        elif pred < 0:
            return "sell"
        return "hold"
