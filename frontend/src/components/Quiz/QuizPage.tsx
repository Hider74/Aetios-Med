import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle, XCircle, PlayCircle, RefreshCw } from 'lucide-react';
import api from '../../services/api';
import { SAQInput } from './SAQInput.tsx';
import type { QuizQuestion, SAQQuestion, SAQResult } from '../../types/study';

interface QuizResult {
  correct: number;
  total: number;
  percentage: number;
}

export const QuizPage: React.FC = () => {
  const [topicInput, setTopicInput] = useState('');
  const [suggestedTopics, setSuggestedTopics] = useState<string[]>([]);
  const [questions, setQuestions] = useState<Array<QuizQuestion | SAQQuestion>>([]);
  const [answers, setAnswers] = useState<Array<number | null>>([]);
  const [saqAnswers, setSaqAnswers] = useState<string[]>([]);
  const [saqResults, setSaqResults] = useState<Record<number, SAQResult>>({});
  const [quizId, setQuizId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [questionType, setQuestionType] = useState<'sba' | 'saq'>('sba');
  const [saqError, setSaqError] = useState<string | null>(null);

  useEffect(() => {
    setQuestions([]);
    setAnswers([]);
    setSaqAnswers([]);
    setSaqResults({});
    setShowResults(false);
    setQuizId(null);
    setSaqError(null);
  }, [questionType]);

  useEffect(() => {
    const loadSuggestedTopics = async () => {
      try {
        const weakTopics = await api.getWeakTopics(0.3);
        const weakIds = weakTopics.map((t: any) => t.topic_id).filter(Boolean);
        if (weakIds.length > 0) {
          setSuggestedTopics(weakIds.slice(0, 5));
          return;
        }

        const graph = await api.getGraph();
        const fallback = graph.nodes.slice(0, 5).map((n) => n.id);
        setSuggestedTopics(fallback);
      } catch (error) {
        setSuggestedTopics([]);
      }
    };

    loadSuggestedTopics();
  }, []);

  const selectedTopics = useMemo(() => {
    const manualTopics = topicInput
      .split(',')
      .map((topic) => topic.trim())
      .filter((topic) => topic.length > 0);

    return manualTopics.length > 0 ? manualTopics : suggestedTopics;
  }, [topicInput, suggestedTopics]);

  const startQuiz = async () => {
    if (selectedTopics.length === 0) return;
    setIsLoading(true);
    setShowResults(false);
    setSaqResults({});
    setSaqError(null);

    try {
      const quizResponse = await api.generateQuiz(selectedTopics, 5, questionType);
      setQuizId(quizResponse.quizId);
      setQuestions(quizResponse.questions);
      setAnswers(new Array(quizResponse.questions.length).fill(null));
      setSaqAnswers(new Array(quizResponse.questions.length).fill(''));
    } catch (error) {
      console.error('Failed to generate quiz:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const submitQuiz = async () => {
    if (questions.length === 0) return;
    setShowResults(true);

    if (questionType === 'saq') {
      return;
    }

    for (let i = 0; i < questions.length; i += 1) {
      const question = questions[i];
      const answer = answers[i];
      if (answer === null) continue;

      const correct = answer === (question as QuizQuestion).correctAnswer;
      try {
        await api.logQuizResult((question as QuizQuestion).topic, correct, question.question);
      } catch (error) {
        console.warn('Failed to log quiz result:', error);
      }
    }
  };

  const submitAllSaq = async () => {
    if (!quizId || questions.length === 0) return;
    if (saqAnswers.some((answer) => !answer.trim())) {
      setSaqError('Please answer all SAQs before submitting.');
      return;
    }

    setIsSubmitting(true);
    setSaqError(null);

    try {
      const results = await Promise.all(
        questions.map((question, idx) =>
          api.submitSAQAnswer(
            quizId,
            `q${idx}`,
            (question as SAQQuestion).topic_id,
            saqAnswers[idx]
          )
        )
      );

      const resultMap: Record<number, SAQResult> = {};
      results.forEach((result, idx) => {
        resultMap[idx] = result;
      });

      setSaqResults(resultMap);
      setShowResults(true);
    } catch (error) {
      console.error('Failed to submit SAQ answers:', error);
      setSaqError('Failed to submit SAQ answers. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const result: QuizResult | null = useMemo(() => {
    if (!showResults || questions.length === 0) return null;
    if (questionType === 'saq') {
      const results = Object.values(saqResults);
      const total = results.reduce((sum, r) => sum + r.max_score, 0);
      const correct = results.reduce((sum, r) => sum + r.score, 0);
      return {
        correct,
        total,
        percentage: total > 0 ? (correct / total) * 100 : 0,
      };
    }

    const correct = answers.filter((answer, idx) => answer === (questions[idx] as QuizQuestion)?.correctAnswer).length;
    const total = questions.length;
    return {
      correct,
      total,
      percentage: total > 0 ? (correct / total) * 100 : 0,
    };
  }, [showResults, answers, questions, questionType, saqResults]);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Quiz Builder
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Generate SBA or SAQ questions. Scoring appears after you submit the full quiz.
        </p>

        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setQuestionType('sba')}
              className={`px-4 py-2 rounded-lg border text-sm font-semibold transition-colors ${
                questionType === 'sba'
                  ? 'border-purple-500 bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-200'
                  : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300'
              }`}
            >
              SBA (Multiple Choice)
            </button>
            <button
              onClick={() => setQuestionType('saq')}
              className={`px-4 py-2 rounded-lg border text-sm font-semibold transition-colors ${
                questionType === 'saq'
                  ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-200'
                  : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300'
              }`}
            >
              SAQ (Short Answer)
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Topics (comma-separated)
            </label>
            <input
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              placeholder={suggestedTopics.length > 0 ? suggestedTopics.join(', ') : 'cardiology, renal, endocrinology'}
              className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Leave blank to use your weakest topics.
            </div>
          </div>

          <button
            onClick={startQuiz}
            disabled={isLoading || selectedTopics.length === 0}
            className="inline-flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg shadow-md hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? <RefreshCw size={18} className="animate-spin" /> : <PlayCircle size={18} />}
            Generate Quiz
          </button>
        </div>
      </div>

      {questions.length > 0 && (
        <div className="space-y-6">
          {questions.map((question, idx) => (
            <div
              key={`${question.question}-${idx}`}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700"
            >
              {questionType === 'saq' ? (
                <SAQInput
                  question={question as SAQQuestion}
                  quizId={quizId || 'quiz'}
                  questionId={`q${idx}`}
                  value={saqAnswers[idx]}
                  onChange={(value: string) => {
                    setSaqAnswers((prev) => {
                      const next = [...prev];
                      next[idx] = value;
                      return next;
                    });
                  }}
                  result={saqResults[idx]}
                  showSubmit={false}
                  isSubmitting={isSubmitting}
                  onSubmit={async () => {
                    throw new Error('Submit all is required.');
                  }}
                />
              ) : (
                <>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                    Q{idx + 1} • {(question as QuizQuestion).topic} • {(question as QuizQuestion).difficulty}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {question.question}
                  </h3>
                  <div className="space-y-2">
                    {(question as QuizQuestion).options.map((option, optionIndex) => {
                      const isSelected = answers[idx] === optionIndex;
                      const isCorrect = showResults && optionIndex === (question as QuizQuestion).correctAnswer;
                      const isWrong = showResults && isSelected && !isCorrect;

                      return (
                        <button
                          key={optionIndex}
                          onClick={() => {
                            if (showResults) return;
                            setAnswers((prev) => {
                              const next = [...prev];
                              next[idx] = optionIndex;
                              return next;
                            });
                          }}
                          className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                            isCorrect
                              ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                              : isWrong
                              ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                              : isSelected
                              ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-purple-400'
                          }`}
                        >
                          {option}
                        </button>
                      );
                    })}
                  </div>

                  {showResults && (
                    <div className="mt-4 p-4 rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/10">
                      <div className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-1">
                        Explanation
                      </div>
                      <p className="text-sm text-blue-900 dark:text-blue-200">
                        {(question as QuizQuestion).explanation}
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}

          {!showResults && questionType === 'sba' && (
            <button
              onClick={submitQuiz}
              className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              Submit Quiz
            </button>
          )}

          {!showResults && questionType === 'saq' && (
            <div className="space-y-3">
              {saqError && (
                <div className="text-sm text-red-600 dark:text-red-400">
                  {saqError}
                </div>
              )}
              <button
                onClick={submitAllSaq}
                disabled={isSubmitting}
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
              >
                {isSubmitting ? 'Submitting...' : 'Submit All SAQs'}
              </button>
            </div>
          )}

          {showResults && result && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                {result.percentage >= 70 ? (
                  <CheckCircle size={28} className="text-green-500" />
                ) : (
                  <XCircle size={28} className="text-red-500" />
                )}
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {result.correct} / {result.total}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Score: {result.percentage.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
