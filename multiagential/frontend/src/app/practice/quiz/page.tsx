'use client';

import { useState, useEffect, Suspense, useCallback } from 'react';
import { SessionManager } from '@/lib/session';
import { getApiUrl } from '@/lib/config';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

interface QuizQuestion {
  question: string;
  options: string[];
}

interface QuizData {
  quiz_id: string;
  topic: string;
  difficulty: string;
  questions: QuizQuestion[];
  num_questions: number;
}

interface PerformanceAnalysis {
  mastery_updates: { [key: string]: { mastery_score: number; skill_level: string; trend: string; attempts: number; confidence: number; } };
  difficulty_recommendations: { [key: string]: string };
  path_adjustments: { skip_topics: string[]; review_topics: string[]; add_topics: string[]; reasoning: string; };
  knowledge_gaps: string[];
  strengths: string[];
  performance_summary: string;
  confidence: number;
}

interface QuizResult {
  score: number;
  total: number;
  score_percent: number;
  results: Array<{
    question: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
  }>;
  mastery_update?: {
    topic: string;
    old_score: number;
    new_score: number;
  };
  performance_analysis?: PerformanceAnalysis;
  feedback?: string;
}

function QuizPageContent() {
  const searchParams = useSearchParams();
  const topic = searchParams?.get('topic') || '';

  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [userAnswers, setUserAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);

  const loadQuiz = useCallback(async () => {
    try {
      const userId = SessionManager.getUserId();
      const response = await fetch(
        `${getApiUrl()}/adaptive/quiz?topic=${encodeURIComponent(topic)}&num_questions=5`,
        {
          headers: {
            'x-user-key': userId,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to generate quiz');
      }

      const data: QuizData = await response.json();
      setQuizData(data);
      setUserAnswers(new Array(data.num_questions).fill(''));
    } catch (err) {
      setError('Failed to load quiz. Please try again.');
      console.error('Quiz load error:', err);
    } finally {
      setLoading(false);
    }
  }, [topic]);

  useEffect(() => {
    if (topic) {
      loadQuiz();
    } else {
      setError('No topic specified');
      setLoading(false);
    }
  }, [topic, loadQuiz]);

  const handleAnswerSelect = (questionIndex: number, answer: string) => {
    const newAnswers = [...userAnswers];
    newAnswers[questionIndex] = answer;
    setUserAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    if (!quizData) return;

    // Check if all questions are answered
    const unanswered = userAnswers.filter(a => !a).length;
    if (unanswered > 0) {
      setError(`Please answer all questions (${unanswered} unanswered)`);
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const userId = SessionManager.getUserId();
      const response = await fetch(`${getApiUrl()}/adaptive/quiz/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-key': userId,
        },
        body: JSON.stringify({
          quiz_id: quizData.quiz_id,
          answers: userAnswers,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit quiz');
      }

      const result: QuizResult = await response.json();
      setQuizResult(result);
    } catch (err) {
      setError('Failed to submit quiz. Please try again.');
      console.error('Quiz submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-4xl mx-auto py-12 px-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Generating your quiz...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error && !quizData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-4xl mx-auto py-12 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Unable to Load Quiz
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
            <Link
              href="/practice"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Back to Practice
            </Link>
          </div>
        </main>
      </div>
    );
  }

  // Show results if quiz is submitted
  if (quizResult) {
    return <ResultsView result={quizResult} topic={topic} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />

      <main className="max-w-4xl mx-auto py-8 px-4">
        {/* Quiz Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                {quizData?.topic}
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {quizData?.num_questions} questions • {quizData?.difficulty} difficulty
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600 dark:text-gray-400">Progress</div>
              <div className="text-2xl font-bold text-blue-600">
                {userAnswers.filter(a => a).length}/{quizData?.num_questions}
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${((userAnswers.filter(a => a).length) / (quizData?.num_questions || 1)) * 100}%`,
              }}
            ></div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Questions */}
        <div className="space-y-6 mb-8">
          {quizData?.questions.map((q, index) => (
            <QuestionCard
              key={index}
              question={q}
              questionNumber={index + 1}
              selectedAnswer={userAnswers[index]}
              onAnswerSelect={(answer) => handleAnswerSelect(index, answer)}
            />
          ))}
        </div>

        {/* Submit Button */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <Link
              href="/practice"
              className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </Link>
            <button
              onClick={handleSubmit}
              disabled={submitting || userAnswers.filter(a => a).length !== quizData?.num_questions}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Submitting...' : 'Submit Quiz'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

function QuestionCard({
  question,
  questionNumber,
  selectedAnswer,
  onAnswerSelect,
}: {
  question: QuizQuestion;
  questionNumber: number;
  selectedAnswer: string;
  onAnswerSelect: (answer: string) => void;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded-full flex items-center justify-center font-bold">
          {questionNumber}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {question.question}
          </h3>
          <div className="space-y-3">
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => onAnswerSelect(option)}
                className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all ${
                  selectedAnswer === option
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100'
                    : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedAnswer === option
                        ? 'border-blue-600 bg-blue-600'
                        : 'border-gray-400 dark:border-gray-600'
                    }`}
                  >
                    {selectedAnswer === option && (
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    )}
                  </div>
                  <span>{option}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ResultsView({ result, topic }: { result: QuizResult; topic: string }) {
  const scorePercent = result.score_percent;
  const passed = scorePercent >= 70;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />

      <main className="max-w-4xl mx-auto py-8 px-4">
        {/* Results Header */}
        <div className={`rounded-lg shadow-xl p-8 mb-8 ${
          passed
            ? 'bg-gradient-to-r from-green-600 to-green-700'
            : 'bg-gradient-to-r from-orange-600 to-orange-700'
        }`}>
          <div className="text-center text-white">
            <div className="text-6xl mb-4">{passed ? '🎉' : '💪'}</div>
            <h1 className="text-3xl font-bold mb-2">
              {passed ? 'Great Job!' : 'Keep Practicing!'}
            </h1>
            <p className="text-xl mb-6">
              You scored {result.score}/{result.total} ({Math.round(scorePercent)}%)
            </p>
            <div className="max-w-md mx-auto bg-white/20 backdrop-blur rounded-full h-4 mb-4">
              <div
                className="bg-white h-4 rounded-full transition-all duration-1000"
                style={{ width: `${scorePercent}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Mastery Update */}
        {result.mastery_update && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              📊 Mastery Update
            </h2>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">{result.mastery_update.topic}</span>
              <div className="flex items-center gap-4">
                <span className="text-gray-500 dark:text-gray-400">
                  {Math.round(result.mastery_update.old_score)}%
                </span>
                <span className="text-blue-600 dark:text-blue-400">→</span>
                <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {Math.round(result.mastery_update.new_score)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Question Review */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Review Your Answers
          </h2>
          <div className="space-y-6">
            {result.results.map((r, index) => (
              <div key={index} className="border-l-4 pl-4 py-2" style={{
                borderColor: r.is_correct ? '#10b981' : '#f59e0b'
              }}>
                <div className="flex items-start gap-3 mb-2">
                  <span className={`text-2xl ${r.is_correct ? 'text-green-500' : 'text-orange-500'}`}>
                    {r.is_correct ? '✓' : '✗'}
                  </span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white mb-2">
                      {r.question}
                    </p>
                    <div className="space-y-1 text-sm">
                      <p className="text-gray-600 dark:text-gray-400">
                        Your answer: <span className={r.is_correct ? 'text-green-600 dark:text-green-400 font-semibold' : 'text-orange-600 dark:text-orange-400'}>{r.user_answer}</span>
                      </p>
                      {!r.is_correct && (
                        <p className="text-gray-600 dark:text-gray-400">
                          Correct answer: <span className="text-green-600 dark:text-green-400 font-semibold">{r.correct_answer}</span>
                        </p>
                      )}
                      {r.explanation && (
                        <p className="text-gray-600 dark:text-gray-400 mt-2 italic">
                          {r.explanation}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Link
            href={`/practice/quiz?topic=${encodeURIComponent(topic)}`}
            className="flex-1 px-6 py-3 bg-blue-600 text-white text-center rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Try Again
          </Link>
          <Link
            href="/practice"
            className="flex-1 px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-center rounded-lg font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Back to Practice
          </Link>
          <Link
            href="/progress"
            className="flex-1 px-6 py-3 bg-green-600 text-white text-center rounded-lg font-semibold hover:bg-green-700 transition-colors"
          >
            View Progress
          </Link>
        </div>
      </main>
    </div>
  );
}

function Navigation() {
  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex space-x-8">
          <Link
            href="/"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">🏠</span>
            Home
          </Link>
          <Link
            href="/practice"
            className="py-4 px-1 border-b-2 border-blue-600 font-medium text-sm text-blue-600 dark:text-blue-400"
          >
            <span className="mr-2">💪</span>
            Practice
          </Link>
          <Link
            href="/progress"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">📊</span>
            Progress
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default function QuizPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading quiz...</p>
        </div>
      </div>
    }>
      <QuizPageContent />
    </Suspense>
  );
}
