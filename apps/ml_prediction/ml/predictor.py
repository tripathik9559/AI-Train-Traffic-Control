"""
ML Delay Predictor
Loads the trained model and provides predictions with risk classification.
"""

import os
import logging
import numpy as np
import joblib
from functools import lru_cache

logger = logging.getLogger(__name__)


class DelayPredictor:
    """Wraps the trained Random Forest pipeline for inference."""

    RISK_THRESHOLDS = {
        'LOW': (0, 10),
        'MEDIUM': (10, 30),
        'HIGH': (30, 60),
        'CRITICAL': (60, float('inf')),
    }

    WEATHER_LABELS = {
        0: 'Clear',
        1: 'Light Rain',
        2: 'Heavy Rain',
        3: 'Dense Fog',
        4: 'Extreme Weather',
    }

    TRAIN_TYPE_ENCODING = {
        'FREIGHT': 0,
        'PASSENGER': 1,
        'MAIL': 2,
        'EXPRESS': 3,
        'SPECIAL': 4,
        'DURONTO': 5,
        'SHATABDI': 6,
        'RAJDHANI': 7,
        'VANDE_BHARAT': 8,
    }

    _instance = None
    _model_data = None

    def __new__(cls, model_path: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_path: str):
        self.model_path = model_path
        if self._model_data is None:
            self._load_model()

    def _load_model(self):
        """Load the trained model from disk."""
        if os.path.exists(self.model_path):
            try:
                self.__class__._model_data = joblib.load(self.model_path)
                logger.info(f"ML model loaded: version {self._model_data.get('version')}")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                self.__class__._model_data = None
        else:
            logger.warning(f"ML model not found at {self.model_path}. Run training first.")

    @property
    def is_ready(self):
        return self._model_data is not None and 'pipeline' in self._model_data

    def predict(self, features: dict) -> dict:
        """
        Make a single delay prediction.

        Args:
            features: dict with keys matching FEATURE_NAMES

        Returns:
            dict with prediction, risk_level, confidence, breakdown
        """
        if not self.is_ready:
            return self._fallback_prediction(features)

        try:
            pipeline = self._model_data['pipeline']
            feature_names = self._model_data['feature_names']

            X = np.array([[features.get(f, 0) for f in feature_names]])
            predicted_delay = max(0.0, float(pipeline.predict(X)[0]))

            # Estimate confidence based on feature values
            confidence = self._estimate_confidence(features, predicted_delay)

            risk_level = self._classify_risk(predicted_delay)

            # Breakdown explanation
            fi = self._model_data.get('feature_importances', {})
            breakdown = self._build_breakdown(features, fi, predicted_delay)

            return {
                'predicted_delay_minutes': round(predicted_delay, 1),
                'risk_level': risk_level,
                'confidence_score': round(confidence, 3),
                'confidence_pct': round(confidence * 100, 1),
                'breakdown': breakdown,
                'model_version': self._model_data.get('version', 'v1.0'),
                'success': True,
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._fallback_prediction(features)

    def predict_for_train(self, train, date=None) -> dict:
        """Convenience method: predict delay for a Train object."""
        import random
        from datetime import date as date_type

        if date is None:
            from django.utils import timezone
            date = timezone.now()

        day_of_week = date.weekday() if hasattr(date, 'weekday') else 0
        hour = date.hour if hasattr(date, 'hour') else 12

        features = {
            'train_type_encoded': self.TRAIN_TYPE_ENCODING.get(train.train_type, 3),
            'day_of_week': day_of_week,
            'hour_of_day': hour,
            'weather_code': random.choice([0, 0, 0, 1, 1, 2, 3]),
            'traffic_density': round(random.uniform(0.2, 0.8), 3),
            'historical_avg_delay': train.current_delay or random.uniform(5, 25),
            'section_congestion': round(random.uniform(0.1, 0.6), 3),
            'is_peak_hour': 1 if (7 <= hour <= 10 or 17 <= hour <= 20) else 0,
            'scheduled_distance': random.uniform(100, 1500),
        }

        return self.predict(features)

    def _classify_risk(self, delay_minutes: float) -> str:
        """Classify predicted delay into risk level."""
        for level, (low, high) in self.RISK_THRESHOLDS.items():
            if low <= delay_minutes < high:
                return level
        return 'CRITICAL'

    def _estimate_confidence(self, features: dict, prediction: float) -> float:
        """Estimate prediction confidence based on input quality."""
        base = 0.82
        # High weather impact reduces confidence
        weather = features.get('weather_code', 0)
        if weather >= 3:
            base -= 0.08
        elif weather >= 2:
            base -= 0.04

        # High traffic density increases uncertainty
        traffic = features.get('traffic_density', 0.5)
        if traffic > 0.8:
            base -= 0.05

        return max(0.60, min(0.97, base))

    def _build_breakdown(self, features: dict, importances: dict, prediction: float) -> list:
        """Build human-readable feature contribution breakdown."""
        breakdown = []

        if importances:
            sorted_fi = sorted(importances.items(), key=lambda x: x[1], reverse=True)
            for feature, importance in sorted_fi[:5]:
                value = features.get(feature, 0)
                contrib = importance * prediction

                label_map = {
                    'train_type_encoded': f"Train Type (code {int(value)})",
                    'day_of_week': f"Day of Week ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][int(value) % 7]})",
                    'hour_of_day': f"Hour ({int(value):02d}:00)",
                    'weather_code': f"Weather ({self.WEATHER_LABELS.get(int(value), 'Unknown')})",
                    'traffic_density': f"Traffic Density ({value:.0%})",
                    'historical_avg_delay': f"Historical Avg Delay ({value:.1f} min)",
                    'section_congestion': f"Section Congestion ({value:.0%})",
                    'is_peak_hour': f"Peak Hour ({'Yes' if value else 'No'})",
                    'scheduled_distance': f"Journey Distance ({value:.0f} km)",
                }

                breakdown.append({
                    'feature': label_map.get(feature, feature),
                    'importance': round(importance * 100, 1),
                    'contribution': round(contrib, 1),
                })

        return breakdown

    def _fallback_prediction(self, features: dict) -> dict:
        """Return a rule-based prediction when model is unavailable."""
        delay = features.get('historical_avg_delay', 15)
        delay += features.get('weather_code', 0) * 8
        delay += features.get('traffic_density', 0.5) * 20
        delay = max(0, delay)

        return {
            'predicted_delay_minutes': round(delay, 1),
            'risk_level': self._classify_risk(delay),
            'confidence_score': 0.55,
            'confidence_pct': 55.0,
            'breakdown': [],
            'model_version': 'rule-based-fallback',
            'success': False,
        }

    def get_model_info(self) -> dict:
        """Return model metadata."""
        if not self.is_ready:
            return {'ready': False, 'message': 'Model not loaded. Run training first.'}

        metrics = self._model_data.get('metrics', {})
        return {
            'ready': True,
            'version': self._model_data.get('version'),
            'trained_at': self._model_data.get('trained_at'),
            'r2_score': metrics.get('r2_score'),
            'mae': metrics.get('mean_absolute_error'),
            'rmse': metrics.get('root_mean_squared_error'),
            'cv_score': metrics.get('cross_val_score'),
            'feature_importances': self._model_data.get('feature_importances', {}),
        }
