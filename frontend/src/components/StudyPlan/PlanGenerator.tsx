import React, { useState } from 'react';
import { Calendar as CalendarIcon, Sparkles, Download } from 'lucide-react';
import { api } from '../../services/api';
import type { Exam, StudyPlan } from '../../types/study';

export const PlanGenerator: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExam, setSelectedExam] = useState<string>('');
  const [dailyGoal, setDailyGoal] = useState(120);
  const [generating, setGenerating] = useState(false);
  const [generatedPlan, setGeneratedPlan] = useState<StudyPlan | null>(null);

  React.useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    const data = await api.getExams();
    setExams(data.filter(e => !e.completed));
  };

  const handleGenerate = async () => {
    if (!selectedExam) return;
    
    setGenerating(true);
    try {
      const plan = await api.generateStudyPlan(selectedExam, {
        dailyGoalMinutes: dailyGoal,
      });
      setGeneratedPlan(plan);
    } catch (error) {
      console.error('Failed to generate plan:', error);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles size={24} className="text-purple-500" />
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            Generate Study Plan
          </h3>
        </div>

        <div className="space-y-4">
          {/* Exam Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Exam
            </label>
            <select
              value={selectedExam}
              onChange={(e) => setSelectedExam(e.target.value)}
              className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Choose an exam...</option>
              {exams.map(exam => (
                <option key={exam.id} value={exam.id}>
                  {exam.name} - {new Date(exam.date).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          {/* Daily Goal */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Daily Study Goal: {dailyGoal} minutes
            </label>
            <input
              type="range"
              min="30"
              max="480"
              step="30"
              value={dailyGoal}
              onChange={(e) => setDailyGoal(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>30 min</span>
              <span>8 hours</span>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={!selectedExam || generating}
            className="w-full py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all font-medium flex items-center justify-center gap-2"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Generate Smart Study Plan
              </>
            )}
          </button>
        </div>
      </div>

      {/* Generated Plan Preview */}
      {generatedPlan && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
              {generatedPlan.name}
            </h4>
            <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2">
              <Download size={16} />
              Export to Calendar
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <div className="text-2xl font-bold text-blue-500">{generatedPlan.tasks.length}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Tasks</div>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <div className="text-2xl font-bold text-green-500">
                {Math.round((generatedPlan.progress || 0) * 100)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Progress</div>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <div className="text-2xl font-bold text-purple-500">
                {Math.ceil((generatedPlan.endDate.getTime() - generatedPlan.startDate.getTime()) / (1000 * 60 * 60 * 24))}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Days</div>
            </div>
          </div>

          <div className="text-sm text-gray-600 dark:text-gray-400">
            View full plan in the Calendar tab
          </div>
        </div>
      )}
    </div>
  );
};
