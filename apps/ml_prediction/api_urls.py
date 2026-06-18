from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_delay, name='api_predict'),
    path('model-info/', views.model_info_api, name='api_model_info'),
    path('train/<int:train_id>/', views.predict_for_train, name='api_predict_train'),
    path('retrain/', views.train_model, name='api_retrain'),
]
