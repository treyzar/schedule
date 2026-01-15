# parse_calendar/views.py

import os
import urllib.parse
from datetime import datetime, date, time, timedelta
import logging

from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone as django_timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Убедитесь, что эти библиотеки установлены: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.transport.requests

# Получаем экземпляр логгера
logger = logging.getLogger(__name__)


# --- Вспомогательная функция для обновления токена ---
def get_refreshed_credentials(session):
    """Проверяет и обновляет токен, если он истек, сохраняя его в сессию."""
    if 'google_credentials' not in session:
        return None
        
    credentials = google.oauth2.credentials.Credentials(**session['google_credentials'])
    
    if credentials.expired and credentials.refresh_token:
        logger.info("Google credentials expired. Refreshing...")
        try:
            credentials.refresh(google.auth.transport.requests.Request())
            # Сохраняем обновленные credentials обратно в сессию
            session['google_credentials'] = {
                'token': credentials.token, 'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri, 'client_id': credentials.client_id,
                'client_secret': credentials.client_secret, 'scopes': credentials.scopes
            }
            session.save()
            logger.info("Successfully refreshed Google credentials.")
        except Exception as e:
            logger.error("Failed to refresh Google credentials.", exc_info=True)
            # Если не удалось обновить, удаляем старые данные, чтобы заставить пользователя перелогиниться
            del session['google_credentials']
            return None

    return credentials


# --- Вьюха для начала авторизации ---
class GoogleAuthorizeView(APIView):
    def get(self, request):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            settings.CLIENT_SECRETS_FILE, scopes=settings.GOOGLE_SCOPES)
        redirect_uri = request.build_absolute_uri(reverse('google_callback'))
        flow.redirect_uri = redirect_uri
        authorization_url, state = flow.authorization_url(
            access_type='offline', include_granted_scopes='true', prompt='consent')
        request.session['state'] = state
        return redirect(authorization_url)


# --- Вьюха для коллбэка от Google ---
class GoogleCallbackView(APIView):
    def get(self, request):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        state = request.session.get('state')
        frontend_redirect_url = f"{settings.FRONTEND_URL}/daily-schedule-config"
        try:
            flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                settings.CLIENT_SECRETS_FILE, scopes=settings.GOOGLE_SCOPES, state=state)
            flow.redirect_uri = request.build_absolute_uri(reverse('google_callback'))
            flow.fetch_token(authorization_response=request.build_absolute_uri())
            credentials = flow.credentials
            request.session['google_credentials'] = {
                'token': credentials.token, 'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri, 'client_id': credentials.client_id,
                'client_secret': credentials.client_secret, 'scopes': credentials.scopes
            }
            final_url = f"{frontend_redirect_url}?auth=success"
            return HttpResponseRedirect(final_url)
        except Exception:
            logger.error("Error in GoogleCallbackView", exc_info=True)
            return HttpResponseRedirect(f"{frontend_redirect_url}?auth=error")


# --- Вьюха для ДНЕВНОГО расписания (`/initial-data/`) ---
class GetInitialDataView(APIView):
    def get(self, request):
        credentials = get_refreshed_credentials(request.session)
        if not credentials:
            return Response({'error': 'User not authenticated or token expired.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            now = django_timezone.now()
            time_min_dt = django_timezone.make_aware(datetime.combine(now.date(), time.min))
            time_max_dt = django_timezone.make_aware(datetime.combine(now.date(), time.max))
            
            events_result = service.events().list(
                calendarId='primary', timeMin=time_min_dt.isoformat(),
                timeMax=time_max_dt.isoformat(), singleEvents=True,
                orderBy='startTime').execute()

            return Response({'calendar_events': events_result.get('items', [])})
        except Exception as e:
            logger.error(f"Error in GetInitialDataView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Вьюха для НЕДЕЛЬНОГО/МЕСЯЧНОГО расписания (`/events/`) ---
class GoogleEventsView(APIView):
    def get(self, request):
        credentials = get_refreshed_credentials(request.session)
        if not credentials:
            return Response({'error': 'User not authenticated or token expired.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            if not (start_date_str and end_date_str):
                return Response({'error': 'start_date and end_date query parameters are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            start_date_obj = date.fromisoformat(start_date_str)
            end_date_obj = date.fromisoformat(end_date_str)
            time_min_dt = django_timezone.make_aware(datetime.combine(start_date_obj, time.min))
            time_max_dt = django_timezone.make_aware(datetime.combine(end_date_obj, time.max))
            
            events_result = service.events().list(
                calendarId='primary', timeMin=time_min_dt.isoformat(),
                timeMax=time_max_dt.isoformat(), singleEvents=True,
                orderBy='startTime').execute()
            
            return Response(events_result.get('items', []))
            
        except Exception as e:
            logger.error(f"Error in GoogleEventsView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Вьюха для управления ОДНИМ событием (PATCH/DELETE) ---
class EventDetailView(APIView):
    def get_service_and_credentials(self, request):
        credentials = get_refreshed_credentials(request.session)
        if not credentials:
            return None
        service = build('calendar', 'v3', credentials=credentials)
        return service

    def patch(self, request, event_id):
        service = self.get_service_and_credentials(request)
        if not service: return Response({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            update_data = request.data
            if 'summary' in update_data: event['summary'] = update_data['summary']
            if 'description' in update_data: event['description'] = update_data['description']
            if 'start' in update_data and 'end' in update_data:
                event['start'] = {'dateTime': update_data['start'], 'timeZone': settings.TIME_ZONE}
                event['end'] = {'dateTime': update_data['end'], 'timeZone': settings.TIME_ZONE}
            updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            return Response(updated_event, status=status.HTTP_200_OK)
        except Exception as e: 
            logger.error(f"Error in EventDetailView PATCH: {e}", exc_info=True)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, event_id):
        service = self.get_service_and_credentials(request)
        if not service: return Response({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in EventDetailView DELETE: {e}", exc_info=True)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
