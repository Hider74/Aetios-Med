import React from 'react';
import { TrendingUp, Target, Award, AlertCircle } from 'lucide-react';
import type { GraphStats } from '../../types/curriculum';

interface ConfidenceOverviewProps {
  stats: GraphStats | null;
  curriculumStats?: any;
  loading?: boolean;
}

export const ConfidenceOverview: React.FC<ConfidenceOverviewProps> = ({ stats, curriculumStats, loading }) => {
  // Use curriculum stats from API if available, otherwise fall back to graph stats
  const displayStats = curriculumStats || stats;
  
  if (loading || !displayStats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-6 animate-pulse">
            <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Topics',
      value: displayStats.total_topics || displayStats.totalNodes || 0,
      icon: Target,
      color: 'bg-blue-500',
      change: null,
    },
    {
      title: 'Average Confidence',
      value: `${((displayStats.average_confidence || displayStats.averageConfidence || 0) * 100).toFixed(0)}%`,
      icon: TrendingUp,
      color: 'bg-green-500',
      change: (displayStats.average_confidence || displayStats.averageConfidence || 0) >= 0.6 ? '+5%' : null,
    },
    {
      title: 'Mastered Topics',
      value: displayStats.mastered_count || displayStats.masteredCount || 0,
      icon: Award,
      color: 'bg-purple-500',
      change: null,
    },
    {
      title: 'Need Review',
      value: displayStats.low_confidence_count || displayStats.lowConfidenceCount || 0,
      icon: AlertCircle,
      color: 'bg-red-500',
      change: null,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  {card.title}
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {card.value}
                </p>
                {card.change && (
                  <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                    {card.change} from last week
                  </p>
                )}
              </div>
              <div className={`${card.color} p-3 rounded-lg`}>
                <Icon size={24} className="text-white" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
