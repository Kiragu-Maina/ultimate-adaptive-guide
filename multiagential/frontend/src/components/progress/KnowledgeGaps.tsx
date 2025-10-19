'use client';

import { useState, useEffect } from 'react';
import { SessionManager } from '@/lib/session';
import Link from 'next/link';

interface TopicMastery {
  topic: string;
  mastery_score: number;
  quizzes_taken: number;
  last_practiced?: string;
}

interface MasteryData {
  mastery: TopicMastery[];
  knowledge_gaps?: string[];
}

export default function KnowledgeGaps() {
  const [gaps, setGaps] = useState<TopicMastery[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadKnowledgeGaps();
  }, []);

  const loadKnowledgeGaps = async () => {
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

      const data: MasteryData = await response.json();

      // Filter topics with mastery < 50%
      const lowMasteryTopics = data.mastery?.filter(
        topic => topic.mastery_score < 50
      ) || [];

      // Sort by lowest mastery first
      lowMasteryTopics.sort((a, b) => a.mastery_score - b.mastery_score);

      setGaps(lowMasteryTopics);
    } catch (err) {
      setError('Failed to load knowledge gaps');
      console.error('Knowledge gaps load error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">🎯</span>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Knowledge Gaps
        </h2>
      </div>

      {error ? (
        <div className="text-center py-6">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      ) : gaps.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-5xl mb-3">✨</div>
          <p className="text-gray-900 dark:text-white font-semibold mb-2">
            No Knowledge Gaps Detected!
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            You&apos;re maintaining strong mastery across all practiced topics
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Topics where you need more practice (mastery below 50%)
          </p>

          {gaps.map((gap, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {gap.topic}
                  </h3>
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded ${
                    gap.mastery_score < 30
                      ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                      : 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300'
                  }`}>
                    {Math.round(gap.mastery_score)}% mastery
                  </span>
                </div>

                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>
                    {gap.quizzes_taken} quiz{gap.quizzes_taken !== 1 ? 'zes' : ''} taken
                  </span>
                  {gap.last_practiced && (
                    <span>
                      Last practiced: {new Date(gap.last_practiced).toLocaleDateString()}
                    </span>
                  )}
                </div>

                {/* Progress bar */}
                <div className="mt-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      gap.mastery_score < 30
                        ? 'bg-red-500'
                        : 'bg-orange-500'
                    }`}
                    style={{ width: `${gap.mastery_score}%` }}
                  ></div>
                </div>
              </div>

              <div className="ml-4 flex flex-col gap-2">
                <Link
                  href={`/adaptive/content?topic=${encodeURIComponent(gap.topic)}`}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors text-center whitespace-nowrap"
                >
                  Study Topic
                </Link>
                <Link
                  href={`/practice/quiz?topic=${encodeURIComponent(gap.topic)}`}
                  className="px-4 py-2 bg-orange-600 text-white text-sm font-semibold rounded-lg hover:bg-orange-700 transition-colors text-center whitespace-nowrap"
                >
                  Practice Quiz
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {gaps.length > 0 && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            💡 Tip: Focus on your weakest topics first to build a strong foundation
          </p>
        </div>
      )}
    </div>
  );
}
