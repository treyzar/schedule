import type { Metadata } from 'next';
import Header from '@/components/common/Header';
import TabNavigation from '@/components/common/TabNavigation';
import NavigationBreadcrumb from '@/components/common/NavigationBreadcrumb';
import StatusIndicator from '@/components/common/StatusIndicator';
import QuickActions from '@/components/common/QuickActions';
import DailyScheduleInteractive from './components/DailyScheduleInteractive';

export const metadata: Metadata = {
  title: 'Дневное расписание - SmartScheduler',
  description:
    'Управляйте своим дневным расписанием с детальным почасовым планированием, настройкой рабочих часов и автоматической оптимизацией задач с помощью AI.',
};

export default function DailyScheduleConfigPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-[60px] pb-20 md:pb-6">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <NavigationBreadcrumb />
            <div className="flex items-center gap-3">
              <StatusIndicator />
              <QuickActions />
            </div>
          </div>

          <div className="mb-6">
            <TabNavigation />
          </div>

          <DailyScheduleInteractive />
        </div>
      </main>
    </div>
  );
}
