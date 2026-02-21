import React from 'react';
import { AlertTriangle, TrendingDown, RefreshCw } from 'lucide-react';

interface WeakTopicsWidgetProps {
  topics: any[];
  loading?: boolean;
  onRefresh?: () => void;
}

export const WeakTopicsWidget: React.FC<WeakTopicsWidgetProps> = ({ topics, loading, onRefresh }) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence < 0.2) return 'bg-red-500';
    if (confidence < 0.3) return 'bg-orange-500';
    return 'bg-yellow-500';
  };

  // Show top 5 weakest topics
  const topicsToShow = topics.slice(0, 5);

  return (
    <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 border-2 border-red-200 dark:border-red-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle size={24} className="text-red-600 dark:text-red-400" />
          <h3 className="text-lg font-bold text-red-900 dark:text-red-100">
            Topics Needing Attention
          </h3>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw size={16} className="text-red-600 dark:text-red-400" />
          </button>
        )}
      </div>

      {/* Topics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {loading ? (
          [...Array(5)].map((_, i) => (
            <div
              key={i}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-red-200 dark:border-red-800 animate-pulse"
            >
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-3" />
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          ))
        ) : topicsToShow.length === 0 ? (
          <div className="col-span-full bg-white/70 dark:bg-gray-800/70 rounded-lg p-5 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-800 dark:text-red-200">
              No low-confidence topics yet. Start a quiz or study session to build your profile.
            </p>
          </div>
        ) : (
          topicsToShow.map((topic, idx) => (
            <div
              key={idx}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-red-200 dark:border-red-800 hover:shadow-lg transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-gray-900 dark:text-white text-sm truncate group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors">
                    {topic.topic_id || topic.label || 'Unknown Topic'}
                  </h4>
                </div>
                <TrendingDown size={16} className="text-red-500 flex-shrink-0 ml-2" />
              </div>

              {/* Confidence Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">Confidence</span>
                  <span className="font-bold text-red-600 dark:text-red-400">
                    {((topic.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getConfidenceColor(topic.confidence || 0)} transition-all`}
                    style={{ width: `${(topic.confidence || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Call to Action */}
      <div className="mt-4 p-3 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-lg border border-red-200 dark:border-red-800">
        <p className="text-sm text-red-800 dark:text-red-200">
          <strong>{topics.length} topics</strong> below 30% confidence.
          Review these topics to improve retention and exam readiness.
        </p>
      </div>
    </div>
  );
};
