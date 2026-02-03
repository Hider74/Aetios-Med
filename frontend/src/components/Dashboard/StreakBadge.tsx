import React from 'react';
import { Flame } from 'lucide-react';
import { useSettingsStore } from '../../stores/settingsStore';

export const StreakBadge: React.FC = () => {
  const { currentStreak, longestStreak } = useSettingsStore();

  return (
    <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-lg p-6 text-white shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">Study Streak</h3>
        <Flame size={32} className="text-yellow-300" />
      </div>
      
      <div className="space-y-3">
        <div>
          <div className="text-4xl font-bold mb-1">{currentStreak} days</div>
          <div className="text-sm opacity-90">Current streak</div>
        </div>
        
        {longestStreak > 0 && (
          <div className="pt-3 border-t border-white/30">
            <div className="text-lg font-semibold mb-1">{longestStreak} days</div>
            <div className="text-xs opacity-80">Personal best</div>
          </div>
        )}
      </div>
      
      {currentStreak === 0 && (
        <div className="mt-4 text-sm opacity-90 italic">
          Start studying to begin your streak!
        </div>
      )}
      
      {currentStreak > 0 && (
        <div className="mt-4 text-sm opacity-90">
          🔥 Keep it up! Study today to maintain your streak.
        </div>
      )}
    </div>
  );
};
