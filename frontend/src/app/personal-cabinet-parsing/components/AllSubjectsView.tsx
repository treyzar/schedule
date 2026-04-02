'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface Subject {
  subject_key: string;
  subject_name: string;
  has_active_program: boolean;
  stream: boolean | null;
  program: boolean | null;
  modules_count: number;
  metrics: {
    lessons_current: number;
    lessons_total: number;
    lessons_rating: number | null;
    homework_current: number;
    homework_total: number;
    homework_rating: number | null;
    tests_current: number;
    tests_total: number;
    tests_rating: number | null;
    progress_percentage: number;
  } | null;
}

interface AllSubjectsViewProps {
  onSubjectClick?: (subjectKey: string) => void;
}

export default function AllSubjectsView({ onSubjectClick }: AllSubjectsViewProps) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllSubjects = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/parse_avatar/all-subjects/', {
        credentials: 'include',
      });

      if (response.status === 401) {
        setError('Требуется авторизация');
        setIsLoading(false);
        return;
      }

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Не удалось загрузить данные');
      }

      const data = await response.json();
      if (data.success) {
        setSubjects(data.subjects || []);
      } else {
        setError(data.error || 'Ошибка загрузки');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllSubjects();
  }, []);

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'text-success';
    if (percentage >= 50) return 'text-warning';
    return 'text-muted-foreground';
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-success';
    if (percentage >= 50) return 'bg-warning';
    return 'bg-primary';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Icon name="ArrowPathIcon" size={48} className="animate-spin text-primary" />
        <p className="ml-4 text-muted-foreground">Загрузка предметов...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-error/10 border border-error rounded-lg text-center">
        <Icon name="ExclamationTriangleIcon" size={48} className="text-error mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-error mb-2">Ошибка загрузки</h3>
        <p className="text-muted-foreground">{error}</p>
        <button
          onClick={fetchAllSubjects}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (subjects.length === 0) {
    return (
      <div className="p-6 bg-muted/30 border border-border rounded-lg text-center">
        <Icon name="BookOpenIcon" size={48} className="text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Нет предметов</h3>
        <p className="text-muted-foreground">У вас пока нет активных предметов</p>
      </div>
    );
  }

  // Группируем предметы по статусу
  const activeSubjects = subjects.filter(s => s.has_active_program || s.metrics?.lessons_total);
  const emptySubjects = subjects.filter(s => !s.has_active_program && !s.metrics?.lessons_total);

  return (
    <div className="space-y-8">
      {/* Активные предметы */}
      {activeSubjects.length > 0 && (
        <div>
          <h2 className="text-xl font-heading font-semibold mb-4 flex items-center gap-2">
            <Icon name="CheckCircleIcon" size={24} className="text-success" />
            Активные предметы ({activeSubjects.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeSubjects.map((subject) => (
              <div
                key={subject.subject_key}
                className="bg-card border border-border rounded-xl p-5 hover:shadow-lg hover:border-primary/30 transition-all cursor-pointer group"
                onClick={() => onSubjectClick?.(subject.subject_key)}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary/10 to-blue-500/10 rounded-xl flex items-center justify-center group-hover:from-primary/20 group-hover:to-blue-500/20 transition-all">
                      <Icon name="AcademicCapIcon" size={24} className="text-primary" />
                    </div>
                    <div>
                      <h3 className="font-heading font-semibold text-foreground">{subject.subject_name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        {subject.has_active_program && (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-success/10 text-success">
                            Активен
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Программа/Поток */}
                {(subject.stream || subject.program) && (
                  <div className="mb-4 p-3 bg-muted/30 rounded-lg">
                    {subject.stream && (
                      <div className="mb-2">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                          <Icon name="VideoCameraIcon" size={14} />
                          <span>Поток</span>
                        </div>
                        <p className="text-sm font-medium text-foreground">Доступен</p>
                      </div>
                    )}
                    {subject.program && (
                      <div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                          <Icon name="DocumentTextIcon" size={14} />
                          <span>Программа</span>
                        </div>
                        <p className="text-sm font-medium text-foreground">Доступна</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Прогресс */}
                {subject.metrics && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-muted-foreground">Прогресс</span>
                      <span className={`text-sm font-medium ${getProgressColor(subject.metrics.progress_percentage)}`}>
                        {subject.metrics.progress_percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${getProgressBarColor(subject.metrics.progress_percentage)}`}
                        style={{ width: `${subject.metrics.progress_percentage}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Статистика */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 bg-muted/30 rounded-lg">
                    <div className="text-lg font-bold text-foreground">
                      {subject.metrics?.lessons_current || 0}/{subject.metrics?.lessons_total || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Уроки</div>
                  </div>
                  <div className="p-2 bg-muted/30 rounded-lg">
                    <div className="text-lg font-bold text-foreground">
                      {subject.metrics?.homework_rating || '—'}
                    </div>
                    <div className="text-xs text-muted-foreground">Ср. балл ДЗ</div>
                  </div>
                  <div className="p-2 bg-muted/30 rounded-lg">
                    <div className="text-lg font-bold text-foreground">
                      {subject.modules_count}
                    </div>
                    <div className="text-xs text-muted-foreground">Модулей</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Пустые предметы */}
      {emptySubjects.length > 0 && (
        <div>
          <h2 className="text-xl font-heading font-semibold mb-4 flex items-center gap-2 text-muted-foreground">
            <Icon name="CircleStackIcon" size={24} />
            Неактивные предметы ({emptySubjects.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {emptySubjects.map((subject) => (
              <div
                key={subject.subject_key}
                className="bg-muted/30 border border-border rounded-lg p-4 opacity-75"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon name="AcademicCapIcon" size={20} className="text-muted-foreground" />
                  <span className="font-medium text-foreground">{subject.subject_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Нет активных программ</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
