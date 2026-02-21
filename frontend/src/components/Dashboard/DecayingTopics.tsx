import React from 'react';
import { AlertTriangle, TrendingDown, Clock, RefreshCw } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { TopicNode } from '../../types/curriculum';

interface DecayingTopicsProps {
  topics: any[];
  loading?: boolean;
  onRefresh?: () => void;
}

// Note: This component displays topics needing review based on FSRS-predicted retention
// data from the backend RetentionService. The confidence values are calculated using
// the FSRS (Free Spaced Repetition Scheduler) algorithm which predicts memory retention.

export const DecayingTopics: React.FC<DecayingTopicsProps> = ({ topics, loading, onRefresh }) => {
  const getUrgencyColor = (confidence: number) => {
    if (confidence < 0.3) return 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400';
    if (confidence < 0.5) return 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400';
    return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
  };

  const getUrgencyLabel = (confidence: number) => {
    if (confidence < 0.3) return 'Critical';
    if (confidence < 0.5) return 'High';
    return 'Medium';
  };

  // Show top 10 topics needing review
  const topicsToShow = topics.slice(0, 10);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingDown size={20} className="text-orange-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Topics Needing Review
          </h3>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw size={16} className={`text-orange-500 ${loading ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>

      {/* Topics List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="p-4 rounded-lg bg-gray-100 dark:bg-gray-700 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : topicsToShow.length === 0 ? (
        <div className="text-center py-8">
          <AlertTriangle size={48} className="text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400">
            Great job! No topics need urgent review.
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {topicsToShow.map((topic, idx) => (
            <div
              key={topic.topic_id || topic.id || idx}
              className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {topic.topic_id || topic.label || 'Unknown Topic'}
                  </h4>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock size={14} className="text-gray-400" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {topic.days_since_review 
                        ? `${topic.days_since_review} days since review`
                        : topic.lastReviewed
                          ? `Last reviewed ${formatDistanceToNow(topic.lastReviewed, { addSuffix: true })}`
                          : 'Never reviewed'
                      }
                    </span>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getUrgencyColor(topic.confidence || 0)}`}>
                  {getUrgencyLabel(topic.confidence || 0)}
                </span>
              </div>

              {/* Confidence Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">Confidence</span>
                  <span className="font-semibold">{((topic.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      (topic.confidence || 0) < 0.3 ? 'bg-red-500' :
                      (topic.confidence || 0) < 0.5 ? 'bg-orange-500' :
                      (topic.confidence || 0) < 0.7 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${(topic.confidence || 0) * 100}%` }}
                  />
                </div>
              </div>

              {/* Times Reviewed */}
              <div className="mt-2 text-xs text-gray-500">
                Reviewed {topic.timesReviewed} {topic.timesReviewed === 1 ? 'time' : 'times'}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      {topicsToShow.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button className="w-full py-2 text-sm text-blue-500 hover:text-blue-600 font-medium">
            View All Topics ({topics.length})
          </button>
        </div>
      )}
    </div>
  );
};
