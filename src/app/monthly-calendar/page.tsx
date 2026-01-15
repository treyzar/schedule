import type { Metadata } from 'next';
import Header from '@/components/common/Header';
import TabNavigation from '@/components/common/TabNavigation';
import NavigationBreadcrumb from '@/components/common/NavigationBreadcrumb';
import StatusIndicator from '@/components/common/StatusIndicator';
import QuickActions from '@/components/common/QuickActions';
import MonthlyCalendarInteractive from './components/MonthlyCalendarInteractive'; // Убедимся, что путь правильный

export const metadata: Metadata = {
  title: 'Месячный календарь - SmartScheduler',
  description:
    'Просматривайте и управляйте своим расписанием на месяц с визуализацией плотности событий, статистикой и быстрой навигацией по датам.',
};

export default function MonthlyCalendarPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-[60px] pb-20 md:pb-6">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <NavigationBreadcrumb />
            <div className="flex items-center gap-2">
              <StatusIndicator />
              <QuickActions />
            </div>
          </div>

          <div className="mb-6">
            <TabNavigation />
          </div>

          <MonthlyCalendarInteractive />
        </div>
      </main>
    </div>
  );
}
