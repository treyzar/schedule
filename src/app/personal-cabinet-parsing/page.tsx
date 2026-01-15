import type { Metadata } from 'next';
import Header from '@/components/common/Header';
import TabNavigation from '@/components/common/TabNavigation';
import NavigationBreadcrumb from '@/components/common/NavigationBreadcrumb';
import StatusIndicator from '@/components/common/StatusIndicator';
import QuickActions from '@/components/common/QuickActions';
import ParsingInteractive from './components/ParsingInteractive';

export const metadata: Metadata = {
  title: 'Парсинг личного кабинета - SmartScheduler',
  description:
    'Настройка и мониторинг интеграций календарей для автоматической синхронизации расписания из различных источников',
};

export default function PersonalCabinetParsingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-[60px] pb-20 md:pb-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <NavigationBreadcrumb />
            <div className="flex items-center gap-3">
              <StatusIndicator />
              <QuickActions />
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-3xl font-heading font-bold text-foreground mb-2">
              Парсинг личного кабинета
            </h1>
            <p className="text-base font-body text-muted-foreground">
              Управление источниками календарей и настройка автоматической синхронизации расписания
            </p>
          </div>

          <TabNavigation />

          <div className="mt-6">
            <ParsingInteractive />
          </div>
        </div>
      </main>
    </div>
  );
}
