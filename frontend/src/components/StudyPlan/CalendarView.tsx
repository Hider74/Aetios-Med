import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, isSameDay, addMonths, subMonths } from 'date-fns';
import type { StudyTask } from '../../types/study';

interface CalendarViewProps {
  tasks?: StudyTask[];
  onTaskClick?: (task: StudyTask) => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({ tasks = [], onTaskClick }) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // Group tasks by date
  const tasksByDate = new Map<string, StudyTask[]>();
  tasks.forEach(task => {
    const dateKey = format(task.scheduledDate, 'yyyy-MM-dd');
    if (!tasksByDate.has(dateKey)) {
      tasksByDate.set(dateKey, []);
    }
    tasksByDate.get(dateKey)!.push(task);
  });

  const getTasksForDay = (day: Date): StudyTask[] => {
    const dateKey = format(day, 'yyyy-MM-dd');
    return tasksByDate.get(dateKey) || [];
  };

  const goToPreviousMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const goToNextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white">
          {format(currentMonth, 'MMMM yyyy')}
        </h3>
        <div className="flex gap-2">
          <button
            onClick={goToPreviousMonth}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-2">
        {/* Day Headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="text-center text-sm font-semibold text-gray-600 dark:text-gray-400 py-2">
            {day}
          </div>
        ))}

        {/* Calendar Days */}
        {daysInMonth.map((day) => {
          const dayTasks = getTasksForDay(day);
          const isCurrentDay = isToday(day);
          const completedTasks = dayTasks.filter(t => t.completed).length;

          return (
            <div
              key={day.toISOString()}
              className={`
                min-h-24 p-2 rounded-lg border transition-all
                ${isCurrentDay 
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                  : 'border-gray-200 dark:border-gray-700'
                }
                ${dayTasks.length > 0 ? 'hover:shadow-md cursor-pointer' : ''}
              `}
            >
              <div className={`
                text-sm font-medium mb-1
                ${isCurrentDay ? 'text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white'}
              `}>
                {format(day, 'd')}
              </div>

              {/* Task Indicators */}
              {dayTasks.length > 0 && (
                <div className="space-y-1">
                  {dayTasks.slice(0, 3).map((task, idx) => (
                    <div
                      key={task.id}
                      onClick={() => onTaskClick?.(task)}
                      className={`
                        text-xs p-1 rounded truncate
                        ${task.completed 
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400 line-through' 
                          : 'bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400'
                        }
                      `}
                    >
                      {task.topicName}
                    </div>
                  ))}
                  {dayTasks.length > 3 && (
                    <div className="text-xs text-gray-500 text-center">
                      +{dayTasks.length - 3} more
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-purple-100 dark:bg-purple-900/20 rounded" />
          <span className="text-gray-600 dark:text-gray-400">Scheduled</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-100 dark:bg-green-900/20 rounded" />
          <span className="text-gray-600 dark:text-gray-400">Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 rounded" />
          <span className="text-gray-600 dark:text-gray-400">Today</span>
        </div>
      </div>
    </div>
  );
};
