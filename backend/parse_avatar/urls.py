# parse_avatar/urls.py

from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    # Авторизация Skyeng
    path('login/', views.SkyengLoginView.as_view(), name='skyeng_login'),
    path('status/', views.SkyengAuthStatusView.as_view(), name='skyeng_status'),
    path('logout/', views.SkyengLogoutView.as_view(), name='skyeng_logout'),

    # Данные
    path('lessons/', views.SkyengLessonsView.as_view(), name='skyeng_lessons'),
    path('activities/', views.SkyengActivitiesView.as_view(), name='skyeng_activities'),
    path('all-subjects/', views.SkyengAllSubjectsView.as_view(), name='skyeng_all_subjects'),
    
    # Детальная информация по предмету
    path('subjects/<str:subject_key>/', views.SkyengSubjectsDetailView.as_view(), name='skyeng_subject_detail'),
]

