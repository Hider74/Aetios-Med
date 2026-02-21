import React, { useEffect, useState } from 'react';
import { ConfidenceOverview } from './ConfidenceOverview';
import { UpcomingExams } from './UpcomingExams';
import { DecayingTopics } from './DecayingTopics';
import { AnkiCardsDue } from './AnkiCardsDue';
import { StreakBadge } from './StreakBadge';
import { DailyGoals } from './DailyGoals';
import { WeakTopicsWidget } from './WeakTopicsWidget';
import { useGraph } from '../../hooks/useGraph';
import api from '../../services/api';
import { Zap } from 'lucide-react';

interface DashboardProps {
  onNavigate?: (page: string) => void;
  onQuickStudy?: (topic: string) => void;
  onStartQuiz?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate, onQuickStudy, onStartQuiz }) => {
  const { stats, nodesNeedingReview } = useGraph();
  const [showNoTopicsMessage, setShowNoTopicsMessage] = useState(false);
  const [curriculumStats, setCurriculumStats] = useState<any>(null);
  const [weakTopics, setWeakTopics] = useState<any[]>([]);
  const [decayingTopics, setDecayingTopics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch dashboard data on mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [curriculum, weak, decaying] = await Promise.all([
          api.getCurriculumOverview(),
          api.getWeakTopics(0.3),
          api.getDecayingTopics(7),
        ]);
        setCurriculumStats(curriculum);
        setWeakTopics(weak);
        setDecayingTopics(decaying);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  const handleQuickStudy = () => {
    // Find the weakest topic
    const weakestTopic = nodesNeedingReview[0];
    
    if (!weakestTopic) {
      // If no topics need review, show inline message
      setShowNoTopicsMessage(true);
      setTimeout(() => setShowNoTopicsMessage(false), 3000);
      return;
    }

    // Call the callback to navigate and start study
    if (onQuickStudy) {
      onQuickStudy(weakestTopic.label);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Welcome and Quick Study */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome back! 👋
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Here's your study progress overview
          </p>
        </div>
        
        {/* Quick Study Button */}
        <div className="flex flex-col items-end gap-2">
          <button
            onClick={handleQuickStudy}
            disabled={nodesNeedingReview.length === 0}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
          >
            <Zap size={20} />
            <span>Quick Study</span>
          </button>
          
          {/* Success message */}
          {showNoTopicsMessage && (
            <div className="px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-lg text-sm animate-fade-in">
              🎉 Great job! No topics need immediate review.
            </div>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <ConfidenceOverview stats={stats} curriculumStats={curriculumStats} loading={loading} />

      {/* Weak Topics Alert */}
      <WeakTopicsWidget
        topics={weakTopics}
        loading={loading}
        onRefresh={() => api.getWeakTopics(0.3).then(setWeakTopics)}
      />

      {/* Streak and Daily Goals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StreakBadge />
        <DailyGoals />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <UpcomingExams />
        <DecayingTopics topics={decayingTopics} loading={loading} onRefresh={() => api.getDecayingTopics(7).then(setDecayingTopics)} />
        <AnkiCardsDue />
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <h3 className="text-xl font-bold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate?.('study')}
            className="bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-lg p-4 transition-colors text-left"
          >
            <div className="text-2xl mb-2">📚</div>
            <div className="font-semibold">Start Study Session</div>
            <div className="text-sm opacity-90">Review your topics</div>
          </button>
          <button
            onClick={() => (onStartQuiz ? onStartQuiz() : onNavigate?.('quiz'))}
            className="bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-lg p-4 transition-colors text-left"
          >
            <div className="text-2xl mb-2">🎯</div>
            <div className="font-semibold">Take a Quiz</div>
            <div className="text-sm opacity-90">Test your knowledge</div>
          </button>
          <button
            onClick={() => onNavigate?.('study')}
            className="bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-lg p-4 transition-colors text-left"
          >
            <div className="text-2xl mb-2">📅</div>
            <div className="font-semibold">Plan Study Schedule</div>
            <div className="text-sm opacity-90">Generate a study plan</div>
          </button>
        </div>
      </div>
    </div>
  );
};
