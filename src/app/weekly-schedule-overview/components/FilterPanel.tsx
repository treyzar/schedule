'use client';

import { useState } from 'react';
import Icon from '@/components/ui/AppIcon';

interface FilterOptions {
  categories: string[];
  sources: string[];
  priorities: string[];
}

interface FilterPanelProps {
  filters: FilterOptions;
  activeFilters: {
    categories: string[];
    sources: string[];
    priorities: string[];
  };
  onFilterChange: (type: string, value: string) => void;
}

const FilterPanel = ({ filters, activeFilters, onFilterChange }: FilterPanelProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const categoryColors: Record<string, string> = {
    Работа: 'bg-primary',
    Личное: 'bg-secondary',
    Встречи: 'bg-accent',
    Обучение: 'bg-warning',
  };

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-muted transition-smooth"
      >
        <div className="flex items-center gap-2">
          <Icon name="FunnelIcon" size={20} className="text-muted-foreground" />
          <span className="text-sm font-heading font-semibold text-foreground">Фильтры</span>
          {(activeFilters.categories.length > 0 ||
            activeFilters.sources.length > 0 ||
            activeFilters.priorities.length > 0) && (
            <span className="px-2 py-0.5 text-xs font-caption bg-primary text-primary-foreground rounded-full">
              {activeFilters.categories.length +
                activeFilters.sources.length +
                activeFilters.priorities.length}
            </span>
          )}
        </div>
        <Icon
          name={isExpanded ? 'ChevronUpIcon' : 'ChevronDownIcon'}
          size={20}
          className="text-muted-foreground"
        />
      </button>

      {isExpanded && (
        <div className="p-4 border-t border-border space-y-4">
          <div>
            <p className="text-sm font-heading font-semibold text-foreground mb-2">Категории</p>
            <div className="flex flex-wrap gap-2">
              {filters.categories.map((category) => (
                <button
                  key={category}
                  onClick={() => onFilterChange('categories', category)}
                  className={`
                    flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-body transition-smooth
                    ${
                      activeFilters.categories.includes(category)
                        ? `${categoryColors[category] || 'bg-primary'} text-white`
                        : 'bg-muted text-foreground hover:bg-muted/80'
                    }
                  `}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-heading font-semibold text-foreground mb-2">Источники</p>
            <div className="flex flex-wrap gap-2">
              {filters.sources.map((source) => (
                <button
                  key={source}
                  onClick={() => onFilterChange('sources', source)}
                  className={`
                    flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-body transition-smooth
                    ${
                      activeFilters.sources.includes(source)
                        ? 'bg-secondary text-secondary-foreground'
                        : 'bg-muted text-foreground hover:bg-muted/80'
                    }
                  `}
                >
                  <Icon name="CheckCircleIcon" size={16} />
                  {source}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-heading font-semibold text-foreground mb-2">Приоритет</p>
            <div className="flex flex-wrap gap-2">
              {filters.priorities.map((priority) => (
                <button
                  key={priority}
                  onClick={() => onFilterChange('priorities', priority)}
                  className={`
                    flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-body transition-smooth
                    ${
                      activeFilters.priorities.includes(priority)
                        ? 'bg-accent text-accent-foreground'
                        : 'bg-muted text-foreground hover:bg-muted/80'
                    }
                  `}
                >
                  {priority}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;
