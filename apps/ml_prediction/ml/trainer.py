"""
ML Model Trainer
Generates synthetic historical delay data and trains a Random Forest Regressor
to predict train delays based on operational features.
"""

import os
import logging
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class DelayModelTrainer:
    """
    Trains a Random Forest Regressor for train delay prediction.

    Features used:
        - train_type_encoded: Encoded train category (0-8)
        - day_of_week: 0=Monday … 6=Sunday
        - hour_of_day: 0–23
        - weather_code: 0=Clear, 1=Light Rain, 2=Heavy Rain, 3=Fog, 4=Extreme
        - traffic_density: 0.0–1.0
        - historical_avg_delay: Historical average delay for this train (minutes)
        - section_congestion: Current section congestion level 0.0–1.0
        - is_peak_hour: 1=peak, 0=off-peak
        - scheduled_distance: Journey distance (km)

    Target:
        - actual_delay_minutes: Actual delay incurred (minutes)
    """

    FEATURE_NAMES = [
        'train_type_encoded',
        'day_of_week',
        'hour_of_day',
        'weather_code',
        'traffic_density',
        'historical_avg_delay',
        'section_congestion',
        'is_peak_hour',
        'scheduled_distance',
    ]

    MODEL_VERSION = 'v1.0'

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, 'delay_model.pkl')
        os.makedirs(model_dir, exist_ok=True)

    def generate_training_data(self, n_samples: int = 5000) -> pd.DataFrame:
        """Generate realistic synthetic training data."""
        np.random.seed(42)
        logger.info(f"Generating {n_samples} synthetic training samples...")

        # Type encoding: 0=Freight, 1=Passenger, 2=Mail, 3=Express, 4=Special,
        #                5=Duronto, 6=Shatabdi, 7=Rajdhani, 8=VandeBharat
        train_type = np.random.randint(0, 9, n_samples)
        day_of_week = np.random.randint(0, 7, n_samples)
        hour_of_day = np.random.randint(4, 24, n_samples)
        weather_code = np.random.choice([0, 1, 2, 3, 4], n_samples,
                                        p=[0.55, 0.20, 0.10, 0.10, 0.05])
        traffic_density = np.random.beta(2, 3, n_samples)
        historical_avg_delay = np.abs(np.random.normal(15, 10, n_samples))
        section_congestion = np.random.beta(2, 4, n_samples)
        is_peak_hour = ((hour_of_day >= 7) & (hour_of_day <= 10) |
                        (hour_of_day >= 17) & (hour_of_day <= 20)).astype(int)
        scheduled_distance = np.random.uniform(50, 2000, n_samples)

        # Build delay based on feature interactions
        base_delay = np.zeros(n_samples)

        # Train type effect: freight/passenger has higher base delay
        type_delay = np.array([8, 6, 5, 3, 4, 2, 2, 1, 0])[train_type]
        base_delay += type_delay

        # Weather effect
        weather_delay = np.array([0, 5, 15, 20, 35])[weather_code]
        base_delay += weather_delay

        # Traffic density non-linear effect
        base_delay += traffic_density ** 1.5 * 40

        # Historical pattern
        base_delay += historical_avg_delay * 0.4

        # Section congestion
        base_delay += section_congestion * 25

        # Peak hour adds delay
        base_delay += is_peak_hour * 8

        # Distance effect (longer journey = more accumulated delay)
        base_delay += np.log1p(scheduled_distance) * 1.5

        # Day of week: Friday and Sunday have more delays
        day_factor = np.array([1.0, 1.0, 1.0, 1.1, 1.3, 1.0, 1.2])[day_of_week]
        base_delay *= day_factor

        # Add realistic noise
        noise = np.random.exponential(scale=5, size=n_samples)
        actual_delay = np.maximum(0, base_delay + noise - 5)  # Can be on-time (0)

        df = pd.DataFrame({
            'train_type_encoded': train_type,
            'day_of_week': day_of_week,
            'hour_of_day': hour_of_day,
            'weather_code': weather_code,
            'traffic_density': traffic_density.round(4),
            'historical_avg_delay': historical_avg_delay.round(2),
            'section_congestion': section_congestion.round(4),
            'is_peak_hour': is_peak_hour,
            'scheduled_distance': scheduled_distance.round(1),
            'actual_delay_minutes': actual_delay.round(2),
        })

        logger.info(f"Generated data: mean delay={df['actual_delay_minutes'].mean():.1f} min, "
                    f"std={df['actual_delay_minutes'].std():.1f}")
        return df

    def train(self, df: pd.DataFrame = None) -> dict:
        """Train the Random Forest model and save it."""
        if df is None:
            df = self.generate_training_data()

        X = df[self.FEATURE_NAMES].values
        y = df['actual_delay_minutes'].values

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Build pipeline: scaler + Random Forest
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('rf', RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1,
            ))
        ])

        logger.info("Training Random Forest Regressor...")
        pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = pipeline.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = mean_squared_error(y_test, y_pred) ** 0.5
        r2 = r2_score(y_test, y_pred)

        # Cross-validation
        cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='r2')
        cv_mean = cv_scores.mean()

        metrics = {
            'r2_score': round(r2, 4),
            'mean_absolute_error': round(mae, 3),
            'root_mean_squared_error': round(rmse, 3),
            'cross_val_score': round(cv_mean, 4),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
        }

        logger.info(f"Model trained: R²={r2:.4f}, MAE={mae:.2f} min, RMSE={rmse:.2f} min")

        # Feature importances
        importances = pipeline.named_steps['rf'].feature_importances_
        fi = dict(zip(self.FEATURE_NAMES, importances.round(4)))
        logger.info(f"Feature importances: {fi}")

        # Save model with metadata
        model_data = {
            'pipeline': pipeline,
            'version': self.MODEL_VERSION,
            'feature_names': self.FEATURE_NAMES,
            'metrics': metrics,
            'feature_importances': fi,
            'trained_at': datetime.now().isoformat(),
        }

        joblib.dump(model_data, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

        # Persist metadata to DB
        self._save_metadata(metrics, fi)

        return {**metrics, 'feature_importances': fi, 'model_path': self.model_path}

    def _save_metadata(self, metrics: dict, feature_importances: dict):
        """Save model metadata to database."""
        try:
            from apps.ml_prediction.models import MLModelMetadata
            MLModelMetadata.objects.filter(is_active=True).update(is_active=False)
            MLModelMetadata.objects.create(
                version=self.MODEL_VERSION,
                algorithm='Random Forest Regressor',
                training_samples=metrics['training_samples'],
                features_count=len(self.FEATURE_NAMES),
                r2_score=metrics['r2_score'],
                mean_absolute_error=metrics['mean_absolute_error'],
                root_mean_squared_error=metrics['root_mean_squared_error'],
                cross_val_score=metrics['cross_val_score'],
                is_active=True,
                model_file_path=self.model_path,
                hyperparameters={
                    'n_estimators': 200,
                    'max_depth': 12,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'max_features': 'sqrt',
                    'feature_importances': feature_importances,
                },
            )
        except Exception as e:
            logger.warning(f"Could not save ML metadata to DB: {e}")

    def save_training_csv(self):
        """Save generated dataset to CSV for inspection."""
        df = self.generate_training_data(2000)
        csv_path = os.path.join(self.model_dir, 'training_data.csv')
        df.to_csv(csv_path, index=False)
        logger.info(f"Training CSV saved: {csv_path}")
        return csv_path
