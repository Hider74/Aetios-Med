import React, { useState } from 'react';
import { CheckCircle, XCircle, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import type { SAQQuestion, SAQResult } from '../../types/study';

interface SAQInputProps {
  question: SAQQuestion;
  quizId: string;
  questionId: string;
  onSubmit: (answer: string) => Promise<SAQResult>;
}

export const SAQInput: React.FC<SAQInputProps> = ({ question, quizId, questionId, onSubmit }) => {
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<SAQResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showModelAnswer, setShowModelAnswer] = useState(false);

  const handleSubmit = async () => {
    if (!answer.trim()) return;
    
    setIsSubmitting(true);
    try {
      const markingResult = await onSubmit(answer);
      setResult(markingResult);
    } catch (error) {
      console.error('Failed to submit SAQ answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const wordCount = answer.trim().split(/\s+/).filter(w => w).length;
  const charCount = answer.length;

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6 border-2 border-blue-200 dark:border-blue-800">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
          <FileText size={20} className="text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-1">Short Answer Question (SAQ)</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Topic: {question.topic_id} • {question.marks} marks • {question.difficulty}
          </p>
        </div>
      </div>

      {/* Question */}
      <div className="mb-4">
        <p className="text-lg font-medium text-gray-900 dark:text-white">
          {question.question}
        </p>
      </div>

      {/* Answer Input */}
      {!result && (
        <div className="mb-4">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer here..."
            disabled={isSubmitting}
            rows={8}
            className="w-full p-4 border-2 border-gray-300 dark:border-gray-700 rounded-lg 
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                     focus:border-blue-500 focus:outline-none resize-y"
          />
          <div className="flex justify-between items-center mt-2 text-sm text-gray-600 dark:text-gray-400">
            <span>{wordCount} words • {charCount} characters</span>
          </div>
        </div>
      )}

      {/* Submit Button */}
      {!result && (
        <button
          onClick={handleSubmit}
          disabled={!answer.trim() || isSubmitting}
          className="w-full py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 
                   disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isSubmitting ? 'Marking...' : 'Submit Answer'}
        </button>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Score Summary */}
          <div className={`
            p-4 rounded-lg border-2
            ${result.percentage >= 70 
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
              : result.percentage >= 50
              ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
              : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
            }
          `}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                {result.percentage >= 70 ? (
                  <CheckCircle size={24} className="text-green-600" />
                ) : (
                  <XCircle size={24} className={result.percentage >= 50 ? "text-yellow-600" : "text-red-600"} />
                )}
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  {result.score} / {result.max_score}
                </span>
              </div>
              <span className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                {result.percentage.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Key Points Assessment */}
          <div className="space-y-2">
            <h5 className="font-semibold text-gray-900 dark:text-white">Mark Breakdown:</h5>
            {result.key_points_assessment.map((kp, idx) => (
              <div 
                key={idx}
                className={`
                  p-3 rounded-lg border-l-4
                  ${kp.awarded 
                    ? 'bg-green-50 dark:bg-green-900/10 border-green-500' 
                    : 'bg-red-50 dark:bg-red-900/10 border-red-500'
                  }
                `}
              >
                <div className="flex items-start gap-2">
                  {kp.awarded ? (
                    <CheckCircle size={18} className="text-green-600 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {kp.key_point}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {kp.student_evidence}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Feedback */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
            <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Examiner Feedback:</h5>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {result.feedback}
            </p>
          </div>

          {/* Areas to Review */}
          {result.areas_to_review && result.areas_to_review.length > 0 && (
            <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-200 dark:border-purple-800">
              <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Areas to Review:</h5>
              <div className="flex flex-wrap gap-2">
                {result.areas_to_review.map((area, idx) => (
                  <span 
                    key={idx}
                    className="px-3 py-1 bg-purple-200 dark:bg-purple-800 text-purple-900 dark:text-purple-100 
                             rounded-full text-sm font-medium"
                  >
                    {area}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Model Answer (Expandable) */}
          <div className="border-2 border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowModelAnswer(!showModelAnswer)}
              className="w-full p-4 flex items-center justify-between bg-gray-50 dark:bg-gray-800 
                       hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <span className="font-semibold text-gray-900 dark:text-white">
                View Model Answer
              </span>
              {showModelAnswer ? (
                <ChevronUp size={20} className="text-gray-600 dark:text-gray-400" />
              ) : (
                <ChevronDown size={20} className="text-gray-600 dark:text-gray-400" />
              )}
            </button>
            {showModelAnswer && (
              <div className="p-4 bg-white dark:bg-gray-900">
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {result.model_answer}
                </p>
              </div>
            )}
          </div>

          {/* Student's Answer (for reference) */}
          <div className="border-2 border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Your Answer:</h5>
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {answer}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
