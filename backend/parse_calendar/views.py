# parse_calendar/views.py

import os
import urllib.parse
from datetime import datetime, date, time, timedelta
import logging
from typing import Optional, Dict, Any

from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone as django_timezone
from django.utils.timesince import timesince
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from services.google_auth import GoogleAuthService, GoogleCredentials
from services.google_calendar_service import GoogleCalendarService
from services.skyeng_auth import SkyengAuthService, SkyengCredentials, SkyengAuthError, SkyengInvalidCredentialsError
from .models import UserCredentials

logger = logging.getLogger(__name__)
User = get_user_model()

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:4028')


# --- Вспомогательные функции ---

def get_user_credentials_or_none(user) -> Optional[UserCredentials]:
    """Получает credentials пользователя или None"""
    # Сначала проверяем что пользователь аутентифицирован
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return None
    
    try:
        return user.external_credentials
    except UserCredentials.DoesNotExist:
        return None


def get_or_create_user_credentials(user) -> UserCredentials:
    """Получает или создает credentials для пользователя"""
    creds, _ = UserCredentials.objects.get_or_create(user=user)
    return creds


def get_refreshed_google_credentials(session) -> Optional[Any]:
    """Проверяет статус токена и обновляет его при необходимости."""
    if 'google_credentials' not in session:
        return None

    auth_service = GoogleAuthService()
    old_creds_data = session['google_credentials']
    refreshed = auth_service.refresh_credentials(old_creds_data)

    if refreshed:
        new_creds_data = refreshed.to_dict()
        if new_creds_data['token'] != old_creds_data['token']:
            session['google_credentials'] = new_creds_data
            session.modified = True
            session.save()
            logger.info("Google credentials обновлены в сессии")
        return refreshed  # Возвращаем GoogleCredentials объект

    return None


# --- Вьюха для выхода ---

class GoogleLogoutView(APIView):
    """Выход из Google Calendar"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        if 'google_credentials' in request.session:
            del request.session['google_credentials']
        if 'google_calendar_last_sync' in request.session:
            del request.session['google_calendar_last_sync']
        request.session.save()
        return Response({'success': True})


class SkyengLogoutView(APIView):
    """Выход из Skyeng"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Очищает Skyeng credentials пользователя.
        """
        try:
            user_creds = get_user_credentials_or_none(request.user)
            if user_creds:
                user_creds.skyeng_token = None
                user_creds.skyeng_refresh_token = None
                user_creds.skyeng_token_expiry = None
                user_creds.skyeng_email = None
                user_creds.last_sync_skyeng = None
                user_creds.save()
                logger.info(f"Skyeng logout for user {request.user.username}")
            
            return Response({'success': True})
        except Exception as e:
            logger.error(f"Skyeng logout error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Вьюха для статуса авторизации ---

class GoogleAuthStatusView(APIView):
    """Проверка статуса авторизации Google Calendar"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        session_key = request.session.session_key
        credentials = get_refreshed_google_credentials(request.session)
        is_authenticated = credentials is not None

        logger.info(f"Checking auth status: authenticated={is_authenticated}, session_key={session_key}")

        last_sync = request.session.get('google_calendar_last_sync', None)
        last_sync_formatted = None

        if last_sync:
            try:
                sync_time = datetime.fromisoformat(last_sync)
                last_sync_formatted = timesince(sync_time) + ' назад'
            except (ValueError, TypeError):
                last_sync_formatted = None

        email = None
        google_authenticated = False
        skyeng_authenticated = False
        skyeng_email = None
        skyeng_token_expired = False
        
        if credentials:
            google_authenticated = True
            auth_service = GoogleAuthService()
            email = auth_service.get_user_email({'token': credentials.token})
        
        # Проверяем Skyeng авторизацию в БД
        if request.user.is_authenticated:
            user_creds = get_user_credentials_or_none(request.user)
            if user_creds and user_creds.has_skyeng_credentials():
                skyeng_authenticated = True
                skyeng_email = user_creds.skyeng_email
                skyeng_token_expired = user_creds.is_skyeng_token_expired()
        elif request.session.get('google_credentials_temp'):
            # Пользователь в процессе авторизации (Google прошёл, Skyeng ещё нет)
            google_authenticated = True

        return Response({
            'is_authenticated': is_authenticated,
            'google_authenticated': google_authenticated,
            'skyeng_authenticated': skyeng_authenticated,
            'skyeng_email': skyeng_email,
            'skyeng_token_expired': skyeng_token_expired,
            'last_sync': last_sync_formatted,
            'email': email,
            'is_fully_authenticated': google_authenticated and skyeng_authenticated,
            'requires_skyeng_auth': google_authenticated and not skyeng_authenticated,
        })


# --- Вьюха для статуса Skyeng ---

class SkyengStatusView(APIView):
    """Проверка статуса авторизации Skyeng"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Возвращает детальный статус подключения к Skyeng.
        """
        user_creds = None
        is_authenticated = False
        email = None
        token_expired = False
        last_sync = None
        last_sync_formatted = None
        
        # Проверяем в БД если пользователь авторизован
        if request.user.is_authenticated:
            user_creds = get_user_credentials_or_none(request.user)
            if user_creds and user_creds.has_skyeng_credentials():
                is_authenticated = True
                email = user_creds.skyeng_email
                token_expired = user_creds.is_skyeng_token_expired()
                if user_creds.last_sync_skyeng:
                    last_sync = user_creds.last_sync_skyeng
                    try:
                        sync_time = django_timezone.make_aware(last_sync) if isinstance(last_sync, datetime) else last_sync
                        last_sync_formatted = timesince(sync_time) + ' назад'
                    except (ValueError, TypeError):
                        last_sync_formatted = None
        
        # Статус подключения
        connection_status = 'disconnected'
        if is_authenticated:
            if token_expired:
                connection_status = 'expired'
            else:
                connection_status = 'connected'
        
        return Response({
            'is_authenticated': is_authenticated,
            'connection_status': connection_status,  # 'connected', 'expired', 'disconnected'
            'email': email,
            'token_expired': token_expired,
            'last_sync': last_sync_formatted,
            'requires_auth': not is_authenticated,
        })


# --- Вьюха для начала авторизации Google ---

class GoogleAuthorizeView(APIView):
    """Начинает процесс авторизации Google OAuth"""
    permission_classes = [AllowAny]
    
    def __init__(self):
        self.auth_service = GoogleAuthService()

    def get(self, request):
        try:
            if not request.session.session_key:
                request.session.create()

            redirect_uri = request.build_absolute_uri(reverse('google_callback'))
            auth_url, state, code_verifier = self.auth_service.create_authorization_url(request)

            request.session['state'] = state
            request.session['code_verifier'] = code_verifier
            request.session.modified = True
            request.session.save()

            logger.info(f"OAuth start: verifier сохранен в сессию {request.session.session_key}")
            return redirect(auth_url)
        except Exception as e:
            logger.error(f"Error creating authorization URL: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Вьюха для коллбэка от Google ---

class GoogleCallbackView(APIView):
    """Обработка коллбэка от Google OAuth"""
    permission_classes = [AllowAny]
    
    def __init__(self):
        self.auth_service = GoogleAuthService()

    def get(self, request):
        # После Google OAuth перенаправляем на главную страницу календаря
        frontend_redirect_url = FRONTEND_URL

        try:
            code = request.GET.get('code')
            state_from_url = request.GET.get('state')
            saved_state = request.session.get('state')
            code_verifier = request.session.get('code_verifier')

            logger.info(f"Callback data: state_url={state_from_url}, has_verifier={code_verifier is not None}")

            effective_state = saved_state or state_from_url
            redirect_uri = request.build_absolute_uri(reverse('google_callback'))

            if not code:
                logger.error("No code in callback request")
                return HttpResponseRedirect(f"{frontend_redirect_url}?auth=error")

            credentials = self.auth_service.exchange_code_for_credentials(
                code=code,
                redirect_uri=redirect_uri,
                state=effective_state,
                code_verifier=code_verifier
            )

            # Сохраняем Google credentials в сессию (для обратной совместимости)
            request.session['google_credentials'] = credentials.to_dict()
            request.session['google_calendar_last_sync'] = django_timezone.now().isoformat()

            # Сохраняем state для последующей связи с пользователем
            request.session['google_email_temp'] = self.auth_service.get_user_email(credentials.to_dict())
            request.session['google_credentials_temp'] = credentials.to_dict()

            # Очищаем временные данные OAuth
            if 'state' in request.session:
                del request.session['state']
            if 'code_verifier' in request.session:
                del request.session['code_verifier']

            request.session.modified = True
            request.session.save()

            logger.info(f"OAuth success! Session: {request.session.session_key}")

            # Перенаправляем на главную страницу календаря
            final_url = f"{frontend_redirect_url}"
            return HttpResponseRedirect(final_url)

        except Exception as e:
            logger.error(f"Callback error: {str(e)}", exc_info=True)
            return HttpResponseRedirect(f"{frontend_redirect_url}?auth=error")


# --- Вьюха для авторизации Skyeng ---

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class SkyengLoginView(APIView):
    """
    Авторизация в Skyeng по логину/паролю.
    Вызывается после успешной Google OAuth.
    """
    permission_classes = [AllowAny]

    def __init__(self):
        self.skyeng_auth = SkyengAuthService()

    def post(self, request):
        """
        Аутентификация в Skyeng.
        
        POST /parse_calendar/skyeng-login/
        
        Body:
        {
            "email": "user@example.com",
            "password": "secret"
        }
        """
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                return Response(
                    {'error': 'Email и пароль обязательны'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Аутентификация в Skyeng
            credentials = self.skyeng_auth.authenticate(email, password)

            logger.info(f"Skyeng auth success for {email}, user_id={credentials.user_id}")

            # Получаем пользователя из сессии или создаем нового
            User = get_user_model()
            user = None
            if request.user.is_authenticated:
                user = request.user
            else:
                # Пытаемся найти пользователя по email
                # Сначала проверяем email из Skyeng
                user = User.objects.filter(email=email).first()
                
                # Если не нашли, проверяем email из Google сессии
                if not user:
                    google_email = request.session.get('google_email_temp')
                    if google_email:
                        user = User.objects.filter(email=google_email).first()

                # Если не нашли, создаем нового пользователя
                if not user:
                    # Генерируем уникальный username
                    base_username = email.split('@')[0]
                    username = base_username
                    counter = 1
                    
                    # Проверяем, существует ли уже такой username
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                    )
                    logger.info(f"Created new user: {username} (email: {email})")
            
            # Логиним пользователя в системе (обновляем сессию)
            from django.contrib.auth import login
            login(request, user)
            logger.info(f"User {user.username} logged in successfully")

            # Сохраняем credentials в БД
            user_creds = get_or_create_user_credentials(user)
            user_creds.set_skyeng_credentials(
                token=credentials.token,
                refresh_token=credentials.refresh_token,
                expiry=credentials.expires_at,
                email=credentials.email,
            )
            user_creds.save()
            
            # Сохраняем cookies сессии для parse_avatar (обратная совместимость)
            if credentials._session_cookies:
                request.session['skyeng_cookies'] = credentials._session_cookies
                request.session['skyeng_authenticated'] = True
                request.session['skyeng_email'] = credentials.email
                logger.info(f"Skyeng cookies saved to session for parse_avatar compatibility")

            # Возвращаем успех
            return Response({
                'success': True,
                'message': 'Успешная авторизация в Skyeng!',
                'redirect': '/weekly-schedule-overview',
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in SkyengLoginView: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def options(self, request):
        """Обработка CORS preflight запросов"""
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


# =============================================================================
# === DEBUG / Diagnostic Views ===
# =============================================================================

class DebugCredentialsView(APIView):
    """
    Debug view для проверки credentials в сессии.
    
    GET /parse_calendar/debug/credentials/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        credentials = request.session.get('google_credentials')
        
        debug_info = {
            'session_key': session_key,
            'session_exists': bool(session_key),
            'has_credentials': bool(credentials),
            'credentials_keys': list(credentials.keys()) if credentials else None,
            'credentials_partial': {
                k: v[:20] + '...' if isinstance(v, str) and len(v) > 20 else v
                for k, v in credentials.items()
            } if credentials else None,
            'all_session_data': {
                k: v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v
                for k, v in request.session.items()
            },
        }
        
        # Проверяем валидность credentials
        if credentials:
            from services.google_auth import GoogleAuthService
            auth_service = GoogleAuthService()
            status, creds = auth_service.check_credential_status(credentials)
            debug_info['credentials_status'] = status
            debug_info['credentials_valid'] = status == 'valid'
            
            # Пробуем получить сервис
            service = auth_service.get_calendar_service(credentials)
            debug_info['calendar_service_available'] = bool(service)
            
            # Пробуем получить список календарей
            if service:
                try:
                    calendars = service.calendarList().list().execute()
                    debug_info['primary_calendar'] = calendars.get('items', [{}])[0].get('summary') if calendars.get('items') else None
                except Exception as e:
                    debug_info['calendar_list_error'] = str(e)
        
        return Response(debug_info)

    def post(self, request):
        """
        Обрабатывает логин в Skyeng.
        
        Ожидает:
            email: Email от Skyeng
            password: Пароль от Skyeng
        
        Возвращает:
            success: True если авторизация успешна
            redirect: URL для перенаправления на главную
        """
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email и пароль обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Аутентификация в Skyeng
            skyeng_credentials = self.skyeng_auth.authenticate(email, password)
            
            logger.info(f"Skyeng auth success for {email}, user_id={skyeng_credentials.user_id}")

            # Получаем пользователя из сессии или создаем нового
            user = None
            if request.user.is_authenticated:
                user = request.user
            else:
                # Пытаемся найти пользователя по email из Google сессии
                google_email = request.session.get('google_email_temp')
                if google_email:
                    user = User.objects.filter(email=google_email).first()
                
                # Если не нашли, создаем нового пользователя
                if not user:
                    username = email.split('@')[0]
                    user = User.objects.create_user(
                        username=username,
                        email=email or google_email,
                    )
                    logger.info(f"Created new user: {username}")

            # Сохраняем credentials в БД
            user_creds = get_or_create_user_credentials(user)
            user_creds.set_skyeng_credentials(
                token=skyeng_credentials.token,
                refresh_token=skyeng_credentials.refresh_token,
                expiry=skyeng_credentials.expires_at,
                email=skyeng_credentials.email,
            )
            
            # Если есть Google credentials во временной сессии, сохраняем и их
            google_creds_temp = request.session.get('google_credentials_temp')
            google_email_temp = request.session.get('google_email_temp')
            if google_creds_temp:
                user_creds.set_google_credentials(google_creds_temp, google_email_temp)
                # Сохраняем в сессию для обратной совместимости
                request.session['google_credentials'] = google_creds_temp
                request.session['google_calendar_last_sync'] = django_timezone.now().isoformat()
            
            user_creds.save()
            
            # Очищаем временные данные сессии
            if 'google_email_temp' in request.session:
                del request.session['google_email_temp']
            if 'google_credentials_temp' in request.session:
                del request.session['google_credentials_temp']
            
            request.session.modified = True
            request.session.save()

            logger.info(f"Saved credentials for user {user.username}")

            return Response({
                'success': True,
                'redirect': f"{settings.FRONTEND_URL}/weekly-schedule-overview",
                'skyeng_email': skyeng_credentials.email,
            })

        except SkyengInvalidCredentialsError as e:
            logger.warning(f"Skyeng invalid credentials: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except SkyengAuthError as e:
            logger.error(f"Skyeng auth error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in SkyengLoginView: {e}", exc_info=True)
            return Response(
                {'error': 'Внутренняя ошибка сервера'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- Вьюха для ДНЕВНОГО расписания (`/initial-data/`) ---

class GetInitialDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        credentials = get_refreshed_google_credentials(request.session)
        
        # Конвертируем GoogleCredentials в google.oauth2.credentials.Credentials
        if credentials:
            from shared.credentials import GoogleCredentials
            if isinstance(credentials, GoogleCredentials):
                credentials = credentials.to_google_credentials()
        
        if not credentials:
            # Пытаемся получить из БД
            user_creds = get_user_credentials_or_none(request.user)
            if user_creds and user_creds.has_google_credentials():
                from google.oauth2.credentials import Credentials
                creds_dict = user_creds.get_google_credentials_dict()
                credentials = Credentials(**creds_dict) if creds_dict else None

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

            request.session['google_calendar_last_sync'] = now.isoformat()
            request.session.save()

            return Response({'calendar_events': events_result.get('items', [])})
        except Exception as e:
            logger.error(f"Error in GetInitialDataView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Вьюха для НЕДЕЛЬНОГО/МЕСЯЧНОГО расписания (`/events/`) ---

class GoogleEventsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        credentials = get_refreshed_google_credentials(request.session)
        
        # Конвертируем GoogleCredentials в google.oauth2.credentials.Credentials
        if credentials:
            from shared.credentials import GoogleCredentials
            if isinstance(credentials, GoogleCredentials):
                credentials = credentials.to_google_credentials()
        
        if not credentials:
            user_creds = get_user_credentials_or_none(request.user)
            if user_creds and user_creds.has_google_credentials():
                from google.oauth2.credentials import Credentials
                creds_dict = user_creds.get_google_credentials_dict()
                credentials = Credentials(**creds_dict) if creds_dict else None

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
    permission_classes = [AllowAny]

    def get_service_and_credentials(self, request):
        credentials = get_refreshed_google_credentials(request.session)
        
        # Конвертируем GoogleCredentials в google.oauth2.credentials.Credentials
        if credentials:
            from shared.credentials import GoogleCredentials
            if isinstance(credentials, GoogleCredentials):
                credentials = credentials.to_google_credentials()
        
        if not credentials:
            user_creds = get_user_credentials_or_none(request.user)
            if user_creds and user_creds.has_google_credentials():
                from google.oauth2.credentials import Credentials
                creds_dict = user_creds.get_google_credentials_dict()
                credentials = Credentials(**creds_dict) if creds_dict else None

        if not credentials:
            return None
        service = build('calendar', 'v3', credentials=credentials)
        return service

    def patch(self, request, event_id):
        service = self.get_service_and_credentials(request)
        if not service:
            return Response({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            update_data = request.data
            if 'summary' in update_data:
                event['summary'] = update_data['summary']
            if 'description' in update_data:
                event['description'] = update_data['description']
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
        if not service:
            return Response({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in EventDetailView DELETE: {e}", exc_info=True)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# === НОВЫЕ API для создания и управления событиями в Google Calendar ===
# =============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class CreateGoogleEventView(APIView):
    """
    Создание события в Google Calendar.

    POST /parse_calendar/events/create/

    Body:
    {
        "summary": "Встреча с командой",
        "start_datetime": "2024-04-02T15:00:00",
        "end_datetime": "2024-04-02T16:00:00",
        "description": "Обсуждение проекта",  // опционально
        "location": "Офис",  // опционально
        "attendees": ["user@example.com"],  // опционально
        "category": "work",  // опционально
        "priority": "high"  // опционально
    }
    """
    permission_classes = [AllowAny]

    def options(self, request):
        """Обработка CORS preflight запросов"""
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        try:
            # Проверяем авторизацию
            credentials_data = request.session.get('google_credentials')
            if not credentials_data:
                return Response(
                    {'error': 'Необходимо авторизоваться в Google Calendar'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Валидируем данные
            summary = request.data.get('summary')
            start_datetime = request.data.get('start_datetime')
            end_datetime = request.data.get('end_datetime')
            
            if not summary:
                return Response(
                    {'error': 'Название события обязательно'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not start_datetime or not end_datetime:
                return Response(
                    {'error': 'Укажите время начала и окончания события'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Парсим datetime
            from datetime import datetime
            try:
                start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            except ValueError as e:
                return Response(
                    {'error': f'Неверный формат даты: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Создаём событие
            calendar_service = GoogleCalendarService()
            event = calendar_service.create_event(
                session=request.session,
                summary=summary,
                start_datetime=start_dt,
                end_datetime=end_dt,
                description=request.data.get('description'),
                location=request.data.get('location'),
                attendees=request.data.get('attendees', []),
                category=request.data.get('category'),
                priority=request.data.get('priority'),
            )
            
            return Response({
                'success': True,
                'event': event,
                'message': 'Событие успешно создано'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating Google event: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class UpdateGoogleEventView(APIView):
    """
    Обновление события в Google Calendar.
    
    PATCH /parse_calendar/events/{event_id}/update/
    """
    permission_classes = [AllowAny]
    
    def patch(self, request, event_id):
        try:
            credentials_data = request.session.get('google_credentials')
            if not credentials_data:
                return Response(
                    {'error': 'Необходимо авторизоваться в Google Calendar'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            calendar_service = GoogleCalendarService()
            
            # Парсим datetime если есть
            start_dt = None
            end_dt = None
            if request.data.get('start_datetime'):
                from datetime import datetime
                start_dt = datetime.fromisoformat(request.data['start_datetime'].replace('Z', '+00:00'))
            if request.data.get('end_datetime'):
                from datetime import datetime
                end_dt = datetime.fromisoformat(request.data['end_datetime'].replace('Z', '+00:00'))
            
            event = calendar_service.update_event(
                session=request.session,
                event_id=event_id,
                summary=request.data.get('summary'),
                start_datetime=start_dt,
                end_datetime=end_dt,
                description=request.data.get('description'),
                location=request.data.get('location'),
                status=request.data.get('status'),
            )
            
            return Response({
                'success': True,
                'event': event,
                'message': 'Событие успешно обновлено'
            })
            
        except Exception as e:
            logger.error(f"Error updating Google event: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class DeleteGoogleEventView(APIView):
    """
    Удаление события из Google Calendar.
    
    DELETE /parse_calendar/events/{event_id}/delete/
    """
    permission_classes = [AllowAny]
    
    def delete(self, request, event_id):
        try:
            credentials_data = request.session.get('google_credentials')
            if not credentials_data:
                return Response(
                    {'error': 'Необходимо авторизоваться в Google Calendar'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            calendar_service = GoogleCalendarService()
            calendar_service.delete_event(
                session=request.session,
                event_id=event_id,
                send_notifications=True
            )
            
            return Response({
                'success': True,
                'message': 'Событие успешно удалено'
            })
            
        except Exception as e:
            logger.error(f"Error deleting Google event: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class CheckEventConflictView(APIView):
    """
    Проверка конфликтов при создании события.

    POST /parse_calendar/events/check-conflict/

    Body:
    {
        "start_datetime": "2024-04-02T15:00:00",
        "end_datetime": "2024-04-02T16:00:00"
    }
    """
    permission_classes = [AllowAny]

    def options(self, request):
        """Обработка CORS preflight запросов"""
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        try:
            credentials_data = request.session.get('google_credentials')
            if not credentials_data:
                return Response(
                    {'error': 'Необходимо авторизоваться в Google Calendar'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            from datetime import datetime
            start_dt = datetime.fromisoformat(request.data.get('start_datetime', '').replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(request.data.get('end_datetime', '').replace('Z', '+00:00'))
            
            calendar_service = GoogleCalendarService()
            conflicts = calendar_service.check_event_conflict(
                session=request.session,
                start_datetime=start_dt,
                end_datetime=end_dt
            )
            
            return Response({
                'has_conflict': len(conflicts) > 0,
                'conflicts': conflicts,
                'conflict_count': len(conflicts)
            })
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class FindFreeTimeView(APIView):
    """
    Поиск свободного времени в календаре.

    POST /parse_calendar/events/find-free-time/

    Body:
    {
        "duration_minutes": 60,
        "date_start": "2024-04-01",
        "date_end": "2024-04-07",
        "working_hours_start": 9,
        "working_hours_end": 18
    }
    """
    permission_classes = [AllowAny]

    def options(self, request):
        """Обработка CORS preflight запросов"""
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        try:
            credentials_data = request.session.get('google_credentials')
            if not credentials_data:
                return Response(
                    {'error': 'Необходимо авторизоваться в Google Calendar'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            from datetime import datetime
            duration = request.data.get('duration_minutes', 60)
            date_start = datetime.fromisoformat(request.data.get('date_start', datetime.now().strftime('%Y-%m-%d')))
            date_end = datetime.fromisoformat(request.data.get('date_end', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')))
            
            calendar_service = GoogleCalendarService()
            free_slots = calendar_service.find_free_time(
                session=request.session,
                duration_minutes=duration,
                date_start=date_start,
                date_end=date_end,
                working_hours_start=request.data.get('working_hours_start', 9),
                working_hours_end=request.data.get('working_hours_end', 18),
            )
            
            return Response({
                'free_slots': free_slots,
                'total_found': len(free_slots)
            })
            
        except Exception as e:
            logger.error(f"Error finding free time: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
