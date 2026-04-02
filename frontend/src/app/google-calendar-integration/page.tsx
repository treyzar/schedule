import type { Metadata } from 'next';
import Header from '@/components/common/Header';
import TabNavigation from '@/components/common/TabNavigation';
import NavigationBreadcrumb from '@/components/common/NavigationBreadcrumb';
import StatusIndicator from '@/components/common/StatusIndicator';
import QuickActions from '@/components/common/QuickActions';
import GoogleCalendarIntegrationInteractive from './components/GoogleCalendarIntegrationInteractive';

export const metadata: Metadata = {
  title: 'Интеграция Google Calendar - SmartScheduler',
  description:
    'Подключите Google Calendar для автоматической синхронизации событий, настройте параметры синхронизации и управляйте календарями в SmartScheduler.',
};

export default function GoogleCalendarIntegrationPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-[60px] pb-20 md:pb-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <NavigationBreadcrumb />
            <div className="flex items-center gap-3">
              <StatusIndicator />
              <QuickActions />
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-3xl font-heading font-bold text-foreground mb-2">
              Интеграция Google Calendar
            </h1>
            <p className="text-muted-foreground">
              Подключите свой Google Calendar для автоматической синхронизации событий и управления
              расписанием в одном месте
            </p>
          </div>

          <GoogleCalendarIntegrationInteractive />
        </div>
      </main>

    </div>
  );
}
