# parse_avatar/urls.py

from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('login/', views.SkyengLoginView.as_view(), name='skyeng_login'),
    path('all-subjects/', views.SkyengAllSubjectsView.as_view(), name='skyeng_all_subjects'),
]

