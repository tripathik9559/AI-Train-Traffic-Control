from django.urls import path
from . import views

app_name = 'ml_prediction'

urlpatterns = [
    path('', views.prediction_dashboard, name='dashboard'),
    path('predict/', views.predict_delay, name='predict'),
    path('train-model/', views.train_model, name='train_model'),
    path('train/<int:train_id>/', views.predict_for_train, name='predict_for_train'),
]
