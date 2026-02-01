import React, { useState, useEffect } from 'react';
import { Calendar, Plus, Edit, Trash2 } from 'lucide-react';
import { format, differenceInDays } from 'date-fns';
import { api } from '../../services/api';
import type { Exam } from '../../types/study';

export const UpcomingExams: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      const data = await api.getExams();
      // Sort by date, soonest first
      const sorted = data.sort((a, b) => a.date.getTime() - b.date.getTime());
      setExams(sorted.slice(0, 5)); // Show only next 5
    } catch (error) {
      console.error('Failed to load exams:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400';
      case 'high': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400';
      case 'medium': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'low': return 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const getDaysUntil = (date: Date) => {
    const days = differenceInDays(date, new Date());
    if (days < 0) return 'Past due';
    if (days === 0) return 'Today!';
    if (days === 1) return 'Tomorrow';
    return `${days} days`;
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar size={20} className="text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Upcoming Exams
          </h3>
        </div>
        <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
          <Plus size={18} />
        </button>
      </div>

      {/* Exams List */}
      {exams.length === 0 ? (
        <div className="text-center py-8">
          <Calendar size={48} className="text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400">No upcoming exams</p>
          <button className="mt-3 text-sm text-blue-500 hover:text-blue-600">
            Add your first exam
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {exams.map((exam) => {
            const daysUntil = getDaysUntil(exam.date);
            const isUrgent = differenceInDays(exam.date, new Date()) <= 7;

            return (
              <div
                key={exam.id}
                className={`
                  p-4 rounded-lg border-2 transition-all hover:shadow-md
                  ${isUrgent 
                    ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10' 
                    : 'border-gray-200 dark:border-gray-700'
                  }
                `}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {exam.name}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {format(exam.date, 'MMMM dd, yyyy')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(exam.priority)}`}>
                      {exam.priority}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className={`text-sm font-medium ${isUrgent ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-400'}`}>
                      {daysUntil}
                    </span>
                    <span className="text-xs text-gray-500">
                      {exam.topics.length} topics
                    </span>
                  </div>
                  <div className="flex gap-1">
                    <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
                      <Edit size={14} />
                    </button>
                    <button className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded text-red-600">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
