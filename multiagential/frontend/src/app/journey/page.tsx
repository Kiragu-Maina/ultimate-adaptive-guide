'use client';

import { useState, useEffect, useCallback } from 'react';
import { SessionManager } from '@/lib/session';
import Link from 'next/link';

interface JourneyMilestone {
  topic: string;
  description: string;
  estimated_hours: number;
  prerequisites: string[];
  status?: 'completed' | 'current' | 'upcoming';
}

export default function JourneyPage() {
  const [journey, setJourney] = useState<JourneyMilestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hasProfile, setHasProfile] = useState(false);

  const loadJourney = useCallback(async () => {
    try {
      const userId = SessionManager.getUserId();
      const response = await fetch('http://localhost:8007/adaptive/journey', {
        headers: {
          'x-user-key': userId,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load journey');
      }

      const data = await response.json();

      // Add status to milestones (first is current, rest are upcoming)
      const milestonesWithStatus = data.journey.map((milestone: JourneyMilestone, index: number) => ({
        ...milestone,
        status: index === 0 ? 'current' : 'upcoming',
      }));

      setJourney(milestonesWithStatus);
    } catch (err) {
      setError('Failed to load your learning journey. Please try again.');
      console.error('Journey load error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkProfileAndLoadJourney = useCallback(async () => {
    const userId = SessionManager.getUserId();
    const onboardingStatus = SessionManager.getOnboardingStatus();
    const profileExists = onboardingStatus === userId;
    setHasProfile(profileExists);

    if (!profileExists) {
      setLoading(false);
      return;
    }

    await loadJourney();
  }, [loadJourney]);

  useEffect(() => {
    checkProfileAndLoadJourney();
  }, [checkProfileAndLoadJourney]);

  const getProgressPercentage = () => {
    const completed = journey.filter(m => m.status === 'completed').length;
    return journey.length > 0 ? Math.round((completed / journey.length) * 100) : 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-6xl mx-auto py-12 px-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading your journey...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!hasProfile) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-6xl mx-auto py-12 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">🗺️</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              No Learning Journey Yet
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Complete onboarding to get your personalized learning path created by AI agents.
            </p>
            <Link
              href="/adaptive"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Start Onboarding
            </Link>
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
            Your Learning Journey
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Personalized path designed by the Journey Architect Agent
          </p>
        </div>

        {/* Progress Overview */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Overall Progress
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {journey.length} topics in your journey
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600">{getProgressPercentage()}%</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Complete</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Journey Milestones */}
        <div className="space-y-4">
          {journey.map((milestone, index) => (
            <MilestoneCard
              key={index}
              milestone={milestone}
              index={index}
            />
          ))}
        </div>

        {journey.length === 0 && !error && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              No milestones in your journey yet. Try refreshing or completing onboarding again.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

function MilestoneCard({ milestone, index }: { milestone: JourneyMilestone; index: number }) {
  const isCurrent = milestone.status === 'current';
  const isCompleted = milestone.status === 'completed';
  const isUpcoming = milestone.status === 'upcoming';

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 transition-all ${
        isCurrent
          ? 'border-blue-600 ring-2 ring-blue-200 dark:ring-blue-800'
          : isCompleted
          ? 'border-green-500 opacity-75'
          : 'border-gray-300 dark:border-gray-700'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Status Badge */}
          <div className="flex items-center gap-3 mb-3">
            <div
              className={`flex items-center justify-center w-8 h-8 rounded-full font-semibold ${
                isCurrent
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
                  : isCompleted
                  ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}
            >
              {isCompleted ? '✓' : index + 1}
            </div>

            {isCurrent && (
              <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full">
                Current Milestone
              </span>
            )}
            {isCompleted && (
              <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs font-semibold rounded-full">
                Completed
              </span>
            )}
          </div>

          {/* Topic Title */}
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            {milestone.topic}
          </h3>

          {/* Description */}
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {milestone.description}
          </p>

          {/* Metadata */}
          <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-1">
              <span>⏱️</span>
              <span>{milestone.estimated_hours}h estimated</span>
            </div>
            {milestone.prerequisites.length > 0 && (
              <div className="flex items-center gap-1">
                <span>📋</span>
                <span>{milestone.prerequisites.length} prerequisites</span>
              </div>
            )}
          </div>

          {/* Prerequisites */}
          {milestone.prerequisites.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                Prerequisites:
              </p>
              <div className="flex flex-wrap gap-2">
                {milestone.prerequisites.map((prereq, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                  >
                    {prereq}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="ml-4">
          {isCurrent && (
            <Link
              href={`/adaptive/content?topic=${encodeURIComponent(milestone.topic)}`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm whitespace-nowrap"
            >
              Start Topic
            </Link>
          )}
          {isUpcoming && (
            <button
              disabled
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-lg font-semibold text-sm cursor-not-allowed"
            >
              Locked
            </button>
          )}
        </div>
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
            className="py-4 px-1 border-b-2 border-blue-600 font-medium text-sm text-blue-600 dark:text-blue-400"
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
