'use client';

import { useState } from 'react';
import Icon from '@/components/ui/AppIcon';

interface ConfigOption {
  id: string;
  label: string;
  description: string;
  value: string | number | boolean;
  type: 'select' | 'number' | 'toggle';
  options?: { label: string; value: string }[];
}

interface ConfigSection {
  title: string;
  icon: string;
  options: ConfigOption[];
}

interface ConfigurationPanelProps {
  sections: ConfigSection[];
  onUpdate: (optionId: string, value: any) => void;
}

export default function ConfigurationPanel({ sections, onUpdate }: ConfigurationPanelProps) {
  const [isHydrated, setIsHydrated] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>([sections[0]?.title]);

  useState(() => {
    setIsHydrated(true);
  });

  const toggleSection = (title: string) => {
    setExpandedSections((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]
    );
  };

  if (!isHydrated) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-elevation-sm">
        <h2 className="text-lg font-heading font-semibold text-foreground mb-4">
          Настройки парсинга
        </h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border border-border rounded-lg p-4">
              <div className="h-5 w-48 bg-muted rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-elevation-sm">
      <h2 className="text-lg font-heading font-semibold text-foreground mb-4">
        Настройки парсинга
      </h2>
      <div className="space-y-3">
        {sections.map((section) => {
          const isExpanded = expandedSections.includes(section.title);
          return (
            <div key={section.title} className="border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection(section.title)}
                className="w-full flex items-center justify-between p-4 hover:bg-muted transition-smooth"
              >
                <div className="flex items-center gap-3">
                  <Icon name={section.icon as any} size={20} className="text-primary" />
                  <span className="text-sm font-body font-medium text-foreground">
                    {section.title}
                  </span>
                </div>
                <Icon
                  name="ChevronDownIcon"
                  size={20}
                  className={`text-muted-foreground transition-smooth ${
                    isExpanded ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {isExpanded && (
                <div className="p-4 pt-0 space-y-4">
                  {section.options.map((option) => (
                    <div key={option.id} className="space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <label className="text-sm font-body font-medium text-foreground">
                            {option.label}
                          </label>
                          <p className="text-xs font-caption text-muted-foreground mt-1">
                            {option.description}
                          </p>
                        </div>

                        {option.type === 'toggle' && (
                          <button
                            onClick={() => onUpdate(option.id, !option.value)}
                            className={`
                              relative w-12 h-6 rounded-full transition-smooth ml-4
                              ${option.value ? 'bg-primary' : 'bg-muted'}
                            `}
                            aria-label={option.label}
                          >
                            <span
                              className={`
                                absolute top-1 w-4 h-4 rounded-full bg-white shadow-elevation-sm transition-smooth
                                ${option.value ? 'left-7' : 'left-1'}
                              `}
                            />
                          </button>
                        )}
                      </div>

                      {option.type === 'select' && option.options && (
                        <select
                          value={option.value as string}
                          onChange={(e) => onUpdate(option.id, e.target.value)}
                          className="w-full px-3 py-2 bg-background border border-input rounded-lg text-sm font-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
                        >
                          {option.options.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      )}

                      {option.type === 'number' && (
                        <input
                          type="number"
                          value={option.value as number}
                          onChange={(e) => onUpdate(option.id, parseInt(e.target.value))}
                          className="w-full px-3 py-2 bg-background border border-input rounded-lg text-sm font-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
