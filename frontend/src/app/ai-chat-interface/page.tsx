import type { Metadata } from 'next';
import Header from '@/components/common/Header';
import TabNavigation from '@/components/common/TabNavigation';
import NavigationBreadcrumb from '@/components/common/NavigationBreadcrumb';
import StatusIndicator from '@/components/common/StatusIndicator';
import QuickActions from '@/components/common/QuickActions';
import AIChatInteractive from './components/AIChatInteractive';

export const metadata: Metadata = {
  title: 'AI Помощник - SmartScheduler',
  description:
    'Интеллектуальный AI-помощник для управления расписанием, поиска свободного времени, оптимизации задач и анализа использования времени с поддержкой естественного языка.',
};

export default function AIChatInterfacePage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="pt-[60px] pb-[72px] md:pb-0">
        <div className="max-w-[1920px] mx-auto">
          <div className="px-4 md:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between mb-4">
              <NavigationBreadcrumb />
              <div className="flex items-center gap-2">
                <StatusIndicator />
                <QuickActions />
              </div>
            </div>

            <div
              className="bg-card rounded-lg shadow-elevation-md border border-border overflow-hidden"
              style={{ height: 'calc(100vh - 280px)' }}
            >
              <AIChatInteractive />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
