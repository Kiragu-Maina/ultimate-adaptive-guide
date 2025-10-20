'use client';

import { useState, useEffect } from 'react';
import { SessionManager } from '@/lib/session';
import { getApiUrl } from '@/lib/config';

interface TopicMastery {
  topic: string;
  mastery_score: number;
  quizzes_taken: number;
  last_practiced?: string;
}

interface MasteryData {
  mastery: TopicMastery[];
  overall_skill_level: string;
}

export default function LearningInsights() {
  const [insights, setInsights] = useState<{
    totalQuizzes: number;
    avgMastery: number;
    topicsLearned: number;
    learningVelocity: string;
    strongestTopic: string | null;
    recentActivity: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    try {
      const userId = SessionManager.getUserId();
      const response = await fetch(`${getApiUrl()}/adaptive/mastery`, {
        headers: {
          'x-user-key': userId,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load mastery data');
      }

      const data: MasteryData = await response.json();

      if (data.mastery && data.mastery.length > 0) {
        // Calculate insights
        const totalQuizzes = data.mastery.reduce((sum, t) => sum + t.quizzes_taken, 0);
        const avgMastery = data.mastery.reduce((sum, t) => sum + t.mastery_score, 0) / data.mastery.length;
        const topicsLearned = data.mastery.length;

        // Find strongest topic
        const strongest = data.mastery.reduce((prev, current) =>
          current.mastery_score > prev.mastery_score ? current : prev
        );

        // Calculate learning velocity (quizzes per topic)
        const velocity = totalQuizzes / topicsLearned;
        let velocityLabel = 'Steady';
        if (velocity > 3) velocityLabel = 'Fast';
        else if (velocity < 1.5) velocityLabel = 'Slow';

        // Recent activity
        const hasRecentPractice = data.mastery.some(t =>
          t.last_practiced &&
          (new Date().getTime() - new Date(t.last_practiced).getTime()) < 7 * 24 * 60 * 60 * 1000
        );

        setInsights({
          totalQuizzes,
          avgMastery: Math.round(avgMastery),
          topicsLearned,
          learningVelocity: velocityLabel,
          strongestTopic: strongest.topic,
          recentActivity: hasRecentPractice ? 'Active' : 'Inactive',
        });
      } else {
        setInsights(null);
      }
    } catch (err) {
      console.error('Insights load error:', err);
      setInsights(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">💡</span>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Learning Insights
          </h2>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-600 dark:text-gray-400">
            Complete quizzes to see your learning insights
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-2xl">💡</span>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Learning Insights
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Total Quizzes */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">📝</span>
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase">
              Total
            </span>
          </div>
          <div className="text-3xl font-bold text-blue-700 dark:text-blue-300">
            {insights.totalQuizzes}
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400 mt-1">
            Quizzes Taken
          </div>
        </div>

        {/* Average Mastery */}
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">📊</span>
            <span className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase">
              Average
            </span>
          </div>
          <div className="text-3xl font-bold text-green-700 dark:text-green-300">
            {insights.avgMastery}%
          </div>
          <div className="text-sm text-green-600 dark:text-green-400 mt-1">
            Mastery Score
          </div>
        </div>

        {/* Topics Learned */}
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">📚</span>
            <span className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase">
              Count
            </span>
          </div>
          <div className="text-3xl font-bold text-orange-700 dark:text-orange-300">
            {insights.topicsLearned}
          </div>
          <div className="text-sm text-orange-600 dark:text-orange-400 mt-1">
            Topics Practiced
          </div>
        </div>

        {/* Learning Velocity */}
        <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">⚡</span>
            <span className={`text-xs font-semibold uppercase ${
              insights.learningVelocity === 'Fast'
                ? 'text-green-600 dark:text-green-400'
                : insights.learningVelocity === 'Slow'
                ? 'text-orange-600 dark:text-orange-400'
                : 'text-blue-600 dark:text-blue-400'
            }`}>
              {insights.learningVelocity}
            </span>
          </div>
          <div className="text-xl font-bold text-gray-900 dark:text-white">
            {insights.learningVelocity} Pace
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Learning Velocity
          </div>
        </div>

        {/* Strongest Topic */}
        {insights.strongestTopic && (
          <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">🏆</span>
              <span className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
                Best
              </span>
            </div>
            <div className="text-sm font-bold text-gray-900 dark:text-white line-clamp-2">
              {insights.strongestTopic}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Strongest Topic
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🔥</span>
            <span className={`text-xs font-semibold uppercase ${
              insights.recentActivity === 'Active'
                ? 'text-green-600 dark:text-green-400'
                : 'text-gray-600 dark:text-gray-400'
            }`}>
              {insights.recentActivity}
            </span>
          </div>
          <div className="text-xl font-bold text-gray-900 dark:text-white">
            {insights.recentActivity === 'Active' ? '7 Days' : 'None'}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Recent Activity
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          {insights.recentActivity === 'Active'
            ? `Great work! You're maintaining ${insights.avgMastery}% average mastery across ${insights.topicsLearned} topics.`
            : `You're doing well with ${insights.avgMastery}% average mastery. Keep practicing to stay on track!`}
        </p>
      </div>
    </div>
  );
}
