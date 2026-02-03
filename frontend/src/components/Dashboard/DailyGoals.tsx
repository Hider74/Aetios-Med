import React, { useEffect } from 'react';
import { Target, BookOpen, Brain } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';

export const DailyGoals: React.FC = () => {
  const {
    dailyGoalTopics,
    dailyGoalQuizzes,
    topicsReviewedToday,
    quizzesCompletedToday,
    checkAndResetDailyGoals,
  } = useSettingsStore();

  // Check and reset daily goals on mount and periodically
  useEffect(() => {
    checkAndResetDailyGoals();
    
    // Check every hour
    const interval = setInterval(() => {
      checkAndResetDailyGoals();
    }, 60 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [checkAndResetDailyGoals]);

  const topicsProgress = Math.min((topicsReviewedToday / dailyGoalTopics) * 100, 100);
  const quizzesProgress = Math.min((quizzesCompletedToday / dailyGoalQuizzes) * 100, 100);
  const overallProgress = (topicsProgress + quizzesProgress) / 2;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Target size={24} className="text-blue-500" />
          Daily Goals
        </h3>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {overallProgress === 100 ? '🎉 Complete!' : `${Math.round(overallProgress)}%`}
        </div>
      </div>

      <div className="space-y-4">
        {/* Topics Goal */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <BookOpen size={18} className="text-purple-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Topics Reviewed
              </span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {topicsReviewedToday} / {dailyGoalTopics}
            </span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
              style={{ width: `${topicsProgress}%` }}
            />
          </div>
        </div>

        {/* Quizzes Goal */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain size={18} className="text-green-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Quizzes Completed
              </span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {quizzesCompletedToday} / {dailyGoalQuizzes}
            </span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
              style={{ width: `${quizzesProgress}%` }}
            />
          </div>
        </div>

        {/* Motivational message */}
        {overallProgress === 100 && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg text-sm text-green-700 dark:text-green-400 text-center">
            🎉 Amazing work! You've hit all your goals today!
          </div>
        )}
        
        {overallProgress > 0 && overallProgress < 100 && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-700 dark:text-blue-400 text-center">
            💪 Keep going! You're making great progress!
          </div>
        )}
        
        {overallProgress === 0 && (
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm text-gray-700 dark:text-gray-400 text-center">
            🚀 Start studying to work towards your daily goals!
          </div>
        )}
      </div>
    </div>
  );
};
