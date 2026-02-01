import React from 'react';
import { ConfidenceOverview } from './ConfidenceOverview';
import { UpcomingExams } from './UpcomingExams';
import { DecayingTopics } from './DecayingTopics';
import { useGraph } from '../../hooks/useGraph';

export const Dashboard: React.FC = () => {
  const { stats, nodesNeedingReview } = useGraph();

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Welcome */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome back! 👋
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Here's your study progress overview
        </p>
      </div>

      {/* Stats Grid */}
      <ConfidenceOverview stats={stats} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <UpcomingExams />
        <DecayingTopics topics={nodesNeedingReview} />
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <h3 className="text-xl font-bold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-lg p-4 transition-colors text-left">
            <div className="text-2xl mb-2">📚</div>
            <div className="font-semibold">Start Study Session</div>
            <div className="text-sm opacity-90">Review your topics</div>
          </button>
          <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-lg p-4 transition-colors text-left">
            <div className="text-2xl mb-2">🎯</div>
            <div className="font-semibold">Take a Quiz</div>
            <div className="text-sm opacity-90">Test your knowledge</div>
          </button>
          <button className="bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-lg p-4 transition-colors text-left">
            <div className="text-2xl mb-2">📅</div>
            <div className="font-semibold">Plan Study Schedule</div>
            <div className="text-sm opacity-90">Generate a study plan</div>
          </button>
        </div>
      </div>
    </div>
  );
};
