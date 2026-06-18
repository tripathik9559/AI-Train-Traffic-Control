"""
ML Prediction Views — Delay Prediction Dashboard
"""

import json
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils import timezone

from apps.trains.models import Train
from .models import DelayPrediction, MLModelMetadata
from .ml.predictor import DelayPredictor
from .ml.trainer import DelayModelTrainer

logger = logging.getLogger(__name__)


def get_predictor():
    return DelayPredictor(model_path=str(settings.ML_MODEL_PATH))


@never_cache
@login_required
def prediction_dashboard(request):
    """ML Prediction main dashboard."""
    predictor = get_predictor()
    model_info = predictor.get_model_info()

    recent_predictions = DelayPrediction.objects.select_related('train').order_by('-predicted_at')[:20]

    trains = Train.objects.filter(
        is_active=True,
        current_status__in=['SCHEDULED', 'RUNNING', 'DELAYED']
    ).select_related('source_station', 'destination_station')

    # Risk summary
    today = timezone.now().date()
    today_preds = DelayPrediction.objects.filter(scheduled_date=today)
    risk_summary = {
        'LOW': today_preds.filter(risk_level='LOW').count(),
        'MEDIUM': today_preds.filter(risk_level='MEDIUM').count(),
        'HIGH': today_preds.filter(risk_level='HIGH').count(),
        'CRITICAL': today_preds.filter(risk_level='CRITICAL').count(),
    }

    context = {
        'model_info': model_info,
        'recent_predictions': recent_predictions,
        'trains': trains,
        'risk_summary': risk_summary,
        'page_title': 'ML Delay Prediction',
        'active_nav': 'ml_prediction',
        'weather_options': DelayPredictor.WEATHER_LABELS,
    }
    return render(request, 'ml_prediction/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def predict_delay(request):
    """Handle prediction form submission (AJAX or form)."""
    predictor = get_predictor()

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        data = request.POST.dict()

    train_id = data.get('train_id')
    train = None
    if train_id:
        try:
            train = Train.objects.get(id=int(train_id))
        except Train.DoesNotExist:
            pass

    features = {
        'train_type_encoded': int(data.get('train_type_encoded', 3)),
        'day_of_week': int(data.get('day_of_week', timezone.now().weekday())),
        'hour_of_day': int(data.get('hour_of_day', timezone.now().hour)),
        'weather_code': int(data.get('weather_code', 0)),
        'traffic_density': float(data.get('traffic_density', 0.5)),
        'historical_avg_delay': float(data.get('historical_avg_delay', 15.0)),
        'section_congestion': float(data.get('section_congestion', 0.3)),
        'is_peak_hour': int(data.get('is_peak_hour', 0)),
        'scheduled_distance': float(data.get('scheduled_distance', 300.0)),
    }

    result = predictor.predict(features)

    # Persist prediction
    pred = DelayPrediction.objects.create(
        train=train,
        train_type_encoded=features['train_type_encoded'],
        day_of_week=features['day_of_week'],
        hour_of_day=features['hour_of_day'],
        weather_code=features['weather_code'],
        traffic_density=features['traffic_density'],
        historical_avg_delay=features['historical_avg_delay'],
        section_congestion=features['section_congestion'],
        is_peak_hour=bool(features['is_peak_hour']),
        scheduled_distance=features['scheduled_distance'],
        predicted_delay_minutes=result['predicted_delay_minutes'],
        risk_level=result['risk_level'],
        confidence_score=result['confidence_score'],
        model_version=result['model_version'],
        scheduled_date=timezone.now().date(),
    )

    return JsonResponse({
        'success': True,
        'prediction_id': pred.id,
        'train_number': train.train_number if train else 'Custom',
        'predicted_delay_minutes': result['predicted_delay_minutes'],
        'risk_level': result['risk_level'],
        'risk_color': pred.risk_color,
        'risk_icon': pred.risk_icon,
        'confidence_pct': result['confidence_pct'],
        'breakdown': result['breakdown'],
        'model_version': result['model_version'],
    })


@login_required
def train_model(request):
    """Admin: Trigger model retraining."""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Admin only'}, status=403)

    if request.method == 'POST':
        trainer = DelayModelTrainer(model_dir=str(settings.ML_MODELS_DIR))
        try:
            metrics = trainer.train()
            # Reload predictor
            DelayPredictor._model_data = None
            get_predictor()
            return JsonResponse({'success': True, 'metrics': metrics})
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def model_info_api(request):
    """API: Return model metadata."""
    predictor = get_predictor()
    info = predictor.get_model_info()

    try:
        meta = MLModelMetadata.objects.filter(is_active=True).first()
        if meta:
            info['db_metadata'] = {
                'training_samples': meta.training_samples,
                'r2_score': meta.r2_score,
                'mae': meta.mean_absolute_error,
                'rmse': meta.root_mean_squared_error,
                'cv_score': meta.cross_val_score,
                'hyperparameters': meta.hyperparameters,
            }
    except Exception:
        pass

    return JsonResponse(info)


@login_required
def predict_for_train(request, train_id):
    """Quick prediction for a specific train using current conditions."""
    train = get_object_or_404(Train, id=train_id)
    predictor = get_predictor()
    result = predictor.predict_for_train(train, date=timezone.now())

    return JsonResponse({
        'train_number': train.train_number,
        'train_name': train.train_name,
        'predicted_delay_minutes': result['predicted_delay_minutes'],
        'risk_level': result['risk_level'],
        'confidence_pct': result['confidence_pct'],
        'model_version': result['model_version'],
    })
