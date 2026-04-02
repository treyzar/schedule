'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';
import AllSubjectsView from './AllSubjectsView';

// ==============================================================================
// ОСНОВНОЙ КОМПОНЕНТ ПАРСЕРА
// ==============================================================================
export default function ParsingInteractive() {
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [subjectsData, setSubjectsData] = useState<AllSubjectsResponse | null>(null);
  const [showSkyengSection, setShowSkyengSection] = useState<boolean>(false);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);

  /**
   * Функция для получения данных по предметам с бэкенда.
   */
  const fetchSubjectsData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/parse_avatar/all-subjects/', {
        credentials: 'include',
      });

      if (response.status === 401) {
        setIsLoggedIn(false);
        setIsLoading(false);
        return;
      }

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Не удалось загрузить данные по предметам.');
      }

      const data = await response.json();
      setSubjectsData(data);
      setIsLoggedIn(true);
    } catch (err: any) {
      if (!(err instanceof TypeError && err.message === 'Failed to fetch')) {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Проверяем параметр ?skyeng=open при загрузке
  useEffect(() => {
    const skyengParam = searchParams.get('skyeng');
    if (skyengParam === 'open') {
      setShowSkyengSection(true);
    }
  }, [searchParams]);

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/parse_avatar/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      setIsLoggedIn(false);
      setSubjectsData(null);
      setError(null);
      setShowSkyengSection(false);
    } catch (err) {
      console.error('Logout error:', err);
      setError('Ошибка при выходе');
    }
  };

  useEffect(() => {
    fetchSubjectsData();
  }, []);

  // --- РЕНДЕРИНГ ---

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background flex items-center justify-center">
        <div className="text-center">
          <Icon name="ArrowPathIcon" size={48} className="animate-spin text-primary mx-auto mb-4" />
          <p className="text-lg font-body text-muted-foreground">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-card border border-border rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-blue-600 rounded-xl flex items-center justify-center shadow-md">
                <Icon name="AcademicCapIcon" size={28} className="text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-heading font-bold text-foreground">
                  Парсер данных Skyeng
                </h1>
                <p className="text-sm text-muted-foreground">
                  Просмотр предметов и программ
                </p>
              </div>
            </div>
            
            {isLoggedIn && (
              <button
                onClick={handleLogout}
                className="px-4 py-2.5 bg-muted/50 text-muted-foreground rounded-lg hover:bg-error/10 hover:text-error transition-all flex items-center gap-2 text-sm font-medium"
              >
                <Icon name="ArrowRightOnRectangleIcon" size={18} />
                <span>Выйти</span>
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-card border border-error rounded-2xl shadow-lg p-6 mb-6 animate-in fade-in slide-in-from-top-2">
            <div className="flex items-start gap-3">
              <Icon name="ExclamationTriangleIcon" size={24} className="text-error mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-error mb-1">Ошибка</h3>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Not Logged In State */}
        {!isLoggedIn && !error && (
          <div className="bg-card border border-border rounded-2xl shadow-lg p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-6">
                <Icon name="LockClosedIcon" size={40} className="text-muted-foreground" />
              </div>
              <h2 className="text-xl font-heading font-semibold text-foreground mb-3">
                Требуется авторизация
              </h2>
              <p className="text-muted-foreground mb-6">
                Для просмотра данных необходимо авторизоваться в системе Skyeng
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => window.location.href = '/skyeng-login'}
                  className="w-full px-6 py-3 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-all flex items-center justify-center gap-2 shadow-md"
                >
                  <Icon name="ArrowRightOnRectangleIcon" size={20} />
                  <span>Войти через Skyeng</span>
                </button>
                <div className="p-4 bg-muted/30 rounded-lg">
                  <p className="text-xs text-muted-foreground">
                    <Icon name="InformationCircleIcon" size={16} className="inline mr-1" />
                    Авторизация через личный кабинет Skyeng
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Logged In - Data Display */}
        {isLoggedIn && (
          <AllSubjectsView onSubjectClick={(subjectKey) => setSelectedSubject(subjectKey)} />
        )}
      </div>
    </div>
  );
}
