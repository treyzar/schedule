'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Icon from '@/components/ui/AppIcon';

export default function Home() {
  const router = useRouter();
  const { is_authenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (is_authenticated) {
        // Авторизованные пользователи идут на главную страницу расписания
        router.push('/daily-schedule-config');
      } else {
        // Неавторизованные - на страницу авторизации
        router.push('/google-auth');
      }
    }
  }, [is_authenticated, isLoading, router]);

  // Показываем лоадер во время редиректа
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center">
        <Icon name="ArrowPathIcon" size={48} className="animate-spin text-primary mx-auto mb-4" />
        <h1 className="text-xl font-heading font-semibold text-foreground mb-2">
          SmartScheduler
        </h1>
        <p className="text-muted-foreground">Загрузка...</p>
      </div>
    </div>
  );
}
