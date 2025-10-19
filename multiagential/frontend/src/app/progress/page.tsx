'use client';

import { useState, useEffect, useCallback } from 'react';
import { SessionManager } from '@/lib/session';
import Link from 'next/link';
import MasteryRadar from '@/components/progress/MasteryRadar';
import KnowledgeGaps from '@/components/progress/KnowledgeGaps';
import LearningInsights from '@/components/progress/LearningInsights';

interface TopicMastery {
  topic: string;
  mastery_score: number;
  quizzes_taken: number;
  last_practiced?: string;
}

interface MasteryData {
  mastery: TopicMastery[];
  overall_skill_level: string;
  knowledge_gaps?: string[];
  strengths?: string[];
  message?: string;
}

export default function ProgressPage() {
  const [masteryData, setMasteryData] = useState<MasteryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadMasteryData = useCallback(async () => {
    try {
      const userId = SessionManager.getUserId();
      const response = await fetch('http://localhost:8007/adaptive/mastery', {
        headers: {
          'x-user-key': userId,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load mastery data');
      }

      const data = await response.json();
      setMasteryData(data);
    } catch (err) {
      setError('Failed to load progress data. Please try again.');
      console.error('Progress load error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkProfileAndLoadProgress = useCallback(async () => {
    const userId = SessionManager.getUserId();
    const onboardingStatus = SessionManager.getOnboardingStatus();
    const profileExists = onboardingStatus === userId;

    if (!profileExists) {
      setLoading(false);
      return;
    }

    await loadMasteryData();
  }, [loadMasteryData]);

  useEffect(() => {
    checkProfileAndLoadProgress();
  }, [checkProfileAndLoadProgress]);


  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-6xl mx-auto py-12 px-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading your progress...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!masteryData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-6xl mx-auto py-12 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              No Progress Data Yet
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Complete onboarding and start learning to track your progress.
            </p>
            <Link
              href="/adaptive"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Start Learning
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const hasData = masteryData && masteryData.mastery && masteryData.mastery.length > 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />

      <main className="max-w-6xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Learning Progress
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Track your mastery scores and identify areas for improvement
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Overall Skill Level */}
        {masteryData && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                  Overall Skill Level
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Based on performance across all topics
                </p>
              </div>
              <div className="text-right">
                <div className="inline-block px-6 py-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <span className="text-2xl font-bold text-blue-700 dark:text-blue-300 capitalize">
                    {masteryData.overall_skill_level || 'Beginner'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Learning Insights */}
        <div className="mb-8">
          <LearningInsights />
        </div>

        {/* Mastery Radar Chart */}
        <div className="mb-8">
          <MasteryRadar />
        </div>

        {/* Knowledge Gaps */}
        <div className="mb-8">
          <KnowledgeGaps />
        </div>

        {/* Strengths and Knowledge Gaps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Strengths */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <span>💪</span>
              Your Strengths
            </h2>
            {masteryData?.strengths && masteryData.strengths.length > 0 ? (
              <ul className="space-y-2">
                {masteryData.strengths.map((strength, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-gray-700 dark:text-gray-300"
                  >
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">
                Complete quizzes to discover your strengths
              </p>
            )}
          </div>

          {/* Knowledge Gaps */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <span>🎯</span>
              Areas to Improve
            </h2>
            {masteryData?.knowledge_gaps && masteryData.knowledge_gaps.length > 0 ? (
              <ul className="space-y-2">
                {masteryData.knowledge_gaps.map((gap, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-gray-700 dark:text-gray-300"
                  >
                    <span className="text-orange-500 mt-0.5">→</span>
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">
                Your knowledge gaps will appear here as you practice
              </p>
            )}
          </div>
        </div>

        {/* Mastery Scores */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Topic Mastery Scores
          </h2>

          {hasData ? (
            <div className="space-y-4">
              {masteryData.mastery.map((topic, index) => (
                <MasteryBar key={index} topic={topic} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📈</div>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {masteryData?.message || 'No mastery data yet'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mb-6">
                Take quizzes to start tracking your progress
              </p>
              <Link
                href="/practice"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Start Practicing
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function MasteryBar({ topic }: { topic: TopicMastery }) {
  const getMasteryColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const getMasteryLabel = (score: number) => {
    if (score >= 80) return 'Mastered';
    if (score >= 60) return 'Proficient';
    if (score >= 40) return 'Learning';
    return 'Beginner';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {topic.topic}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {topic.quizzes_taken} quiz{topic.quizzes_taken !== 1 ? 'zes' : ''} taken
            {topic.last_practiced && ` • Last practiced ${new Date(topic.last_practiced).toLocaleDateString()}`}
          </p>
        </div>
        <div className="text-right ml-4">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {Math.round(topic.mastery_score)}%
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            {getMasteryLabel(topic.mastery_score)}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div
          className={`${getMasteryColor(topic.mastery_score)} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${topic.mastery_score}%` }}
        ></div>
      </div>
    </div>
  );
}

function Navigation() {
  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex space-x-8">
          <Link
            href="/"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">🏠</span>
            Home
          </Link>
          <Link
            href="/journey"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">🗺️</span>
            My Journey
          </Link>
          <Link
            href="/practice"
            className="py-4 px-1 border-b-2 border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white font-medium text-sm transition-colors"
          >
            <span className="mr-2">💪</span>
            Practice
          </Link>
          <Link
            href="/progress"
            className="py-4 px-1 border-b-2 border-blue-600 font-medium text-sm text-blue-600 dark:text-blue-400"
          >
            <span className="mr-2">📊</span>
            Progress
          </Link>
        </div>
      </div>
    </nav>
  );
}
