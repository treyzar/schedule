'use client';

import Icon from '@/components/ui/AppIcon';

const TypingIndicator = () => {
  return (
    <div className="flex gap-3 mb-4">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary flex items-center justify-center">
        <Icon name="SparklesIcon" size={20} className="text-primary-foreground" />
      </div>

      <div className="bg-card border border-border rounded-lg p-4 shadow-elevation-sm">
        <div className="flex gap-1.5">
          <div
            className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <div
            className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
