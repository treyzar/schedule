from django.urls import path
from .views import HealthCheckView, DetailedHealthCheckView

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health_check'),
    path('detailed/', DetailedHealthCheckView.as_view(), name='health_detailed'),
]
