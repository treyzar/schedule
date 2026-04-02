# parse_calendar/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # === Авторизация Google ===
    path('authorize/', views.GoogleAuthorizeView.as_view(), name='google_authorize'),
    path('oauth2callback/', views.GoogleCallbackView.as_view(), name='google_callback'),
    path('logout/', views.GoogleLogoutView.as_view(), name='google_logout'),

    # === Авторизация Skyeng ===
    path('skyeng-login/', views.SkyengLoginView.as_view(), name='skyeng_login'),
    path('skyeng-status/', views.SkyengStatusView.as_view(), name='skyeng_status'),
    path('skyeng-logout/', views.SkyengLogoutView.as_view(), name='skyeng_logout'),

    # === Статус авторизации ===
    path('status/', views.GoogleAuthStatusView.as_view(), name='google_auth_status'),

    # === Данные календаря ===
    path('initial-data/', views.GetInitialDataView.as_view(), name='get_initial_data'),
    
    # === НОВЫЕ API для управления событиями (ДО events/<str:event_id>/!) ===
    path('events/create/', views.CreateGoogleEventView.as_view(), name='create_google_event'),
    path('events/check-conflict/', views.CheckEventConflictView.as_view(), name='check_event_conflict'),
    path('events/find-free-time/', views.FindFreeTimeView.as_view(), name='find_free_time'),
    path('events/<str:event_id>/update/', views.UpdateGoogleEventView.as_view(), name='update_google_event'),
    path('events/<str:event_id>/delete/', views.DeleteGoogleEventView.as_view(), name='delete_google_event'),
    
    # === EventDetailView должен быть ПОСЛЕ всех конкретных путей ===
    path('events/', views.GoogleEventsView.as_view(), name='google_events_list'),
    path('events/<str:event_id>/', views.EventDetailView.as_view(), name='event_detail'),

    # === DEBUG ===
    path('debug/credentials/', views.DebugCredentialsView.as_view(), name='debug_credentials'),
]
