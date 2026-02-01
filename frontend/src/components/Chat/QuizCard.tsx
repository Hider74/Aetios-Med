import React, { useState } from 'react';
import { CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import type { QuizData } from '../../types/chat';

interface QuizCardProps {
  quiz: QuizData;
  onAnswer: (answer: number) => void;
}

export const QuizCard: React.FC<QuizCardProps> = ({ quiz, onAnswer }) => {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (selectedAnswer !== null) {
      onAnswer(selectedAnswer);
      setSubmitted(true);
    }
  };

  const isCorrect = submitted && selectedAnswer === quiz.correctAnswer;
  const isIncorrect = submitted && selectedAnswer !== quiz.correctAnswer;

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg p-6 border-2 border-purple-200 dark:border-purple-800">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
          <HelpCircle size={20} className="text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-1">Quiz Question</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">Topic: {quiz.topic}</p>
        </div>
      </div>

      {/* Question */}
      <p className="text-lg font-medium text-gray-900 dark:text-white mb-4">
        {quiz.question}
      </p>

      {/* Options */}
      <div className="space-y-2 mb-4">
        {quiz.options.map((option, idx) => {
          const isSelected = selectedAnswer === idx;
          const isCorrectOption = idx === quiz.correctAnswer;
          
          let optionClass = 'border-gray-300 dark:border-gray-700 hover:border-purple-500';
          if (submitted) {
            if (isCorrectOption) {
              optionClass = 'border-green-500 bg-green-50 dark:bg-green-900/20';
            } else if (isSelected && !isCorrectOption) {
              optionClass = 'border-red-500 bg-red-50 dark:bg-red-900/20';
            }
          } else if (isSelected) {
            optionClass = 'border-purple-500 bg-purple-50 dark:bg-purple-900/20';
          }

          return (
            <button
              key={idx}
              onClick={() => !submitted && setSelectedAnswer(idx)}
              disabled={submitted}
              className={`
                w-full p-4 text-left border-2 rounded-lg transition-all
                ${optionClass}
                ${submitted ? 'cursor-default' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div className={`
                    w-6 h-6 rounded-full border-2 flex items-center justify-center
                    ${isSelected ? 'border-purple-500 bg-purple-500' : 'border-gray-300'}
                  `}>
                    {isSelected && <div className="w-3 h-3 bg-white rounded-full" />}
                  </div>
                  <span className="text-gray-900 dark:text-white">{option}</span>
                </div>
                
                {submitted && isCorrectOption && (
                  <CheckCircle size={20} className="text-green-500" />
                )}
                {submitted && isSelected && !isCorrectOption && (
                  <XCircle size={20} className="text-red-500" />
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Submit Button */}
      {!submitted && (
        <button
          onClick={handleSubmit}
          disabled={selectedAnswer === null}
          className="w-full py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
        >
          Submit Answer
        </button>
      )}

      {/* Explanation */}
      {submitted && (
        <div className={`
          mt-4 p-4 rounded-lg border-2
          ${isCorrect 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
            : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          }
        `}>
          <div className="flex items-center gap-2 mb-2">
            {isCorrect ? (
              <>
                <CheckCircle size={20} className="text-green-600" />
                <span className="font-semibold text-green-700 dark:text-green-400">
                  Correct!
                </span>
              </>
            ) : (
              <>
                <XCircle size={20} className="text-red-600" />
                <span className="font-semibold text-red-700 dark:text-red-400">
                  Not quite right
                </span>
              </>
            )}
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300">
            {quiz.explanation}
          </p>
        </div>
      )}
    </div>
  );
};
