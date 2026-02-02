import React, { useState, useEffect } from 'react';
import { CreditCard, Play, AlertTriangle } from 'lucide-react';

interface AnkiCardsDueData {
  total: number;
  byTopic: Array<{
    topic: string;
    count: number;
  }>;
}

export const AnkiCardsDue: React.FC = () => {
  const [data, setData] = useState<AnkiCardsDueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnkiDue();
  }, []);

  const loadAnkiDue = async () => {
    try {
      const response = await fetch('http://localhost:8741/api/ingest/anki/due');
      if (!response.ok) {
        throw new Error('Failed to fetch Anki cards due');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Failed to load Anki cards due:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewNow = () => {
    // TODO: Navigate to Anki review interface
    console.log('Starting Anki review session...');
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard size={20} className="text-purple-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Anki Cards Due
          </h3>
        </div>
        <div className="text-center py-4">
          <AlertTriangle size={48} className="text-red-300 dark:text-red-600 mx-auto mb-3" />
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <CreditCard size={20} className="text-purple-500" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Anki Cards Due
        </h3>
      </div>

      {/* Total Count */}
      <div className="mb-6">
        <div className="text-4xl font-bold text-gray-900 dark:text-white mb-1">
          {data?.total || 0}
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          cards due today
        </div>
      </div>

      {/* Breakdown by Topic */}
      {data && data.byTopic.length > 0 ? (
        <div className="space-y-3 mb-6 max-h-64 overflow-y-auto">
          {data.byTopic.slice(0, 5).map((item, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600"
            >
              <span className="text-sm font-medium text-gray-900 dark:text-white truncate flex-1 mr-2">
                {item.topic}
              </span>
              <span className="text-sm font-semibold text-purple-600 dark:text-purple-400 whitespace-nowrap">
                {item.count} cards
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-6 mb-6">
          <CreditCard size={48} className="text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400">No cards due today</p>
        </div>
      )}

      {/* Review Button */}
      {data && data.total > 0 && (
        <button
          onClick={handleReviewNow}
          className="w-full py-3 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Play size={18} />
          Review Now
        </button>
      )}
    </div>
  );
};
