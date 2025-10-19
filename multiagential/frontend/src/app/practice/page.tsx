'use client';

import { useState, useEffect, useCallback } from 'react';
import { SessionManager } from '@/lib/session';
import Link from 'next/link';

interface Topic {
  name: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  recommended: boolean;
}

interface Recommendation {
  topic: string;
}

export default function PracticePage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const getDefaultTopics = useCallback((): Topic[] => [
    { name: 'Python Basics', difficulty: 'beginner', recommended: false },
    { name: 'Variables and Data Types', difficulty: 'beginner', recommended: false },
    { name: 'Control Flow', difficulty: 'beginner', recommended: false },
    { name: 'Functions and Modules', difficulty: 'intermediate', recommended: false },
    { name: 'Object-Oriented Programming', difficulty: 'intermediate', recommended: false },
    { name: 'Data Structures', difficulty: 'intermediate', recommended: false },
    { name: 'File Operations', difficulty: 'intermediate', recommended: false },
    { name: 'Error Handling', difficulty: 'intermediate', recommended: false },
    { name: 'Machine Learning Basics', difficulty: 'advanced', recommended: false },
    { name: 'Deep Learning', difficulty: 'advanced', recommended: false },
    { name: 'Web Development with Python', difficulty: 'advanced', recommended: false },
  ], []);

  const loadDefaultTopics = useCallback(() => {
    setTopics(getDefaultTopics());
  }, [getDefaultTopics]);

  const loadRecommendedTopics = useCallback(async () => {
    try {
      const userId = SessionManager.getUserId();
      const response = await fetch('http://localhost:8007/adaptive/recommendations', {
        headers: {
          'x-user-key': userId,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Map recommendations to topics
        const recommendedTopics: Topic[] = data.recommendations?.map((rec: Recommendation) => ({
          name: rec.topic,
          difficulty: 'beginner',
          recommended: true,
        })) || [];

        // Add some additional practice topics
        const allTopics = [
          ...recommendedTopics,
          ...getDefaultTopics().filter(t =>
            !recommendedTopics.some(r => r.name === t.name)
          ),
        ];

        setTopics(allTopics);
      } else {
        loadDefaultTopics();
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
      loadDefaultTopics();
    }
  }, [getDefaultTopics, loadDefaultTopics]);

  const checkProfileAndLoadTopics = useCallback(async () => {
    const userId = SessionManager.getUserId();
    const onboardingStatus = SessionManager.getOnboardingStatus();
    const profileExists = onboardingStatus === userId;

    if (profileExists) {
      await loadRecommendedTopics();
    } else {
      // Load default topics if no profile
      loadDefaultTopics();
    }
    setLoading(false);
  }, [loadDefaultTopics, loadRecommendedTopics]);

  useEffect(() => {
    checkProfileAndLoadTopics();
  }, [checkProfileAndLoadTopics]);

  const filteredTopics = topics.filter(topic =>
    topic.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const recommendedTopics = filteredTopics.filter((t: Topic) => t.recommended);
  const otherTopics = filteredTopics.filter((t: Topic) => !t.recommended);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-6xl mx-auto py-12 px-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading practice topics...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />

      <main className="max-w-6xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Practice & Quizzes
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Test your knowledge with adaptive quizzes and practice sessions
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative">
            <input
              type="text"
              placeholder="Search topics..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 pl-12 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white"
            />
            <span className="absolute left-4 top-3.5 text-gray-400">🔍</span>
          </div>
        </div>

        {/* Recommended Topics */}
        {recommendedTopics.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <span>⭐</span>
              Recommended for You
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendedTopics.map((topic, index) => (
                <TopicCard key={index} topic={topic} />
              ))}
            </div>
          </div>
        )}

        {/* All Topics */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            All Topics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {otherTopics.map((topic, index) => (
              <TopicCard key={index} topic={topic} />
            ))}
          </div>
        </div>

        {filteredTopics.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              No topics found matching &quot;{searchTerm}&quot;
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

function TopicCard({ topic }: { topic: Topic }) {
  const difficultyColors = {
    beginner: 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300',
    intermediate: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
    advanced: 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow">
      {/* Topic Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex-1">
            {topic.name}
          </h3>
          {topic.recommended && (
            <span className="text-yellow-500 ml-2">⭐</span>
          )}
        </div>
        <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${difficultyColors[topic.difficulty]}`}>
          {topic.difficulty.charAt(0).toUpperCase() + topic.difficulty.slice(1)}
        </span>
      </div>

      {/* Action Buttons */}
      <div className="space-y-2">
        <Link
          href={`/adaptive/content?topic=${encodeURIComponent(topic.name)}`}
          className="block w-full px-4 py-2 bg-blue-600 text-white text-center rounded-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          📚 Study Topic
        </Link>
        <Link
          href={`/practice/quiz?topic=${encodeURIComponent(topic.name)}`}
          className="block w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white text-center rounded-lg font-semibold hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          🎯 Take Quiz
        </Link>
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
