'use client';

import { useState } from 'react';
import Icon from '@/components/ui/AppIcon';

interface StatItem {
  label: string;
  value: string | number;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

interface ParsingStatsProps {
  stats: StatItem[];
}

export default function ParsingStats({ stats }: ParsingStatsProps) {
  const [isHydrated, setIsHydrated] = useState(false);

  useState(() => {
    setIsHydrated(true);
  });

  const getTrendColor = (trend?: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return 'text-success';
      case 'down':
        return 'text-error';
      case 'neutral':
        return 'text-muted-foreground';
      default:
        return 'text-muted-foreground';
    }
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return 'ArrowTrendingUpIcon';
      case 'down':
        return 'ArrowTrendingDownIcon';
      default:
        return 'MinusIcon';
    }
  };

  if (!isHydrated) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-elevation-sm">
        <h2 className="text-lg font-heading font-semibold text-foreground mb-4">
          Статистика парсинга
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-4 bg-muted rounded-lg">
              <div className="h-4 w-24 bg-background rounded mb-2" />
              <div className="h-8 w-16 bg-background rounded mb-2" />
              <div className="h-3 w-20 bg-background rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-elevation-sm">
      <h2 className="text-lg font-heading font-semibold text-foreground mb-4">
        Статистика парсинга
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="p-4 bg-muted rounded-lg hover:shadow-elevation-sm transition-smooth"
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon name={stat.icon as any} size={20} className="text-primary" />
              <span className="text-sm font-caption text-muted-foreground">{stat.label}</span>
            </div>
            <p className="text-2xl font-heading font-bold text-foreground mb-1">{stat.value}</p>
            {stat.trend && stat.trendValue && (
              <div className="flex items-center gap-1">
                <Icon
                  name={getTrendIcon(stat.trend) as any}
                  size={14}
                  className={getTrendColor(stat.trend)}
                />
                <span className={`text-xs font-caption ${getTrendColor(stat.trend)}`}>
                  {stat.trendValue}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
