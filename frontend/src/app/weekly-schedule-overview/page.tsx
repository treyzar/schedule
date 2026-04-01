import type { Metadata } from 'next';
import Header from '@/components/common/Header';
import TabNavigation from '@/components/common/TabNavigation';
import NavigationBreadcrumb from '@/components/common/NavigationBreadcrumb';
import StatusIndicator from '@/components/common/StatusIndicator';
import QuickActions from '@/components/common/QuickActions';
import WeeklyScheduleInteractive from './components/WeeklyScheduleInteractive';

export const metadata: Metadata = {
  title: 'Недельное расписание - SmartScheduler',
  description:
    'Просматривайте и управляйте своим расписанием на неделю с возможностью перетаскивания событий, фильтрации по категориям и анализа загруженности.',
};

export default function WeeklyScheduleOverviewPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-[60px] pb-20 md:pb-6">
        <div className="container mx-auto px-4 py-6 max-w-7xl">
          <div className="flex items-center justify-between mb-4">
            <NavigationBreadcrumb />
            <div className="flex items-center gap-3">
              <StatusIndicator />
              <QuickActions />
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-3xl font-heading font-bold text-foreground mb-2">
              Недельное расписание
            </h1>
            <p className="text-sm font-body text-muted-foreground">
              Управляйте событиями на неделю с помощью перетаскивания и фильтрации
            </p>
          </div>

          <TabNavigation />

          <div className="mt-6">
            <WeeklyScheduleInteractive />
          </div>
        </div>
      </main>
    </div>
  );
}
