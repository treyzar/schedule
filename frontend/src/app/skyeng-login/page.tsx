'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';

export default function SkyengLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Проверяем, успешна ли была Google авторизация
  const googleAuthSuccess = searchParams.get('auth') === 'success';
  const googleAuthError = searchParams.get('auth') === 'error';

  useEffect(() => {
    if (googleAuthError) {
      setError('Ошибка авторизации Google. Попробуйте еще раз.');
    }
  }, [googleAuthError]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setIsLoading(true);

    if (!email || !password) {
      setError('Введите email и пароль');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/parse_calendar/skyeng-login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ 
          email: email.trim(), 
          password 
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccessMessage('Успешная авторизация в Skyeng!');

        // Обновляем статус авторизации
        try {
          await fetch('http://localhost:8000/parse_calendar/status/', {
            credentials: 'include',
          });
        } catch (err) {
          console.error('Failed to refresh status:', err);
        }

        // Небольшая задержка для показа сообщения об успехе
        setTimeout(() => {
          // Перенаправляем на страницу настроек с параметром для открытия Skyeng секции
          const nextUrl = searchParams.get('next');
          if (nextUrl) {
            router.push(nextUrl);
          } else {
            // Открываем настройки с открытой секцией Skyeng
            router.push('/personal-cabinet-parsing?skyeng=open');
          }
        }, 1000);
      } else {
        setError(data.error || 'Ошибка при входе. Проверьте логин и пароль.');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Произошла ошибка при подключении к серверу');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    // Пропускаем авторизацию в Skyeng и переходим на главную
    const nextUrl = searchParams.get('next');
    router.push(nextUrl || '/weekly-schedule-overview');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background flex items-center justify-center p-4">
      {/* Декоративные элементы фона */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Карточка авторизации */}
        <div className="bg-card border border-border rounded-2xl shadow-xl overflow-hidden">
          {/* Header с градиентом */}
          <div className="bg-gradient-to-r from-primary/10 to-blue-500/10 px-8 py-6 border-b border-border">
            <div className="flex items-center justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-primary to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                <Icon name="UserCircleIcon" size={36} className="text-white" />
              </div>
            </div>
            <h1 className="text-2xl font-heading font-bold text-foreground text-center">
              Вход в Skyeng
            </h1>
            <p className="text-muted-foreground text-center mt-2 text-sm">
              Опционально (можно пропустить)
            </p>
          </div>

          {/* Тело формы */}
          <div className="px-8 py-6">
            {/* Сообщение об успехе Google авторизации */}
            {googleAuthSuccess && (
              <div className="mb-6 p-4 bg-success/10 border border-success rounded-lg">
                <div className="flex items-start gap-3">
                  <Icon name="CheckCircleIcon" size={20} className="text-success mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-success">Google авторизация успешна!</p>
                    <p className="text-xs text-success/80 mt-1">При желании войдите в Skyeng</p>
                  </div>
                </div>
              </div>
            )}

            {/* Сообщение об ошибке */}
            {error && (
              <div className="mb-6 p-4 bg-error/10 border border-error rounded-lg animate-in fade-in slide-in-from-top-2">
                <div className="flex items-start gap-3">
                  <Icon name="ExclamationTriangleIcon" size={20} className="text-error mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-error">{error}</p>
                </div>
              </div>
            )}

            {/* Сообщение об успехе */}
            {successMessage && (
              <div className="mb-6 p-4 bg-success/10 border border-success rounded-lg animate-in fade-in slide-in-from-top-2">
                <div className="flex items-start gap-3">
                  <Icon name="CheckCircleIcon" size={20} className="text-success mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-success">{successMessage}</p>
                </div>
              </div>
            )}

            {/* Форма входа */}
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium text-foreground">
                  Email от Skyeng
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Icon name="EnvelopeIcon" size={20} className="text-muted-foreground" />
                  </div>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-foreground placeholder-muted-foreground transition-all"
                    placeholder="your@email.com"
                    autoComplete="email"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-foreground">
                  Пароль
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Icon name="LockClosedIcon" size={20} className="text-muted-foreground" />
                  </div>
                  <input
                    type="password"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-foreground placeholder-muted-foreground transition-all"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full px-6 py-3.5 bg-gradient-to-r from-primary to-blue-600 text-primary-foreground font-medium rounded-lg hover:from-primary/90 hover:to-blue-600/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
              >
                {isLoading ? (
                  <>
                    <Icon name="ArrowPathIcon" size={20} className="animate-spin" />
                    <span>Вход...</span>
                  </>
                ) : (
                  <>
                    <Icon name="ArrowRightOnRectangleIcon" size={20} />
                    <span>Войти</span>
                  </>
                )}
              </button>
            </form>

            {/* Кнопка пропуска */}
            <div className="mt-4">
              <button
                onClick={handleSkip}
                disabled={isLoading}
                className="w-full px-6 py-3 bg-muted/50 text-muted-foreground font-medium rounded-lg hover:bg-muted transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Пропустить сейчас
              </button>
            </div>
          </div>

          {/* Footer с информацией */}
          <div className="px-8 py-5 bg-muted/30 border-t border-border">
            <div className="flex items-start gap-2.5">
              <Icon name="InformationCircleIcon" size={18} className="text-muted-foreground mt-0.5 flex-shrink-0" />
              <p className="text-xs text-muted-foreground leading-relaxed">
                Авторизация в Skyeng опциональна. Используйте для импорта расписания из Skyeng.
              </p>
            </div>
          </div>
        </div>

        {/* Навигация назад */}
        <div className="mt-6 text-center">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <Icon name="ArrowLeftIcon" size={16} />
            <span>Назад</span>
          </button>
        </div>
      </div>
    </div>
  );
}
